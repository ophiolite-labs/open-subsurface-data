"""Verification: what our tools can establish about a record today.

L1 (origin reachable) and L2 (sample files checksummed, licence text captured) are implemented.
L3 (outlines derived from the data) and L4 (canonical conversion) are chartered epics; their
checks are declared here with outcome "skip" so the level ladder and its records are stable.

Reachability is one of four closed classes: ok, blocked (403/429 or a challenge page: not dead,
L1 passes with a detail), moved (final host differs: passes with a hint), dead (404/410, DNS
failure, timeout or 5xx after one retry).

The network is injected twice: a Fetcher probes an origin (first 16 KB), an Opener streams a
body in chunks and raises FetchError. Tests pass fakes, so the required CI check stays offline.
"""

from __future__ import annotations

import hashlib
import html
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
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

from . import __version__, paths
from .records import load_outline, load_records

LEVELS = ["L0", "L1", "L2", "L3", "L4"]
USER_AGENT = ("open-subsurface-data-verifier/" + __version__
              + " (+https://github.com/ophiolite-labs/open-subsurface-data)")
PROBE_BYTES = 16384
CHUNK = 1 << 20
RUN_BYTE_BUDGET = 2 * 1024**3  # charter: never hash more than 2 GB per run
LISTING_BYTES = 32 * 1024**2
LICENCE_BYTES = 8 * 1024**2
PAUSE_S = 2.0
STALE_DAYS = 30
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


