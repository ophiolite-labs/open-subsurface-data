"""Verification: what our tools can establish about a record today.

L1 (origin reachable) is implemented. L2 (checksums and licence text), L3 (outlines derived
from the data) and L4 (canonical conversion) are chartered epics; their checks are declared
here with outcome "skip" so the level ladder and its records are stable from the start.

The fetcher is injected so tests never touch the network and the required CI check stays
offline.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import __version__, paths
from .records import load_outline, load_records

LEVELS = ["L0", "L1", "L2", "L3", "L4"]
USER_AGENT = "open-subsurface-data-verifier/" + __version__ + " (+https://github.com/ophiolite-labs)"


@dataclass(frozen=True)
class Fetched:
    status: int
    final_url: str
    content_type: str
    elapsed_ms: int


Fetcher = Callable[[str], Fetched]


def http_fetch(url: str, timeout: float = 20.0) -> Fetched:
    """GET with a small read; HEAD is refused by too many publishers to be useful."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Fetched(
                resp.status, resp.geturl(), resp.headers.get("Content-Type", ""),
                int((time.monotonic() - t0) * 1000),
            )
    except urllib.error.HTTPError as e:
        return Fetched(e.code, url, "", int((time.monotonic() - t0) * 1000))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return Fetched(0, url, str(e)[:120], int((time.monotonic() - t0) * 1000))


def level_from_checks(checks: list[dict]) -> str:
    """The highest level whose every check passed, with no gaps below it."""
    level = "L0"
    for lv in LEVELS[1:]:
        mine = [c for c in checks if c["level"] == lv]
        if not mine or any(c["outcome"] != "pass" for c in mine):
            break
        level = lv
    return level


def verify_record(rec: dict, fetch: Fetcher, outline: dict | None, now: datetime | None = None) -> dict:
    checks: list[dict] = []
    origin: dict = {}

    f = fetch(rec["origin"]["url"])
    origin = {"http_status": f.status, "final_url": f.final_url, "content_type": f.content_type[:100],
              "elapsed_ms": f.elapsed_ms}
    ok = 200 <= f.status < 400
    checks.append({"name": "origin-reachable", "level": "L1", "outcome": "pass" if ok else "fail",
                   "detail": f"HTTP {f.status} from {f.final_url}"[:500]})

    checks.append({"name": "files-checksummed", "level": "L2", "outcome": "skip", "detail": "E02"})
    checks.append({"name": "licence-text-captured", "level": "L2", "outcome": "skip", "detail": "E02"})

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
    }


def verify_all(ids: list[str] | None = None, fetch: Fetcher = http_fetch,
               out_dir: Path = paths.VERIFICATION_DIR) -> list[dict]:
    recs = load_records()
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for rid, rec in recs.items():
        if ids and rid not in ids:
            continue
        op = paths.outline_path(rid)
        outline = load_outline(op) if op.exists() else None
        v = verify_record(rec, fetch, outline)
        (out_dir / (rid.replace("/", "__") + ".json")).write_text(json.dumps(v, indent=2) + "\n")
        results.append(v)
    return results
