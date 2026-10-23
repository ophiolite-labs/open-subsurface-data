"""Verification: what our tools can establish about a record today.

L1 (origin reachable), L2 (sample files checksummed, licence text captured) and L3 (outlines
derived from the data, E03: see osd.outlines) are established by the network run. L4 (canonical
conversion, E09) comes from a fidelity/1 record a workspace wrote: `apply_fidelity` derives the
`canonical-conversion` check from it against the latest verification's files, keeps the record's
own L1-L3 checks verbatim and recomputes the level with `level_from_checks`. The snapshot the
fidelity names is identity on the check, not a criterion. A network run carries a passed check
forward while the record's hashed files are the same bytes, and declares it "skip" otherwise.

Reachability is one of four closed, exclusive classes, decided on the final response:
  blocked  HTTP 403 or 429, or a challenge page at any status: a separate observation that awards
           no level (OSD-D9); `blocked_since` keeps the first date of an unbroken blocked run
  ok       2xx/3xx with the origin's host
  moved    2xx/3xx on another host: passes, the detail suggests a record update
  dead     anything else: status 0 (DNS, timeout, refused), 401, 404, 410, other 4xx, 5xx;
           timeouts, refused connections and 5xx are retried once first
Sampling policy (which listed files L2 hashes) is tool configuration in verifier/samples.yaml,
keyed by record id, never a record field (OSD-D11). Listings are read by shape (osd.verifier.listings,
E23); a publisher's stated checksum is computed from the same stream beside SHA-256 and compared, and
an export the server truncated is kept apart from `files` as a partial export.

The network is injected twice: a Fetcher probes an origin (first 16 KB), an Opener streams a
body in chunks and raises FetchError. Tests pass fakes, so the required CI check stays offline.
"""

from __future__ import annotations

import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from fnmatch import fnmatchcase
from functools import cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from . import __version__, outlines, paths
from .records import load_outline, load_records
from .verifier.listings import TRUNCATED, Entry, ListingError, parse_listing, read_listing  # noqa: F401 (E07)

SAMPLES_PATH = Path(__file__).parent / "verifier" / "samples.yaml"

LEVELS = ["L0", "L1", "L2", "L3", "L4"]
USER_AGENT = ("open-subsurface-data-verifier/" + __version__
              + " (+https://github.com/ophiolite-labs/open-subsurface-data)")
PROBE_BYTES = 16384
CHUNK = 1 << 20
RUN_BYTE_BUDGET = 2 * 1024**3  # charter: never hash more than 2 GB per run
RECORD_SAMPLE_BYTES = 512 * 1024**2  # E23: one record's share of the run budget (sample + inventory)
COMPARABLE = {"md5": "md5", "sha1": "sha1", "sha256": "sha256"}  # normalised name -> hashlib name
LISTING_BYTES = 32 * 1024**2
LICENCE_BYTES = 8 * 1024**2
LICENCE_TEXT_CHARS = 100_000  # stored with its hash in the results store
PAUSE_S = 2.0
STALE_DAYS = 30
NO_FIDELITY = "no fidelity record (osd verify <id> --fidelity-from)"
COVERAGE = re.compile(r"^(\d+) of (\d+) inputs converted")
CHALLENGE_MARKERS = (b"cf-chl", b"challenge-platform", b"Just a moment...",
                     b"Attention Required! | Cloudflare", b"_Incapsula_Resource")


@dataclass(frozen=True)
class Fetched:
    status: int
    final_url: str
    content_type: str
    elapsed_ms: int
    body: bytes = b""
    error: str = ""  # "", "timeout", "dns" or "connection" when status is 0


class FetchError(Exception):
    def __init__(self, url: str, status: int = 0, error: str = ""):
        self.url, self.status, self.error = url, status, error
        super().__init__(f"HTTP {status} from {url}" if status else f"{error or 'error'} at {url}")


Fetcher = Callable[[str], Fetched]
Opener = Callable[[str], Iterable[bytes]]


# --- network (only used outside tests) ---------------------------------------------------

def _error_kind(e: BaseException) -> str:
    reason = getattr(e, "reason", e)
    if isinstance(reason, socket.gaierror):
        return "dns"
    if isinstance(reason, TimeoutError) or "timed out" in str(reason):
        return "timeout"
    return "connection"