def http_open(url: str, timeout: float = 60.0) -> Iterable[bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            while chunk := resp.read(CHUNK):
                yield chunk
    except urllib.error.HTTPError as e:
        raise FetchError(url, e.code) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FetchError(url, 0, _error_kind(e)) from None


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

    def o(url: str) -> Iterable[bytes]:
        pacer.wait(url)
        try:
            yield from opener(url)
        finally:
            pacer.done(url)

    return f, o


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


class _OverBudget(Exception):
    pass


@dataclass(frozen=True)
class Entry:
    name: str  # as the listing states it
    url: str
    size: int | None = None


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href and not href.startswith(("#", "mailto:", "javascript:")):
                self.hrefs.append(href)


def _json_entries(node, base: str, out: list[Entry]) -> None:
    if isinstance(node, list):
        for x in node:
            if isinstance(x, str):
                out.append(Entry(x, urljoin(base, x)))
            else:
                _json_entries(x, base, out)
    elif isinstance(node, dict):
        name = node.get("path") or node.get("name") or node.get("key")
        size = node.get("size") if isinstance(node.get("size"), int) else None
        if "download_url" in node:  # GitHub contents API: directories have none
            if isinstance(node["download_url"], str):
                out.append(Entry(name or node["download_url"], node["download_url"], size))
            return
        for k in ("href", "url"):
            if isinstance(node.get(k), str):
                out.append(Entry(name if isinstance(name, str) else node[k], urljoin(base, node[k]), size))
                break
        for v in node.values():
            if isinstance(v, (list, dict)):
                _json_entries(v, base, out)


def parse_listing(body: bytes, base: str) -> list[Entry]:
    """JSON (GitHub contents, STAC hrefs, name lists), S3 ListBucketResult, HTML links, or text lines."""
    text = body.decode("utf-8", "replace")
    head = text.lstrip()[:600]
    out: list[Entry] = []
    if head.startswith(("{", "[")):
        _json_entries(json.loads(text), base, out)
    elif "<ListBucketResult" in head:
        u = urlsplit(base)
        prefix = f"{u.scheme}://{u.netloc}{u.path.rstrip('/')}/"
        for c in re.findall(r"<Contents>(.*?)</Contents>", text, re.DOTALL):
            key = html.unescape(re.search(r"<Key>(.*?)</Key>", c, re.DOTALL).group(1))
            size = re.search(r"<Size>(\d+)</Size>", c)
            out.append(Entry(key, prefix + quote(key), int(size.group(1)) if size else None))
    elif head.startswith("<"):
        p = _Links()
        p.feed(text)
        out = [Entry(h, urljoin(base, h)) for h in p.hrefs]
    else:
        out = [Entry(s, urljoin(base, s)) for s in (x.strip() for x in text.splitlines())
               if s and not s.startswith("#")]
    return out


def _read(stream: Iterable[bytes], cap: int) -> bytes:
    buf = bytearray()
    for chunk in stream:
        buf += chunk
        if len(buf) >= cap:
            break
    return bytes(buf[:cap])


def _hash(stream: Iterable[bytes], budget: ByteBudget) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    for chunk in stream:
        if len(chunk) > budget.remaining:
            budget.used = budget.limit  # the rest of this run has no room either
            raise _OverBudget
        budget.used += len(chunk)
        h.update(chunk)
        n += len(chunk)
    return h.hexdigest(), n


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


def check_files(rec: dict, opener: Opener, budget: ByteBudget) -> tuple[dict, list[dict]]:
    def check(outcome: str, detail: str) -> dict:
        return {"name": "files-checksummed", "level": "L2", "outcome": outcome, "detail": detail[:500]}

    manifest = rec["origin"].get("manifest_url")
    sample = rec.get("verification", {}).get("sample", {}).get("files") or []
    if not manifest:
        return check("skip", "no origin.manifest_url"), []
    if not sample:
        return check("skip", "no verification.sample allow-list"), []
    robots = _Robots(opener)
    if not robots.allowed(manifest):
        return check("skip", f"robots.txt disallows the listing {manifest}"), []
    try:
        entries = parse_listing(_read(opener(manifest), LISTING_BYTES), manifest)
    except FetchError as e:
        return check("fail", f"listing: {e}"), []
    except ValueError as e:
        return check("fail", f"listing unreadable: {e}"), []
    picked, seen = [], set()
    for e in entries:
        if e.url not in seen and any(fnmatchcase(e.name, p) or fnmatchcase(e.url, p) for p in sample):
            picked.append(e)
            seen.add(e.url)
    if not picked:
        return check("fail", f"no file in the listing ({len(entries)} entries) matches verification.sample"), []
    files: list[dict] = []
    notes: list[str] = []
    for i, e in enumerate(picked):
        if not robots.allowed(e.url):
            notes.append(f"robots.txt disallows {e.name}")
            continue
        if budget.remaining <= 0 or (e.size is not None and e.size > budget.remaining):
            notes.append(f"sample cut at 2 GB per run: {len(files)} of {len(picked)} files")
            break
        try:
            digest, n = _hash(opener(e.url), budget)
        except _OverBudget:
            notes.append(f"sample cut at 2 GB per run: {len(files)} of {len(picked)} files")
            break
        except FetchError as err:
            return check("fail", f"{e.name}: {err}"), files
        files.append({"path": e.name, "url": e.url, "bytes": n, "sha256": digest})
    if not files:
        return check("skip", "; ".join(notes) or "nothing hashed"), files
    total = sum(f["bytes"] for f in files)
    return check("pass", "; ".join([f"{len(files)} files, {total} bytes hashed", *notes])), files


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


def check_licence(rec: dict, opener: Opener, previous: dict | None) -> tuple[dict, str | None]:
    def check(outcome: str, detail: str) -> dict:
        return {"name": "licence-text-captured", "level": "L2", "outcome": outcome, "detail": detail[:500]}

    url = rec["licence"].get("url")
    if not url:
        return check("skip", "no licence.url"), None
    try:
        body = _read(opener(url), LICENCE_BYTES)
    except FetchError as e:
        return check("fail", f"blocked from this runner ({e})" if e.status in (403, 429) else str(e)), None
    if _challenge(body):
        return check("fail", f"blocked from this runner (challenge page at {url})"), None
    text = licence_text(body)
    if not text:
        return check("fail", f"no text at {url}"), None
    sha = hashlib.sha256(text.encode()).hexdigest()
    before = (previous or {}).get("licence_text_sha256")
    if before and before != sha:
        return check("pass", f"licence text changed since {previous['checked_at'][:10]}"), sha
    return check("pass", f"{len(text)} characters captured from {url}"), sha


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
                  budget: ByteBudget | None = None) -> dict:
    checks: list[dict] = []
    extra: dict = {}

    url = rec["origin"]["url"]
    f = probe(url, fetch)
    reach, detail = classify(f, url)
    origin = {"http_status": f.status, "final_url": f.final_url, "content_type": f.content_type[:100],
              "elapsed_ms": f.elapsed_ms, "reachability": reach}
    checks.append({"name": "origin-reachable", "level": "L1", "outcome": "fail" if reach == "dead" else "pass",
                   "detail": detail[:500]})

    if opener is None or reach == "dead":
        why = "origin not reachable" if reach == "dead" else "no opener (offline run)"
        checks.append({"name": "files-checksummed", "level": "L2", "outcome": "skip", "detail": why})
        checks.append({"name": "licence-text-captured", "level": "L2", "outcome": "skip", "detail": why})
    else:
        c, files = check_files(rec, opener, budget or ByteBudget())
        checks.append(c)
        if files:
            extra["files"] = files
        c, sha = check_licence(rec, opener, previous)
        checks.append(c)
        if sha:
            extra["licence_text_sha256"] = sha

    if outline is None:
        checks.append({"name": "outline-present", "level": "L3", "outcome": "fail",
                       "detail": "no outlines file"})
    else:
        approx = [x for x in outline.get("features", []) if x["properties"].get("approximate")]
        checks.append({"name": "outline-present", "level": "L3", "outcome": "pass",
                       "detail": f"{len(outline.get('features', []))} features"})
        checks.append({"name": "outline-derived", "level": "L3",
                       "outcome": "fail" if approx else "skip",
                       "detail": f"{len(approx)} approximate features" if approx else "E03"})
    checks.append({"name": "canonical-conversion", "level": "L4", "outcome": "skip", "detail": "E09"})

    return {
        "record_id": rec["id"],
        "checked_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
        "tool_version": __version__,
        "level": level_from_checks(checks),
        "checks": checks,
        "origin": origin,
        **extra,
    }


def verify_all(ids: list[str] | None = None, fetch: Fetcher | None = None, opener: Opener | None = None,
               out_dir: Path = paths.VERIFICATION_DIR, budget: ByteBudget | None = None) -> list[dict]:
    """Defaults are the network, paced; tests inject both and are not paced."""
    if fetch is None and opener is None:
        fetch, opener = paced(http_fetch, http_open, Pacer())
    recs = load_records()
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = budget or ByteBudget()
    results = []
    for rid, rec in recs.items():
        if ids and rid not in ids:
            continue
        op = paths.outline_path(rid)
        outline = load_outline(op) if op.exists() else None
        out = out_dir / (rid.replace("/", "__") + ".json")
        previous = json.loads(out.read_text()) if out.exists() else None
        v = verify_record(rec, fetch, outline, opener=opener, previous=previous, budget=budget)
        out.write_text(json.dumps(v, indent=2) + "\n")
        results.append(v)
    return results
