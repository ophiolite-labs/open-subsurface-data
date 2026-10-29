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
from . import shards as shards_mod
from . import starters as starters_mod
from . import verify as verify_mod
from .records import load_records, validate_outlines, validate_records
from .verify import apply_fidelity, conversion_coverage, http_open, is_stale, verify_all


def cmd_validate(a: argparse.Namespace) -> int:
    """Records, outlines and the starter packs (E40); with documents given, those starter documents alone,
    wherever they are (Ophiolite E129 runs `osd validate <pack>.json` before and after its upload)."""
    records_dir, starters_dir = Path(a.records), Path(a.starters)
    ev = starters_mod.Evidence(load_records(records_dir), Path(a.vdir), Path(a.custody))
    problems = [] if a.documents else validate_records(records_dir) + validate_outlines(Path(a.outlines), records_dir)
    for p in problems:
        print(f"  {p}")
    if a.documents:
        checked = []
        for d in map(Path, a.documents):
            try:
                doc = json.loads(d.read_text())
            except (OSError, ValueError) as e:
                checked.append((d, starters_mod.Result(problems=[str(e)])))
                continue
            inside = d.parent.resolve() == starters_dir.resolve()
            checked.append((d, starters_mod.check(doc, ev, d.parent, d.name if inside else None) if isinstance(doc, dict)
                            else starters_mod.Result(problems=["(root): not an object"])))
    else:
        checked = [(p, r) for p, _, r in starters_mod.check_dir(starters_dir, ev)]
    bad = 0
    for p, r in checked:
        bad += len(r.problems)
        for line in r.problems:
            print(f"  {p}: {line}")
        for line in r.unchecked:
            print(f"  {p}: unchecked here: {line}")
        for line in r.notes:
            print(f"  {p}: note: {line}")
    if a.documents:
        print(f"{len(checked)} starter documents, {bad} problems")
    else:
        print(f"{len(load_records(records_dir))} records, {len(checked)} starter packs, {len(problems) + bad} problems")
    return 1 if problems or bad else 0


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
    ids = a.ids or None
    if a.shard is not None:  # H2: the records whose origin host hashes to shard I of N
        if a.ids:
            print("refused: --shard selects the records itself; give either ids or --shard")
            return 2
        try:
            i, n = shards_mod.parse(a.shard)
        except ValueError as e:
            print(f"refused: {e}")
            return 2
        ids = shards_mod.select(load_records(), i, n)
        print(f"shard {i}/{n}: {len(ids)} records")
    results = verify_all(ids=ids, derive=a.outlines, fetch_inputs=a.outline_inputs) if ids != [] else []
    for v in results:
        o = v["origin"]
        l2 = "; ".join(f"{c['name']}: {c['outcome']} ({c.get('detail', '')})" for c in v["checks"] if c["level"] == "L2")
        l3 = "; ".join(f"{c['name']}: {c['outcome']} ({c.get('detail', '')})" for c in v["checks"] if c["level"] == "L3")
        l1 = next((c.get("detail", "") for c in v["checks"] if c["name"] == "origin-reachable"), "")
        print(f"  {v['level']}  {v['record_id']}  (origin {o.get('reachability')} HTTP {o.get('http_status')}: {l1}; "
              f"{l2}; {l3})")
    print(f"{len(results)} verified -> {paths.VERIFICATION_DIR}")
    if a.ids_out:
        Path(a.ids_out).write_text("".join(v["record_id"] + "\n" for v in results))
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
    if bool(a.ids) == bool(a.starter):
        print("refused: give record, collection or feature ids, or --starter <pack id>, not both")
        return 2
    try:
        doc = (manifest_mod.from_starter(a.starter, Path(a.catalog), a.catalog_url) if a.starter
               else manifest_mod.from_catalog(a.ids, Path(a.catalog), a.catalog_url))
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


def _store(a: argparse.Namespace):
    return mirror_mod.open_store(a.store, a.public_url)


