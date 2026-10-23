import copy
import json
import re
import subprocess
from datetime import UTC, datetime, timedelta

import pytest
from jsonschema import Draft202012Validator, ValidationError

from osd import paths
from osd.build import build
from osd.cli import status_lines
from osd.records import load_record, load_records
from osd.verify import (
    USER_AGENT,
    ByteBudget,
    Fetched,
    FetchError,
    Pacer,
    is_stale,
    level_from_checks,
    load_samples,
    verify_all,
    verify_record,
)

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
REC = load_record(paths.RECORDS_DIR / "terranubis" / "f3-demo-2020.yaml")
BASE = "https://fixture.test/"
CHALLENGE = b"<html><head><title>Just a moment...</title></head><body>cf-chl</body></html>"


def fetch_ok(url):
    return Fetched(200, url, "text/html", 12)


def fetch_dead(url):
    return Fetched(404, url, "", 12)


class Counting:
    """A fake fetcher answering from a list, one answer per call; the last answer repeats."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), 0

    def __call__(self, url):
        a = self.answers[min(self.calls, len(self.answers) - 1)]
        self.calls += 1
        return a if isinstance(a, Fetched) else a(url)


def timeout(url):
    return Fetched(0, url, "", 20000, error="timeout")


def dir_opener(root, calls=None):
    """Serve https://fixture.test/<path> from a local directory, in small chunks."""

    def open_(url):
        if calls is not None:
            calls.append(url)
        p = root / url[len(BASE):].split("?")[0] if url.startswith(BASE) else None
        if p is None or not p.is_file():
            raise FetchError(url, 404)
        data = p.read_bytes()
        return iter([data[i:i + 7] for i in range(0, len(data), 7)])

    return open_


def l2_fixture(tmp_path, files=None, licence="Licence text, version one."):
    files = files or {"a.sgy": b"alpha" * 100, "b.las": b"bravo" * 33, "c.csv": b"x,y\n1,2\n"}
    for name, data in files.items():
        (tmp_path / "data" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / name).write_bytes(data)
    (tmp_path / "data" / "README.txt").write_text("not in the sample")
    listing = [{"path": f"data/{n}", "href": f"data/{n}"} for n in [*files, "README.txt"]]
    (tmp_path / "index.json").write_text(json.dumps({"files": listing}))
    (tmp_path / "licence.html").write_text(
        f"<html><head><script>var t={datetime.now().timestamp()}</script></head><body><p>{licence}</p></body></html>")
    rec = copy.deepcopy(REC)
    rec["origin"]["manifest_url"] = BASE + "index.json"
    rec["licence"]["url"] = BASE + "licence.html"
    return rec


SAMPLE = ["*.sgy", "*.las", "*.csv"]


def outcome(v, name):
    return next(c for c in v["checks"] if c["name"] == name)


# --- L1: reachability classes ------------------------------------------------------------

@pytest.mark.parametrize("answer,level,origin_outcome,needle", [
    (Fetched(200, "https://terranubis.com/x", "text/html", 5), "L1", "pass", "HTTP 200"),
    (Fetched(403, "https://terranubis.com/x", "text/html", 5, body=CHALLENGE), "L0", "skip",
     "blocked from this runner"),
    (Fetched(404, "https://terranubis.com/x", "", 5), "L0", "fail", "HTTP 404"),
    (Fetched(0, "https://terranubis.com/x", "", 20000, error="timeout"), "L0", "fail", "timeout"),
], ids=["ok", "blocked", "dead", "timeout"])
def test_classification_four_fetchers(answer, level, origin_outcome, needle):
    v = verify_record(REC, Counting(answer), None, now=NOW)
    c = outcome(v, "origin-reachable")
    assert (v["level"], c["outcome"]) == (level, origin_outcome)
    assert needle in c["detail"]


def test_timeout_is_retried_once():
    f = Counting(timeout)
    v = verify_record(REC, f, None, now=NOW)
    assert f.calls == 2
    assert v["origin"]["reachability"] == "dead"


def test_timeout_then_ok_is_L1():
    v = verify_record(REC, Counting(timeout, fetch_ok), None, now=NOW)
    assert v["level"] == "L1"


