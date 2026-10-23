"""The mirror store (E07): eligible files copied once, verified, held under a custody document.

Eligibility (OSD-D6) is a pure function of a record, its latest verification and its `mirror:` rule
in verifier/samples.yaml. The verifier writes the inventory (`inventory()`, called from
`osd verify` for records with a rule): every listing entry the rule selects, hashed, so a mirror
copies exactly what a verification run checksummed, never a whole-dataset claim beyond it.

Store layout, one transport interface (slice 1: `LocalDirectory`; slice 2: S3):

  staging/<sha256>/<name>              an upload in progress, never public
  mirror/<record id>/<sha256>/<name>   the public copy
  custody/<sha256>.json                its custody document (osd.custody/1), written before the move
  custody/<sha256>.removed.json        the tombstone: a removed digest is never mirrored again

`put()` per file: tombstone -> refused; public object and custody -> present; complete staging ->
custody, move (no origin fetch); otherwise stream the origin to staging, compare size and sha256,
write custody, move. An interrupted run leaves at most a staging object, which the next run checks
and finishes or replaces. `remove()` writes the tombstone first, then deletes every object of the copy.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import Path
from urllib.parse import quote

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
    outcome: str      # published | present | refused | mismatch | origin-dead
    detail: str = ""


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


def _put_one(rec: dict, v: dict, f: dict, store, opener: Opener, now: datetime) -> Copied:
    sha, n = f["sha256"], f["bytes"]
    k = keys_for(rec["id"], sha, f["path"])
    c = lambda outcome, detail="": Copied(f["path"], sha, outcome, detail)
    if store.exists(k.tombstone):
        t = store.get_json(k.tombstone)["removal"]
        return c("refused", f"removed {t['removed_at'][:10]} on {t['request']}: never mirrored again")
    if store.exists(k.custody):
        held = store.get_json(k.custody)["record_id"]
        if held != rec["id"]:
            return c("refused", f"this digest is held for {held}")
        if store.exists(k.public):
            return c("present", k.public)
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
        now: datetime | None = None) -> list[Copied]:
    e = eligibility(rec, verification, rule)
    if not e.eligible:
        raise NotEligible(f"{rec['id']}: " + "; ".join(e.reasons))
    now = now or datetime.now(UTC)
    return [_put_one(rec, verification, f, store, opener, now) for f in e.files]


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


def public_index(custody_dir: Path) -> list[dict]:
    """The copies held, from the custody documents (never hand-written); tombstoned digests excluded."""
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
        out.append({k: doc[k] for k in ("record_id", "path", "sha256", "bytes", "href")})
    return out
