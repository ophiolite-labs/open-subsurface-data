"""E08: the dead-link report (injected fetcher, no network) and `osd new` (injected page). H1: open
origin-dead issues close when this run sees the origin answer again; the workflow's report step runs
here with a fake `gh` (no network, no issue touched)."""

import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import date

import pytest
import yaml

from osd import paths
from osd.cli import main
from osd.new import new_record, page_title, record_id, scaffold
from osd.records import validate_records
from osd.report import dead_reports, read_issues, recovered, report, report_lines
from osd.verify import Fetched, verify_all


def rec(rid):
    return {"id": rid, "title": rid, "publisher": {"name": "Acme", "url": "https://acme.example"},
            "origin": {"url": f"https://acme.example/{rid.split('/')[1]}", "access": "anonymous"},
            "licence": {"name": "CC BY 4.0", "redistribution": "allowed", "attribution": "required"},
            "kinds": ["seismic-3d"], "region": {}, "listed_by": ["community"], "added": "2026-10-23"}


RECS = {r["id"]: r for r in map(rec, ["acme/dies", "acme/blocks", "acme/stays", "acme/was-dead"])}
ANSWERS = {  # status per record, before the run and after it
    "dies": (200, 404), "blocks": (200, 403), "stays": (200, 200), "was-dead": (404, 404)}


def fetcher(phase):
    def fetch(url):
        return Fetched(ANSWERS[url.rsplit("/", 1)[1]][phase], url, "text/html", 5)
    return fetch


@pytest.fixture
def runs(tmp_path, monkeypatch):
    """A stored run, then a later run over the same records with one origin gone and one blocked."""
    monkeypatch.setattr("osd.verify.load_records", lambda: RECS)
    monkeypatch.setattr("osd.verify.load_samples", dict)
    monkeypatch.setattr("osd.paths.outline_path", lambda rid: tmp_path / "none.geojson")
    before, after = tmp_path / "before", tmp_path / "after"
    verify_all(fetch=fetcher(0), out_dir=before)
    shutil.copytree(before, after)
    verify_all(fetch=fetcher(1), out_dir=after)
    return before, after


def test_404_after_a_stored_L1_opens_exactly_one_issue(runs):
    r = dead_reports(*runs)
    assert [i["title"] for i in r["open"]] == ["origin dead: acme/dies"]
    (issue,) = r["open"]
    assert issue["http_class"] == "HTTP 404 (4xx)"
    assert issue["died"] == date.today().isoformat()
    assert "HTTP 404 (4xx)" in issue["body"] and "| before | L1 |" in issue["body"]
    assert report_lines(r, dry_run=True) == [
        "dead-link report (dry run): 1 issue to open, 0 already reported, 1 blocked (no issue, OSD-D9)",
        f'  would open  "origin dead: acme/dies"  HTTP 404 (4xx) on {date.today().isoformat()}',
        "  skip  acme/blocks: blocked, not dead",
    ]


def test_blocked_never_opens_an_issue(runs):
    r = dead_reports(*runs)
    assert r["blocked"] == ["acme/blocks"]
    assert "acme/blocks" not in [i["record_id"] for i in r["open"]]


def test_a_record_already_reported_opens_nothing(runs):
    r = dead_reports(*runs, open_titles={"origin dead: acme/dies"})
    assert r["open"] == [] and r["reported"] == ["acme/dies"]


def test_dead_last_time_too_is_not_new(runs):
    assert "acme/was-dead" not in [i["record_id"] for i in dead_reports(*runs)["open"]]


def test_a_record_not_reverified_opens_nothing(runs):
    before, _ = runs
    assert dead_reports(before, before)["open"] == []


def test_no_answer_names_the_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("osd.verify.load_records", lambda: {"acme/dies": RECS["acme/dies"]})
    monkeypatch.setattr("osd.verify.load_samples", dict)
    monkeypatch.setattr("osd.paths.outline_path", lambda rid: tmp_path / "none.geojson")
    verify_all(fetch=fetcher(0), out_dir=tmp_path / "b")
    shutil.copytree(tmp_path / "b", tmp_path / "a")
    verify_all(fetch=lambda u: Fetched(0, u, "", 5, error="dns"), out_dir=tmp_path / "a")
    (issue,) = dead_reports(tmp_path / "b", tmp_path / "a")["open"]
    assert issue["http_class"] == "no HTTP answer (dns)"