def cmd_mirror_put(a: argparse.Namespace, opener=http_open) -> int:
    recs, rules, bad, to_copy = load_records(), mirror_mod.load_rules(), False, []
    dry = getattr(a, "dry_run", False)
    try:
        store = _store(a)
        if hasattr(store, "check"):
            store.check()               # HEAD on the bucket: the keys reach it
    except mirror_mod.MirrorError as e:
        print(f"refused: {e}")
        return 1
    for rid in a.ids:
        try:
            out = mirror_mod.put(recs[rid], build_mod.latest_verification(rid, Path(a.vdir)), rules.get(rid),
                                 store, opener, dry_run=dry)
        except mirror_mod.MirrorError as e:     # NotEligible, or the store refused
            print(f"refused: {e}")
            bad = True
            continue
        for c in out:
            print(f"  {c.outcome:11} {rid} {c.path} {c.sha256[:12]}  ({c.detail})")
            bad |= c.outcome in ("mismatch", "origin-dead")
            to_copy += [c] if c.outcome in ("would-copy", "would-finish") else []
    if dry:
        print(f"dry run: {len(to_copy)} files, {sum(c.bytes for c in to_copy)} bytes would be copied;"
              f" nothing written to {store.root}")
    tombs = sum(k.endswith(".removed.json") for k in store.keys("custody/"))
    print(f"store {store.root}: {len(store.keys('mirror/'))} objects, "
          f"{len(store.keys('custody/')) - tombs} custody documents, {tombs} tombstones")
    return 1 if bad else 0


def _uploaded(rid: str, out: list, store) -> None:
    for c in out:
        print(f"  {c.outcome:11} {rid} {c.path} {c.sha256[:12]}  ({c.bytes} bytes)")
    print(f"{len(out)} files, {sum(c.bytes for c in out)} bytes in {store.root}: "
          f"{sum(c.outcome == 'published' for c in out)} published, {sum(c.outcome == 'present' for c in out)} present")


def cmd_mirror_deposit(a: argparse.Namespace) -> int:
    """E41: no network but the store; the page and the licence text are files the person saved."""
    recs = load_records()
    if a.record_id not in recs:
        print(f"refused: no record {a.record_id}")
        return 1
    try:
        store = _store(a)
        if hasattr(store, "check"):
            store.check()
        out = mirror_mod.deposit(recs[a.record_id], Path(a.dir), store, obtained=a.obtained, by=a.by,
                                 page_url=a.page_url, page=Path(a.page), licence=Path(a.licence_text))
    except mirror_mod.MirrorError as e:
        print(f"refused: {e}")
        return 1
    _uploaded(a.record_id, out, store)
    return 0


def cmd_mirror_put_derived(a: argparse.Namespace) -> int:
    """E41: a starter pack's artefacts; no network but the store. Prints, per artefact, the custody
    key a recipe fills into its pack (matched on sha256 and bytes)."""
    path = Path(a.pack) if a.pack else starters_mod.STARTERS_DIR / starters_mod.file_name(a.pack_id)
    try:
        pack = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        print(f"refused: the pack document {path}: {e}")
        return 1
    bad = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
           for e in starters_mod._validator().iter_errors(pack)]
    if bad or pack["id"] != a.pack_id:
        print(f"refused: {path}: " + ("; ".join(bad) if bad else f"its id is {pack['id']}, not {a.pack_id}"))
        return 1
    recs = load_records()
    if pack["record_id"] not in recs:
        print(f"refused: no record {pack['record_id']}")
        return 1
    try:
        store = _store(a)
        if hasattr(store, "check"):
            store.check()
        out = mirror_mod.put_derived(pack, recs[pack["record_id"]], Path(a.dir), store)
    except mirror_mod.MirrorError as e:
        print(f"refused: {e}")
        return 1
    _uploaded(pack["record_id"], out, store)
    return 0


