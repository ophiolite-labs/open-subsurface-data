"""The mirror store (E07): eligible files copied once, verified, held under a custody document.

Eligibility (OSD-D6) is a pure function of a record, its latest verification and its `mirror:` rule
in verifier/samples.yaml. The verifier writes the inventory (`inventory()`, called from
`osd verify` for records with a rule): every listing entry the rule selects, hashed, so a mirror
copies exactly what a verification run checksummed, never a whole-dataset claim beyond it.

Store layout, one transport interface (`LocalDirectory` for tests and dry runs; `S3`, slice 2, for the
bucket, selected by a `s3://<bucket>` store spec with keys from the environment):

  staging/<sha256>/<name>              an upload in progress, never public
  mirror/<record id>/<sha256>/<name>   the public copy
  custody/<sha256>.json                its custody document (osd.custody/1; /2 deposits and derived artefacts, E40), written before the move
  custody/<sha256>.removed.json        the tombstone: a removed digest is never mirrored again

`put()` per file: tombstone -> refused; public object and custody -> present; complete staging ->
custody, move (no origin fetch); otherwise stream the origin to staging, compare size and sha256,
write custody, move. An interrupted run leaves at most a staging object, which the next run checks
and finishes or replaces. `remove()` writes the tombstone first, then deletes every object of the copy.

Local uploads (E41) take the same staging, digest comparison and custody-before-move from a
directory instead of an origin: `deposit()` (a maintainer's deposit of a publisher's download,
custody/2 `deposit`) and `put_derived()` (a starter pack's artefacts, custody/2 `derived`). Both walk
regular files only (`walk()`: relative paths, a symlink refuses), refuse at the cap from the sizes
before hashing, hash each file, refuse a tombstoned or otherwise-held digest before writing anything,
then hash again while streaming to staging: the two digests must agree before the custody document
is written. No network but the store.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import stat
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlsplit

import yaml

from . import custody, paths
from .verify import (
    CHUNK,
    LEVELS,
    LISTING_BYTES,
    SAMPLES_PATH,
    ByteBudget,
    FetchError,
    Opener,
    _hash,
    _OverBudget,
    _read,
    _Robots,
    licence_text,
    parse_listing,
)

CAP_BYTES = 20 * 10**9          # OSD-D6: under 20 GB, decimal
MIRROR_DIR = paths.BUILD_DIR / "mirror"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MirrorError(Exception):
    pass


class NotEligible(MirrorError):
    pass


def load_rules(path: Path = SAMPLES_PATH) -> dict[str, list[str]]:
    return (yaml.safe_load(path.read_text()) or {}).get("mirror") or {}


# --- inventory (run by the verifier) -------------------------------------------------------------

def inventory(rec: dict, rule: list[str], opener: Opener, budget: ByteBudget,
              known: list[dict] = ()) -> tuple[list[dict], dict | None]:
    """Hash every listing entry the rule selects; files already hashed in this run (`known`, by url)
    are reused. Returns (files, inventory), or ([], None) when the listing cannot be read."""
    listing = rec["origin"].get("manifest_url")
    if not listing:
        return [], None
    robots = _Robots(opener)
    try:
        if not robots.allowed(listing):
            return [], None
        entries = parse_listing(_read(opener(listing), LISTING_BYTES), listing)
    except (FetchError, ValueError):
        return [], None
    selected, seen = [], set()
    for e in entries:
        if e.url not in seen and any(fnmatchcase(e.name, p) or fnmatchcase(e.url, p) for p in rule):
            selected.append(e)
            seen.add(e.url)
    have = {f["url"]: f for f in known if f.get("url")}
    files = []
    for e in selected:
        if e.url in have:
            files.append(dict(have[e.url], path=e.name))
            continue
        if budget.remaining <= 0 or not robots.allowed(e.url):
            continue
        try:
            digest, n = _hash(opener(e.url), budget)
        except (_OverBudget, FetchError):
            continue
        files.append({"path": e.name, "url": e.url, "bytes": n, "sha256": digest})
    complete = len(files) == len(selected) and bool(selected)
    return files, {"rule": list(rule), "listed": len(entries), "selected": [e.name for e in selected],
                   "coverage": "complete" if complete else "partial"}


# --- eligibility ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class Eligibility:
    record_id: str
    eligible: bool
    reasons: tuple[str, ...]
    files: tuple[dict, ...]
    bytes: int


def eligibility(rec: dict, verification: dict | None, rule: list[str] | None) -> Eligibility:
    v = verification or {}
    reasons: list[str] = []
    rights = rec["licence"]["redistribution"]
    if rights != "allowed":
        reasons.append(f"redistribution {rights}, not allowed (OSD-D6)")
    declared = (rec.get("size") or {}).get("bytes_estimate")
    if declared is not None and declared >= CAP_BYTES:
        reasons.append(f"declared size {declared / 1e9:.1f} GB, not under 20 GB")
    level = v.get("level", "L0")
    if LEVELS.index(level) < LEVELS.index("L2"):
        reasons.append(f"level {level}, L2 required")
    reach = (v.get("origin") or {}).get("reachability")
    if reach in ("blocked", "dead"):
        reasons.append(f"origin {reach}")
    inv = v.get("inventory")
    files: list[dict] = []
    if not rule:
        reasons.append("no mirror: rule in verifier/samples.yaml")
    elif not inv:
        reasons.append("no inventory in the latest verification")
    elif inv.get("rule") != list(rule):
        reasons.append("inventory made under another mirror rule")
    elif not inv.get("selected"):
        reasons.append("the mirror rule selects no entry of the listing")
    else:
        by_path = {f["path"]: f for f in v.get("files", [])}
        for name in inv["selected"]:
            f = by_path.get(name)
            if f is None:
                reasons.append(f"{name}: selected by the rule, not hashed")
                continue
            if not isinstance(f.get("bytes"), int):
                reasons.append(f"{name}: no bytes")
            if not SHA256.match(f.get("sha256") or ""):
                reasons.append(f"{name}: no sha256")
            files.append(f)
        total = sum(f["bytes"] for f in files if isinstance(f.get("bytes"), int))
        if total >= CAP_BYTES:
            reasons.append(f"inventory {total / 1e9:.1f} GB, not under 20 GB")
    total = sum(f.get("bytes") or 0 for f in files)
    return Eligibility(rec["id"], not reasons, tuple(reasons), tuple(files), total)


# --- transport -----------------------------------------------------------------------------------

class LocalDirectory:
    """The store as a directory (slice 1, tests and dry runs). `public_url` is where the directory is
    served; the S3 transport (slice 2) has the same methods."""

    def __init__(self, root: Path, public_url: str):
        self.root, self.base = Path(root), public_url.rstrip("/") + "/"

    def _p(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if not p.is_relative_to(self.root.resolve()):
            raise MirrorError(f"key {key} leaves the store")
        return p

    def exists(self, key: str) -> bool:
        return self._p(key).is_file()

    def size(self, key: str) -> int | None:
        p = self._p(key)
        return p.stat().st_size if p.is_file() else None

    def open(self, key: str) -> Iterator[bytes]:
        with self._p(key).open("rb") as f:
            while chunk := f.read(CHUNK):
                yield chunk

    def upload(self, key: str, chunks: Iterable[bytes]) -> None:
        p = self._p(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("wb") as f:
            for chunk in chunks:
                f.write(chunk)

    def move(self, src: str, dst: str) -> None:
        d = self._p(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        os.replace(self._p(src), d)
        self._prune(self._p(src).parent)

    def delete(self, key: str) -> None:
        p = self._p(key)
        if p.is_file():
            p.unlink()
            self._prune(p.parent)

    def _prune(self, d: Path) -> None:
        while d != self.root.resolve() and d.is_dir() and not any(d.iterdir()):
            d.rmdir()
            d = d.parent

    def put_json(self, key: str, doc: dict) -> None:
        p = self._p(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".partial")
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(doc, indent=2) + "\n")
        os.replace(tmp, p)

    def get_json(self, key: str) -> dict:
        return json.loads(self._p(key).read_text())

    def keys(self, prefix: str) -> list[str]:
        if not self.root.is_dir():
            return []
        out = (p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file())
        return sorted(k for k in out if k.startswith(prefix) and not k.endswith(".partial"))

    def public_url(self, key: str) -> str:
        return self.base + quote(key)


# --- S3 transport (slice 2) ----------------------------------------------------------------------

PART = 16 * 2**20             # multipart above this; one part held in memory at a time
COPY_LIMIT = 5 * 2**30        # CopyObject's limit; above it UploadPartCopy in COPY_PART ranges
COPY_PART = 2**30
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
PUBLIC_PREFIXES = ("mirror/", "custody/")   # public-read objects; staging/ stays private
ENV_KEYS = ("OSD_S3_ENDPOINT", "OSD_S3_ACCESS_KEY", "OSD_S3_SECRET_KEY")


@dataclass(frozen=True)
class Reply:
    status: int
    headers: Mapping[str, str]      # lower-case names
    read: Callable[..., bytes]      # read() all, read(n) up to n bytes


Send = Callable[[str, str, dict, bytes], Reply]


def _urlopen(method: str, url: str, headers: dict, body: bytes) -> Reply:
    req = urllib.request.Request(url, data=body if method in ("PUT", "POST") else None,
                                 headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=120)
        status = r.status
    except urllib.error.HTTPError as e:
        r, status = e, e.code
    except (urllib.error.URLError, OSError) as e:
        raise MirrorError(f"S3 {method} {urlsplit(url).path}: {e}") from None
    return Reply(status, {k.lower(): v for k, v in r.headers.items()}, r.read)


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def sigv4(method: str, url: str, headers: dict, payload_sha256: str, access_key: str, secret_key: str,
          region: str, now: datetime) -> dict:
    """AWS Signature Version 4 for S3: the request's headers plus x-amz-date, x-amz-content-sha256 and
    Authorization. `url` is already percent-encoded; it is the canonical URI as sent."""
    u = urlsplit(url)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    h = {k.lower(): " ".join(str(v).split()) for k, v in headers.items()}
    h.update({"host": u.netloc, "x-amz-date": amz_date, "x-amz-content-sha256": payload_sha256})
    signed = sorted(k for k in h if k in ("host", "range", "content-md5") or k.startswith("x-amz-"))
    query = "&".join(f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}"
                     for k, v in sorted(parse_qsl(u.query, keep_blank_values=True)))
    canonical = "\n".join([method, u.path or "/", query, "".join(f"{k}:{h[k]}\n" for k in signed),
                           ";".join(signed), payload_sha256])
    scope = f"{amz_date[:8]}/{region}/s3/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode()).hexdigest()])
    key = _hmac(_hmac(_hmac(_hmac(("AWS4" + secret_key).encode(), amz_date[:8]), region), "s3"), "aws4_request")
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    out = {k: v for k, v in headers.items()}
    out.update({"x-amz-date": amz_date, "x-amz-content-sha256": payload_sha256,
                "Authorization": f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, "
                                 f"SignedHeaders={';'.join(signed)}, Signature={signature}"})
    return out


def _xml_text(body: bytes, tag: str) -> list[str]:
    try:
        return [e.text or "" for e in ET.fromstring(body).iter() if e.tag.rsplit("}", 1)[-1] == tag]
    except ET.ParseError:
        return []


class S3:
    """The store as an S3 bucket (Hetzner Object Storage), the same methods as `LocalDirectory`.
    Path-style requests signed with SigV4 over the payload's sha256; `send` is the one network seam
    (tests inject an in-memory S3). Objects under mirror/ and custody/ are written public-read, staging/
    private; the bucket itself is never listable anonymously. The keys are never printed."""

    def __init__(self, bucket: str, endpoint: str, access_key: str, secret_key: str,
                 public_url: str | None = None, region: str | None = None, send: Send | None = None,
                 clock: Callable[[], datetime] | None = None):
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
            raise MirrorError(f"{bucket!r} is not a bucket name")
        u = urlsplit(endpoint)
        self.bucket, self.endpoint = bucket, f"{u.scheme}://{u.netloc}"
        self.region = region or u.netloc.split(".")[0]      # fsn1: Hetzner refuses a mismatched region
        self._keys = (access_key, secret_key)
        self.base = (public_url or f"{u.scheme}://{bucket}.{u.netloc}").rstrip("/") + "/"
        self.root = f"s3://{bucket}"
        self._send = send or _urlopen
        self._now = clock or (lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return f"S3({self.root} at {self.endpoint})"

    @classmethod
    def from_env(cls, bucket: str, public_url: str | None = None, environ: Mapping[str, str] = os.environ,
                 send: Send | None = None) -> S3:
        missing = [k for k in ENV_KEYS if not environ.get(k)]
        if missing:
            raise MirrorError("the S3 store needs " + ", ".join(missing) + " in the environment")
        return cls(bucket, environ["OSD_S3_ENDPOINT"], environ["OSD_S3_ACCESS_KEY"],
                   environ["OSD_S3_SECRET_KEY"], public_url, environ.get("OSD_S3_REGION"), send)

    def _call(self, method: str, key: str = "", query: str = "", headers: dict | None = None,
              body: bytes = b"", ok: tuple[int, ...] = (200,)) -> Reply:
        url = f"{self.endpoint}/{self.bucket}/{quote(key, safe='/-_.~')}" + (f"?{query}" if query else "")
        signed = sigv4(method, url, dict(headers or {}), hashlib.sha256(body).hexdigest() if body else
                       EMPTY_SHA256, *self._keys, self.region, self._now())
        r = self._send(method, url, signed, body)
        if r.status not in ok:
            detail = "" if method == "HEAD" else " ".join(_xml_text(r.read(), "Code"))
            raise MirrorError(f"S3 {method} {key or '(bucket)'}{'?' + query if query else ''}: "
                              f"HTTP {r.status} {detail}".rstrip())
        return r

    @staticmethod
    def _acl(key: str) -> dict:
        return {"x-amz-acl": "public-read"} if key.startswith(PUBLIC_PREFIXES) else {}

    def check(self) -> None:
        """HEAD on the bucket: the keys reach it (reads only)."""
        self._call("HEAD")

    def exists(self, key: str) -> bool:
        return self.size(key) is not None

    def size(self, key: str) -> int | None:
        r = self._call("HEAD", key, ok=(200, 404))
        return int(r.headers["content-length"]) if r.status == 200 else None

    def open(self, key: str) -> Iterator[bytes]:
        r = self._call("GET", key)
        while chunk := r.read(CHUNK):
            yield chunk

    def upload(self, key: str, chunks: Iterable[bytes]) -> None:
        """Streams: one PutObject below PART, multipart above; any error aborts the multipart upload,
        so a failed stream leaves no object."""
        buf, upload_id, parts = bytearray(), None, []
        try:
            for chunk in chunks:
                buf += chunk
                while len(buf) >= PART:
                    upload_id = upload_id or self._create(key)
                    parts.append(self._part(key, upload_id, len(parts) + 1, bytes(buf[:PART])))
                    del buf[:PART]
            if upload_id is None:
                self._call("PUT", key, headers=self._acl(key), body=bytes(buf))
                return
            if buf:
                parts.append(self._part(key, upload_id, len(parts) + 1, bytes(buf)))
            self._complete(key, upload_id, parts)
        except BaseException:
            if upload_id is not None:
                try:
                    self._call("DELETE", key, f"uploadId={quote(upload_id, safe='')}", ok=(200, 204, 404))
                except MirrorError:
                    pass
            raise

    def _create(self, key: str, headers: dict | None = None) -> str:
        r = self._call("POST", key, "uploads", headers={**self._acl(key), **(headers or {})})
        ids = _xml_text(r.read(), "UploadId")
        if not ids:
            raise MirrorError(f"S3 POST {key}?uploads: no UploadId")
        return ids[0]

    def _part(self, key: str, upload_id: str, n: int, body: bytes = b"", headers: dict | None = None) -> str:
        r = self._call("PUT", key, f"partNumber={n}&uploadId={quote(upload_id, safe='')}",
                       headers=headers, body=body)
        if headers:      # UploadPartCopy: the ETag is in the body, and an error may come with 200
            payload = r.read()
            if _xml_text(payload, "Code"):
                raise MirrorError(f"S3 copy part {n} of {key}: " + " ".join(_xml_text(payload, "Code")))
            etag = (_xml_text(payload, "ETag") or [""])[0]
        else:
            etag = r.headers.get("etag", "")
        if not etag:
            raise MirrorError(f"S3 part {n} of {key}: no ETag")
        return etag

    def _complete(self, key: str, upload_id: str, etags: list[str]) -> None:
        body = "<CompleteMultipartUpload>" + "".join(
            f"<Part><PartNumber>{i}</PartNumber><ETag>{e}</ETag></Part>" for i, e in enumerate(etags, 1)
        ) + "</CompleteMultipartUpload>"
        r = self._call("POST", key, f"uploadId={quote(upload_id, safe='')}", body=body.encode())
        payload = r.read()
        if _xml_text(payload, "Code"):    # S3 may report a failed completion inside a 200
            raise MirrorError(f"S3 complete {key}: " + " ".join(_xml_text(payload, "Code")))

    def move(self, src: str, dst: str) -> None:
        """Server-side copy, then delete the source. A copy error inside a 200 is an error."""
        n = self.size(src)
        if n is None:
            raise MirrorError(f"S3 move: {src} does not exist")
        source = {"x-amz-copy-source": quote(f"/{self.bucket}/{src}", safe="/-_.~")}
        if n <= COPY_LIMIT:
            payload = self._call("PUT", dst, headers={**source, **self._acl(dst)}).read()
            if _xml_text(payload, "Code"):
                raise MirrorError(f"S3 copy {src} -> {dst}: " + " ".join(_xml_text(payload, "Code")))
        else:
            upload_id = self._create(dst)
            try:
                etags = [self._part(dst, upload_id, i, headers={
                    **source, "x-amz-copy-source-range": f"bytes={a}-{min(a + COPY_PART, n) - 1}"})
                    for i, a in enumerate(range(0, n, COPY_PART), 1)]
                self._complete(dst, upload_id, etags)
            except BaseException:
                self._call("DELETE", dst, f"uploadId={quote(upload_id, safe='')}", ok=(200, 204, 404))
                raise
        self.delete(src)

    def delete(self, key: str) -> None:
        self._call("DELETE", key, ok=(200, 204, 404))

    def put_json(self, key: str, doc: dict) -> None:
        self._call("PUT", key, headers={"Content-Type": "application/json", **self._acl(key)},
                   body=(json.dumps(doc, indent=2) + "\n").encode())

    def get_json(self, key: str) -> dict:
        return json.loads(self._call("GET", key).read())

    def keys(self, prefix: str) -> list[str]:
        out, token = [], None
        while True:
            q = f"list-type=2&prefix={quote(prefix, safe='')}"
            if token:
                q += f"&continuation-token={quote(token, safe='')}"
            body = self._call("GET", query=q).read()
            out += _xml_text(body, "Key")
            token = (_xml_text(body, "NextContinuationToken") or [None])[0]
            if (_xml_text(body, "IsTruncated") or ["false"])[0] != "true" or not token:
                return sorted(out)

    def public_url(self, key: str) -> str:
        return self.base + quote(key)


def open_store(spec: str, public_url: str | None, environ: Mapping[str, str] = os.environ):
    """`s3://<bucket>` is the bucket (keys from the environment); anything else a local directory."""
    if spec.startswith("s3://"):
        return S3.from_env(spec.removeprefix("s3://").strip("/"), public_url, environ)
    if not public_url:
        raise MirrorError("a local store needs --public-url (where the directory is served)")
    return LocalDirectory(Path(spec), public_url)


# --- publication ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class Keys:
    staging: str
    public: str
    custody: str
    tombstone: str


def keys_for(record_id: str, sha256: str, path: str) -> Keys:
    name = custody.object_name(path)
    return Keys(f"staging/{sha256}/{name}", custody.object_key(record_id, sha256, path),
                f"custody/{sha256}.json", f"custody/{sha256}.removed.json")


@dataclass(frozen=True)
class Copied:
    path: str
    sha256: str
    outcome: str      # published | present | refused | mismatch | origin-dead; dry run: would-copy | would-finish
    detail: str = ""
    bytes: int = 0


def _hash_object(store, key: str) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    for chunk in store.open(key):
        h.update(chunk)
        n += len(chunk)
    return h.hexdigest(), n


def _hashing(chunks: Iterable[bytes], h, count: list[int]) -> Iterator[bytes]:
    for chunk in chunks:
        h.update(chunk)
        count[0] += len(chunk)
        yield chunk


def _publish(rec, v, f, k: Keys, store, now) -> None:
    doc = custody.document(rec, v, f, store.public_url(k.public), now)
    bad = custody.problems(doc, k.custody.split("/")[1], store.size(k.staging))
    if bad:   # never publish a copy without a valid custody document
        store.delete(k.staging)
        raise MirrorError(f"{rec['id']} {f['path']}: custody document refused: " + "; ".join(bad))
    store.put_json(k.custody, doc)
    store.move(k.staging, k.public)


def _put_one(rec: dict, v: dict, f: dict, store, opener: Opener, now: datetime, dry_run: bool = False) -> Copied:
    sha, n = f["sha256"], f["bytes"]
    k = keys_for(rec["id"], sha, f["path"])
    c = lambda outcome, detail="": Copied(f["path"], sha, outcome, detail, n)
    if store.exists(k.tombstone):
        t = store.get_json(k.tombstone)["removal"]
        return c("refused", f"removed {t['removed_at'][:10]} on {t['request']}: never mirrored again")
    if store.exists(k.custody):
        held = store.get_json(k.custody)["record_id"]
        if held != rec["id"]:
            return c("refused", f"this digest is held for {held}")
        if store.exists(k.public):
            return c("present", k.public)
    if dry_run:      # reads only: what a real run would do from here
        if store.exists(k.staging):
            return c("would-finish", f"{n} bytes in staging, checked and finished by the real run")
        return c("would-copy", f"{n} bytes from {f['url']}")
    if store.exists(k.staging):
        if _hash_object(store, k.staging) == (sha, n):
            _publish(rec, v, f, k, store, now)
            return c("published", f"{n} bytes, finished from staging without an origin fetch")
        store.delete(k.staging)
    h, count = hashlib.sha256(), [0]
    try:
        store.upload(k.staging, _hashing(opener(f["url"]), h, count))
    except FetchError as e:
        store.delete(k.staging)
        return c("origin-dead", str(e))
    if count[0] != n or h.hexdigest() != sha:
        store.delete(k.staging)
        return c("mismatch", f"{count[0]} bytes sha256 {h.hexdigest()}; the inventory states {n} bytes {sha}")
    _publish(rec, v, f, k, store, now)
    return c("published", f"{n} bytes")


def put(rec: dict, verification: dict | None, rule: list[str] | None, store, opener: Opener,
        now: datetime | None = None, dry_run: bool = False) -> list[Copied]:
    """Copy the record's inventory into the store. `dry_run` reads the store and writes nothing."""
    e = eligibility(rec, verification, rule)
    if not e.eligible:
        raise NotEligible(f"{rec['id']}: " + "; ".join(e.reasons))
    now = now or datetime.now(UTC)
    return [_put_one(rec, verification, f, store, opener, now, dry_run) for f in e.files]