def http_fetch(url: str, timeout: float = 20.0) -> Fetched:
    """GET the first 16 KB; HEAD is refused by too many publishers to be useful."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Range": f"bytes=0-{PROBE_BYTES - 1}"})
    t0 = time.monotonic()
    ms = lambda: int((time.monotonic() - t0) * 1000)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(PROBE_BYTES)
            return Fetched(resp.status, resp.geturl(), resp.headers.get("Content-Type", ""), ms(), body)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(PROBE_BYTES)
        except OSError:
            body = b""
        return Fetched(e.code, url, e.headers.get("Content-Type", "") if e.headers else "", ms(), body)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return Fetched(0, url, "", ms(), error=_error_kind(e))


class _Body:
    """A streamed GET; `content_type` is known once iteration has started (listing reasons name it)."""

    def __init__(self, url: str, timeout: float):
        self.url, self.timeout, self.content_type = url, timeout, ""

    def __iter__(self):
        req = urllib.request.Request(self.url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                self.content_type = resp.headers.get("Content-Type", "")
                while chunk := resp.read(CHUNK):
                    yield chunk
        except urllib.error.HTTPError as e:
            raise FetchError(self.url, e.code) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise FetchError(self.url, 0, _error_kind(e)) from None


def http_open(url: str, timeout: float = 60.0) -> Iterable[bytes]:
    return _Body(url, timeout)


class Pacer:
    """One request at a time (the verifier is sequential) and a pause per host after each."""

    def __init__(self, pause: float = PAUSE_S, clock=time.monotonic, sleep=time.sleep):
        self.pause, self.clock, self.sleep = pause, clock, sleep
        self.last: dict[str, float] = {}

    def wait(self, url: str) -> None:
        host = urlsplit(url).hostname or ""
        if host in self.last:
            delay = self.last[host] + self.pause - self.clock()
            if delay > 0:
                self.sleep(delay)

    def done(self, url: str) -> None:
        self.last[urlsplit(url).hostname or ""] = self.clock()


def paced(fetch: Fetcher, opener: Opener, pacer: Pacer) -> tuple[Fetcher, Opener]:
    def f(url: str) -> Fetched:
        pacer.wait(url)
        try:
            return fetch(url)
        finally:
            pacer.done(url)

    class _Paced:
        def __init__(self, url: str):
            self.url, self.inner = url, None

        @property
        def content_type(self) -> str:
            return getattr(self.inner, "content_type", "")

        def __iter__(self):
            pacer.wait(self.url)
            try:
                self.inner = opener(self.url)
                yield from self.inner
            finally:
                pacer.done(self.url)

    return f, _Paced


# --- L1 ------------------------------------------------------------------------------------

def _challenge(body: bytes) -> bool:
    return any(m in body[:PROBE_BYTES] for m in CHALLENGE_MARKERS)


def _transient(f: Fetched) -> bool:
    return f.error in ("timeout", "connection") or (f.status >= 500 and not _challenge(f.body))


def probe(url: str, fetch: Fetcher) -> Fetched:
    """One retry for what may pass by itself (timeout, refused connection, 5xx); none for DNS or 4xx."""
    f = fetch(url)
    return fetch(url) if _transient(f) else f


def classify(f: Fetched, url: str) -> tuple[str, str]:
    challenge = _challenge(f.body)
    if f.status in (403, 429) or (f.status and challenge):
        why = "challenge page" if challenge else f"HTTP {f.status}"
        return "blocked", f"blocked from this runner ({why}, HTTP {f.status} from {f.final_url})"
    if 200 <= f.status < 400:
        a, b = urlsplit(url).hostname, urlsplit(f.final_url).hostname
        if a != b:
            return "moved", (f"HTTP {f.status}; moved from {a} to {b}: a known_issues note or a new "
                             f"origin.url is due")
        return "ok", f"HTTP {f.status} from {f.final_url}"
    return "dead", (f"HTTP {f.status} from {f.final_url}" if f.status else f"{f.error or 'error'} at {url}")


# --- L2 ------------------------------------------------------------------------------------

class ByteBudget:
    """Bytes hashed (or abandoned mid-stream) in one run, shared across records."""

    def __init__(self, limit: int = RUN_BYTE_BUDGET):
        self.limit, self.used = limit, 0

    @property
    def remaining(self) -> int:
        return self.limit - self.used

    def add(self, n: int) -> None:
        self.used += n

    def exhaust(self) -> None:
        self.used = self.limit

    def share(self, cap: int) -> ByteBudget:
        """A record's share: at most `cap` bytes, every byte also drawn from this budget."""
        return _Share(self, cap)


