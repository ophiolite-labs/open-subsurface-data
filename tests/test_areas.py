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


# --- slice 1: the real area files, the real catalogue ---------------------------------------------------

REAL = paths.AREAS_DIR


def test_real_area_files_stay_under_25_mb():
    files = {p.name: p.stat().st_size for p in areas.area_files(REAL)}
    assert set(files) == {"country.geojson", "province.geojson", "basin.geojson", "no.geojson", "us.geojson"}   # E51: licence/no, licence/us
    assert sum(files.values()) < 25_000_000, files


@pytest.mark.full
def test_real_area_files_validate():
    """In the gate `osd validate` (make validate) reads the same files; here under `full` only (E46 slice 2)."""
    assert areas.validate_areas(REAL) == []


def test_sources_md_quotes_each_terms_sentence_and_digest():
    text = (REAL / "SOURCES.md").read_text()
    for p in areas.area_files(REAL):
        if areas.file_kind(p.relative_to(REAL).as_posix()) == "licence":
            continue   # E51: a read file; SOURCES.md names its address and credit (osd validate)
        src = json.loads(p.read_text())["source"]
        assert src["sha256"] in text and src["edition"] in text and src["retrieved"] in text, p.name
    assert '"All versions of Natural Earth raster + vector map data found on this\nwebsite are in the public domain."' in text
    assert 'Use_Constraints "None."' in text


def test_id_patterns_are_the_schema_patterns():
    for rule in areas.schema()["allOf"]:
        kind = rule["if"]["properties"]["kind"]["const"]
        props = rule["then"]["properties"]["features"]["items"]["properties"]["properties"]
        assert props["properties"]["area_id"]["pattern"] == areas.ID_PATTERNS[kind]


@pytest.fixture(scope="module")
def real(full_build) -> tuple[dict, dict]:
    index = json.loads((full_build / "areas.json").read_text())
    recs = {r["id"]: r for r in json.loads((full_build / "records.json").read_text())["records"]}
    return index, recs


def test_real_build_holds_no_empty_area_and_agrees_both_ways(real, full_build):
    index, recs = real
    assert not list(areas.validator("index").iter_errors(index))
    for k, v in index["kinds"].items():
        assert v["areas"] and all(a["n"] == len(a["ids"]) >= 1 for a in v["areas"]), k
        drawn = json.loads((full_build / f"areas-{k}.geojson").read_text())
        assert [f["properties"]["area_id"] for f in drawn["features"]] == [a["area_id"] for a in v["areas"]]
        assert all(f["properties"]["n"] >= 1 for f in drawn["features"])
    from_index = {(k, a["area_id"], rid) for k, v in index["kinds"].items() for a in v["areas"] for rid in a["ids"]}
    from_records = {(k, aid, rid) for rid, r in recs.items() for k, ids in r["areas"].items() for aid in ids}
    assert from_index == from_records and {rid for _, _, rid in from_index} <= set(recs)


def test_sodir_register_lights_more_than_one_basin_and_one_country(real):
    a = real[1]["sodir/factpages"]["areas"]
    assert len(a["basin"]) > 1 and a["country"] == ["NO"]


def test_national_record_without_outline_lights_its_country_and_no_basin(real):
    """Every national record without an outline in the catalogue (E52 adds them): its country, no province,
    no basin."""
    recs = real[1]
    for rid, r in recs.items():
        if r["region"].get("national") and not paths.outline_path(rid).exists():
            assert r["areas"] == {"country": [r["region"]["country"]], "province": [], "basin": [], "licence": []}, rid


@pytest.mark.full
def test_a_real_record_made_national_lights_only_its_country(real):
    """A real record with a box made national: its country only. Under `full` (E46 slice 2): it loads the area set
    again, and the fixture's `test_national_dataset_lights_its_country_only` guards the same rule in the gate."""
    index, recs = real
    rid = next(rid for rid, r in sorted(recs.items()) if r["region"].get("bbox") and r["region"].get("country")
               in {a["area_id"] for a in index["kinds"]["country"]["areas"]} and not paths.outline_path(rid).exists())
    rec = copy.deepcopy(recs[rid])
    rec["region"]["national"] = True
    assert areas.count({rid: rec}, {rid: None}, areas.AreaSet.load())[rid] == {
        "country": [rec["region"]["country"]], "province": [], "basin": [], "licence": []}   # E51: licence


