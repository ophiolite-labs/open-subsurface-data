"""E46 areas that hold data (charter E46-areas-that-hold-data.md, strategy -STRATEGY.md): area/1, the count
in osd build, areas.json and records[].areas. Slice 0: the contract over tests/fixtures/areas/ (README there)."""

import copy
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from osd import areas, cli, paths
from osd.build import build

FIX = Path(__file__).parent / "fixtures" / "areas"
GOLDEN = FIX / "areas.json"


def _build(tmp_path: Path, areas_dir: Path = FIX / "areas") -> Path:
    out = tmp_path / "catalog"
    (tmp_path / "noverif").mkdir(exist_ok=True)
    build(out, tmp_path / "noverif", now=datetime(2026, 11, 25, tzinfo=UTC), mirror_dir=tmp_path / "nomirror",
          records_dir=FIX / "records", source_commit=None, verification_commit=None,
          starters_dir=tmp_path / "nostarters", areas_dir=areas_dir, outlines_dir=FIX / "outlines")
    return out


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    return _build(tmp_path_factory.mktemp("areas"))


def _areas(built: Path, rid: str) -> dict:
    return {r["id"]: r for r in json.loads((built / "records.json").read_text())["records"]}[rid]["areas"]


# --- acceptance 1: area/1 ---------------------------------------------------------------------------

def test_area_schema_id_is_area_1():
    assert areas.schema()["$id"] == "https://open-subsurface-data.org/schema/area/1"
    for p in areas.area_files(FIX / "areas"):
        assert not list(areas.validator().iter_errors(json.loads(p.read_text()))), p


# --- acceptance 2: the golden index and the six records, one by one ---------------------------------

def test_fixture_areas_json_equals_the_golden_file(built):
    assert (built / "areas.json").read_bytes() == GOLDEN.read_bytes()


def test_register_with_wells_lights_two_basins_and_not_its_box(built):
    """Wells in basins 1001 and 1002 light both; the well at (3, 3) lies in Atlantis South's hole, so it
    lights the enclave Carpania and not Atlantis South; the well in the sea lights nothing; the box middle
    (17, 7) in Borduria East is not used because the register has outlines."""
    assert _areas(built, "fixture/register") == {
        "country": ["XA", "XB", "XC"], "province": ["XA-N", "XB-W"], "basin": ["usgs-1001", "usgs-1002"]}


def test_survey_across_a_border_lights_both_countries_and_a_basin_its_line_crosses(built):
    """The polygon spans Atlantis and Borduria; its 2D line crosses basin 1002 with no vertex (and no
    middle) inside it: the edge crossing lights it."""
    assert _areas(built, "fixture/survey") == {
        "country": ["XA", "XB"], "province": ["XA-S", "XB-W"], "basin": ["usgs-1002"]}


def test_bbox_only_dataset_counts_by_its_box_middle(built):
    assert _areas(built, "fixture/boxed") == {"country": ["XA"], "province": ["XA-N"], "basin": ["usgs-1001"]}


def test_national_dataset_lights_its_country_only(built):
    """national, no outline: its country; its box middle (15, 3) in Borduria East and basin 1002 is not used."""
    assert _areas(built, "fixture/national") == {"country": ["XB"], "province": [], "basin": []}


def test_dataset_with_nothing_lights_nothing(built):
    assert _areas(built, "fixture/nothing") == {"country": [], "province": [], "basin": []}


def test_box_middle_in_the_sea_falls_back_to_its_country(built):
    """Box middle (-3, 5) is in no country: the record counts for region.country (inbox 1, accepted)."""
    assert _areas(built, "fixture/offshore") == {"country": ["XA"], "province": [], "basin": []}