class _Share(ByteBudget):
    def __init__(self, parent: ByteBudget, cap: int):
        super().__init__(cap)
        self.parent = parent

    @property
    def remaining(self) -> int:
        return min(self.limit - self.used, self.parent.remaining)

    def add(self, n: int) -> None:
        self.used += n
        self.parent.add(n)

    def exhaust(self) -> None:
        if self.parent.remaining <= self.limit - self.used:
            self.parent.exhaust()  # the run, not only this record, has no room left
        self.used = self.limit


class _OverBudget(Exception):
    pass


def _read(stream: Iterable[bytes], cap: int) -> bytes:
    buf = bytearray()
    for chunk in stream:
        buf += chunk
        if len(buf) >= cap:
            break
    return bytes(buf[:cap])


def _digest(stream: Iterable[bytes], budget: ByteBudget, algorithms: Iterable[str] = (),
            watch: bool = False) -> tuple[str, int, dict[str, str], bool]:
    """SHA-256, byte count, the publisher's algorithms over the same stream, and whether a generated
    export said the server truncated it (`"exceededTransferLimit": true`, across chunk borders)."""
    h, n = hashlib.sha256(), 0
    more = {a: hashlib.new(COMPARABLE[a]) for a in algorithms}
    truncated, tail = False, b""
    for chunk in stream:
        if len(chunk) > budget.remaining:
            budget.exhaust()
            raise _OverBudget
        budget.add(len(chunk))
        h.update(chunk)
        for x in more.values():
            x.update(chunk)
        if watch and not truncated:
            truncated = bool(TRUNCATED.search(tail + chunk))
            tail = (tail + chunk)[-64:]
        n += len(chunk)
    return h.hexdigest(), n, {a: x.hexdigest() for a, x in more.items()}, truncated


def _hash(stream: Iterable[bytes], budget: ByteBudget) -> tuple[str, int]:
    digest, n, _, _ = _digest(stream, budget)
    return digest, n


def comparable(checksum: dict | None) -> str | None:
    """The hashlib algorithm a stated checksum can be compared with, or None (recorded, not compared)."""
    if not checksum:
        return None
    alg = COMPARABLE.get(re.sub(r"[^a-z0-9]", "", str(checksum.get("algorithm", "")).lower()))
    width = {"md5": 32, "sha1": 40, "sha256": 64}.get(alg or "")
    return alg if width and re.fullmatch(f"[0-9a-fA-F]{{{width}}}", str(checksum.get("digest", ""))) else None


class _Robots:
    """robots.txt per host: 2xx is obeyed, 4xx allows everything, anything else disallows (RFC 9309)."""

    def __init__(self, opener: Opener):
        self.opener, self.hosts = opener, {}

    def allowed(self, url: str) -> bool:
        u = urlsplit(url)
        key = f"{u.scheme}://{u.netloc}"
        if key not in self.hosts:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.parse(_read(self.opener(key + "/robots.txt"), 512 * 1024).decode("utf-8", "replace").splitlines())
            except FetchError as e:
                if 400 <= e.status < 500:
                    rp.allow_all = True
                else:
                    rp.disallow_all = True
            self.hosts[key] = rp
        return self.hosts[key].can_fetch(USER_AGENT, url)


def load_samples(path: Path = SAMPLES_PATH) -> dict[str, list[str] | str]:
    """Sample globs by record id, or a sentence saying why the listing has nothing to sample; the
    `mirror:` section is the mirror's (osd.mirror.load_rules)."""
    return {k: v for k, v in (yaml.safe_load(path.read_text()) or {}).items() if k != "mirror"}