def test_cli_report_writes_the_issues_for_the_workflow(runs, tmp_path, capsys):
    before, after = runs
    issues = tmp_path / "open.json"
    issues.write_text(json.dumps([{"number": 3, "title": "origin dead: acme/other", "labels": []}]))
    out = tmp_path / "report.json"
    assert main(["report", "--before", str(before), "--after", str(after),
                 "--open-issues", str(issues), "--out", str(out), "--dry-run"]) == 0
    assert "would open" in capsys.readouterr().out
    doc = json.loads(out.read_text())
    assert set(doc) == {"open", "recovered"}
    assert [i["title"] for i in doc["open"]] == ["origin dead: acme/dies"] and doc["recovered"] == []


# --- H1: recovery --------------------------------------------------------------------------------

FIXTURES = paths.ROOT / "tests" / "fixtures" / "report"
BACK = {  # status per record before and after; kept is left out of the run's ids
    "back": (404, 200), "up": (200, 200), "kept": (200, 200), "still-dead": (404, 404),
    "blocks": (404, 403), "dies": (200, 404)}
BACK_RECS = {r["id"]: r for r in map(rec, [f"acme/{k}" for k in BACK])}
VERIFIED = {f"acme/{k}" for k in BACK} - {"acme/kept"}
IDS = " ".join(sorted(VERIFIED))  # as the workflow passes steps.ids.outputs.ids


@pytest.fixture
def back(tmp_path, monkeypatch):
    """Stored results, then a partial run that verified every record but acme/kept."""
    monkeypatch.setattr("osd.verify.load_records", lambda: BACK_RECS)
    monkeypatch.setattr("osd.verify.load_samples", dict)
    before, after = tmp_path / "before", tmp_path / "after"

    def answer(phase):
        return lambda url: Fetched(BACK[url.rsplit("/", 1)[1]][phase], url, "text/html", 5)

    verify_all(fetch=answer(0), out_dir=before)
    shutil.copytree(before, after)
    verify_all(ids=sorted(VERIFIED), fetch=answer(1), out_dir=after)
    return before, after


def issues():
    return json.loads((FIXTURES / "open-issues.json").read_text())


def closes(after, issue_list=None, verified=VERIFIED):
    return [r["record_id"] for r in recovered(after, issues() if issue_list is None else issue_list, verified)]


def test_previous_L0_now_L1_counts_as_recovered(back):
    # mutation: recovery behind dead_reports' "not reachable last time either" skip -> acme/back lost
    assert closes(back[1]) == ["acme/back", "acme/up"]


def test_retained_result_not_verified_this_run_is_not_recovered(back):
    # mutation: the verified ids ignored -> acme/kept (a stored L1 from an earlier run) closed
    assert "acme/kept" not in closes(back[1])
    assert "acme/kept" in closes(back[1], verified="all")


def test_dead_or_blocked_is_not_recovered(back):
    # mutation: the level test dropped -> acme/still-dead and acme/blocks closed
    got = closes(back[1])
    assert "acme/still-dead" not in got and "acme/blocks" not in got


def test_record_absent_is_not_recovered(back):
    # mutation: an absent result treated as reachable -> #27 (acme/gone, no such record) closed
    assert "acme/gone" not in closes(back[1], verified="all")


def test_recovered_needs_an_open_issue_with_the_exact_title_and_label(back):
    # mutation: the title or label match dropped -> a near title or an unlabelled issue closed
    label = [{"name": "origin-dead"}]
    near = [{"number": 1, "title": "origin dead: acme/up (again)", "labels": label},
            {"number": 2, "title": "Origin dead: acme/up", "labels": label},
            {"number": 3, "title": "origin dead: acme/up", "labels": [{"name": "bug"}]},
            {"number": 4, "title": "origin dead:acme/up", "labels": label}]
    assert closes(back[1], near) == []
    assert closes(back[1], []) == []  # no open issue: nothing to close, even for an L1 record


def test_recovered_closes_by_number_with_the_run_named(back):
    # mutation: the run left out of the comment, or the issue named by title -> red
    run = "https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/123456"
    got = {r["number"]: r for r in recovered(back[1], issues(), VERIFIED, run)}
    assert sorted(got) == [17, 23]
    r = got[17]
    v = json.loads((back[1] / "acme__back.json").read_text())
    assert (r["record_id"], r["level"], r["checked_at"], r["http_status"]) == ("acme/back", "L1", v["checked_at"], 200)
    assert r["comment"] == (
        f"The origin of `acme/back` answers again: [run 123456]({run}) of the `verify` workflow observed "
        f"it at **L1** on {v['checked_at']} (origin HTTP 200 from https://acme.example/back). "
        "Closed by the dead-link report (`osd report`).")


