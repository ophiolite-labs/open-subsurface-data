"""Dead-link report: which records fell from L1 or higher to a dead origin since the last stored run,
and which open origin-dead issues this run saw answer again (H1).

Reads two verification directories (the stored results before a run, the results after it) and
the open `origin-dead` issues as `gh issue list --json number,title,labels` writes them. Returns
one issue per newly dead record, titled "origin dead: <id>", with the HTTP class and the date it
died. Never one for:
  blocked  a 403, 429 or challenge page awards no level and is not dead (OSD-D9)
  L0 before  it was not reachable last time either: the death is not new
  reported  an issue with the same title is already open
And one close per open issue, by number, whose record this run verified (a partial run keeps
older results: they are not an observation) and found at L1 or above, whatever it stood at before.
If the open issues could not be listed, nothing is opened and nothing is closed.
No network here: the `verify` workflow lists the open issues, creates and closes them.
"""

from __future__ import annotations

import json
from pathlib import Path

TITLE = "origin dead: {}"
LABEL = "origin-dead"


def _results(vdir: Path) -> dict[str, dict]:
    out = {}
    for p in sorted(vdir.glob("*.json")) if vdir.is_dir() else []:
        v = json.loads(p.read_text())
        out[v["record_id"]] = v
    return out


def _l1(v: dict) -> str:
    return next((c.get("detail", "") for c in v.get("checks", []) if c["name"] == "origin-reachable"), "")


def http_class(v: dict) -> str:
    """HTTP 404 (4xx), HTTP 503 (5xx), or the failure with no HTTP answer (dns, timeout, connection)."""
    status = v.get("origin", {}).get("http_status") or 0
    if status:
        return f"HTTP {status} ({status // 100}xx)"
    kind = _l1(v).split(" at ", 1)[0] or "error"
    return f"no HTTP answer ({kind})"


def _body(rid: str, before: dict, after: dict) -> str:
    o = after.get("origin", {})
    return "\n".join([
        f"The origin of `{rid}` stopped answering: **{http_class(after)}** on **{after['checked_at'][:10]}**.",
        "",
        "| | level | checked | origin |",
        "|---|---|---|---|",
        f"| before | {before['level']} | {before['checked_at']} | {_l1(before)} |",
        f"| now | {after['level']} | {after['checked_at']} | {_l1(after)} |",
        "",
        f"Final URL: {o.get('final_url', '')}",
        "",
        ("Opened by the dead-link report of the `verify` workflow (`osd report`). If the publisher "
        "moved the data, update `origin.url` in the record; if it is gone, add a `known_issues` "
        "line. Close this issue when a later verify run reaches the origin again."),
    ])


def read_issues(path: Path | None) -> list[dict] | None:
    """The open issues `gh issue list --json number,title,labels` wrote, or None when they could not
    be listed (no file, an empty file after a failed `gh`, anything else than that array)."""
    try:
        issues = json.loads(path.read_text()) if path else None
    except (OSError, ValueError):
        return None
    if not isinstance(issues, list) or not all(
            isinstance(i, dict) and isinstance(i.get("number"), int) and isinstance(i.get("title"), str)
            for i in issues):
        return None
    return issues


def _labelled(issue: dict) -> bool:
    return LABEL in {lb.get("name") for lb in issue.get("labels") or [] if isinstance(lb, dict)}


def _comment(rid: str, v: dict, run_url: str) -> str:
    o = v.get("origin", {})
    run = f"[run {run_url.rstrip('/').rsplit('/', 1)[-1]}]({run_url})" if run_url else "a local run"
    return (f"The origin of `{rid}` answers again: {run} of the `verify` workflow observed it at "
            f"**{v['level']}** on {v['checked_at']} (origin HTTP {o.get('http_status')} from "
            f"{o.get('final_url', '')}). Closed by the dead-link report (`osd report`).")


def recovered(after_dir: Path, issues: list[dict], verified: set[str] | str, run_url: str = "") -> list[dict]:
    """Open origin-dead issues to close: the record was verified in this run ("all" or the ids the
    run was given) and now stands at L1 or above. Sorted by issue number."""
    after = _results(after_dir)
    prefix, out = TITLE.format(""), []
    for i in sorted(issues, key=lambda i: i["number"]):
        if not _labelled(i) or not i["title"].startswith(prefix):
            continue
        rid = i["title"][len(prefix):]
        v = after.get(rid)  # exact title: "origin dead: <id>" and nothing around the id
        if v is None:
            continue  # no result for that record (renamed or removed)
        if verified != "all" and rid not in verified:
            continue  # a result kept from an earlier run is not an observation of this one
        if v.get("level", "L0") == "L0":
            continue
        o = v.get("origin", {})
        out.append({"number": i["number"], "record_id": rid, "title": i["title"], "level": v["level"],
                    "checked_at": v["checked_at"], "http_status": o.get("http_status"),
                    "comment": _comment(rid, v, run_url)})
    return out


def report(before_dir: Path, after_dir: Path, issues: list[dict] | None, verified: set[str] | str,
           run_url: str = "") -> dict:
    """The `--out` document {"open": [...], "recovered": [...]} plus what was skipped and why;
    `issues` None (not listed) empties both lists."""
    if issues is None:
        r = dead_reports(before_dir, after_dir)
        return {**r, "open": [], "recovered": [], "unlisted": True}
    r = dead_reports(before_dir, after_dir, {i["title"] for i in issues})
    return {**r, "recovered": recovered(after_dir, issues, verified, run_url), "unlisted": False}


def dead_reports(before_dir: Path, after_dir: Path, open_titles: set[str] = frozenset()) -> dict:
    """{"open": [issue...], "reported": [id...], "blocked": [id...]}, each sorted by record id."""
    before, after = _results(before_dir), _results(after_dir)
    out: dict[str, list] = {"open": [], "reported": [], "blocked": []}
    for rid, a in sorted(after.items()):
        b = before.get(rid)
        if not b or b.get("level", "L0") == "L0":
            continue  # never verified before, or not reachable last time either
        reach = a.get("origin", {}).get("reachability")
        if reach == "blocked":
            out["blocked"].append(rid)
            continue
        if reach != "dead" or a["level"] != "L0":
            continue
        title = TITLE.format(rid)
        if title in open_titles:
            out["reported"].append(rid)
            continue
        out["open"].append({"record_id": rid, "title": title, "http_class": http_class(a),
                            "died": a["checked_at"][:10], "label": LABEL, "body": _body(rid, b, a)})
    return out


def report_lines(r: dict, dry_run: bool) -> list[str]:
    verb, close = ("would open", "would close") if dry_run else ("open", "close")
    n, k = len(r["open"]), len(r.get("recovered", []))
    lines = [(f"dead-link report{' (dry run)' if dry_run else ''}: {n} issue{'s' * (n != 1)} to open, "
             f"{len(r['reported'])} already reported, {len(r['blocked'])} blocked (no issue, OSD-D9)"
             + (f", {k} to close (recovered)" if "recovered" in r else ""))]
    if r.get("unlisted"):
        lines.append("  the open origin-dead issues could not be listed: no issue opened or closed")
    lines += [f"  {verb}  \"{i['title']}\"  {i['http_class']} on {i['died']}" for i in r["open"]]
    lines += [f"  {close}  #{i['number']} \"{i['title']}\"  {i['level']} on {i['checked_at']}, "
              f"origin HTTP {i['http_status']}" for i in r.get("recovered", [])]
    lines += [f"  skip  {rid}: an open issue already names it" for rid in r["reported"]]
    lines += [f"  skip  {rid}: blocked, not dead" for rid in r["blocked"]]
    return lines