def check_files(rec: dict, sample: list[str] | str | None, opener: Opener,
                budget: ByteBudget) -> tuple[dict, list[dict], list[dict]]:
    """The files-checksummed check, the files hashed, and the exports the server truncated."""
    def check(outcome: str, detail: str) -> dict:
        return {"name": "files-checksummed", "level": "L2", "outcome": outcome, "detail": detail[:500]}

    manifest = rec["origin"].get("manifest_url")
    if not manifest:
        return check("skip", "no origin.manifest_url"), [], []
    if isinstance(sample, str):
        return check("skip", f"nothing to sample (verifier/samples.yaml): {sample}"), [], []
    if not sample:
        return check("skip", "no sample for this record in verifier/samples.yaml"), [], []
    robots = _Robots(opener)
    if not robots.allowed(manifest):
        return check("skip", f"robots.txt disallows the listing {manifest}"), [], []
    try:
        stream = opener(manifest)
        body = _read(stream, LISTING_BYTES)
        listing = read_listing(body, manifest, getattr(stream, "content_type", "") or "")
    except FetchError as e:
        return check("fail", f"listing: {e}"), [], []
    except ListingError as e:
        return check("fail", str(e)), [], []
    except ValueError as e:
        return check("fail", f"listing unreadable: {e}"), [], []
    entries = listing.entries
    if not entries:
        return check("fail", f"the listing ({listing.shape}) names no files"), [], []
    picked, seen = [], set()
    for e in entries:
        if e.url not in seen and any(fnmatchcase(e.name, p) or fnmatchcase(e.url, p) for p in sample):
            picked.append(e)
            seen.add(e.url)
    if not picked:
        return check("fail", f"no entry of the listing ({len(entries)} entries, {listing.shape}) matches the sample"), [], []
    files: list[dict] = []
    partial: list[dict] = []
    notes: list[str] = []
    mismatches: list[str] = []
    for e in picked:
        if not robots.allowed(e.url):
            notes.append(f"robots.txt disallows {e.name}")
            continue
        if budget.remaining <= 0 or (e.size is not None and e.size > budget.remaining):
            notes.append(f"sample would exceed the run budget ({e.size if e.size is not None else 'unknown'} "
                         f"bytes listed for {e.name}, {max(budget.remaining, 0)} bytes left)")
            continue
        alg = comparable(e.checksum)
        try:
            digest, n, theirs, truncated = _digest(opener(e.url), budget, [alg] if alg else [], e.generated)
        except _OverBudget:
            notes.append(f"sample cut at the run budget: {e.name} abandoned mid-stream and not recorded; "
                         f"{len(files)} of {len(picked)} files hashed")
            break
        except FetchError as err:
            return check("fail", f"{e.name}: {err}"), files, partial
        f = {"path": e.name, "url": e.url, "bytes": n, "sha256": digest}
        if e.checksum:
            f["publisher_checksum"] = dict(e.checksum)
            f["compared"] = alg is not None
            if alg and theirs[alg] != e.checksum["digest"].lower():
                mismatches.append(f"{e.name}: publisher {e.checksum['algorithm']} {e.checksum['digest']}, "
                                  f"computed {theirs[alg]}")
        if truncated:
            partial.append({**f, "partial": True})
            notes.append(f"export truncated by the server (exceededTransferLimit): {e.name} kept as a "
                         f"partial export, not a hashed file")
            continue
        files.append(f)
    if mismatches:
        return check("fail", "publisher checksum mismatch: " + "; ".join(mismatches)), files, partial
    if not files:
        return check("skip", "; ".join(notes) or "nothing hashed"), files, partial
    total = sum(f["bytes"] for f in files)
    said = [f for f in files if f.get("compared")]
    parts = [f"sample, not the whole dataset: {len(files)} of {len(picked)} selected files hashed ({total} bytes); "
             f"{len(entries)} entries listed"]
    if said:
        parts.append(f"publisher checksums match for {len(said)} of {len(files)}")
    if listing.listed_at:
        parts.append(f"listing dated {listing.listed_at}")
    return check("pass", "; ".join(parts + notes)), files, partial


class _Text(HTMLParser):
    SKIP = frozenset({"script", "style", "noscript", "head", "template"})

    def __init__(self):
        super().__init__()
        self.depth, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        self.depth += tag in self.SKIP

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth:
            self.parts.append(data)