def test_issue_enumeration_failure_mutates_nothing(back, tmp_path):
    # mutation: an unreadable issue list read as "none open" -> acme/dies would be opened again
    for bad in ["", "not json", '{"message": "HTTP 502"}', '[{"title": "origin dead: acme/up"}]']:
        (tmp_path / "issues.json").write_text(bad)
        assert read_issues(tmp_path / "issues.json") is None
    assert read_issues(tmp_path / "missing.json") is None and read_issues(None) is None
    r = report(*back, None, VERIFIED)
    assert (r["open"], r["recovered"]) == ([], [])
    assert "  the open origin-dead issues could not be listed: no issue opened or closed" in report_lines(r, False)
    assert [i["record_id"] for i in report(*back, [], VERIFIED)["open"]] == ["acme/dies"]


# --- H1: the workflow's report step, run as the workflow runs it --------------------------------

GH = """#!{py}
import json, os, sys
a, path = sys.argv[1:], os.environ["GH_STATE"]
st = json.load(open(path))
if a[:2] == ["issue", "list"]:
    if st.get("fail"):
        sys.exit("gh: HTTP 502")
    label = a[a.index("--label") + 1] if "--label" in a else None
    print(json.dumps([i for i in st["issues"] if label is None or label in [x["name"] for x in i["labels"]]]))
    sys.exit(0)
with open(os.environ["GH_LOG"], "a") as log:
    log.write(json.dumps(a) + "\\n")
if a[:2] == ["issue", "create"]:
    st["issues"].append({{"number": st["next"], "title": a[a.index("--title") + 1],
                         "labels": [{{"name": a[a.index("--label") + 1]}}]}})
    st["next"] += 1
elif a[:2] == ["issue", "close"]:
    st["issues"] = [i for i in st["issues"] if i["number"] != int(a[2])]
json.dump(st, open(path, "w"))
"""
UV = """#!/bin/sh
[ "$1" = run ] && [ "$2" = osd ] || exit 2
shift 2
exec {py} -m osd.cli "$@"
"""


def report_step():
    wf = yaml.safe_load((paths.ROOT / ".github" / "workflows" / "verify.yml").read_text())
    (step,) = [s for s in wf["jobs"]["verify"]["steps"] if s.get("name", "").startswith("dead-link report")]
    assert "${{" not in step["run"]  # the script reads only its env, so this test runs it unchanged
    return step


class Repo:
    """A workdir with build/verification-before and build/verification, a fake gh with issue state."""

    def __init__(self, tmp_path, before, after, issue_list, fail=False):
        self.dir, self.bin = tmp_path / "work", tmp_path / "bin"
        self.bin.mkdir()
        shutil.copytree(before, self.dir / "build" / "verification-before")
        shutil.copytree(after, self.dir / "build" / "verification")
        for name, text in (("gh", GH.format(py=sys.executable)), ("uv", UV.format(py=sys.executable))):
            (self.bin / name).write_text(text)
            (self.bin / name).chmod((self.bin / name).stat().st_mode | stat.S_IEXEC)
        self.state, self.log = tmp_path / "gh.json", tmp_path / "gh.log"
        self.state.write_text(json.dumps({"issues": issue_list, "next": 100, "fail": fail}))
        self.log.write_text("")

    def run(self, event="workflow_dispatch", ref="refs/heads/main", ids=IDS):
        step = report_step()
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "EVENT": event, "REF": ref,
               "IDS": ids, "RUN_URL": "https://github.com/o/r/actions/runs/42", "GH_STATE": str(self.state),
               "GH_LOG": str(self.log), "GITHUB_STEP_SUMMARY": str(self.dir / "summary.md"), "GH_TOKEN": "x",
               "PYTHONPATH": str(paths.ROOT / "src")}
        p = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]],
                           cwd=self.dir, env=env, capture_output=True, text=True, timeout=60, check=False)
        assert p.returncode == 0, p.stderr
        return p.stdout

    def mutations(self) -> list[list[str]]:
        return [json.loads(x) for x in self.log.read_text().splitlines()]

    def open_numbers(self) -> list[int]:
        return sorted(i["number"] for i in json.loads(self.state.read_text())["issues"])


