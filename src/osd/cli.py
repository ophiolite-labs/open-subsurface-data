"""osd: validate | verify | build | status | new | report"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from . import build as build_mod
from . import new as new_mod
from . import paths
from . import report as report_mod
from .records import load_records, validate_outlines, validate_records
from .verify import is_stale, verify_all


def cmd_validate(_: argparse.Namespace) -> int:
    problems = validate_records() + validate_outlines()
    for p in problems:
        print(f"  {p}")
    n = len(load_records())
    print(f"{n} records, {len(problems)} problems")
    return 1 if problems else 0


def cmd_verify(a: argparse.Namespace) -> int:
    results = verify_all(ids=a.ids or None, derive=a.outlines, fetch_inputs=a.outline_inputs)
    for v in results:
        o = v["origin"]
        l2 = "; ".join(f"{c['name']}: {c['outcome']} ({c.get('detail', '')})" for c in v["checks"] if c["level"] == "L2")
        l3 = "; ".join(f"{c['name']}: {c['outcome']} ({c.get('detail', '')})" for c in v["checks"] if c["level"] == "L3")
        print(f"  {v['level']}  {v['record_id']}  (origin {o.get('reachability')} HTTP {o.get('http_status')}; {l2}; {l3})")
    print(f"{len(results)} verified -> {paths.VERIFICATION_DIR}")
    return 0


def cmd_build(_: argparse.Namespace) -> int:
    n = build_mod.build()
    print(f"built {n} -> {paths.CATALOG_DIR}")
    return 0


def status_lines(vdir: Path = paths.VERIFICATION_DIR, now: datetime | None = None) -> list[str]:
    """The levels `osd build` publishes, read from the same verification directory."""
    lines = [f"{'level':5} {'id':36} {'checked':36} {'access':12} {'redistribution':14} kinds"]
    for rid, r in load_records().items():
        v = build_mod.latest_verification(rid, vdir)
        lv, checked = (v["level"], v["checked_at"]) if v else ("L0", None)
        when = (checked or "never")[:10] + (" stale" if is_stale(checked, now) else "")
        blocked = (v or {}).get("origin", {}).get("blocked_since")
        when += f" blocked since {blocked[:10]}" if blocked else ""
        lines.append(f"{lv:5} {rid:36} {when:36} {r['origin']['access']:12} "
                     f"{r['licence']['redistribution']:14} {','.join(r['kinds'])}")
    return lines


def cmd_status(_: argparse.Namespace) -> int:
    print("\n".join(status_lines()))
    return 0


def cmd_new(a: argparse.Namespace) -> int:
    try:
        out = new_mod.new_record(a.url, title=a.title, rid=a.id, records_dir=paths.RECORDS_DIR)
    except FileExistsError as e:
        print(f"refused: {e}")
        return 1
    rel = str(out.relative_to(paths.RECORDS_DIR))
    todo: dict[str, str] = {}  # field -> its last problem (an enum's choices beat "not a string")
    for p in validate_records(paths.RECORDS_DIR):
        if p.path == rel:
            field, _, why = p.message.partition(": ")
            todo[field] = why
    print(f"wrote {out}; {len(todo)} fields for a human to fill from the publisher's page:")
    for field, why in todo.items():
        print(f"  {field}: {why}")
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    titles = set(Path(a.open_titles).read_text().splitlines()) if a.open_titles else set()
    r = report_mod.dead_reports(Path(a.before), Path(a.after), titles)
    print("\n".join(report_mod.report_lines(r, a.dry_run)))
    if a.out:
        Path(a.out).write_text(json.dumps(r["open"], indent=2) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="osd", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="records and outlines against their schemas").set_defaults(fn=cmd_validate)
    pv = sub.add_parser("verify", help="network: reach each origin, write verification records")
    pv.add_argument("ids", nargs="*")
    pv.add_argument("--outlines", action="store_true",
                    help="also fetch outline inputs and rewrite outlines/ (osd.outlines, E03)")
    pv.add_argument("--outline-inputs", action="store_true",
                    help="also fetch outline inputs and check the committed outlines against them (CI)")
    pv.set_defaults(fn=cmd_verify)
    sub.add_parser("build", help="write build/catalog").set_defaults(fn=cmd_build)
    sub.add_parser("status", help="one line per record").set_defaults(fn=cmd_status)
    pn = sub.add_parser("new", help="scaffold records/<id>.yaml from a dataset page (reads its title)")
    pn.add_argument("url")
    pn.add_argument("--id", help="publisher/dataset (default: from the address)")
    pn.add_argument("--title", help="skip reading the page")
    pn.set_defaults(fn=cmd_new)
    pr = sub.add_parser("report", help="dead-link report: records that fell from L1+ to a dead origin")
    pr.add_argument("--before", required=True, help="verification results stored before the run")
    pr.add_argument("--after", default=str(paths.VERIFICATION_DIR), help="results after the run")
    pr.add_argument("--open-titles", help="file with the titles of open issues, one per line")
    pr.add_argument("--out", help="write the issues to open as JSON")
    pr.add_argument("--dry-run", action="store_true", help="say 'would open'; the workflow opens nothing")
    pr.set_defaults(fn=cmd_report)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