def licence_text(body: bytes) -> str:
    """The visible text, whitespace collapsed: markup and script churn is not a licence change."""
    text = body.decode("utf-8", "replace")
    if re.match(r"\s*(<!doctype|<html|<\?xml|<head|<body)", text, re.IGNORECASE):
        p = _Text()
        p.feed(text)
        text = " ".join(p.parts)
    return " ".join(text.split())


def check_licence(rec: dict, opener: Opener, previous: dict | None) -> tuple[dict, str | None, str | None]:
    def check(outcome: str, detail: str) -> dict:
        return {"name": "licence-text-captured", "level": "L2", "outcome": outcome, "detail": detail[:500]}

    url = rec["licence"].get("url")
    if not url:
        return check("skip", "no licence.url"), None, None
    try:
        body = _read(opener(url), LICENCE_BYTES)
    except FetchError as e:
        if e.status in (403, 429):
            return check("fail", f"blocked from this runner ({e})"), None, None
        why = f"answered HTTP {e.status}" if e.status else f"did not answer ({e.error or 'error'})"
        return check("fail", f"licence page {url} {why}"), None, None
    if _challenge(body):
        return check("fail", f"blocked from this runner (challenge page at {url})"), None, None
    text = licence_text(body)[:LICENCE_TEXT_CHARS]
    if not text:
        return check("fail", f"no text at {url}"), None, None
    sha = hashlib.sha256(text.encode()).hexdigest()
    before = (previous or {}).get("licence_text_sha256")
    if before and before != sha:
        return check("pass", f"licence text changed since {previous['checked_at'][:10]}"), sha, text
    return check("pass", f"{len(text)} characters captured from {url}"), sha, text


# --- the record ------------------------------------------------------------------------------

def level_from_checks(checks: list[dict]) -> str:
    """The highest level whose every check passed, with no gaps below it."""
    level = "L0"
    for lv in LEVELS[1:]:
        mine = [c for c in checks if c["level"] == lv]
        if not mine or any(c["outcome"] != "pass" for c in mine):
            break
        level = lv
    return level


def is_stale(checked_at: str | None, now: datetime | None = None) -> bool:
    if not checked_at:
        return True
    return (now or datetime.now(UTC)) - datetime.fromisoformat(checked_at) > timedelta(days=STALE_DAYS)


def verify_record(rec: dict, fetch: Fetcher, outline: dict | None, now: datetime | None = None,
                  opener: Opener | None = None, previous: dict | None = None,
                  budget: ByteBudget | None = None, sample: list[str] | None = None,
                  outline_rule: dict | None = None, stored: dict[str, str] | None = None,
                  refused: str | None = None, mirror_rule: list[str] | None = None) -> dict:
    checks: list[dict] = []
    extra: dict = {}

    stamp = (now or datetime.now(UTC)).isoformat(timespec="seconds")
    url = rec["origin"]["url"]
    f = probe(url, fetch)
    reach, detail = classify(f, url)
    origin = {"http_status": f.status, "final_url": f.final_url, "content_type": f.content_type[:100],
              "elapsed_ms": f.elapsed_ms, "reachability": reach}
    if reach == "blocked":
        before = (previous or {}).get("origin", {})
        origin["blocked_since"] = before.get("blocked_since", stamp) if before.get("reachability") == "blocked" else stamp
        detail = f"{detail}; blocked since {origin['blocked_since'][:10]}"
    outcome = {"ok": "pass", "moved": "pass", "blocked": "skip", "dead": "fail"}[reach]
    checks.append({"name": "origin-reachable", "level": "L1", "outcome": outcome, "detail": detail[:500]})

    if opener is None or reach == "dead":
        why = "origin not reachable" if reach == "dead" else "no opener (offline run)"
        checks.append({"name": "files-checksummed", "level": "L2", "outcome": "skip", "detail": why})
        checks.append({"name": "licence-text-captured", "level": "L2", "outcome": "skip", "detail": why})
    else:
        # the sample and the inventory share one budget: this record's share of the run's
        share = (budget or ByteBudget()).share(RECORD_SAMPLE_BYTES)
        c, files, partial = check_files(rec, sample, opener, share)
        checks.append(c)
        if partial:
            extra["partial_exports"] = partial
        if mirror_rule:   # E07: hash every entry the record's mirror rule selects (the inventory)
            from .mirror import inventory
            more, inv = inventory(rec, mirror_rule, opener, share, known=files)
            if inv:
                files = files + [f for f in more if f["url"] not in {x["url"] for x in files}]
                extra["inventory"] = inv
        if files:
            extra["files"] = files
        c, sha, text = check_licence(rec, opener, previous)
        checks.append(c)
        if sha:
            extra["licence_text_sha256"] = sha
            extra["licence_text"] = text

    if outline is None:
        checks.append({"name": "outline-present", "level": "L3", "outcome": "fail",
                       "detail": ("no outlines file" + (f"; derivation refused: {refused}" if refused else ""))[:500]})
    else:
        checks.append({"name": "outline-present", "level": "L3", "outcome": "pass",
                       "detail": f"{len(outline.get('features', []))} features"})
        o, d = outlines.check(rec, outline, outline_rule, stored or {}, refused)
        checks.append({"name": "outline-derived", "level": "L3", "outcome": o, "detail": d[:500]})
    checks.append(carried_conversion(previous, extra.get("files", [])))

    return {
        "record_id": rec["id"],
        "checked_at": stamp,
        "tool_version": __version__,
        "level": level_from_checks(checks),
        "checks": checks,
        "origin": origin,
        **extra,
    }