# --- slice 1: the cache (F13, F18) -----------------------------------------------------------------------

def _write(tmp_path, out_name, cache, areas_dir=FIX / "areas", outlines_dir=FIX / "outlines"):
    from osd.records import load_records
    recs = load_records(FIX / "records")
    out = tmp_path / out_name
    out.mkdir()
    records_out = [dict(r) for r in recs.values()]
    areas.write(out, records_out, recs, outlines_dir, areas_dir, cache_dir=cache)
    return {r["id"]: r["areas"] for r in records_out}


def test_cache_serves_a_second_build_and_never_a_stale_one(tmp_path, capsys):
    cache = tmp_path / "cache"
    first = _write(tmp_path, "a", cache)
    assert "6 records counted, 0 from the cache" in capsys.readouterr().err
    assert _write(tmp_path, "b", cache) == first
    assert "0 records counted, 6 from the cache" in capsys.readouterr().err
    outl = tmp_path / "outlines"   # an outline changes: that record alone is counted again
    shutil.copytree(FIX / "outlines", outl)
    p = outl / "fixture__register.geojson"
    fc = json.loads(p.read_text())
    fc["features"] = fc["features"][:1]
    p.write_text(json.dumps(fc))
    got = _write(tmp_path, "c", cache, outlines_dir=outl)
    assert "1 records counted, 5 from the cache" in capsys.readouterr().err
    assert got["fixture/register"]["basin"] == ["usgs-1001"]
    d = tmp_path / "areas"         # an area file changes: everything is counted again
    shutil.copytree(FIX / "areas", d)
    doc = json.loads((d / "basin.geojson").read_text())
    doc["features"] = doc["features"][1:]
    (d / "basin.geojson").write_text(json.dumps(doc))
    got = _write(tmp_path, "d", cache, areas_dir=d)
    assert "6 records counted, 0 from the cache" in capsys.readouterr().err
    assert got["fixture/boxed"]["basin"] == []
    assert len(list(cache.glob("areas-*.json"))) == 1 and not list(cache.glob("*.tmp"))


def test_cache_is_not_published(full_build):
    assert not list(full_build.rglob("areas-cache*")) and not (full_build / "areas-cache").exists()


# --- slice 1: preparation (F11, F19) ----------------------------------------------------------------------

