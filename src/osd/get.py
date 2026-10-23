"""osd get <manifest> --dest D (E06): fetch a manifest's assets from their origins, honestly.

Each asset lands at D/<collection_id>/<asset key>, confined to D. An existing file is rehashed
before it is skipped; a download streams to a temporary file in the same directory, is compared
with `file:size` and sha256, and only then renamed into place. Outcomes per asset:

  verified       bytes match the catalogue's sha256 (fetched now, or already on disk)
  fetched        downloaded, but the catalogue states no checksum: not verified
  mismatch       size or sha256 differ: nothing written, the run stops
  not-attempted  after a mismatch
  needs-sign-in  the origin answered 401 or 403
  origin-dead    any other HTTP failure or no answer; the run continues

An asset with alternates (osd.manifest/2: the mirror, E07) is tried there first when the catalogue
states its sha256, and from origin on any failure of the alternate: no answer, a refusal, or bytes
that do not match (a `mismatch` from the mirror, recorded in `attempts`, never written). Each
outcome names the location that served it (`source`).

Entries without assets are the to-do list: their origin page and the reason. ATTRIBUTION.md is
written from the licence objects as the records state them, nothing invented.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .manifest import Entry, Manifest, ManifestError
from .verify import CHUNK, FetchError, Opener, http_open

FAILED = ("mismatch", "needs-sign-in", "origin-dead")


@dataclass(frozen=True)
class Outcome:
    collection_id: str
    key: str
    outcome: str
    detail: str = ""
    requested: bool = False
    source: str = "origin"                              # the location that served the bytes
    attempts: tuple[tuple[str, str, str], ...] = ()     # (location, outcome, detail) that failed first


def target(dest: Path, entry: Entry, key: str) -> Path:
    base = (dest / entry.collection_id).resolve()
    p = (base / key).resolve()
    if key.startswith(("/", "\\")) or not p.is_relative_to(base) or p == base:
        raise ManifestError(f"{entry.collection_id}: asset key '{key}' leaves {base}")
    return p


def plan(m: Manifest, dest: Path) -> list[tuple[Entry, object, Path]]:
    """Every (entry, asset, path), refused as a whole if two assets would share a file."""
    out, seen = [], {}
    for e in m.entries:
        for a in e.assets:
            p = target(dest, e, a.key)
            if p in seen:
                raise ManifestError(f"{a.href} and {seen[p]} would both be written to {p}")
            seen[p] = a.href
            out.append((e, a, p))
    return out


def _sha256_file(p: Path) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    with p.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def _download(e: Entry, a, href: str, p: Path, opener: Opener) -> tuple[str, str]:
    """Stream href to a temporary file beside p; rename into place only when size and sha256 match."""
    fd, tmp = tempfile.mkstemp(prefix=".osd-get-", suffix=".partial", dir=p.parent)
    try:
        h, n = hashlib.sha256(), 0
        with os.fdopen(fd, "wb") as f:
            try:
                for chunk in opener(href):
                    h.update(chunk)
                    n += len(chunk)
                    f.write(chunk)
            except FetchError as err:
                if err.status in (401, 403):
                    return "needs-sign-in", f"HTTP {err.status}: sign in at {e.origin_url}"
                return "origin-dead", str(err)
        if a.size is not None and n != a.size:
            return "mismatch", f"{n} bytes, the catalogue states {a.size}"
        if a.sha256 and h.hexdigest() != a.sha256:
            return "mismatch", f"sha256 {h.hexdigest()}, the catalogue states {a.sha256}"
        os.replace(tmp, p)
        return ("verified" if a.sha256 else "fetched"), f"{n} bytes"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _fetch_one(e: Entry, a, p: Path, opener: Opener) -> Outcome:
    if p.is_file():
        digest, n = _sha256_file(p)
        if a.sha256 and digest == a.sha256:
            return Outcome(e.collection_id, a.key, "verified", "already on disk", False, "disk")
        if not a.sha256 and a.size is not None and n == a.size:
            return Outcome(e.collection_id, a.key, "fetched", "already on disk, size matches, no checksum to verify",
                           False, "disk")
    p.parent.mkdir(parents=True, exist_ok=True)
    attempts = []
    for name, href in (a.alternates if a.sha256 else ()):   # an alternate is trusted only by checksum
        what, detail = _download(e, a, href, p, opener)
        if what == "verified":
            return Outcome(e.collection_id, a.key, what, detail, True, name)
        attempts.append((name, "unreachable" if what == "origin-dead" else what, detail))
    what, detail = _download(e, a, a.href, p, opener)
    return Outcome(e.collection_id, a.key, what, detail, True, "origin", tuple(attempts))


def get(m: Manifest, dest: Path, opener: Opener = http_open) -> list[Outcome]:
    dest = Path(dest)
    steps = plan(m, dest)   # refuse before any request
    out: list[Outcome] = []
    stopped = None
    for e, a, p in steps:
        if stopped:
            out.append(Outcome(e.collection_id, a.key, "not-attempted", f"stopped after the mismatch of {stopped}"))
            continue
        r = _fetch_one(e, a, p, opener)
        out.append(r)
        if r.outcome == "mismatch":
            stopped = f"{r.collection_id}/{r.key}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "ATTRIBUTION.md").write_text(attribution(m))
    return out


def _licence_label(e: Entry) -> str:
    return e.licence.spdx or e.licence.name


def entry_attribution(e: Entry) -> list[str]:
    """The ATTRIBUTION.md block of one entry; custody documents carry the same lines (E07)."""
    lic = e.licence
    lines = [f"## {e.title}", "",
             f"- Record: {e.record_id} (collection {e.collection_id})"
             + (f", feature {e.feature_id}" if e.feature_id else ""),
             f"- Origin: {e.origin_url}",
             f"- Licence: {lic.name}" + (f" ({lic.spdx})" if lic.spdx else " (no SPDX identifier)")
             + (f", {lic.url}" if lic.url else ""),
             f"- Attribution: {lic.attribution}",
             f"- Redistribution: {lic.redistribution}"]
    if lic.share_alike is True:
        lines.append(f"- Share-alike: derived work must carry {_licence_label(e)}")
    elif lic.share_alike is False:
        lines.append("- Share-alike: no")
    else:
        lines.append("- Share-alike: not stated")
    if lic.statement is not None:
        lines += ["- Statement, verbatim:", "", f"  > {lic.statement}"]
    else:
        lines.append("- Statement: none stated by the publisher in the record")
    for k in e.known_issues:
        lines.append(f"- Known issue: {k}")
    return lines


def attribution(m: Manifest) -> str:
    lines = ["# Attribution", "",
             ("Written by `osd get` from the licence objects the catalogue records state. Statements are "
             "copied verbatim; what a record does not state is shown as not stated."), ""]
    for e in m.entries:
        lines += entry_attribution(e) + [""]
    return "\n".join(lines)


def _detail(r: Outcome) -> str:
    """Where the bytes came from when an alternate was in play; origin-only lines are unchanged."""
    if r.source not in ("origin", "disk"):
        return f"{r.detail} from {r.source}"
    tried = "; ".join(f"{n} {w}: {d}" for n, w, d in r.attempts)
    return f"{r.detail} from origin; {tried}" if tried else r.detail


def summary(m: Manifest, outcomes: list[Outcome]) -> list[str]:
    lines = [f"  {r.outcome:13} {r.collection_id}/{r.key}" + (f"  ({_detail(r)})" if _detail(r) else "")
             for r in outcomes]
    for e in m.entries:
        if not e.assets:
            lines.append(f"  to-do         {e.collection_id}" + (f" {e.feature_id}" if e.feature_id else "")
                         + f": {e.unresolved} -> {e.origin_url}")
    n = Counter(r.outcome for r in outcomes)
    lines.append(", ".join(f"{v} {k}" for k, v in sorted(n.items())) or "no assets")
    sa = Counter(_licence_label(e) for e in m.entries if e.licence.share_alike is True)
    for lic, k in sorted(sa.items()):
        lines.append(f"{k} item{'s' if k > 1 else ''} require{'s' if k == 1 else ''} derived work to carry {lic}")
    sampled = sum(1 for e in m.entries if e.coverage == "sampled")
    if sampled:
        lines.append(f"{sampled} item{'s' if sampled > 1 else ''}: the files the verifier sampled, "
                     "not the whole dataset")
    return lines


def failed(outcomes: list[Outcome]) -> bool:
    return any(r.outcome in FAILED for r in outcomes)