def test_dns_failure_is_dead_without_retry():
    f = Counting(Fetched(0, REC["origin"]["url"], "", 3, error="dns"))
    v = verify_record(REC, f, None, now=NOW)
    assert (f.calls, v["level"], v["origin"]["reachability"]) == (1, "L0", "dead")


@pytest.mark.parametrize("status", [200, 503])
def test_challenge_body_is_blocked_at_any_status(status):
    v = verify_record(REC, Counting(Fetched(status, REC["origin"]["url"], "text/html", 5, body=CHALLENGE)),
                      None, now=NOW)
    assert (v["origin"]["reachability"], v["level"]) == ("blocked", "L0")


def test_blocked_since_keeps_the_first_date():
    blocked = Counting(Fetched(403, REC["origin"]["url"], "text/html", 5))
    first = verify_record(REC, blocked, None, now=NOW - timedelta(days=9))
    second = verify_record(REC, blocked, None, now=NOW, previous=first)
    assert second["origin"]["blocked_since"] == first["checked_at"]
    assert "blocked since 2026-10-14" in outcome(second, "origin-reachable")["detail"]
    healed = verify_record(REC, fetch_ok, None, now=NOW, previous=second)
    again = verify_record(REC, blocked, None, now=NOW + timedelta(days=1), previous=healed)
    assert again["origin"]["blocked_since"] == again["checked_at"]


@pytest.mark.parametrize("status", [401, 410, 500])
def test_every_other_status_is_dead(status):
    v = verify_record(REC, Counting(Fetched(status, REC["origin"]["url"], "", 5)), None, now=NOW)
    assert (v["origin"]["reachability"], v["level"]) == ("dead", "L0")


def test_moved_host_passes_with_hint():
    v = verify_record(REC, Counting(Fetched(200, "https://elsewhere.example/x", "text/html", 5)), None, now=NOW)
    c = outcome(v, "origin-reachable")
    assert (v["origin"]["reachability"], c["outcome"]) == ("moved", "pass")
    assert "elsewhere.example" in c["detail"] and "known_issues" in c["detail"]


def test_reachable_origin_with_placeholder_outline_is_L1():
    outline = json.loads(paths.outline_path(REC["id"]).read_text())
    v = verify_record(REC, fetch_ok, outline, now=NOW)
    assert v["level"] == "L1"
    names = {c["name"]: c["outcome"] for c in v["checks"]}
    assert names["origin-reachable"] == "pass"
    assert names["outline-derived"] == "fail"  # approximate: true


def test_dead_origin_is_L0():
    v = verify_record(REC, fetch_dead, None, now=NOW)
    assert v["level"] == "L0"


# --- L2: files and licence ---------------------------------------------------------------

def test_l2_checksums_match_sha256sum(tmp_path):
    rec = l2_fixture(tmp_path)
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert len(v["files"]) == 3
    for f in v["files"]:
        local = tmp_path / f["path"]
        expected = subprocess.run(["sha256sum", str(local)], capture_output=True, text=True,
                                  check=True).stdout.split()[0]
        assert f["sha256"] == expected
        assert f["bytes"] == local.stat().st_size
    assert outcome(v, "files-checksummed")["outcome"] == "pass"
    assert outcome(v, "licence-text-captured")["outcome"] == "pass"
    assert v["level"] == "L2"


def test_only_allow_listed_files_are_hashed(tmp_path):
    rec = l2_fixture(tmp_path)
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=["*.las"])
    assert [f["path"] for f in v["files"]] == ["data/b.las"]


def test_no_sample_stays_L1(tmp_path):
    rec = l2_fixture(tmp_path)
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=None)
    c = outcome(v, "files-checksummed")
    assert (c["outcome"], v["level"]) == ("skip", "L1")
    assert "samples.yaml" in c["detail"]


def test_sample_cut_at_byte_budget(tmp_path):
    rec = l2_fixture(tmp_path)
    budget = ByteBudget(600)  # a.sgy is 500 bytes, b.las 165: the second cannot fit
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE,
                      budget=budget)
    assert [f["path"] for f in v["files"]] == ["data/a.sgy"]
    assert "sample cut" in outcome(v, "files-checksummed")["detail"]
    assert budget.used <= 600


