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
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from . import paths
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


# --- the finishing job ---------------------------------------------------------------------------

def check_artifact(d: Path, i: int, n: int, recs: dict[str, dict]) -> tuple[list[str] | None, str]:
    """(ids, "") for an artifact the finishing job accepts, else (None, why it is discarded)."""
    if not (d / "ids.txt").is_file():
        return None, "no id list (the shard failed, was cancelled or uploaded nothing)"
    ids = (d / "ids.txt").read_text().split()
    meta = json.loads((d / "shard.json").read_text()) if (d / "shard.json").is_file() else {}
    if (meta.get("shard"), meta.get("of")) != (i, n):
        return None, f"shard.json names {meta.get('shard')}/{meta.get('of')}, not {i}/{n}"
    for rid in ids:
        if rid not in recs:
            return None, f"names {rid}, not a record of this checkout"
        if shard_of(origin_host(recs[rid]), n) != i:
            return None, f"names {rid}, which is in shard {shard_of(origin_host(recs[rid]), n)}, not {i}"
    files = {p.name for p in (d / "verification").glob("*")} if (d / "verification").is_dir() else set()
    if files != {_file(r) for r in ids}:
        return None, f"files {sorted(files ^ {_file(r) for r in ids})} do not match its id list"
    for rid in ids:
        if json.loads((d / "verification" / _file(rid)).read_text()).get("record_id") != rid:
            return None, f"{_file(rid)} is not the result of {rid}"
    return ids, ""


def overlay(snapshot: Path, shards_dir: Path, out: Path, n: int, recs: dict[str, dict]) -> dict:
    """Copy the snapshot to `out`, then each accepted shard's files over it (a fresh file replaces the
    earlier one; a record without one keeps its earlier file). Returns what was accepted and why the
    rest was discarded: {"accepted": {I: ids}, "discarded": {I: why}, "fresh": [ids], "kept": [ids]}."""
    out.mkdir(parents=True, exist_ok=True)
    if snapshot.resolve() != out.resolve():
        shutil.copytree(snapshot, out, dirs_exist_ok=True)
    accepted, discarded = {}, {}
    for i in range(1, n + 1):
        ids, why = check_artifact(shards_dir / f"shard-{i}", i, n, recs)
        if ids is None:
            discarded[i] = why
            continue
        for rid in ids:
            shutil.copyfile(shards_dir / f"shard-{i}" / "verification" / _file(rid), out / _file(rid))
        accepted[i] = ids
    fresh = {rid for ids in accepted.values() for rid in ids}
    return {"accepted": accepted, "discarded": discarded, "fresh": [r for r in recs if r in fresh],
            "kept": [r for r in recs if r not in fresh]}


def _stamp(v: dict) -> float:
    return datetime.fromisoformat(v["checked_at"]).timestamp()


def timings(shards_dir: Path, accepted: dict[int, list[str]]) -> dict[int, dict]:
    """Per accepted shard: verify-step seconds, bytes hashed, and each record's seconds (from its
    `checked_at` to the next record's, the last to the step's end; a record's time therefore includes
    the next record's outline-input fetch)."""
    out = {}
    for i, ids in accepted.items():
        d = shards_dir / f"shard-{i}"
        meta = json.loads((d / "shard.json").read_text())
        vs = [json.loads((d / "verification" / _file(r)).read_text()) for r in ids]
        ends = [_stamp(v) for v in vs[1:]] + [float(meta.get("finished", 0))]
        out[i] = {"seconds": float(meta.get("finished", 0)) - float(meta.get("started", 0)),
                  "bytes": sum(f.get("bytes", 0) for v in vs for f in v.get("files", [])),
                  "records": {v["record_id"]: max(0.0, e - _stamp(v)) for v, e in zip(vs, ends, strict=True)}}
    return out


def summary_lines(r: dict, n: int, recs: dict[str, dict], times: dict[int, dict] | None = None) -> list[str]:
    times = times or {}
    lines = [f"### verify in {n} shards", "",
             (f"{len(r['fresh'])} of {len(recs)} records verified in this run; "
              f"{len(r['kept'])} keep their earlier result."), "",
             "| shard | records | verify step | bytes hashed | slowest record |", "|---|---|---|---|---|"]
    for i in range(1, n + 1):
        if i in r["discarded"]:
            lines.append(f"| {i}/{n} | {len(select(recs, i, n))} | **failed**: {r['discarded'][i]} | | |")
            continue
        t = times.get(i, {})
        slow = max(t.get("records", {}).items(), key=lambda kv: kv[1], default=None)
        lines.append(f"| {i}/{n} | {len(r['accepted'][i])} | {t.get('seconds', 0) / 60:.1f} min | "
                     f"{t.get('bytes', 0):,} | {f'{slow[0]} ({slow[1]:.0f} s)' if slow else ''} |")
    for i, why in r["discarded"].items():
        lines += ["", f"Shard {i}/{n} failed ({why}); its records keep their earlier results:",
                  *[f"- {rid}" for rid in select(recs, i, n)]]
    every = sorted(((s, rid) for t in times.values() for rid, s in t["records"].items()), reverse=True)[:10]
    if every:
        lines += ["", "Slowest records: " + ", ".join(f"{rid} ({s:.0f} s)" for s, rid in every)]
    if r["kept"]:
        lines += ["", "Records without a fresh result: " + " ".join(r["kept"])]
    return lines


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
    po = sub.add_parser("overlay", help="the finishing job: lay the accepted shards over the snapshot")
    po.add_argument("--snapshot", required=True)
    po.add_argument("--shards", required=True, help="the directory holding shard-<I>/")
    po.add_argument("--out", default=str(paths.VERIFICATION_DIR))
    po.add_argument("-n", type=int, default=SHARDS)
    po.add_argument("--fresh", required=True, help="write the freshly verified ids here, one per line")
    po.add_argument("--summary", help="write the step summary (markdown) here")
    ph = sub.add_parser("hosts", help="origin hosts per shard and the other hosts each shard reaches")
    ph.add_argument("-n", type=int, default=SHARDS)
    ph.add_argument("--vdir", help="verification results whose hashed files count as reached hosts")
    a = ap.parse_args(argv)
    recs = load_records()
    if a.cmd == "hosts":
        print(json.dumps(hosts(recs, a.n, Path(a.vdir) if a.vdir else None), indent=1))
        return 0
    r = overlay(Path(a.snapshot), Path(a.shards), Path(a.out), a.n, recs)
    Path(a.fresh).write_text("".join(rid + "\n" for rid in r["fresh"]))
    lines = summary_lines(r, a.n, recs, timings(Path(a.shards), r["accepted"]))
    if a.summary:
        Path(a.summary).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