@cache
def _validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text()))


# --- L4: the fidelity record (E09) ---------------------------------------------------------------

@cache
def _fidelity_validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads((paths.SCHEMA_DIR / "fidelity.schema.json").read_text()),
                                format_checker=FormatChecker())


def fidelity_problems(doc: dict) -> list[str]:
    return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
            for e in sorted(_fidelity_validator().iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))]


def _rejections(rid: str, doc: dict, v: dict) -> list[str]:
    """Why this fidelity record is no evidence for `rid` today, named one by one; schema problems
    only when nothing named applies (a named guard is never hidden behind the schema)."""
    inputs = doc.get("inputs")
    if inputs == []:
        return ["the fidelity record lists no inputs"]
    inputs = [i for i in inputs if isinstance(i, dict)] if isinstance(inputs, list) else []
    out = []
    if doc.get("record") != rid:
        out.append(f"the fidelity record names record {doc.get('record')}, not {rid}")
    files = {f["sha256"]: f["path"] for f in v.get("files", [])}
    for i in inputs:
        if i.get("sha256") not in files:
            out.append(f"input {i.get('name')} ({str(i.get('sha256'))[:12]}…) is not a file of the latest verification")
    results = {i.get("sha256") for i in inputs}
    missing = [p for sha, p in files.items() if sha not in results]
    if missing:
        out.append(f"{len(missing)} of {len(files)} files of the latest verification have no result: {', '.join(missing)}")
    for i in inputs:
        if i.get("result") in ("partial", "failed") and not i.get("reason"):
            out.append(f"input {i.get('name')} is {i['result']} without a reason")
    if not any(i.get("result") == "converted" for i in inputs):
        out.append("no input converted")
    return out or [f"not an osd.fidelity/1 record: {p}" for p in fidelity_problems(doc)]


def apply_fidelity(rid: str, doc: dict, verification: dict | None) -> tuple[dict | None, list[str]]:
    """The latest verification with its `canonical-conversion` check derived from a fidelity/1 record,
    and why it gives no L4 (empty when it does). A rejected record makes the check `fail` with the
    reasons; an accepted one makes it `pass` with "n of m inputs converted", n the inputs converted
    and m the files of the verification. Nothing else is taken from the file: the other checks stay
    as the catalogue's tools wrote them and the level is level_from_checks over them."""
    if verification is None:
        return None, [f"no verification for {rid}: run osd verify {rid} first"]
    reasons = _rejections(rid, doc, verification)
    if reasons:
        check = {"name": "canonical-conversion", "level": "L4", "outcome": "fail",
                 "detail": ("fidelity rejected: " + "; ".join(reasons))[:500]}
    else:
        done = [i for i in doc["inputs"] if i["result"] == "converted"]
        kinds = sorted({i["output"]["kind"] for i in done})
        check = {"name": "canonical-conversion", "level": "L4", "outcome": "pass",
                 "detail": (f"{len(done)} of {len(verification.get('files', []))} inputs converted to kinds "
                            f"{', '.join(kinds)}; fidelity/1 for snapshot {doc['catalog']['records_digest'][:12]}… "
                            f"built {doc['catalog']['built_at']}")[:500]}
    checks = [check if c["name"] == "canonical-conversion" else c for c in verification["checks"]]
    if check not in checks:
        checks.append(check)
    out = dict(verification, checks=checks, level=level_from_checks(checks))
    if not reasons and out["level"] != "L4":
        reasons = [f"L4 needs the catalogue's own L1-L3: its own checks reach {out['level']}"]
    return out, reasons


