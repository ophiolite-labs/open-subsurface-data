"""Verify in shards (H2): which records a shard verifies, and how the finishing job puts the shards'
results back together.

  shard_of    the shard of an origin host: SHA-256 of the lowercased host (UTF-8), first 8 bytes
              big-endian, modulo N, plus one. One publisher's origin stays in one shard, so the 2 s
              pause per host holds; adding a record moves no other record.
  select      the ids of shard I of N, in catalogue order (`osd verify --shard I/N`)
  overlay     the earlier-results snapshot with each accepted shard's fresh files laid over it; a
              shard without its id list, or naming a record outside its shard, is discarded and its
              records keep their earlier results
  hosts       the measurement behind N: origin hosts per shard, and the other hosts (listings, files,
              licence pages, outline inputs) with the shards that can reach each at once

A shard artifact is a directory `shard-<I>/` holding `ids.txt` (the ids it verified, one per line),
`verification/<id with / as __>.json` (exactly their files) and `shard.json` ({"shard", "of",
"started", "finished"}, epoch seconds of its verify step). No network here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .records import load_records

SHARDS = 12      # the verify workflow's matrix (H2 strategy: measured, not tuned per run)
MAX_SHARDS = 16  # charter: 1 <= I <= N <= 16


def origin_host(rec: dict) -> str:
    return (urlsplit(rec["origin"]["url"]).hostname or "").lower()


def shard_of(host: str, n: int) -> int:
    return int.from_bytes(hashlib.sha256(host.encode("utf-8")).digest()[:8], "big") % n + 1


def parse(spec: str) -> tuple[int, int]:
    """"I/N" -> (I, N); ValueError for anything else or out of range."""
    m = re.fullmatch(r"([0-9]+)/([0-9]+)", spec.strip())
    if not m:
        raise ValueError(f"--shard {spec!r} is not I/N")
    i, n = int(m.group(1)), int(m.group(2))
    if not 1 <= i <= n <= MAX_SHARDS:
        raise ValueError(f"--shard {spec!r}: needs 1 <= I <= N <= {MAX_SHARDS}")
    return i, n


def select(recs: dict[str, dict], i: int, n: int) -> list[str]:
    return [rid for rid, rec in recs.items() if shard_of(origin_host(rec), n) == i]


def _file(rid: str) -> str:
    return rid.replace("/", "__") + ".json"


# --- the measurement behind N --------------------------------------------------------------------

def hosts(recs: dict[str, dict], n: int, vdir: Path | None = None) -> dict:
    """Origin hosts per shard, and every other host a record reaches (manifest_url, licence page,
    outline inputs, files hashed in `vdir`) with the shards whose records reach it."""
    origin = {rid: origin_host(rec) for rid, rec in recs.items()}
    other: dict[str, set[int]] = {}
    for rid, rec in recs.items():
        urls = [rec["origin"].get("manifest_url"), (rec.get("licence") or {}).get("url")]
        urls += [x.get("url") for x in rec.get("inputs") or [] if isinstance(x, dict)]
        v = vdir / _file(rid) if vdir else None
        if v and v.is_file():
            urls += [f.get("url") for f in json.loads(v.read_text()).get("files", [])]
        for u in filter(None, urls):
            h = (urlsplit(u).hostname or "").lower()
            if h and h != origin[rid]:
                other.setdefault(h, set()).add(shard_of(origin[rid], n))
    per = {i: sorted({origin[r] for r in select(recs, i, n)}) for i in range(1, n + 1)}
    return {"origin_hosts": per, "other_hosts": {h: sorted(s) for h, s in sorted(other.items())}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m osd.shards", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    ph = sub.add_parser("hosts", help="origin hosts per shard and the other hosts each shard reaches")
    ph.add_argument("-n", type=int, default=SHARDS)
    ph.add_argument("--vdir", help="verification results whose hashed files count as reached hosts")
    a = ap.parse_args(argv)
    recs = load_records()
    print(json.dumps(hosts(recs, a.n, Path(a.vdir) if a.vdir else None), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
