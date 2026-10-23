"""Validity is three tests, each with its own mutation (a single check can pass vacuously)."""
from osd.records import validate_outlines, validate_records


def test_repository_records_and_outlines_are_valid():
    assert validate_records() == []
    assert validate_outlines() == []


def test_schema_violation_is_reported(tmp_records):
    p = tmp_records / "acme" / "demo.yaml"
    p.write_text(p.read_text().replace("access: anonymous", "access: sometimes"))
    msgs = [str(x) for x in validate_records(tmp_records)]
    assert any("origin/access" in m for m in msgs), msgs


def test_id_must_match_path(tmp_records):
    p = tmp_records / "acme" / "demo.yaml"
    p.write_text(p.read_text().replace("id: acme/demo", "id: acme/other"))
    msgs = [str(x) for x in validate_records(tmp_records)]
    assert any("does not match the file path" in m for m in msgs), msgs


def test_outline_must_name_its_record(tmp_records, tmp_outlines):
    assert validate_outlines(tmp_outlines, tmp_records) == []
    bad = tmp_outlines / "acme__demo.geojson"
    bad.write_text(bad.read_text().replace('"record_id": "acme/demo"', '"record_id": "acme/nope"'))
    msgs = [str(x) for x in validate_outlines(tmp_outlines, tmp_records)]
    assert any("record_id" in m for m in msgs), msgs


def test_outline_without_record_is_reported(tmp_records, tmp_outlines):
    (tmp_outlines / "acme__ghost.geojson").write_text('{"type":"FeatureCollection","features":[]}')
    msgs = [str(x) for x in validate_outlines(tmp_outlines, tmp_records)]
    assert any("no record 'acme/ghost'" in m for m in msgs), msgs
