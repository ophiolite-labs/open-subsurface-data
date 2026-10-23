import json

from osd.build import build
from osd.records import load_records


def test_build_joins_records_outlines_and_levels(tmp_path):
    vdir = tmp_path / "verification"
    vdir.mkdir()
    (vdir / "equinor__volve.json").write_text(json.dumps(
        {"record_id": "equinor/volve", "checked_at": "2026-10-23T12:00:00+00:00",
         "tool_version": "t", "level": "L1", "checks": []}))
    out = tmp_path / "catalog"
    n = build(out, vdir)
    assert n["records"] == len(load_records())
    recs = {r["id"]: r for r in json.loads((out / "records.json").read_text())["records"]}
    assert recs["equinor/volve"]["level"] == "L1"
    assert recs["nlog/nlog"]["level"] == "L0"
    fc = json.loads((out / "outlines.geojson").read_text())
    volve = [f for f in fc["features"] if f["properties"]["record_id"] == "equinor/volve"]
    assert volve and volve[0]["properties"]["level"] == "L1"
    assert volve[0]["properties"]["licence"] == "Equinor Open Data Licence"
    cols = json.loads((out / "collections.json").read_text())["collections"]
    assert any(c["license"] == "CC-BY-SA-4.0" for c in cols)