def _shapefile(d: Path, rows: list[tuple[dict, list]], prj="GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\"]]") -> Path:
    """A polygon Shapefile (.shp, .dbf, .prj, .cpg) of rows (attributes, rings) written byte by byte."""
    import struct
    recs = b""
    for i, (_, rings) in enumerate(rows, 1):
        pts = [p for r in rings for p in r]
        parts, at = [], 0
        for r in rings:
            parts.append(at)
            at += len(r)
        body = struct.pack("<i4d2i", 5, 0, 0, 0, 0, len(rings), len(pts)) + struct.pack(f"<{len(parts)}i", *parts)
        body += b"".join(struct.pack("<2d", *p) for p in pts)
        recs += struct.pack(">2i", i, len(body) // 2) + body
    (d / "t.shp").write_bytes(struct.pack(">7i", 9994, 0, 0, 0, 0, 0, (100 + len(recs)) // 2)
                              + struct.pack("<2i4d4d", 1000, 5, 0, 0, 0, 0, 0, 0, 0, 0) + recs)
    names = list(rows[0][0])
    head = struct.pack("<4BIHH20x", 3, 126, 11, 25, len(rows), 32 + 32 * len(names) + 1, 1 + 20 * len(names))
    fields = b"".join(n.encode().ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([20]) + b"\0" * 15 for n in names)
    data = b"".join(b" " + b"".join(str(a[n]).encode().ljust(20) for n in names) for a, _ in rows)
    (d / "t.dbf").write_bytes(head + fields + b"\r" + data + b"\x1a")
    (d / "t.prj").write_text(prj)
    (d / "t.cpg").write_text("UTF-8")
    return d / "t.shp"


CW = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]           # shapefile exterior: clockwise
CCW_HOLE = [(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)]         # shapefile hole: counterclockwise
RULE = {"id": ["CODE"], "prefix": "usgs-", "name": "NAME", "tolerance_m": 0, "decimals": 6, "exclude": {"CODE": [0]},
        "source": {"name": "t", "url": "https://example.org/t", "licence": "public domain", "credit": "T",
                   "edition": "1", "retrieved": "2026-11-25"}}


def test_shapefile_reader_nests_holes_and_merges_parts(tmp_path):
    shp = _shapefile(tmp_path, [({"CODE": "1001", "NAME": "Alpha"}, [CW, CCW_HOLE]),
                                ({"CODE": "1001", "NAME": "Alpha"}, [[(20, 0), (20, 1), (21, 1), (21, 0), (20, 0)]]),
                                ({"CODE": "0", "NAME": "Ocean"}, [[(30, 0), (30, 1), (31, 1), (31, 0), (30, 0)]])])
    doc, notes = areas.prepare("basin", shp, RULE)
    assert not list(areas.validator().iter_errors(doc)) and notes == []
    assert [f["properties"] for f in doc["features"]] == [{"area_id": "usgs-1001", "name": "Alpha"}]
    g = doc["features"][0]["geometry"]
    assert g["type"] == "MultiPolygon" and len(g["coordinates"][0]) == 2   # the hole stays in its polygon
    ki = areas.KindIndex(doc["features"])
    assert ki.hits(areas.Shapes(points=[(3, 3)])) == set() and ki.hits(areas.Shapes(points=[(5, 5)])) == {"usgs-1001"}
    assert doc["source"]["sha256"] == __import__("hashlib").sha256(shp.read_bytes()).hexdigest()


def test_prepare_refuses_a_projected_file(tmp_path):
    shp = _shapefile(tmp_path, [({"CODE": "1", "NAME": "A"}, [CW])], prj='PROJCS["ED50 / UTM zone 31N"]')
    with pytest.raises(areas.Refused, match="geographic WGS 84"):
        areas.prepare("basin", shp, RULE)


def test_prepare_densifies_an_edge_over_180_degrees():
    g = areas.densify_wide({"type": "Polygon", "coordinates": [[[180, -85], [180, -90], [-180, -90], [-180, -85], [180, -85]]]})
    assert areas.wide_edges(g) == 0 and [0.0, -90.0] in g["coordinates"][0]


def test_prepare_reaches_no_network(tmp_path, monkeypatch, capsys):
    """`osd areas prepare` is local only: with every socket refused it still writes the area file."""
    import socket

    def refuse(*a, **k):
        raise AssertionError("osd areas prepare opened a socket")
    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    d = tmp_path / "areas"
    d.mkdir()
    (d / "prepare.yaml").write_text(json.dumps({"basin": {**RULE, "file": "t.shp"}}))
    shp = _shapefile(tmp_path, [({"CODE": "1001", "NAME": "Alpha"}, [CW])])
    assert cli.main(["areas", "prepare", "basin", str(shp), "--areas", str(d)]) == 0
    assert "1 areas" in capsys.readouterr().out and areas.validate_areas(d) == []


def test_area_tiles_hold_one_layer_per_kind(built, tmp_path):
    if not shutil.which("tippecanoe"):
        pytest.skip("tippecanoe not installed")
    out = tmp_path / "out"
    shutil.copytree(built, out)
    p = areas.write_tiles(out, tmp_path / "tiles")
    assert p and p.stat().st_size > 0
    import gzip
    import struct
    head = p.read_bytes()[:127]
    meta_off, meta_len = struct.unpack("<QQ", head[24:40])
    raw = p.read_bytes()[meta_off:meta_off + meta_len]
    meta = json.loads(gzip.decompress(raw) if head[97] == 2 else raw)
    assert sorted(layer["id"] for layer in meta["vector_layers"]) == ["areas_basin", "areas_country", "areas_province"]