def test_fixture_outputs_validate_and_agree_both_ways(built):
    """areas.json against #/$defs/index, each areas-<kind>.geojson against #/$defs/drawn; every id is a
    record, n = len(ids), no area holds nothing, and records[].areas equals the index both ways."""
    index = json.loads((built / "areas.json").read_text())
    assert not list(areas.validator("index").iter_errors(index))
    recs = {r["id"]: r for r in json.loads((built / "records.json").read_text())["records"]}
    from_index = {(k, a["area_id"], rid) for k, v in index["kinds"].items() for a in v["areas"] for rid in a["ids"]}
    from_records = {(k, aid, rid) for rid, r in recs.items() for k, ids in r["areas"].items() for aid in ids}
    assert from_index == from_records
    assert all(set(r["areas"]) == set(index["kinds"]) for r in recs.values())
    for k, v in index["kinds"].items():
        assert all(a["n"] == len(a["ids"]) >= 1 and set(a["ids"]) <= set(recs) for a in v["areas"])
        drawn = json.loads((built / f"areas-{k}.geojson").read_text())
        assert not list(areas.validator("drawn").iter_errors(drawn))
        assert [(f["properties"]["area_id"], f["properties"]["n"]) for f in drawn["features"]] == \
            [(a["area_id"], a["n"]) for a in v["areas"]]
        assert all(f["id"] == areas.drawn_id(k, f["properties"]["area_id"]) for f in drawn["features"])
    assert "usgs-1003" not in {a["area_id"] for a in index["kinds"]["basin"]["areas"]}   # holds nothing


def test_labels_lie_inside_their_area(built):
    index = json.loads((built / "areas.json").read_text())
    feats = {(k, f["properties"]["area_id"]): f for k in areas.CORE for _, f in areas.AreaSet.load(FIX / "areas").features(k)}
    for k, v in index["kinds"].items():
        for a in v["areas"]:
            ki = areas.KindIndex([feats[(k, a["area_id"])]])
            assert any(p.contains(*a["label"]) for p in ki.parts), (k, a["area_id"])


# --- acceptance 3: an empty areas/ -------------------------------------------------------------------

def test_empty_areas_dir_writes_empty_index_and_no_record_key(tmp_path):
    (tmp_path / "empty").mkdir()
    out = _build(tmp_path, tmp_path / "empty")
    index = json.loads((out / "areas.json").read_text())
    assert index == {"version": "areas/1", "kinds": {k: {"sources": [], "areas": []} for k in areas.CORE}}
    assert not list(areas.validator("index").iter_errors(index))
    assert not any("areas" in r for r in json.loads((out / "records.json").read_text())["records"])
    assert not list(out.glob("areas-*.geojson"))


def test_live_page_requests_none_of_the_new_files():
    """First load unchanged (acceptance 8, the half this lane holds): the live page names no area file."""
    for name in ("app.js", "index.html"):
        p = paths.ROOT / "site" / name
        if p.exists():
            assert "areas" not in p.read_text(), name


# --- guards (acceptance 7 and the Codex findings) ------------------------------------------------------

def _poly(*rings):
    return {"type": "Feature", "properties": {"area_id": "XA", "name": "A"},
            "geometry": {"type": "Polygon", "coordinates": [list(map(list, r)) for r in rings]}}


SQUARE = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
HOLE = [(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)]


def test_point_beyond_a_hole_is_outside():
    ki = areas.KindIndex([_poly(SQUARE, HOLE)])
    sh = areas.Shapes(points=[(3, 3)])
    assert ki.hits(sh) == set()
    assert ki.hits(areas.Shapes(points=[(5, 3)])) == {"XA"}


def test_line_crossing_an_area_with_no_vertex_inside_lights_it():
    ki = areas.KindIndex([_poly(SQUARE)])
    sh = areas.Shapes()
    sh.add({"type": "LineString", "coordinates": [[-1, 5], [11, 5.5]]})
    assert ki.hits(sh) == {"XA"}


