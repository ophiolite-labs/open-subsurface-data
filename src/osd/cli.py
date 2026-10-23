"""osd: validate | verify | build | status"""

from __future__ import annotations

import argparse
import sys

from . import build as build_mod
from . import paths
from .records import load_records, validate_outlines, validate_records
from .verify import verify_all


def cmd_validate(_: argparse.Namespace) -> int:
    problems = validate_records() + validate_outlines()
    for p in problems:
        print(f"  {p}")
    n = len(load_records())
    print(f"{n} records, {len(problems)} problems")
    return 1 if problems else 0


def cmd_verify(a: argparse.Namespace) -> int:
    results = verify_all(ids=a.ids or None)
    for v in results:
        print(f"  {v['level']}  {v['record_id']}  (origin HTTP {v['origin'].get('http_status')})")
    print(f"{len(results)} verified -> {paths.VERIFICATION_DIR}")
    return 0


def cmd_build(_: argparse.Namespace) -> int:
    n = build_mod.build()
    print(f"built {n} -> {paths.CATALOG_DIR}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    recs = load_records()
    print(f"{'level':5} {'id':28} {'access':12} {'redistribution':14} kinds")
    for rid, r in recs.items():
        v = build_mod.latest_verification(rid)
        lv = v["level"] if v else "L0"
        print(f"{lv:5} {rid:28} {r['origin']['access']:12} {r['licence']['redistribution']:14} "
              f"{','.join(r['kinds'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="osd", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="records and outlines against their schemas").set_defaults(fn=cmd_validate)
    pv = sub.add_parser("verify", help="network: reach each origin, write verification records")
    pv.add_argument("ids", nargs="*")
    pv.set_defaults(fn=cmd_verify)
    sub.add_parser("build", help="write build/catalog").set_defaults(fn=cmd_build)
    sub.add_parser("status", help="one line per record").set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