def test_robots_disallow_skips_l2(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /index.json\n")
    calls = []
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path, calls), sample=SAMPLE)
    c = outcome(v, "files-checksummed")
    assert c["outcome"] == "skip" and "robots.txt" in c["detail"]
    assert BASE + "index.json" not in calls


def test_empty_selection_fails(tmp_path):
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=["*.zip"])
    assert (outcome(v, "files-checksummed")["outcome"], v["level"]) == ("fail", "L1")
    assert "files" not in v


def test_failed_file_fetch_prevents_L2(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "data" / "b.las").unlink()
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    c = outcome(v, "files-checksummed")
    assert (c["outcome"], v["level"]) == ("fail", "L1")
    assert "data/b.las" in c["detail"]


def test_failed_or_absent_licence_prevents_L2(tmp_path):
    rec = l2_fixture(tmp_path)
    (tmp_path / "licence.html").unlink()
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert (outcome(v, "licence-text-captured")["outcome"], v["level"]) == ("fail", "L1")
    del rec["licence"]["url"]
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert (outcome(v, "licence-text-captured")["outcome"], v["level"]) == ("skip", "L1")
    (tmp_path / "licence.html").write_bytes(CHALLENGE)
    rec["licence"]["url"] = BASE + "licence.html"
    v = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert (outcome(v, "licence-text-captured")["outcome"], v["level"]) == ("fail", "L1")


def test_licence_text_change_is_a_finding(tmp_path):
    rec = l2_fixture(tmp_path, licence="Licence text, version one.")
    first = verify_record(rec, fetch_ok, None, now=NOW - timedelta(days=3), opener=dir_opener(tmp_path), sample=SAMPLE)
    assert outcome(first, "licence-text-captured")["detail"].startswith("26 characters captured")
    assert first["licence_text"] == "Licence text, version one."
    l2_fixture(tmp_path, licence="Licence text, version one.")  # new script timestamp, same text
    same = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE, previous=first)
    assert "changed" not in outcome(same, "licence-text-captured")["detail"]  # script churn ignored
    l2_fixture(tmp_path, licence="Licence text, version two.")
    second = verify_record(rec, fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE, previous=first)
    c = outcome(second, "licence-text-captured")
    assert c["outcome"] == "pass"
    assert c["detail"] == "licence text changed since 2026-10-20"
    assert second["licence_text_sha256"] != first["licence_text_sha256"]


def test_verify_all_compares_with_the_previous_run(tmp_path, monkeypatch):
    rec = l2_fixture(tmp_path)
    monkeypatch.setattr("osd.verify.load_records", lambda: {rec["id"]: rec})
    monkeypatch.setattr("osd.verify.load_samples", lambda: {rec["id"]: SAMPLE})
    out = tmp_path / "verification"
    verify_all(fetch=fetch_ok, opener=dir_opener(tmp_path), out_dir=out)
    l2_fixture(tmp_path, licence="Rewritten terms.")
    (v,) = verify_all(fetch=fetch_ok, opener=dir_opener(tmp_path), out_dir=out)
    assert outcome(v, "licence-text-captured")["detail"].startswith("licence text changed since")


# --- rate and identity -------------------------------------------------------------------

def test_pacer_waits_two_seconds_per_host():
    t, slept = [100.0], []
    p = Pacer(clock=lambda: t[0], sleep=lambda s: (slept.append(s), t.__setitem__(0, t[0] + s)))
    p.wait("https://a.example/1")
    p.done("https://a.example/1")
    t[0] += 0.5
    p.wait("https://b.example/1")  # another host: no pause
    p.done("https://b.example/1")
    p.wait("https://a.example/2")
    assert slept == [pytest.approx(1.5)]


def test_user_agent_names_the_repository():
    assert "github.com/ophiolite-labs/open-subsurface-data" in USER_AGENT


# --- schema, build, status ---------------------------------------------------------------

def schema(name):
    return Draft202012Validator(json.loads((paths.SCHEMA_DIR / name).read_text()))


