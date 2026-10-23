"""osd: validate | verify | build | status | new | report | manifest | get | mirror"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from . import build as build_mod
from . import get as get_mod
from . import manifest as manifest_mod
from . import mirror as mirror_mod
from . import new as new_mod
from . import paths
from . import reasons as reasons_mod
from . import report as report_mod
from . import verify as verify_mod
from .records import load_records, validate_outlines, validate_records
from .verify import apply_fidelity, conversion_coverage, http_open, is_stale, verify_all


def cmd_validate(_: argparse.Namespace) -> int:
    problems = validate_records() + validate_outlines()
    for p in problems:
        print(f"  {p}")
    n = len(load_records())
    print(f"{n} records, {len(problems)} problems")
    return 1 if problems else 0


def cmd_fidelity(a: argparse.Namespace) -> int:
    """osd verify <id> --fidelity-from F: offline, the L4 rule (E09). Writes the verification back."""
    if len(a.ids) != 1:
        print("refused: --fidelity-from takes exactly one record id, the record the fidelity is for")
        return 2
    (rid,) = a.ids
    vdir = Path(a.vdir)
    try:
        doc = json.loads(Path(a.fidelity_from).read_text())
    except (OSError, ValueError) as e:
        print(f"refused: {a.fidelity_from}: {e}")
        return 1
    v, reasons = apply_fidelity(rid, doc if isinstance(doc, dict) else {}, build_mod.latest_verification(rid, vdir))
    if v is None:
        print(f"refused: {reasons[0]}")
        return 1
    verify_mod._validator().validate(v)   # never write a record the schema refuses
    (vdir / (rid.replace("/", "__") + ".json")).write_text(json.dumps(v, indent=2) + "\n")
    c = next(c for c in v["checks"] if c["name"] == "canonical-conversion")
    if c["outcome"] == "fail":
        for r in reasons:
            print(f"  {v['level']}  {rid}  fidelity rejected: {r}")
        return 1
    print(f"  {v['level']}  {rid}  canonical-conversion: pass ({c['detail']})")
    for r in reasons:
        print(f"  {v['level']}  {rid}  L4 not awarded: {r}")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    if a.fidelity_from:
        return cmd_fidelity(a)
    results = verify_all(ids=a.ids or None, derive=a.outlines, fetch_inputs=a.outline_inputs)
    for v in results:
        o = v["origin"]
        l2 = "; ".join(f"{c['name']}: {c['outcome']} ({c.get('detail', '')})" for c in v["checks"] if c["level"] == "L2")
        l3 = "; ".join(f"{c['name']}: {c['outcome']} ({c.get('detail', '')})" for c in v["checks"] if c["level"] == "L3")
        l1 = next((c.get("detail", "") for c in v["checks"] if c["name"] == "origin-reachable"), "")
        print(f"  {v['level']}  {v['record_id']}  (origin {o.get('reachability')} HTTP {o.get('http_status')}: {l1}; "
              f"{l2}; {l3})")
    print(f"{len(results)} verified -> {paths.VERIFICATION_DIR}")
    return 0


def cmd_build(_: argparse.Namespace) -> int:
    n = build_mod.build()
    print(f"built {n} -> {paths.CATALOG_DIR}")
    return 0


def terms_note(rec: dict, now: datetime | None = None) -> str:
    """"terms expire D" for a publisher-stated absolute `licence.terms.expires` (record/3, E19). The
    date is a UTC calendar day and the terms hold through its end; nothing is computed from a
    duration. Empty when the record states no date."""
    x = (rec.get("licence", {}).get("terms") or {}).get("expires")
    if x is None:
        return ""
    try:
        if not isinstance(x, date) and not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", str(x)):
            raise ValueError(x)
        day = x if isinstance(x, date) else date.fromisoformat(x)
    except ValueError:
        return f"terms expire ? ({x!r} is not a date)"
    today = (now or datetime.now(UTC)).astimezone(UTC).date()
    if today > day:
        return f"terms expired {day.isoformat()}"
    return f"terms expire {day.isoformat()}" + (" (today)" if today == day else "")


def status_lines(vdir: Path = paths.VERIFICATION_DIR, now: datetime | None = None,
                 records_dir: Path = paths.RECORDS_DIR) -> list[str]:
    """The levels `osd build` publishes, read from the same verification directory; an L4 shows
    its coverage beside it, "L4 (2 of 2 converted)" (E09), and a stated expiry of the terms,
    "L1 (terms expire 2027-01-01)" (E19); every line ends with the reason, the string records.json
    carries (osd.reasons, E23/E27)."""
    rows = []
    for rid, r in load_records(records_dir).items():
        v = build_mod.latest_verification(rid, vdir)
        lv, checked = (v["level"], v["checked_at"]) if v else ("L0", None)
        coverage = conversion_coverage(v)
        lv += f" ({coverage})" if coverage else ""
        terms = terms_note(r, now)
        lv += f" ({terms})" if terms else ""
        when = (checked or "never")[:10] + (" stale" if is_stale(checked, now) else "")
        blocked = (v or {}).get("origin", {}).get("blocked_since")
        when += f" blocked since {blocked[:10]}" if blocked else ""
        rows.append((lv, (f"{rid:36} {when:36} {r['origin']['access']:12} "
                          f"{r['licence']['redistribution']:14}"), ",".join(r["kinds"]), reasons_mod.reason(v, r)))
    w = max([5] + [len(lv) for lv, *_ in rows])
    k = max([5] + [len(kinds) for _, _, kinds, _ in rows])
    return ([f"{'level':{w}} {'id':36} {'checked':36} {'access':12} {'redistribution':14} {'kinds':{k}} reason"]
            + [f"{lv:{w}} {rest} {kinds:{k}} {why}".rstrip() for lv, rest, kinds, why in rows])


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
    issues = report_mod.read_issues(Path(a.open_issues) if a.open_issues else None)
    verified = "all" if a.verified.strip() in ("", "all") else set(a.verified.split())
    r = report_mod.report(Path(a.before), Path(a.after), issues, verified, a.run_url)
    print("\n".join(report_mod.report_lines(r, a.dry_run)))
    if a.out:  # the workflow reads .open[] and .recovered[] (and mutates nothing on a dry run)
        Path(a.out).write_text(json.dumps({"open": r["open"], "recovered": r["recovered"]}, indent=2) + "\n")
    return 0


def cmd_manifest(a: argparse.Namespace) -> int:
    try:
        doc = manifest_mod.from_catalog(a.ids, Path(a.catalog), a.catalog_url)
    except manifest_mod.ManifestError as e:
        print(f"refused: {e}")
        return 1
    out = manifest_mod.write(doc, Path(a.out))
    n = sum(len(e["assets"]) for e in doc["entries"])
    todo = sum(1 for e in doc["entries"] if not e["assets"])
    print(f"wrote {out}: {len(doc['entries'])} {doc['selection']}, {n} assets, {todo} to-do")
    return 0


def cmd_get(a: argparse.Namespace) -> int:
    try:
        m = manifest_mod.read(a.manifest)
        outcomes = get_mod.get(m, Path(a.dest))
    except manifest_mod.ManifestError as e:
        print(f"refused: {e}")
        return 1
    print("\n".join(get_mod.summary(m, outcomes)))
    print(f"attribution -> {Path(a.dest) / 'ATTRIBUTION.md'}")
    return 1 if get_mod.failed(outcomes) else 0


def cmd_mirror_eligible(a: argparse.Namespace) -> int:
    rules, n, total = mirror_mod.load_rules(), 0, 0
    for rid, rec in load_records().items():
        if a.ids and rid not in a.ids:
            continue
        e = mirror_mod.eligibility(rec, build_mod.latest_verification(rid, Path(a.vdir)), rules.get(rid))
        n, total = n + e.eligible, total + (e.bytes if e.eligible else 0)
        why = f"{len(e.files)} files, {e.bytes} bytes" if e.eligible else "; ".join(e.reasons)
        print(f"  {'eligible' if e.eligible else 'no':8} {rid:40} {why}")
    print(f"{n} eligible, {total} bytes of inventory")
    return 0


def _store(a: argparse.Namespace) -> mirror_mod.LocalDirectory:
    return mirror_mod.LocalDirectory(Path(a.store), a.public_url)


def cmd_mirror_put(a: argparse.Namespace, opener=http_open) -> int:
    recs, rules, store, bad = load_records(), mirror_mod.load_rules(), _store(a), False
    for rid in a.ids:
        try:
            out = mirror_mod.put(recs[rid], build_mod.latest_verification(rid, Path(a.vdir)), rules.get(rid),
                                 store, opener)
        except mirror_mod.NotEligible as e:
            print(f"refused: {e}")
            bad = True
            continue
        for c in out:
            print(f"  {c.outcome:11} {rid} {c.path} {c.sha256[:12]}  ({c.detail})")
            bad |= c.outcome in ("mismatch", "origin-dead")
    tombs = sum(k.endswith(".removed.json") for k in store.keys("custody/"))
    print(f"store {store.root}: {len(store.keys('mirror/'))} objects, "
          f"{len(store.keys('custody/')) - tombs} custody documents, {tombs} tombstones")
    return 1 if bad else 0


def cmd_mirror_remove(a: argparse.Namespace) -> int:
    try:
        gone = mirror_mod.remove(a.sha256, _store(a), request=a.request, approved_by=a.approved_by)
    except mirror_mod.MirrorError as e:
        print(f"refused: {e}")
        return 1
    for k in gone:
        print(f"  deleted   {k}")
    print(f"  tombstone custody/{a.sha256}.removed.json (osd mirror never copies this digest again)")
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
    pv.add_argument("--fidelity-from", metavar="FILE",
                    help="offline: derive L4 for the one record id from a fidelity/1 record (E09)")
    pv.add_argument("--vdir", default=str(paths.VERIFICATION_DIR), help="with --fidelity-from: verifications")
    pv.set_defaults(fn=cmd_verify)
    sub.add_parser("build", help="write build/catalog").set_defaults(fn=cmd_build)
    sub.add_parser("status", help="one line per record").set_defaults(fn=cmd_status)
    pn = sub.add_parser("new", help="scaffold records/<id>.yaml from a dataset page (reads its title)")
    pn.add_argument("url")
    pn.add_argument("--id", help="publisher/dataset (default: from the address)")
    pn.add_argument("--title", help="skip reading the page")
    pn.set_defaults(fn=cmd_new)
    pr = sub.add_parser("report", help="dead-link report: origins that fell from L1+ to dead, and open issues that recovered")
    pr.add_argument("--before", required=True, help="verification results stored before the run")
    pr.add_argument("--after", default=str(paths.VERIFICATION_DIR), help="results after the run")
    pr.add_argument("--open-issues", help="the open origin-dead issues, `gh issue list --json number,title,labels`;"
                                          " absent or unreadable: nothing is opened or closed")
    pr.add_argument("--verified", default="all", help="the ids this run verified, space separated ('all' or empty: every record)")
    pr.add_argument("--run-url", default="", help="the run named in a closing comment")
    pr.add_argument("--out", help='write {"open": [...], "recovered": [...]} as JSON')
    pr.add_argument("--dry-run", action="store_true", help="say 'would open/close'; the workflow mutates nothing")
    pr.set_defaults(fn=cmd_report)
    pm = sub.add_parser("manifest", help="write a retrieval manifest from the built catalogue")
    pm.add_argument("ids", nargs="+", help="record or collection ids, or feature ids (never a mix)")
    pm.add_argument("-o", "--out", default="manifest.json")
    pm.add_argument("--catalog", default=str(paths.CATALOG_DIR), help="the built catalogue (osd build)")
    pm.add_argument("--catalog-url", default=manifest_mod.CATALOG_URL)
    pm.set_defaults(fn=cmd_manifest)
    pg = sub.add_parser("get", help="network: fetch a manifest's assets, verify, write ATTRIBUTION.md")
    pg.add_argument("manifest")
    pg.add_argument("--dest", required=True)
    pg.set_defaults(fn=cmd_get)
    pmi = sub.add_parser("mirror", help="the mirror store: eligibility, copies, takedown (E07)")
    msub = pmi.add_subparsers(dest="mirror_cmd", required=True)
    me = msub.add_parser("eligible", help="which records may be mirrored, and why not (offline)")
    me.add_argument("ids", nargs="*")
    me.add_argument("--vdir", default=str(paths.VERIFICATION_DIR))
    me.set_defaults(fn=cmd_mirror_eligible)
    store_args = argparse.ArgumentParser(add_help=False)
    store_args.add_argument("--store", default=str(mirror_mod.MIRROR_DIR), help="local store directory (slice 1)")
    store_args.add_argument("--public-url", required=True,
                            help="http(s) address the store is served at; custody hrefs start here")
    mp = msub.add_parser("put", parents=[store_args], help="network: copy eligible records' inventories")
    mp.add_argument("ids", nargs="+")
    mp.add_argument("--vdir", default=str(paths.VERIFICATION_DIR))
    mp.set_defaults(fn=cmd_mirror_put)
    mr = msub.add_parser("remove", parents=[store_args], help="takedown: delete a copy, write its tombstone")
    mr.add_argument("sha256")
    mr.add_argument("--request", required=True, help="the approved takedown issue")
    mr.add_argument("--approved-by", required=True, help="the approving maintainer's GitHub login")
    mr.set_defaults(fn=cmd_mirror_remove)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