def test_workflow_consumes_open_and_recovered(back, tmp_path):
    # mutation: the step reads the old array (`jq '.[]'`) or skips .recovered[] -> no create/close
    repo = Repo(tmp_path, *back, issues())
    out = repo.run()
    assert "close  #17" in out
    got = repo.mutations()
    assert [m[:3] for m in got] == [["label", "create", "origin-dead"], ["issue", "create", "--title"],
                                    ["issue", "close", "17"], ["issue", "close", "23"]]
    assert got[1][3] == "origin dead: acme/dies" and got[1][-2:] == ["--label", "origin-dead"]
    assert got[2][3] == "--comment" and "[run 42](https://github.com/o/r/actions/runs/42)" in got[2][4]
    assert "observed it at **L1**" in got[2][4] and "origin HTTP 200" in got[2][4]
    assert repo.open_numbers() == [24, 25, 26, 27, 100]


@pytest.mark.parametrize("event,ref", [("pull_request", "refs/pull/9/merge"),
                                       ("workflow_dispatch", "refs/heads/h1-origins-that-recover-and-hide")])
def test_dry_run_mutates_nothing(back, tmp_path, event, ref):
    # mutation: the step's `[ -z "$dry" ]` guard removed -> issues created and closed from a branch
    repo = Repo(tmp_path, *back, issues())
    out = repo.run(event, ref)
    assert "(dry run)" in out and 'would open  "origin dead: acme/dies"' in out and "would close  #17" in out
    assert repo.mutations() == []


def test_two_runs_against_one_issue_state_mutate_once(back, tmp_path):
    # mutation: the open dedupe by listed issues removed -> the second run opens acme/dies again
    repo = Repo(tmp_path, *back, issues())
    repo.run()
    first = repo.mutations()
    repo.run()
    assert repo.mutations() == first  # the closed issues are not listed, the opened one is: nothing new


def test_failed_issue_listing_in_the_workflow_mutates_nothing(back, tmp_path):
    # mutation: `|| : > open-issues.json` replaced by an empty list `[]` -> acme/dies opened
    repo = Repo(tmp_path, *back, issues(), fail=True)
    out = repo.run()
    assert "could not be listed: no issue opened or closed" in out
    assert repo.mutations() == []


# --- osd new -------------------------------------------------------------------------------

PAGE = b"<html><head><title>\n  Example X &amp; friends </title></head><body>x</body></html>"


def test_osd_new_fails_validation_only_on_the_human_fields(tmp_path):
    records = tmp_path / "records"
    out = new_record("https://example.org/x", fetch=lambda u: Fetched(200, u, "text/html", 5, PAGE),
                     records_dir=records, today=date(2026, 10, 23))
    assert out == records / "example" / "x.yaml"
    data = yaml.safe_load(out.read_text())
    assert data["title"] == "Example X & friends"
    assert data["origin"]["url"] == "https://example.org/x"
    assert [p.message for p in validate_records(records)] == [
        "kinds: [] should be non-empty",
        "licence/attribution: None is not of type 'string'",
        "licence/attribution: None is not one of ['required', 'not-required', 'unknown']",
        "licence/name: None is not of type 'string'",
        "licence/redistribution: None is not of type 'string'",
        "licence/redistribution: None is not one of ['allowed', 'restricted', 'forbidden', 'unknown']",
        "origin/access: None is not of type 'string'",
        "origin/access: None is not one of ['anonymous', 'registration', 'api', 'request', 'purchase']",
        "publisher/name: None is not of type 'string'",
    ]


def test_osd_new_keeps_the_template_shape():
    tpl = yaml.safe_load((paths.RECORDS_DIR / "_template.yaml").read_text())
    got = yaml.safe_load(scaffold("https://a.example/b", "T", "a/b", date.today()))
    assert set(got) == set(tpl) - {"summary"}  # a summary is the publisher's words, never scaffolded


def test_osd_new_refuses_to_overwrite(tmp_records):
    with pytest.raises(FileExistsError):
        new_record("https://acme.example/demo", title="Demo", records_dir=tmp_records)


@pytest.mark.parametrize("url,rid", [
    ("https://example.org/x", "example/x"),
    ("https://www.data.equinor.com/Volve_Data.html", "equinor/volve-data"),
    ("https://nlog.nl/", "nlog/dataset"),
])
def test_record_id_from_the_address(url, rid):
    assert record_id(url) == rid


def test_page_without_title():
    assert page_title(b"<html><body>no title</body></html>") is None


def test_cli_new_lists_each_field_once(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("osd.paths.RECORDS_DIR", tmp_path)
    assert main(["new", "https://example.org/x", "--title", "Example X"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].endswith("6 fields for a human to fill from the publisher's page:")
    assert [line.split(":")[0].strip() for line in out[1:]] == [
        "kinds", "licence/attribution", "licence/name", "licence/redistribution", "origin/access", "publisher/name"]
