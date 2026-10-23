"""E08: the dead-link report (injected fetcher, no network) and `osd new` (injected page)."""

import shutil
from datetime import date

import pytest
import yaml

from osd import paths
from osd.cli import main
from osd.new import new_record, page_title, record_id, scaffold
from osd.records import validate_records
from osd.report import dead_reports, report_lines
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
    titles = tmp_path / "open.txt"
    titles.write_text("origin dead: acme/other\n")
    out = tmp_path / "issues.json"
    assert main(["report", "--before", str(before), "--after", str(after),
                 "--open-titles", str(titles), "--out", str(out), "--dry-run"]) == 0
    assert "would open" in capsys.readouterr().out
    assert '"title": "origin dead: acme/dies"' in out.read_text()


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