def remove(sha256: str, store, request: str, approved_by: str, now: datetime | None = None) -> list[str]:
    """Takedown: tombstone first (no re-mirror from that moment), then every object of the copy."""
    if not SHA256.match(sha256):
        raise MirrorError(f"{sha256} is not a sha256 digest")
    live, tomb = f"custody/{sha256}.json", f"custody/{sha256}.removed.json"
    if store.exists(live):
        doc = store.get_json(live)
    elif store.exists(tomb):
        doc = store.get_json(tomb)          # a rerun finishes an interrupted removal
    else:
        raise MirrorError(f"no copy with digest {sha256} in the store")
    if doc["removal"]["state"] != "removed":
        doc["removal"] = {"state": "removed",
                          "removed_at": (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "request": request, "approved_by": approved_by}
        bad = custody.problems(doc, tomb.split("/")[1])
        if bad:
            raise MirrorError("tombstone refused: " + "; ".join(bad))
        store.put_json(tomb, doc)
    gone = [k for k in store.keys("mirror/") + store.keys("staging/") if f"/{sha256}/" in k or
            k.startswith(f"staging/{sha256}/")]
    for k in gone + [live]:
        store.delete(k)
    return gone + [live]


def sync_custody(store, out: Path) -> list[str]:
    """Every custody document and tombstone the store holds, written to `out` (replaced whole), so the
    build reads what the store holds without anyone listing the bucket publicly. Each document is
    checked before anything is replaced; a failed read keeps the previous set."""
    docs = {}
    for k in store.keys("custody/"):
        name = k.removeprefix("custody/")
        if "/" in name or not name.endswith(".json"):
            continue
        doc = store.get_json(k)
        bad = custody.problems(doc, name)
        if bad:
            raise MirrorError(f"{k}: " + "; ".join(bad))
        docs[name] = doc
    tmp = out.with_name(out.name + ".partial")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    for name, doc in docs.items():
        (tmp / name).write_text(json.dumps(doc, indent=2) + "\n")
    if out.exists():
        shutil.rmtree(out)
    tmp.rename(out)
    return sorted(docs)


def held_custody(custody_dir: Path) -> list[dict]:
    """The custody documents of the copies held, each checked; tombstoned digests excluded."""
    out = []
    if not custody_dir.is_dir():
        return out
    for p in sorted(custody_dir.glob("*.json")):
        if p.name.endswith(".removed.json") or (custody_dir / (p.stem + ".removed.json")).exists():
            continue
        doc = json.loads(p.read_text())
        bad = custody.problems(doc, p.name)
        if bad:
            raise MirrorError(f"{p}: " + "; ".join(bad))
        out.append(doc)
    return out


def public_index(custody_dir: Path) -> list[dict]:
    """The copies held, from the custody documents (never hand-written); tombstoned digests excluded."""
    return [{k: doc[k] for k in ("record_id", "path", "sha256", "bytes", "href")} for doc in held_custody(custody_dir)]


def deposits_of(held: list[dict], record_id: str) -> list[dict]:
    """The record's held deposits, when every copy the mirror holds of its own files is a deposit
    (E41 design 2); derived artefacts are never the record's files and are not counted."""
    mine = [d for d in held if d["record_id"] == record_id and custody.provenance(d) != "derived"]
    return mine if mine and all(custody.provenance(d) == "deposit" for d in mine) else []


# --- local uploads: deposits and derived artefacts (E41) -----------------------------------------

@dataclass(frozen=True)
class LocalFile:
    path: str           # relative to the walked directory, posix
    source: Path
    bytes: int
    sha256: str = ""


def walk(root: Path, exclude: Iterable[Path] = ()) -> list[LocalFile]:
    """Every regular file under `root` by relative path, sizes from stat; `exclude` (the captured
    page and licence text when they sit inside) is left out. A symlink or any other entry refuses."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise MirrorError(f"{root} is not a directory")
    skip = {Path(p).resolve() for p in exclude}
    out = []
    for d, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(dirs + files):
            p = Path(d) / name
            rel = p.relative_to(root).as_posix()
            if p.is_symlink():
                raise MirrorError(f"symlink {rel}: only regular files are uploaded, as downloaded")
            if name in dirs:
                continue
            st = p.lstat()
            if not stat.S_ISREG(st.st_mode):
                raise MirrorError(f"{rel}: not a regular file")
            if p.resolve() not in skip:
                out.append(LocalFile(rel, p, st.st_size))
    if not out:
        raise MirrorError(f"no regular file in {root}")
    return out


def under_cap(files: list[LocalFile]) -> int:
    total = sum(f.bytes for f in files)
    if total >= CAP_BYTES:
        raise NotEligible(f"{len(files)} files, {total} bytes: not under 20 GB (OSD-D6)")
    return total


def _file_chunks(p: Path) -> Iterator[bytes]:
    with p.open("rb") as f:
        while chunk := f.read(CHUNK):
            yield chunk


def sha256_file(p: Path) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    for chunk in _file_chunks(p):
        h.update(chunk)
        n += len(chunk)
    return h.hexdigest(), n


def hash_local(files: list[LocalFile]) -> list[LocalFile]:
    out = []
    for f in files:
        sha, n = sha256_file(f.source)
        if n != f.bytes:
            raise MirrorError(f"{f.path}: {n} bytes read, {f.bytes} stated by stat: the file is changing")
        out.append(LocalFile(f.path, f.source, n, sha))
    return out


def _holder(doc: dict) -> tuple:
    return doc["record_id"], custody.provenance(doc), (doc.get("derived") or {}).get("pack_id")


def upload_local(record_id: str, files: list[LocalFile], store, document: Callable[[LocalFile, str], dict]) -> list[Copied]:
    """Publish hashed local files: every refusal before anything is written, then per file staging,
    a second digest while streaming, custody (`document(file, href)`), move."""
    first: dict[str, str] = {}
    for f in files:
        if f.sha256 in first:
            raise MirrorError(f"{first[f.sha256]} and {f.path} are the same bytes ({f.sha256[:12]}…): "
                              "the mirror holds one copy per digest")
        first[f.sha256] = f.path
    todo = []
    for f in files:
        k = keys_for(record_id, f.sha256, f.path)
        if store.exists(k.tombstone):
            t = store.get_json(k.tombstone)["removal"]
            raise MirrorError(f"{f.path}: digest {f.sha256[:12]}… was removed {t['removed_at'][:10]} on "
                              f"{t['request']}: never mirrored again")
        if store.exists(k.custody):
            held, want = store.get_json(k.custody), document(f, store.public_url(k.public))
            if _holder(held) != _holder(want):
                rid, prov, pack = _holder(held)
                raise MirrorError(f"{f.path}: digest {f.sha256[:12]}… is held for {rid} as a {prov} copy"
                                  + (f" of {pack}" if pack else ""))
            if store.exists(k.public) and held["path"] == f.path:
                todo.append((f, k, "present"))
                continue
        todo.append((f, k, "upload"))
    out = []
    for f, k, what in todo:
        if what == "present":
            out.append(Copied(f.path, f.sha256, "present", k.public, f.bytes))
            continue
        store.delete(k.staging)
        h, count = hashlib.sha256(), [0]
        store.upload(k.staging, _hashing(_file_chunks(f.source), h, count))
        if (h.hexdigest(), count[0]) != (f.sha256, f.bytes):
            store.delete(k.staging)
            raise MirrorError(f"{f.path}: streamed {count[0]} bytes sha256 {h.hexdigest()}, hashed before as "
                              f"{f.bytes} bytes {f.sha256}: nothing published for it")
        doc = document(f, store.public_url(k.public))
        bad = custody.problems(doc, k.custody.split("/")[1], store.size(k.staging))
        if bad:
            store.delete(k.staging)
            raise MirrorError(f"{f.path}: custody document refused: " + "; ".join(bad))
        store.put_json(k.custody, doc)
        store.move(k.staging, k.public)
        out.append(Copied(f.path, f.sha256, "published", k.public, f.bytes))
    return out


def obtained_at(value: str) -> str:
    """A date (the day the download was made) or a UTC date-time, as custody states it."""
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
        t = datetime.fromisoformat(value)
        if t.tzinfo is None:
            raise ValueError(value)
        return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise MirrorError(f"--obtained {value}: not a date (YYYY-MM-DD) or a date-time with its offset") from None


def deposit(rec: dict, root: Path, store, *, obtained: str, by: str, page_url: str, page: Path,
            licence: Path, now: datetime | None = None) -> list[Copied]:
    """A maintainer's deposit of the publisher's download (E41 design 1, OSD-D22). `page` and
    `licence` are the publisher's page and the licence text as the person saved them; the page is
    kept as its sha256, the licence text as the sha256 of its visible text (the verifier's own
    normalisation, so the two digests compare). The record file is never touched."""
    rights = rec["licence"]["redistribution"]
    if rights != "allowed":
        raise NotEligible(f"{rec['id']}: redistribution {rights}, not allowed (OSD-D6)")
    host = urlsplit(rec["origin"]["url"]).hostname
    if urlsplit(page_url).hostname != host:
        raise MirrorError(f"--page-url {page_url} is not on the record's origin host {host}")
    page, licence = Path(page), Path(licence)
    for what, p in (("--page", page), ("--licence-text", licence)):
        if not p.is_file():
            raise MirrorError(f"{what} {p}: no such file")
    text = licence_text(licence.read_bytes())
    if not text:
        raise MirrorError(f"--licence-text {licence}: no text")
    block = {"obtained_at": obtained_at(obtained), "by": by, "publisher_page_url": page_url,
             "publisher_page_sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
             "licence_text_sha256": hashlib.sha256(text.encode()).hexdigest()}
    files = walk(root, exclude=(page, licence))
    under_cap(files)
    files = hash_local(files)
    now = now or datetime.now(UTC)
    return upload_local(rec["id"], files, store, lambda f, href: custody.deposit_document(
        rec, f.path, f.sha256, f.bytes, href, now, block))