def carried_conversion(previous: dict | None, files: list[dict]) -> dict:
    """The canonical-conversion check of a network run: the previous run's passed check while this
    run hashed the same files (same sha256 set, so the fidelity still names exactly them), else skip."""
    before = next((c for c in (previous or {}).get("checks", []) if c["name"] == "canonical-conversion"), None)
    same = files and {f["sha256"] for f in files} == {f["sha256"] for f in (previous or {}).get("files", [])}
    if before and before["outcome"] == "pass":
        if same:
            return before
        return {"name": "canonical-conversion", "level": "L4", "outcome": "skip",
                "detail": "the record's hashed files changed since the fidelity record; export it again"}
    return {"name": "canonical-conversion", "level": "L4", "outcome": "skip", "detail": NO_FIDELITY}


def conversion_coverage(v: dict | None) -> str | None:
    """"n of m converted" for a verification at L4, else None (osd status prints it beside the level)."""
    if not v or v.get("level") != "L4":
        return None
    for c in v["checks"]:
        if c["name"] == "canonical-conversion" and c["outcome"] == "pass" and (m := COVERAGE.match(c.get("detail", ""))):
            return f"{m.group(1)} of {m.group(2)} converted"
    return None


def derive_outline(rec: dict, rules: dict, opener: Opener, inputs_dir: Path, outline_path: Path,
                   rewrite: bool) -> str | None:
    """Fetch the record's inputs and derive from them; `rewrite` (--outlines) replaces the committed
    file, otherwise (--outline-inputs, the verify workflow) the committed file is checked against
    today's bytes. Returns the reason when refused."""
    try:
        outlines.fetch_inputs(rec, rules, opener, inputs_dir)
        fc = outlines.derive(rec, rules, inputs_dir)
        if rewrite:
            outlines.write_outline(fc, outline_path)
    except outlines.Refused as e:
        return str(e)
    return None


def verify_all(ids: list[str] | None = None, fetch: Fetcher | None = None, opener: Opener | None = None,
               out_dir: Path = paths.VERIFICATION_DIR, budget: ByteBudget | None = None,
               derive: bool = False, fetch_inputs: bool = False, inputs_dir: Path = outlines.INPUTS_DIR,
               outlines_dir: Path = paths.OUTLINES_DIR) -> list[dict]:
    """Defaults are the network, paced; tests inject both and are not paced. `derive` (osd verify
    --outlines) refetches the inputs of records that have outline rules and rewrites their outlines;
    `fetch_inputs` (--outline-inputs) refetches them and checks the committed outlines against them."""
    if fetch is None and opener is None:
        fetch, opener = paced(http_fetch, http_open, Pacer())
    recs = load_records()
    samples = load_samples()
    from .mirror import load_rules
    mirror_rules = load_rules()
    rules = outlines.load_rules()
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = budget or ByteBudget()
    results = []
    for rid, rec in recs.items():
        if ids and rid not in ids:
            continue
        op = outlines_dir / (rid.replace("/", "__") + ".geojson")
        refused = None
        if (derive or fetch_inputs) and opener is not None and rid in rules:
            refused = derive_outline(rec, rules, opener, inputs_dir, op, rewrite=derive)
        outline = load_outline(op) if op.exists() else None
        out = out_dir / (rid.replace("/", "__") + ".json")
        previous = json.loads(out.read_text()) if out.exists() else None
        v = verify_record(rec, fetch, outline, opener=opener, previous=previous, budget=budget,
                          sample=samples.get(rid), outline_rule=rules.get(rid),
                          stored=outlines.stored_inputs(rid, inputs_dir), refused=refused,
                          mirror_rule=mirror_rules.get(rid))
        _validator().validate(v)  # never write a record the schema refuses
        out.write_text(json.dumps(v, indent=2) + "\n")
        results.append(v)
    return results
