import json
from datetime import UTC, datetime

from jsonschema import Draft202012Validator

from osd import paths
from osd.records import load_record
from osd.verify import Fetched, level_from_checks, verify_record

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
REC = load_record(paths.RECORDS_DIR / "terranubis" / "f3-demo-2020.yaml")


def fetch_ok(url):
    return Fetched(200, url, "text/html", 12)


def fetch_dead(url):
    return Fetched(404, url, "", 12)


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


def test_verification_record_matches_schema():
    schema = json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text())
    v = verify_record(REC, fetch_ok, None, now=NOW)
    Draft202012Validator(schema).validate(v)


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