def test_area_inside_a_survey_polygon_is_lit():
    ki = areas.KindIndex([_poly([(4, 4), (5, 4), (5, 5), (4, 5), (4, 4)])])
    sh = areas.Shapes()
    sh.add({"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]})
    assert ki.hits(sh) == {"XA"}


def test_feature_crossing_the_antimeridian_is_split():
    """A line from 179 to -179 crosses the area at [179.5, 180] x [0, 1] with no vertex in it: cut at +-180
    as the committed outlines cut lines, its east part lights it; taken the long way it would not."""
    east = [(179.5, 0), (180, 0), (180, 1), (179.5, 1), (179.5, 0)]
    ki = areas.KindIndex([_poly(east)])
    sh = areas.Shapes()
    sh.add({"type": "LineString", "coordinates": [[179, 0.5], [-179, 0.5]]})
    assert ki.hits(sh) == {"XA"}
    poly = areas.Shapes()   # a survey polygon across the antimeridian holding a small area at -179.5
    poly.add({"type": "Polygon", "coordinates": [[[178, -2], [-178, -2], [-178, 2], [178, 2], [178, -2]]]})
    west = areas.KindIndex([_poly([(-179.6, -0.1), (-179.4, -0.1), (-179.4, 0.1), (-179.6, 0.1), (-179.6, -0.1)])])
    assert west.hits(poly) == {"XA"}


def test_bbox_middle_only_without_an_outline():
    rec = {"region": {"bbox": [16, 5, 18, 9]}}
    assert areas.record_shapes(rec, None).points == [(17, 7)]
    assert areas.record_shapes(rec, {"features": [{"geometry": {"type": "Point", "coordinates": [1, 1]}}]}).points == [(1, 1)]
    assert areas.record_shapes({"region": {**rec["region"], "national": True, "country": "XA"}}, None).points == []
    assert areas.bbox_middle([170, 0, -170, 2]) == (180, 1)


def _area_dir(tmp_path: Path, mutate) -> Path:
    d = tmp_path / "areas"
    shutil.copytree(FIX / "areas", d)
    p = d / "country.geojson"
    doc = json.loads(p.read_text())
    mutate(doc)
    p.write_text(json.dumps(doc))
    return d


def _validate(d: Path, capsys) -> tuple[int, str]:
    rc = cli.main(["validate", "--records", str(FIX / "records"), "--outlines", str(FIX / "outlines"),
                   "--areas", str(d), "--starters", str(d / "nostarters")])
    return rc, capsys.readouterr().out


def test_validate_accepts_the_fixture_areas(capsys):
    assert _validate(FIX / "areas", capsys) == (0, "6 records, 0 starter packs, 0 problems\n")


def test_validate_refuses_empty_source_licence(tmp_path, capsys):
    rc, out = _validate(_area_dir(tmp_path, lambda d: d["source"].update(licence="")), capsys)
    assert rc == 1 and "areas/country.geojson: source/licence" in out


def test_validate_refuses_a_repeated_area_id(tmp_path, capsys):
    rc, out = _validate(_area_dir(tmp_path, lambda d: d["features"].append(copy.deepcopy(d["features"][0]))), capsys)
    assert rc == 1 and "area_id 'XA' repeated in kind country" in out


def test_area_edge_over_180_degrees_refused(tmp_path, capsys):
    ring = [[170, 0], [-170, 0], [-170, 1], [170, 1], [170, 0]]
    rc, out = _validate(_area_dir(tmp_path, lambda d: d["features"][1]["geometry"].update(coordinates=[ring])), capsys)
    assert rc == 1 and "steps more than 180 degrees" in out


@pytest.mark.parametrize("mutate, says", [
    (lambda d: d.update(kind="basin"), "does not match the file path"),
    (lambda d: d["source"].update(sha256="abc"), "source/sha256"),
    (lambda d: d["features"][0]["properties"].update(area_id="Atlantis"), "does not match"),
    (lambda d: d["features"][0]["geometry"].update(coordinates=[[[0, 0], [200, 0], [0, 10], [0, 0]]]), "outside WGS84"),
    (lambda d: d["features"][0]["geometry"].update(type="LineString"), "is not one of"),
])
def test_validate_refuses_a_wrong_area_file(tmp_path, capsys, mutate, says):
    rc, out = _validate(_area_dir(tmp_path, mutate), capsys)
    assert rc == 1 and says in out, out


def test_province_needs_a_known_country(tmp_path, capsys):
    d = tmp_path / "areas"
    shutil.copytree(FIX / "areas", d)
    p = d / "province.geojson"
    doc = json.loads(p.read_text())
    doc["features"][0]["properties"]["country"] = "XZ"
    p.write_text(json.dumps(doc))
    rc, out = _validate(d, capsys)
    assert rc == 1 and "country 'XZ' is not a country area" in out
    del doc["features"][0]["properties"]["country"]
    p.write_text(json.dumps(doc))
    rc, out = _validate(d, capsys)
    assert rc == 1 and "'country' is a required property" in out