def cmd_mirror_custody(a: argparse.Namespace) -> int:
    try:
        names = mirror_mod.sync_custody(_store(a), Path(a.out))
    except mirror_mod.MirrorError as e:
        print(f"refused: {e}")
        return 1
    tombs = sum(n.endswith(".removed.json") for n in names)
    print(f"{len(names) - tombs} custody documents, {tombs} tombstones -> {a.out}")
    return 0


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
    pva = sub.add_parser("validate", help="records, outlines and starter packs against their schemas and rules")
    pva.add_argument("documents", nargs="*", help="starter documents to check alone, anywhere on disk (E40)")
    pva.add_argument("--records", default=str(paths.RECORDS_DIR))
    pva.add_argument("--outlines", default=str(paths.OUTLINES_DIR))
    pva.add_argument("--starters", default=str(starters_mod.STARTERS_DIR))
    pva.add_argument("--vdir", default=str(paths.VERIFICATION_DIR), help="latest verifications (absent: unchecked)")
    pva.add_argument("--custody", default=str(starters_mod.CUSTODY_DIR), help="custody documents (absent: unchecked)")
    pva.set_defaults(fn=cmd_validate)
    pv = sub.add_parser("verify", help="network: reach each origin, write verification records")
    pv.add_argument("ids", nargs="*")
    pv.add_argument("--outlines", action="store_true",
                    help="also fetch outline inputs and rewrite outlines/ (osd.outlines, E03)")
    pv.add_argument("--outline-inputs", action="store_true",
                    help="also fetch outline inputs and check the committed outlines against them (CI)")
    pv.add_argument("--fidelity-from", metavar="FILE",
                    help="offline: derive L4 for the one record id from a fidelity/1 record (E09)")
    pv.add_argument("--vdir", default=str(paths.VERIFICATION_DIR), help="with --fidelity-from: verifications")
    pv.add_argument("--shard", metavar="I/N", help="the records whose origin host hashes to shard I of N (H2)")
    pv.add_argument("--ids-out", metavar="FILE", help="write the ids verified, one per line")
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
    pm.add_argument("ids", nargs="*", help="record or collection ids, or feature ids (never a mix)")
    pm.add_argument("--starter", metavar="PACK_ID", help="one published starter pack, <record id>/<pack> (E40)")
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
    store_args.add_argument("--store", default=str(mirror_mod.MIRROR_DIR),
                            help="a local store directory, or s3://<bucket> (OSD_S3_ENDPOINT, OSD_S3_ACCESS_KEY,"
                                 " OSD_S3_SECRET_KEY from the environment)")
    store_args.add_argument("--public-url",
                            help="http(s) address the store is served at; custody hrefs start here (required"
                                 " for a local store; S3 default https://<bucket>.<endpoint host>/)")
    mp = msub.add_parser("put", parents=[store_args], help="network: copy eligible records' inventories")
    mp.add_argument("ids", nargs="+")
    mp.add_argument("--vdir", default=str(paths.VERIFICATION_DIR))
    mp.add_argument("--dry-run", action="store_true", help="read the store, say what would be copied, write nothing")
    mp.set_defaults(fn=cmd_mirror_put)
    md = msub.add_parser("deposit", parents=[store_args],
                         help="upload a publisher's download a maintainer obtained, with custody/2 deposit (E41;"
                              " no network but the store)")
    md.add_argument("record_id")
    md.add_argument("dir", help="the download as obtained, unmodified (regular files only)")
    md.add_argument("--obtained", required=True, help="when the files were obtained: YYYY-MM-DD or a UTC date-time")
    md.add_argument("--by", required=True, help="a role, never a name (maintainer)")
    md.add_argument("--page-url", required=True, help="the publisher's page the download came from")
    md.add_argument("--page", required=True, help="that page as the person saved it (page.html); kept as its sha256")
    md.add_argument("--licence-text", required=True,
                    help="the licence page or text as the person saved it; kept as the sha256 of its visible text")
    md.set_defaults(fn=cmd_mirror_deposit)
    mpd = msub.add_parser("put-derived", parents=[store_args],
                          help="upload a starter pack's artefacts with custody/2 derived (E41; no network but the store)")
    mpd.add_argument("pack_id", help="<record id>/<pack>, the starter/1 id")
    mpd.add_argument("dir", help="the artefacts as the recipe wrote them, by their pack paths")
    mpd.add_argument("--pack", help="the pack document (default starters/<record id with / as __>__<pack>.json)")
    mpd.set_defaults(fn=cmd_mirror_put_derived)
    mc = msub.add_parser("custody", parents=[store_args],
                         help="copy the store's custody documents and tombstones into a directory (for the build)")
    mc.add_argument("--out", required=True)
    mc.set_defaults(fn=cmd_mirror_custody)
    mr = msub.add_parser("remove", parents=[store_args], help="takedown: delete a copy, write its tombstone")
    mr.add_argument("sha256")
    mr.add_argument("--request", required=True, help="the approved takedown issue")
    mr.add_argument("--approved-by", required=True, help="the approving maintainer's GitHub login")
    mr.set_defaults(fn=cmd_mirror_remove)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
