"""Dead-link report: which records fell from L1 or higher to a dead origin since the last stored run.

Reads two verification directories (the stored results before a run, the results after it) and
the titles of the issues already open. Returns one issue per newly dead record, titled
"origin dead: <id>", with the HTTP class and the date it died. Never one for:
  blocked  a 403, 429 or challenge page awards no level and is not dead (OSD-D9)
  L0 before  it was not reachable last time either: the death is not new
  reported  an issue with the same title is already open
No network here: the `verify` workflow lists the open issues and creates the new ones.
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
    verb = "would open" if dry_run else "open"
    n = len(r["open"])
    lines = [(f"dead-link report{' (dry run)' if dry_run else ''}: {n} issue{'s' * (n != 1)} to open, "
             f"{len(r['reported'])} already reported, {len(r['blocked'])} blocked (no issue, OSD-D9)")]
    lines += [f"  {verb}  \"{i['title']}\"  {i['http_class']} on {i['died']}" for i in r["open"]]
    lines += [f"  skip  {rid}: an open issue already names it" for rid in r["reported"]]
    lines += [f"  skip  {rid}: blocked, not dead" for rid in r["blocked"]]
    return lines