def test_verification_record_matches_schema(tmp_path):
    v = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path), sample=SAMPLE)
    assert v["level"] == "L2"
    schema("verification.schema.json").validate(v)
    for f in (timeout, Fetched(403, "https://x", "", 1, body=CHALLENGE)):
        schema("verification.schema.json").validate(verify_record(REC, Counting(f), None, now=NOW))
    cut = verify_record(l2_fixture(tmp_path), fetch_ok, None, now=NOW, opener=dir_opener(tmp_path),
                        sample=SAMPLE, budget=ByteBudget(600))
    schema("verification.schema.json").validate(cut)


def test_v1_verification_record_still_validates():
    v1 = {"record_id": "equinor/volve", "checked_at": "2026-10-23T12:00:00+00:00", "tool_version": "0.1.0",
          "level": "L1", "checks": [{"name": "origin-reachable", "level": "L1", "outcome": "pass",
                                     "detail": "HTTP 200"}],
          "origin": {"http_status": 200, "final_url": "https://x", "content_type": "text/html", "elapsed_ms": 3}}
    schema("verification.schema.json").validate(v1)


def test_samples_name_records_with_a_listing():
    recs = load_records()
    samples = load_samples()
    assert len(samples) >= 3
    for rid, globs in samples.items():
        assert recs[rid]["origin"].get("manifest_url"), rid
        assert globs and all(isinstance(g, str) and g for g in globs), rid


def test_record_schema_has_no_tool_policy():
    assert "verification" not in schema("record.schema.json").schema["properties"]  # OSD-D11


def test_stale_after_30_days():
    assert not is_stale("2026-09-24T12:00:00+00:00", NOW)
    assert is_stale("2026-09-22T12:00:00+00:00", NOW)
    assert is_stale(None, NOW)


def test_records_json_levels_equal_status_levels(tmp_path):
    vdir = tmp_path / "verification"
    vdir.mkdir()
    levels = {"equinor/volve": "L1", "sodir/factpages": "L2", "seg/open-data-wiki": "L0"}
    for rid, lv in levels.items():
        origin = {"reachability": "blocked", "blocked_since": "2026-10-20T00:00:00+00:00"} if lv == "L0" else {}
        (vdir / (rid.replace("/", "__") + ".json")).write_text(json.dumps(
            {"record_id": rid, "checked_at": "2026-08-01T00:00:00+00:00", "tool_version": "t",
             "level": lv, "checks": [], "origin": origin}))
    out = tmp_path / "catalog"
    build(out, vdir, now=NOW)
    published = {r["id"]: (r["level"], r["stale"], (r["blocked_since"] or "")[:10])
                 for r in json.loads((out / "records.json").read_text())["records"]}
    printed = {}
    for line in status_lines(vdir, now=NOW)[1:]:
        lv, rid, *_ = line.split()
        m = re.search(r"blocked since (\S+)", line)
        printed[rid] = (lv, "stale" in line, m.group(1) if m else "")
    assert published == printed
    assert published["sodir/factpages"] == ("L2", True, "")
    assert published["seg/open-data-wiki"] == ("L0", True, "2026-10-20")
    assert published["terranubis/f3-demo-2020"] == ("L0", True, "")


def test_level_ladder_has_no_gaps():
    # L2 passing cannot lift the level over a failed L1
    checks = [{"name": "a", "level": "L1", "outcome": "fail"},
              {"name": "b", "level": "L2", "outcome": "pass"}]
    assert level_from_checks(checks) == "L0"
    checks[0]["outcome"] = "pass"
    assert level_from_checks(checks) == "L2"
    # a skipped check at a level stops the ladder there
    checks.append({"name": "c", "level": "L3", "outcome": "skip"})
    assert level_from_checks(checks) == "L2"


def test_fetch_error_message_names_the_status():
    assert "HTTP 403" in str(FetchError("https://x", 403))


def test_verify_all_never_writes_an_invalid_record(tmp_path, monkeypatch):
    monkeypatch.setattr("osd.verify.load_records", lambda: {REC["id"]: REC})
    monkeypatch.setattr("osd.verify.verify_record", lambda *a, **k: {"record_id": REC["id"], "level": "L9"})
    with pytest.raises(ValidationError):
        verify_all(fetch=fetch_ok, out_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []
