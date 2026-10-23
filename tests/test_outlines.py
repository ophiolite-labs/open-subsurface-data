"""E03: outlines from the data. Every test runs offline over frozen responses in
tests/fixtures/outlines/ (see its README for what was truncated)."""
import copy
import hashlib
import itertools
import json
import math
import struct
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from pyproj import Transformer
from test_verify import NOW, fetch_ok, l2_fixture, outcome

from osd import outlines, paths
from osd.outlines import (
    Refused,
    check,
    derive,
    fetch_inputs,
    load_rules,
    store,
    stored_inputs,
    write_outline,
)
from osd.outlines.codecs import blosc_decode
from osd.outlines.extractors import segy_hull
from osd.outlines.geometry import ring_area_m2, simplify
from osd.records import load_record, load_records, record_files, validate_outlines
from osd.verify import FetchError, verify_record

FIX = Path(__file__).parent / "fixtures" / "outlines"
RULES = load_rules()
RECS = load_records()


def parts_of(d: Path) -> list[tuple[str, bytes]]:
    return [(str(p.relative_to(d)), p.read_bytes()) for p in sorted(d.rglob("*")) if p.is_file()]


def stage(tmp_path, rid, name, src=None) -> Path:
    """Store a fixture directory as the stored input <rid>/<name>, as fetch_inputs would."""
    inputs = tmp_path / "inputs"
    store(inputs / rid.replace("/", "__") / name, parts_of(src or FIX / rid.replace("/", "__") / name))
    return inputs


def only(rec, *names):
    r = copy.deepcopy(rec)
    r["inputs"] = [i for i in r["inputs"] if i["name"] in names]
    return r


def fixture_ids(d: Path, field: str, keep=None) -> list[str]:
    ids = []
    for p in sorted(d.glob("page-*")):
        for f in json.loads(p.read_bytes())["features"]:
            if keep is None or all(f["properties"].get(k) == v for k, v in keep.items()):
                ids.append(str(f["properties"][field]))
    return ids


def published_ids(fc) -> list[str]:
    return [f["properties"]["publisher_id"] for f in fc["features"]]


# --- register-wfs: id-set equality against frozen paginated responses --------------------

def test_sodir_wellbore_ids_equal_the_fixture_id_set(tmp_path):
    inputs = stage(tmp_path, "sodir/factpages", "wellbores")
    fc = derive(only(RECS["sodir/factpages"], "wellbores"), RULES, inputs)
    want = fixture_ids(FIX / "sodir__factpages" / "wellbores", "NPDID_wellbore")
    assert len(want) == 8 and len(set(want)) == len(want)
    got = published_ids(fc)
    assert len(set(got)) == len(got) and set(got) == set(want)
    assert {f["properties"]["kind"] for f in fc["features"]} == {"wellbore"}


def test_sodir_seismic_ids_equal_the_net_areas_of_the_fixture(tmp_path):
    inputs = stage(tmp_path, "sodir/factpages", "seismic-finished")
    fc = derive(only(RECS["sodir/factpages"], "seismic-finished"), RULES, inputs)
    want = fixture_ids(FIX / "sodir__factpages" / "seismic-finished", "NPDID_for_survey", {"Net_or_gross": "net"})
    assert sorted(published_ids(fc)) == sorted(want) and len(want) == 3
    assert all(f["geometry"]["type"] == "MultiPolygon" for f in fc["features"])


def test_nlog_borehole_ids_equal_the_fixture_id_set(tmp_path):
    inputs = stage(tmp_path, "nlog/nlog", "boreholes")
    fc = derive(only(RECS["nlog/nlog"], "boreholes"), RULES, inputs)
    want = fixture_ids(FIX / "nlog__nlog" / "boreholes", "BOREHOLE_CODE")
    got = published_ids(fc)
    assert len(want) == 8 and len(set(got)) == len(got) and set(got) == set(want)
    assert all(f["properties"]["uwi"] for f in fc["features"])


def test_nlog_3d_survey_ids_equal_the_fixture_id_set(tmp_path):
    inputs = stage(tmp_path, "nlog/nlog", "surveys-3d")
    fc = derive(only(RECS["nlog/nlog"], "surveys-3d"), RULES, inputs)
    want = fixture_ids(FIX / "nlog__nlog" / "surveys-3d", "SIGNAL_COLLECTION_ID")
    assert len(want) == 3 and sorted(published_ids(fc)) == sorted(want)


def test_wfs_hit_count_mismatch_is_refused(tmp_path):
    src = tmp_path / "src"
    for n, b in parts_of(FIX / "sodir__factpages" / "wellbores"):
        (src / n).parent.mkdir(parents=True, exist_ok=True)
        (src / n).write_bytes(b.replace(b'numberMatched="8"', b'numberMatched="9869"'))
    inputs = stage(tmp_path, "sodir/factpages", "wellbores", src)
    with pytest.raises(Refused, match="counts 9869 features, the pages served 8"):
        derive(only(RECS["sodir/factpages"], "wellbores"), RULES, inputs)


def test_transform_known_coordinates_and_axis_order(tmp_path):
    """NLOG serves K18-KOTTER-01 in ED50 / UTM 31N and submitted it in ED50 geographic: both
    paths to WGS84 must agree within a metre, so zone, datum and (east, north) order are right."""
    page = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::23031"}},
            "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [564693, 5881980]},
                          "properties": {"BOREHOLE_CODE": "K18-KOTTER-01", "UWI": "7567", "BOREHOLE_NAME": "K18-KOTTER-01"}}]}
    src = tmp_path / "src"
    src.mkdir()
    (src / "page-000000").write_text(json.dumps(page))
    fc = derive(only(RECS["nlog/nlog"], "boreholes"), RULES, stage(tmp_path, "nlog/nlog", "boreholes", src))
    lon, lat = fc["features"][0]["geometry"]["coordinates"]
    ref_lon, ref_lat = Transformer.from_crs("EPSG:4230", "EPSG:4326", always_xy=True).transform(3.9657778, 53.08225)
    assert abs(lon - ref_lon) * 67000 < 1 and abs(lat - ref_lat) * 111000 < 1
    assert 3.9 < lon < 4.0 and 53.0 < lat < 53.1  # lon first: GeoJSON order


# --- segy-hull: SEG-Y trace headers and MDIO ----------------------------------------------

SEGY_INPUT = {"name": "f3-like", "url": "https://fixture.test/irregular.sgy", "format": "segy", "crs": "EPSG:23031"}
SEGY_RULE = {"extractor": "segy-hull", "kind": "survey-3d"}
EXACT_HULL = [(605040, 6080030), (605160, 6080120), (605025, 6080300), (604920, 6080315),
              (604820, 6080240), (604970, 6080040)]  # lattice (2,0) (8,0) (8,9) (5,12) (0,12) (0,2)


def segy_parts(data=None):
    return [("body", data if data is not None else (FIX / "segy" / "irregular.sgy").read_bytes())]


def test_segy_hull_matches_the_known_exact_hull():
    [f] = segy_hull(SEGY_INPUT, SEGY_RULE, segy_parts())
    ring = f["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1] and len(ring) == len(EXACT_HULL) + 1
    back = Transformer.from_crs("EPSG:4326", "EPSG:23031", always_xy=True)
    got = [back.transform(*p) for p in ring[:-1]]
    for want in EXACT_HULL:
        assert min(abs(x - want[0]) + abs(y - want[1]) for x, y in got) < 1.0, want


def test_segy_known_coordinate_and_axis_order():
    [f] = segy_hull(SEGY_INPUT, SEGY_RULE, segy_parts())
    ring = f["geometry"]["coordinates"][0]
    # lattice (2,0): x 605040 m, y 6080030 m in ED50 / UTM 31N, the hull's lowest vertex
    assert [4.634782, 54.854438] in ring
    assert all(4.6 < lon < 4.7 and 54.8 < lat < 54.9 for lon, lat in ring)


def test_undeclared_units_never_pass():
    data = bytearray(segy_parts()[0][1])
    data[3254:3256] = b"\x00\x00"  # measurement system not stated
    with pytest.raises(Refused, match="units not declared"):
        segy_hull(SEGY_INPUT, SEGY_RULE, segy_parts(bytes(data)))
    assert segy_hull({**SEGY_INPUT, "units": "m"}, SEGY_RULE, segy_parts(bytes(data)))  # the record states it
    with pytest.raises(Refused, match="disagree"):
        segy_hull({**SEGY_INPUT, "units": "ft"}, SEGY_RULE, segy_parts(bytes(data)))


def test_undeclared_crs_never_passes(tmp_path):
    with pytest.raises(Refused, match="CRS not declared"):
        segy_hull({k: v for k, v in SEGY_INPUT.items() if k != "crs"}, SEGY_RULE, segy_parts())
    rec = only(RECS["nlog/nlog"], "boreholes")
    del rec["inputs"][0]["crs"]
    with pytest.raises(Refused, match="CRS not declared"):
        derive(rec, RULES, stage(tmp_path, "nlog/nlog", "boreholes"))
    rec = only(RECS["nlog/nlog"], "boreholes")
    rec["inputs"][0]["crs"] = "EPSG:4326"  # the response declares 23031
    with pytest.raises(Refused, match="declares EPSG:23031"):
        derive(rec, RULES, stage(tmp_path, "nlog/nlog", "boreholes"))


def test_blosc_lz4_decodes_a_real_chunk():
    d = FIX / "nopims__poseidon" / "full-stack-agc"
    raw = blosc_decode((d / "headers" / "0" / "0").read_bytes())
    assert len(raw) == 128 * 128 * 18
    il, xl, scalar, x, y = struct.unpack_from("<iihii", raw, 0)
    assert (il, xl, scalar) == (983, 504, -100) and (x, y) == (41613223, 844759437)
    mask = blosc_decode((d / "trace_mask" / "1" / "1").read_bytes())
    assert len(mask) == 2332 * 3429 and mask.count(1) == (3437 - 2332) * (5053 - 3429)


def test_mdio_hull_from_frozen_poseidon_chunks(tmp_path):
    inputs = stage(tmp_path, "nopims/poseidon", "full-stack-agc")
    [f] = derive(RECS["nopims/poseidon"], RULES, inputs)["features"]
    p = f["properties"]
    assert p["publisher_id"] == "Poseidon" and p["kind"] == "survey-3d"
    ring = f["geometry"]["coordinates"][0]
    assert len(ring) == 5  # every trace live: the four corner traces
    assert [122.22326, -14.04106] in ring  # polygon_decimals 5; inline 983, crossline 504: x 416132.23, y 8447594.37 (MGA 51)


def test_wellbores_without_a_position_are_listed_not_drawn(tmp_path):
    """FactMaps serves [nan,nan] (not JSON) for 6407/9-U-4: listed as unplaced, never dropped."""
    inputs = stage(tmp_path, "sodir/factpages", "wellbores", FIX / "sodir__factpages" / "wellbores-unplaced")
    fc = derive(only(RECS["sodir/factpages"], "wellbores"), RULES, inputs)
    assert sorted(published_ids(fc)) == ["138", "140"] and fc["unplaced"] == ["sodir/factpages#wellbore/139"]
    rules = copy.deepcopy(RULES)
    del rules["sodir/factpages"]["inputs"]["wellbores"]["unplaced"]
    with pytest.raises(Refused, match="geometry"):
        derive(only(RECS["sodir/factpages"], "wellbores"), rules, inputs)
    out = tmp_path / "out.geojson"
    write_outline(fc, out)
    assert json.loads(out.read_text())["unplaced"] == fc["unplaced"]


def test_overlapping_publisher_ids_are_scoped_not_collided(tmp_path):
    """Sodir numbers wellbores and surveys from one NPDID sequence: wellbore 140, survey 140 can
    both exist. The rule's id_scope keeps feature_ids unique; without it they would collide."""
    inputs = stage(tmp_path, "sodir/factpages", "wellbores", FIX / "sodir__factpages" / "wellbores-unplaced")
    store(inputs / "sodir__factpages" / "seismic-finished", [("page-000000", json.dumps({
        "type": "FeatureCollection", "features": [{"type": "Feature", "properties": {
            "NPDID_for_survey": 140, "Survey_name": "S", "Sub_type": "3D", "Net_or_gross": "net"},
            "geometry": {"type": "Polygon", "coordinates": [[[2, 60], [3, 60], [3, 61], [2, 60]]]}}]}).encode())])
    rec = only(RECS["sodir/factpages"], "wellbores", "seismic-finished")
    ids = [f["properties"]["feature_id"] for f in derive(rec, RULES, inputs)["features"]]
    assert "sodir/factpages#wellbore/140" in ids and "sodir/factpages#survey/140" in ids
    rules = copy.deepcopy(RULES)
    for r in rules["sodir/factpages"]["inputs"].values():
        r.pop("id_scope", None)
    with pytest.raises(Refused, match="collisions"):
        derive(rec, rules, inputs)


def test_surveys_without_an_area_are_listed_not_drawn(tmp_path):
    """FactMaps serves {"type":"MultiPolygon",} (not JSON) for CSSC-65 (1965, no area)."""
    inputs = stage(tmp_path, "sodir/factpages", "seismic-finished", FIX / "sodir__factpages" / "seismic-unplaced")
    fc = derive(only(RECS["sodir/factpages"], "seismic-finished"), RULES, inputs)
    assert published_ids(fc) == ["11191"] and fc["unplaced"] == ["sodir/factpages#survey/2000"]


def _to_segment(p, a, b):
    k = 111320 * math.cos(math.radians(p[1]))
    ax, ay, bx, by, px, py = a[0] * k, a[1] * 110540, b[0] * k, b[1] * 110540, p[0] * k, p[1] * 110540
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def test_survey_polygons_are_simplified_within_tolerance_points_exact(tmp_path):
    inputs = stage(tmp_path, "nlog/nlog", "surveys-3d")
    rules = copy.deepcopy(RULES)
    rules["nlog/nlog"]["simplify_m"] = 0
    exact = derive(only(RECS["nlog/nlog"], "surveys-3d"), rules, inputs)
    fc = derive(only(RECS["nlog/nlog"], "surveys-3d"), RULES, inputs)
    before = sum(len(r) for f in exact["features"] for r in f["geometry"]["coordinates"])
    after = sum(len(r) for f in fc["features"] for r in f["geometry"]["coordinates"])
    assert after < before
    for e, s in zip(exact["features"], fc["features"], strict=True):
        assert s["properties"]["simplified_m"] == 50 and e["properties"]["simplified_m"] == 0
        ring = s["geometry"]["coordinates"][0]
        assert ring[0] == ring[-1]
        for p in e["geometry"]["coordinates"][0]:  # every served vertex within 50 m of the simplified ring
            assert min(_to_segment(p, a, b) for a, b in itertools.pairwise(ring)) <= 51  # 50 m plus 5-decimal rounding
    pts = derive(only(RECS["nlog/nlog"], "boreholes"), RULES, stage(tmp_path, "nlog/nlog", "boreholes"))
    assert all("simplified_m" not in f["properties"] for f in pts["features"])


def test_rings_below_tolerance_squared_are_dropped_and_counted():
    """OSD-D16 amended: a ring whose area is below tol² is dropped; a polygon whose exterior is
    dropped goes with its holes; the count is returned for rings_dropped."""
    def square(x, y, d):  # d degrees at 60N: 0.001 deg ~ 56 m x 111 m
        return [[x, y], [x + d, y], [x + d, y + d], [x, y + d], [x, y]]
    big = [square(2, 60, 0.1), square(2.01, 60.01, 0.01), square(2.05, 60.05, 0.0002)]  # hole 11 m x 22 m
    speck = [square(3, 60, 0.0003)]  # 17 m x 33 m < 50 m x 50 m
    g, dropped = simplify({"type": "MultiPolygon", "coordinates": [big, speck]}, 50)
    assert dropped == 2 and len(g["coordinates"]) == 1 and len(g["coordinates"][0]) == 2
    assert ring_area_m2(square(2, 60, 0.001)) == pytest.approx(55.66 * 110.54, rel=1e-3)
    g, dropped = simplify({"type": "Polygon", "coordinates": speck}, 50)  # nothing above tol²: kept
    assert dropped == 0 and g["coordinates"] == speck
    as_served = [[[round(v, 12) for v in p] for p in r] for r in big]
    assert simplify({"type": "Polygon", "coordinates": big}, 0, decimals=12) == ({"type": "Polygon", "coordinates": as_served}, 0)
    g, dropped = simplify({"type": "Polygon", "coordinates": big}, 50, exterior_only=True)  # 2D coverage
    assert dropped == 2 and g["coordinates"] == [square(2, 60, 0.1)]
    g, _ = simplify({"type": "Polygon", "coordinates": [square(2.123456789, 60, 0.1)]}, 50, decimals=5)
    assert g["coordinates"][0][0] == [2.12346, 60]


def test_polygon_rules_are_named_in_the_derivation(tmp_path):
    ring = [[2, 60], [3, 60], [3, 61], [2, 60]]
    store(tmp_path / "sodir__factpages" / "seismic-finished", [("page-000000", json.dumps({
        "type": "FeatureCollection", "features": [{"type": "Feature", "properties": {
            "NPDID_for_survey": n, "Survey_name": s, "Sub_type": s, "Net_or_gross": "net"},
            "geometry": {"type": "Polygon", "coordinates": [ring]}} for n, s in ((1, "2D"), (2, "3D"))]}).encode())])
    fc = derive(only(RECS["sodir/factpages"], "seismic-finished"), RULES, tmp_path)
    src = {f["properties"]["kind"]: f["properties"]["source"] for f in fc["features"]}
    assert src["survey-2d"] == "register-wfs (seismic-finished), simplified 50 m, exterior only, 5 decimals"
    assert src["survey-3d"] == "register-wfs (seismic-finished), simplified 50 m, 5 decimals"


# --- publisher-file and register-csv ------------------------------------------------------

def test_publisher_page_extent(tmp_path):
    inputs = stage(tmp_path, "nzpam/parihaka", "survey-extent")
    [f] = derive(RECS["nzpam/parihaka"], RULES, inputs)["features"]
    assert f["properties"]["publisher_id"] == "927165623" and f["properties"]["name"] == "PARIHAKA-3D : PR3460"
    assert f["geometry"]["type"] == "Polygon" and f["properties"]["simplified_m"] == 50 and f["properties"]["rings_dropped"] == 0
    assert 4 <= len(f["geometry"]["coordinates"][0]) < 152  # 152 positions as served


def test_register_csv_ids_equal_the_fixture_id_set(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "body").write_text("id;name;lon;lat\nW-1;Well 1;4.5;54.1\nW-2;Well 2;4.6;54.2\n")
    rec = {"id": "acme/demo", "licence": {"name": "CC BY 4.0"},
           "inputs": [{"name": "register", "url": "https://acme.example/w.csv", "format": "csv", "crs": "EPSG:4326"}]}
    rules = {"acme/demo": {"inputs": {"register": {"extractor": "register-csv", "kind": "wellbore", "id": "id",
                                                   "name": "name", "x": "lon", "y": "lat", "delimiter": ";"}}}}
    fc = derive(rec, rules, stage(tmp_path, "acme/demo", "register", src))
    assert sorted(published_ids(fc)) == ["W-1", "W-2"]
    assert fc["features"][0]["geometry"]["coordinates"] == [4.5, 54.1]


# --- the derived-feature contract --------------------------------------------------------

def test_derived_features_carry_identity_and_licence(tmp_path):
    inputs = stage(tmp_path, "sodir/factpages", "wellbores")
    fc = derive(only(RECS["sodir/factpages"], "wellbores"), RULES, inputs)
    sha = stored_inputs("sodir/factpages", inputs) or None
    sums = (inputs / "sodir__factpages" / "wellbores" / "SHA256SUMS").read_bytes()
    for f in fc["features"]:
        p = f["properties"]
        assert p["approximate"] is False and p["source"] == "register-wfs (wellbores)"
        assert p["feature_id"] == f"sodir/factpages#wellbore/{p['publisher_id']}"
        assert p["input"] == "wellbores" and "licence" not in p
    assert fc["inputs"] == {"wellbores": {"url": RECS["sodir/factpages"]["inputs"][0]["url"],
                                          "sha256": hashlib.sha256(sums).hexdigest(),
                                          "period_fields": {"start": "Entered_date", "end": "Completed_date"}}}
    assert fc["licence"] == "Norwegian Licence for Open Government Data 2.0"  # OSD-D13, once per file
    assert sha is None  # no inputs.json: only fetch_inputs records what was fetched
    out = tmp_path / "outlines"
    out.mkdir()
    write_outline(fc, out / "sodir__factpages.geojson")
    assert validate_outlines(out) == []


def test_open_ring_is_a_problem(tmp_path, tmp_records, tmp_outlines):
    p = tmp_outlines / "acme__demo.geojson"
    fc = json.loads(p.read_text())
    fc["features"][0]["geometry"]["coordinates"][0].pop()
    p.write_text(json.dumps(fc))
    assert any("not closed" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))
    fc["features"][0]["geometry"]["coordinates"] = [[]]
    p.write_text(json.dumps(fc))
    assert any("fewer than 4" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))


def test_derived_feature_without_identity_is_a_problem(tmp_records, tmp_outlines):
    p = tmp_outlines / "acme__demo.geojson"
    good = p.read_text()
    p.write_text(good.replace('"input": "demo-3d"', '"inputs_": "demo-3d"'))
    assert any("'input' is a required property" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))
    p.write_text(good.replace('"input": "demo-3d"', '"input": "other"'))  # names an input the file lacks
    assert any("not in the collection's inputs" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))
    p.write_text(good.replace('"sha256": "' + "0" * 64, '"sha": "' + "0" * 64))
    assert any("collection: " in str(m) and "sha256" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))
    p.write_text(good.replace('"licence": "CC BY 4.0", ', ""))
    assert any("no licence" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))


# --- fetching through the injected opener ------------------------------------------------

def wfs_opener(d: Path, calls: list):
    """Serve a frozen WFS fixture: resultType=hits -> hits, startIndex=N -> page-N."""
    from urllib.parse import parse_qs, urlsplit

    def open_(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            raise FetchError(url, 404)
        q = parse_qs(urlsplit(url).query)
        if "startIndex" not in q and "resultType" not in q:
            raise FetchError(url, 404)
        name = "hits" if q.get("resultType") == ["hits"] else f"page-{int(q['startIndex'][0]):06d}"
        p = d / name
        if not p.exists():
            return iter([b'{"type":"FeatureCollection","features":[]}'])
        return iter([p.read_bytes()])

    return open_


def test_fetch_stores_parts_and_sums(tmp_path):
    rules = copy.deepcopy(RULES)
    rules["sodir/factpages"]["inputs"] = {"wellbores": {**rules["sodir/factpages"]["inputs"]["wellbores"], "page_size": 3}}
    rec = only(RECS["sodir/factpages"], "wellbores")
    calls = []
    got = fetch_inputs(rec, rules, wfs_opener(FIX / "sodir__factpages" / "wellbores", calls), tmp_path)
    d = tmp_path / "sodir__factpages" / "wellbores"
    assert sorted(p.name for p in d.iterdir()) == ["SHA256SUMS", "hits", "page-000000", "page-000003", "page-000006"]
    assert any("count=3" in c and "startIndex=6" in c and "propertyName=" in c for c in calls)
    assert stored_inputs("sodir/factpages", tmp_path) == {rec["inputs"][0]["url"]: got["wellbores"]}
    (d / "page-000003").write_bytes(b"tampered")
    assert stored_inputs("sodir/factpages", tmp_path) == {}


def test_empty_response_never_passes(tmp_path):
    rec = only(RECS["sodir/factpages"], "wellbores")
    fetch_inputs(rec, RULES, wfs_opener(tmp_path / "nothing", []), tmp_path)
    with pytest.raises(Refused, match="empty response"):
        derive(rec, RULES, tmp_path)
    o, _ = check(rec, {"type": "FeatureCollection", "features": []}, RULES["sodir/factpages"], {})
    assert o == "fail"


def test_missing_inputs_never_passes(tmp_path):
    rec = copy.deepcopy(RECS["sodir/factpages"])
    del rec["inputs"]
    with pytest.raises(Refused, match="declares no inputs"):
        derive(rec, RULES, tmp_path)
    fc = derive(only(RECS["sodir/factpages"], "wellbores"), RULES, stage(tmp_path, "sodir/factpages", "wellbores"))
    o, d = check(rec, fc, {"min_features": 1}, stored_of(fc))
    assert (o, d) == ("fail", "the record declares no inputs")


def test_approximate_feature_never_passes(tmp_path):
    outline = json.loads(paths.outline_path("terranubis/f3-demo-2020").read_text())
    rec = {**RECS["terranubis/f3-demo-2020"], "inputs": [SEGY_INPUT]}
    assert check(rec, outline, {"min_features": 1}, {})[0] == "fail"  # the committed placeholder
    rec, fc, stored = derived_sodir(tmp_path)
    fc["features"][3]["properties"]["approximate"] = True  # identity intact, one placeholder
    o, d = check(rec, fc, {"min_features": 8}, stored)
    assert (o, d) == ("fail", "1 approximate features")


def test_duplicate_feature_id_never_passes(tmp_path):
    src = tmp_path / "src"
    for n, b in parts_of(FIX / "sodir__factpages" / "seismic-finished"):
        (src / n).parent.mkdir(parents=True, exist_ok=True)
        (src / n).write_bytes(b)
    rules = copy.deepcopy(RULES)
    del rules["sodir/factpages"]["inputs"]["seismic-finished"]["keep"]  # gross and net share an id
    rec = only(RECS["sodir/factpages"], "seismic-finished")
    with pytest.raises(Refused, match="feature_id collisions"):
        derive(rec, rules, stage(tmp_path, "sodir/factpages", "seismic-finished", src))
    fc = derive(rec, RULES, stage(tmp_path, "sodir/factpages", "seismic-finished"))
    fc["features"].append(copy.deepcopy(fc["features"][0]))
    o, d = check(rec, fc, {"min_features": 1}, stored_of(fc))
    assert o == "fail" and "duplicate feature_id" in d


# --- the L3 check in the verifier ----------------------------------------------------------

def derived_sodir(tmp_path):
    rec = only(RECS["sodir/factpages"], "wellbores")
    inputs = stage(tmp_path, "sodir/factpages", "wellbores")
    fc = derive(rec, RULES, inputs)
    return rec, fc, stored_of(fc)


def stored_of(fc):
    """What stored_inputs would report for the inputs this collection names."""
    return {i["url"]: i["sha256"] for i in fc["inputs"].values()}


def l2_passing(tmp_path, rec):
    """The verify tests' L2 fixture, wrapped around this record."""
    from test_verify import SAMPLE, dir_opener
    base = l2_fixture(tmp_path)
    r = copy.deepcopy(rec)
    r["origin"]["manifest_url"], r["licence"]["url"] = base["origin"]["manifest_url"], base["licence"]["url"]
    return r, dir_opener(tmp_path), SAMPLE


def test_derived_outline_with_stored_inputs_is_L3(tmp_path):
    rec, fc, stored = derived_sodir(tmp_path)
    rec, opener, sample = l2_passing(tmp_path, rec)
    v = verify_record(rec, fetch_ok, fc, now=NOW, opener=opener, sample=sample,
                      outline_rule={"min_features": 8}, stored=stored)
    assert outcome(v, "outline-derived")["outcome"] == "pass", outcome(v, "outline-derived")
    assert v["level"] == "L3"


def test_derived_outline_without_L2_is_not_L3(tmp_path):
    rec, fc, stored = derived_sodir(tmp_path)
    v = verify_record(rec, fetch_ok, fc, now=NOW, outline_rule={"min_features": 8}, stored=stored)
    assert outcome(v, "outline-derived")["outcome"] == "pass" and v["level"] == "L1"


def test_changed_input_bytes_fail_outline_derived(tmp_path):
    rec, fc, stored = derived_sodir(tmp_path)
    o, d = check(rec, fc, {"min_features": 8}, {k: "f" * 64 for k in stored})
    assert o == "fail" and "differ from the stored input" in d
    assert check(rec, fc, {"min_features": 8}, {})[0] == "skip"  # nothing stored: no pass


def test_feature_count_below_rules_fails(tmp_path):
    rec, fc, stored = derived_sodir(tmp_path)
    assert check(rec, fc, {"min_features": 8}, stored)[0] == "pass"
    o, d = check(rec, fc, {"min_features": 9}, stored)
    assert o == "fail" and "fewer than the 9" in d
    assert check(rec, fc, {}, stored)[0] == "fail"


def test_refused_derivation_is_reported(tmp_path):
    rec, fc, stored = derived_sodir(tmp_path)
    o, d = check(rec, fc, {"min_features": 8}, stored, refused="empty response")
    assert (o, d) == ("fail", "derivation refused this run: empty response")


# --- schemas and rules -----------------------------------------------------------------------

def test_every_version_1_record_validates_under_record_2():
    v1 = Draft202012Validator(json.loads((FIX / "schema" / "record-1.schema.json").read_text()),
                              format_checker=FormatChecker())
    v2 = Draft202012Validator(json.loads((paths.SCHEMA_DIR / "record.schema.json").read_text()),
                              format_checker=FormatChecker())
    assert v2.schema["$id"].endswith("/record/5") and v1.schema["$id"].endswith("/record/1")
    for p in record_files():
        rec = load_record(p)
        if (rec["origin"]["access"] == "purchase" or "terms" in rec["licence"] or {
                "potential-fields", "velocity-model", "geological-model", "airborne-em", "radiometrics", "stress"} & set(rec["kinds"])):
            continue  # record/3 values (E19) and record/4 kinds (E26): not a version-1 record
        rec.pop("inputs", None)  # the version-2 additions: what remains is a version-1 file
        rec.pop("period", None)
        assert not list(v1.iter_errors(rec)), p
        assert not list(v2.iter_errors(rec)), p


def test_every_version_1_outline_validates_under_outline_2_and_3():
    v1 = Draft202012Validator(json.loads((FIX / "schema" / "outline-1.schema.json").read_text()))
    v2 = Draft202012Validator(json.loads((paths.SCHEMA_DIR / "outline.schema.json").read_text()))
    assert v2.schema["$id"].endswith("/outline/3")
    placeholders = [f for p in sorted(paths.OUTLINES_DIR.glob("*.geojson"))
                    for f in json.loads(p.read_text())["features"] if f["properties"]["approximate"]]
    assert placeholders
    for f in placeholders:
        assert not list(v1.iter_errors(f["properties"])) and not list(v2.iter_errors(f["properties"]))


def test_rules_name_records_with_inputs():
    assert set(RULES["defaults"]) <= {"simplify_m", "polygon_decimals"}
    for rid, rule in RULES.items():
        if rid == "defaults":
            continue
        names = {i["name"] for i in RECS[rid].get("inputs", [])}
        assert rule["inputs"] and set(rule["inputs"]) <= names, rid
        assert isinstance(rule["min_features"], int) and rule["min_features"] >= 1, rid
        for r in rule["inputs"].values():
            assert r["extractor"] in outlines.EXTRACTORS, rid


def test_record_schema_has_no_outline_policy():
    props = json.loads((paths.SCHEMA_DIR / "record.schema.json").read_text())["properties"]["inputs"]
    assert set(props["items"]["properties"]) == {"name", "url", "format", "crs", "units", "stated"}  # OSD-D11


def test_outline_inputs_check_the_committed_file_and_outlines_rewrite_it(tmp_path, monkeypatch):
    from osd.verify import verify_all
    rec = only(RECS["sodir/factpages"], "wellbores")
    rules = copy.deepcopy(RULES)
    rules["sodir/factpages"]["inputs"] = {"wellbores": {**rules["sodir/factpages"]["inputs"]["wellbores"], "page_size": 3}}
    rules["sodir/factpages"]["min_features"] = 8
    monkeypatch.setattr("osd.verify.load_records", lambda: {rec["id"]: rec})
    monkeypatch.setattr("osd.verify.outlines.load_rules", lambda: rules)
    od = tmp_path / "outlines"
    od.mkdir()
    committed = od / "sodir__factpages.geojson"
    committed.write_text('{"type":"FeatureCollection","features":[]}\n')
    kw = {"fetch": fetch_ok, "opener": wfs_opener(FIX / "sodir__factpages" / "wellbores", []),
          "out_dir": tmp_path / "v", "inputs_dir": tmp_path / "in", "outlines_dir": od}
    [v] = verify_all(fetch_inputs=True, **kw)
    assert committed.read_text() == '{"type":"FeatureCollection","features":[]}\n'  # checked, not rewritten
    assert outcome(v, "outline-derived")["outcome"] == "fail"
    [v] = verify_all(derive=True, **kw)
    assert len(json.loads(committed.read_text())["features"]) == 8
    assert outcome(v, "outline-derived")["outcome"] == "pass"


# --- E18: the dates a register states for each feature --------------------------------------

DATED_REC = {"id": "fixture/dated-register", "licence": {"name": "Some licence"},
             "inputs": [{"name": "wells", "url": "https://fixture.test/wfs?typeNames=wells", "format": "wfs",
                         "crs": "EPSG:4326"}],
             "period": {"start": "1990", "end": "2000"}}
DATED_RULES = {"fixture/dated-register": {"min_features": 1, "inputs": {"wells": {
    "extractor": "register-wfs", "kind": "wellbore", "id": "WELL_ID", "name": "WELL_NAME", "page_size": 1000,
    "period_fields": {"start": "START", "end": "END"}, "period_placeholders": ["1900-01-01"],
    "params": {"propertyName": "WELL_ID,WELL_NAME,START,END,SHAPE"}}}}}


def dated_register(tmp_path) -> dict:
    """The fixture register derived as osd verify --outlines would (tests/fixtures/outlines/dates)."""
    inputs = stage(tmp_path, DATED_REC["id"], "wells", FIX / "dates" / "wells")
    return derive(DATED_REC, DATED_RULES, inputs)


def _by_local(fc) -> dict:
    return {f["properties"]["feature_id"].split("#", 1)[1]: f["properties"] for f in fc["features"]}


PERIOD_MEMBERS = ("osd:period_start_raw", "osd:period_end_raw", "osd:period_start", "osd:period_end")


def test_fixture_register_outline_period_members(tmp_path):
    fc = dated_register(tmp_path)
    got = {k: {m: p[m] for m in PERIOD_MEMBERS if m in p} for k, p in _by_local(fc).items()}
    assert got == {
        "dated": {"osd:period_start_raw": "1993-06-01", "osd:period_end_raw": "1994-02-28",
                  "osd:period_start": "1993-06-01T00:00:00Z", "osd:period_end": "1994-02-28T23:59:59Z"},
        "undated": {},
        "placeholder": {"osd:period_start_raw": "1900-01-01", "osd:period_end_raw": "1995-01-01",
                        "osd:period_end": "1995-01-01T23:59:59Z"},
        "reversed": {"osd:period_start_raw": "1996-05-01", "osd:period_end_raw": "1995-01-01",
                     "osd:period_start": "1996-05-01T00:00:00Z", "osd:period_end": "1995-01-01T23:59:59Z"},
        "open-end": {"osd:period_start_raw": "1998-03-04", "osd:period_start": "1998-03-04T00:00:00Z"},
        "late-start": {"osd:period_start_raw": "2001-02-03", "osd:period_start": "2001-02-03T00:00:00Z"},
        "malformed": {"osd:period_start_raw": "sometime in 1993", "osd:period_end_raw": "1994-01-01",
                      "osd:period_end": "1994-01-01T23:59:59Z"},
        "timestamp-utc": {"osd:period_start_raw": "1992-07-08T10:11:12", "osd:period_end_raw": "1992-07-09T01:02:03",
                          "osd:period_start": "1992-07-08T10:11:12Z", "osd:period_end": "1992-07-09T01:02:03Z"},
        "timestamp-zoned": {"osd:period_start_raw": "1992-07-08T10:11:12+02:00",
                            "osd:period_end_raw": "1992-07-08T23:00:00Z",
                            "osd:period_start": "1992-07-08T08:11:12Z", "osd:period_end": "1992-07-08T23:00:00Z"},
    }
    assert fc["inputs"]["wells"]["period_fields"] == {"start": "START", "end": "END"}
    assert not validate_outline_3(fc)


def test_placeholder_is_kept_raw_not_normalised(tmp_path):
    p = _by_local(dated_register(tmp_path))["placeholder"]
    assert p["osd:period_start_raw"] == "1900-01-01" and "osd:period_start" not in p
    rules = copy.deepcopy(DATED_RULES)
    rules[DATED_REC["id"]]["inputs"]["wells"]["period_placeholders"] = []
    inputs = stage(tmp_path / "again", DATED_REC["id"], "wells", FIX / "dates" / "wells")
    assert _by_local(derive(DATED_REC, rules, inputs))["placeholder"]["osd:period_start"] == "1900-01-01T00:00:00Z"


@pytest.mark.parametrize("raw, bound, form, want", [
    ("1993-06-01", "start", "iso", "1993-06-01T00:00:00Z"),
    ("1993-06-01", "end", "iso", "1993-06-01T23:59:59Z"),
    ("1992-07-08T10:11:12", "start", "iso", "1992-07-08T10:11:12Z"),
    ("1992-07-08T10:11:12", "end", "iso", "1992-07-08T10:11:12Z"),
    ("1992-07-08T10:11:12.5Z", "start", "iso", "1992-07-08T10:11:12Z"),
    ("1992-07-08T00:30:00+02:00", "start", "iso", "1992-07-07T22:30:00Z"),
    ("2/15/1983", "start", "m/d/y", "1983-02-15T00:00:00Z"),
    ("5/8/1983", "end", "m/d/y", "1983-05-08T23:59:59Z"),
    ("5/1/2021 2:19:33 PM", "start", "m/d/y", "2021-05-01T14:19:33Z"),
    ("6/3/2021 12:07:27 AM", "end", "m/d/y", "2021-06-03T00:07:27Z"),
    ("2/15/1983", "start", "iso", None),
    ("1983-02-15", "start", "m/d/y", None),
    ("1993", "start", "iso", None),
    ("1993-02-30", "start", "iso", None),
    ("13/1/1993", "start", "m/d/y", None),
    ("sometime in 1993", "start", "iso", None),
    ("", "start", "iso", None),
], ids=lambda x: str(x))
def test_normalise_period_values(raw, bound, form, want):
    from osd.outlines.extractors import period_instant
    assert period_instant(raw, bound, form) == want


def test_wfs_requests_carry_the_period_fields():
    """Each register input with dates asks the service for them: the request's propertyName
    names both fields, so the bytes stored and hashed hold the dates the outline carries."""
    from urllib.parse import parse_qs, urlsplit

    from osd.outlines import fetch_parts
    dated = {(rid, n) for rid, r in RULES.items() if rid != "defaults"
             for n, i in r["inputs"].items() if i.get("period_fields") and i["extractor"] == "register-wfs"}
    assert dated == {("sodir/factpages", "wellbores"), ("sodir/factpages", "seismic-finished"),
                     ("sodir/factpages", "seismic-ongoing"), ("sodir/factpages", "seismic-paused"),
                     ("nlog/nlog", "boreholes")}
    robots = type("R", (), {"allowed": staticmethod(lambda u: True)})()
    for rid, name in sorted(dated):
        rule = RULES[rid]["inputs"][name]
        [rec_input] = [i for i in RECS[rid]["inputs"] if i["name"] == name]
        calls = []
        fetch_parts(rec_input, rule, wfs_opener(FIX / "dates" / "wells", calls), robots)
        pages = [c for c in calls if "startIndex=" in c]
        assert pages, (rid, name)
        for c in pages:
            asked = parse_qs(urlsplit(c).query)["propertyName"][0].split(",")
            assert {rule["period_fields"]["start"], rule["period_fields"]["end"]} <= set(asked), (rid, name, asked)
    for rid, name in [("nlog/nlog", "surveys-3d")]:   # the layer states only DATE_RELEASE (evidence/e18)
        assert "period_fields" not in RULES[rid]["inputs"][name]


def validate_outline_3(fc) -> list:
    schema = json.loads((paths.SCHEMA_DIR / "outline.schema.json").read_text())
    v, vc = Draft202012Validator(schema, format_checker=FormatChecker()), Draft202012Validator(
        schema["$defs"]["collection"], format_checker=FormatChecker())
    errs = list(vc.iter_errors({k: x for k, x in fc.items() if k not in ("type", "features")}))
    return errs + [e for f in fc["features"] for e in v.iter_errors(f["properties"])]


def test_outline_2_files_validate_under_outline_2_and_3(tmp_path):
    v2 = json.loads((FIX / "schema" / "outline-2.schema.json").read_text())
    assert v2["$id"].endswith("/outline/2")
    assert json.loads((paths.SCHEMA_DIR / "outline.schema.json").read_text())["$id"].endswith("/outline/3")
    p2, c2 = Draft202012Validator(v2), Draft202012Validator(v2["$defs"]["collection"])
    files = sorted((FIX / "outline-2").glob("*.geojson"))
    assert len(files) == 2
    for p in files:
        fc = json.loads(p.read_text())
        assert not list(c2.iter_errors({k: x for k, x in fc.items() if k not in ("type", "features")})), p
        assert not [e for f in fc["features"] for e in p2.iter_errors(f["properties"])], p
        assert not validate_outline_3(fc), p
    new = dated_register(tmp_path)   # an outline/3 file names its date fields: outline/2 refuses it
    assert list(c2.iter_errors({"inputs": new["inputs"]}))
    bad = copy.deepcopy(new)
    bad["features"][0]["properties"]["osd:period_start"] = "1993-06-01"
    assert validate_outline_3(bad)


# --- E29: ArcGIS Map/Feature Server layers ---------------------------------------------------

ARC = FIX / "arcgis"
ARC_URL = "https://fixture.test/arcgis/rest/services/W/MapServer/4"
ARC_REC = {**copy.deepcopy(RECS["sodir/factpages"]), "id": "fixture/arcgis-register",
           "inputs": [{"name": "wells", "url": ARC_URL, "format": "arcgis", "crs": "EPSG:2193"}],
           "period": {"start": "1960", "end": "2026-10-23"}}   # distinct from every feature's dates
ARC_RULES = {"fixture/arcgis-register": {"min_features": 5, "inputs": {"wells": {
    "extractor": "register-arcgis", "kind": "wellbore", "uwi": "UWI", "name": "Title",
    "period_fields": {"start": "Start_Date", "end": "End_Date"}, "period_format": "epoch-ms"}}}}
ARC_OIDS = {"40", "72", "78", "123", "150"}   # tests/fixtures/outlines/arcgis/features.json; 151 has no position


def arcgis_server(calls: list, layer=None, count=None, sr=None, error_at=None, http_error_at=None,
                  empty_at=None, repeat_at=None):
    """Serve the frozen layer as an ArcGIS server does: the description, returnCountOnly, and pages
    in the asked order and offset with only the asked fields; the keywords break one thing each."""
    from urllib.parse import parse_qs, urlsplit

    lay = layer or json.loads((ARC / "layer.json").read_text())
    data = json.loads((ARC / "features.json").read_text())

    def open_(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            raise FetchError(url, 404)
        u = urlsplit(url)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if not u.path.endswith("/query"):
            return iter([json.dumps(lay).encode()])
        if q.get("returnCountOnly") == "true":
            return iter([json.dumps({"count": len(data["features"]) if count is None else count}).encode()])
        off, n = int(q["resultOffset"]), int(q["resultRecordCount"])
        if off == http_error_at:
            raise FetchError(url, 500)
        if off == error_at:
            return iter([b'{"error":{"code":500,"message":"Unable to complete operation.","details":[]}}'])
        oid = q["orderByFields"].split()[0]
        rows = sorted(data["features"], key=lambda f: f["attributes"][oid])
        page = [] if off == empty_at else rows[off - n:off] if off == repeat_at else rows[off:off + n]
        fields = q["outFields"].split(",")
        out = [{"attributes": {k: f["attributes"][k] for k in fields if k in f["attributes"]},
                **({"geometry": f["geometry"]} if f["geometry"] else {})} for f in page]
        return iter([json.dumps({"spatialReference": sr or data["spatialReference"], "features": out}).encode()])

    return open_


def arcgis_derive(tmp_path, rec=ARC_REC, rules=ARC_RULES, **server):
    calls = []
    fetch_inputs(rec, rules, arcgis_server(calls, **server), tmp_path)
    return derive(rec, rules, tmp_path), calls


def test_arcgis_pages_reassemble_the_object_id_set(tmp_path):
    fc, _ = arcgis_derive(tmp_path)
    got = published_ids(fc)
    assert len(got) == len(set(got)) and set(got) == ARC_OIDS
    assert fc["unplaced"] == ["fixture/arcgis-register#151"]   # null geometry: listed, not drawn
    assert {f["properties"]["feature_id"] for f in fc["features"]} == {f"fixture/arcgis-register#{i}" for i in ARC_OIDS}
    d = tmp_path / "fixture__arcgis-register" / "wells"
    assert sorted(p.name for p in d.iterdir()) == ["SHA256SUMS", "count", "layer", "page-000000", "page-000002",
                                                   "page-000004"]
    by = {f["properties"]["publisher_id"]: f["properties"] for f in fc["features"]}
    assert (by["40"]["name"], by["40"]["uwi"], by["40"]["kind"]) == ("MA-10A", "100000762213", "wellbore")


def test_arcgis_duplicate_object_ids_are_refused(tmp_path):
    with pytest.raises(Refused, match="object id 40 served twice"):   # a server that ignores resultOffset
        arcgis_derive(tmp_path, repeat_at=2)


def test_arcgis_missing_page_is_refused(tmp_path):
    from osd.outlines.extractors import register_arcgis
    arcgis_derive(tmp_path)
    parts = [p for p in outlines.read_parts(tmp_path / "fixture__arcgis-register" / "wells") if p[0] != "page-000002"]
    with pytest.raises(Refused, match="page at offset 2 is missing"):
        register_arcgis(ARC_REC["inputs"][0], ARC_RULES[ARC_REC["id"]]["inputs"]["wells"], parts)
    with pytest.raises(Refused, match="page at offset 2 served 0 features, not the 2"):
        arcgis_derive(tmp_path, empty_at=2)


def test_arcgis_page_error_is_refused(tmp_path):
    with pytest.raises(Refused, match="page at offset 2 answered an error: 500 Unable to complete operation"):
        arcgis_derive(tmp_path, error_at=2)
    with pytest.raises(Refused, match="fetch failed"):
        arcgis_derive(tmp_path, http_error_at=4)


def test_arcgis_count_mismatch_is_refused(tmp_path):
    for count in (5, 7):
        with pytest.raises(Refused, match=f"the layer counts {count} features, the pages served 6"):
            arcgis_derive(tmp_path, count=count)


def test_arcgis_without_pagination_or_object_ids_is_refused(tmp_path):
    lay = json.loads((ARC / "layer.json").read_text())
    no_paging = {**lay, "advancedQueryCapabilities": {"supportsPagination": False}}
    no_oid = {**lay, "fields": [f for f in lay["fields"] if f["type"] != "esriFieldTypeOID"]}
    for layer, why in ((no_paging, "supportsPagination"), (no_oid, "no object id field")):
        calls = []
        with pytest.raises(Refused, match=why):
            fetch_inputs(ARC_REC, ARC_RULES, arcgis_server(calls, layer=layer), tmp_path)
        assert not any("resultOffset" in c for c in calls)
    with_field = {**no_oid, "objectIdField": "OBJECTID"}   # a FeatureServer names it outright
    fc, _ = arcgis_derive(tmp_path, layer=with_field)
    assert set(published_ids(fc)) == ARC_OIDS


def test_arcgis_wkid_mismatch_is_refused(tmp_path):
    with pytest.raises(Refused, match=r"states spatialReference \['EPSG:4326'\], the record EPSG:2193"):
        arcgis_derive(tmp_path, sr={"wkid": 4326, "latestWkid": 4326})
    with pytest.raises(Refused, match="states spatialReference none"):
        arcgis_derive(tmp_path, sr={"wkt": "PROJCS[...]"})
    fc, _ = arcgis_derive(tmp_path, sr={"wkid": 102193, "latestWkid": 2193})   # an Esri code with its EPSG code
    assert set(published_ids(fc)) == ARC_OIDS


def test_arcgis_layer_above_the_cap_is_refused(tmp_path):
    calls = []
    with pytest.raises(Refused, match="counts 50001 features, above the 50000"):
        fetch_inputs(ARC_REC, ARC_RULES, arcgis_server(calls, count=50001), tmp_path)
    assert not any("resultOffset" in c for c in calls)


@pytest.mark.parametrize("case", ["point", "polyline-two-paths", "polygon-with-hole", "polygon-two-exteriors",
                                  "multipoint", "null", "nan-point"])
def test_esri_json_geometries_match_geojson_fixtures(case):
    from osd.outlines.extractors import esri_geometry
    c = json.loads((ARC / "geometries.json").read_text())[case]
    assert esri_geometry(c["esri"]) == c["geojson"]


def test_esri_hole_outside_every_exterior_is_refused():
    from osd.outlines.extractors import esri_geometry
    with pytest.raises(Refused, match="inside no exterior"):
        esri_geometry({"rings": [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]], [[20, 20], [28, 20], [28, 28], [20, 20]]]})


def test_arcgis_native_coordinates_transform_like_wfs(tmp_path):
    """The Esri point (1638611.12, 5621550.6) in NZTM2000 lands where pyproj puts it and where the WFS
    path puts the same native position: one transform, from the record's crs."""
    from osd.outlines.extractors import register_wfs
    fc, _ = arcgis_derive(tmp_path)
    [got] = [f["geometry"]["coordinates"] for f in fc["features"] if f["properties"]["publisher_id"] == "40"]
    lon, lat = Transformer.from_crs("EPSG:2193", "EPSG:4326", always_xy=True).transform(1638611.12, 5621550.6)
    assert got == [round(lon, 6), round(lat, 6)] and 173 < lon < 174 and -40 < lat < -39   # Maui, offshore Taranaki
    page = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"ID": 40},
            "geometry": {"type": "Point", "coordinates": [1638611.12, 5621550.6]}}]}
    [wfs] = register_wfs({"name": "w", "crs": "EPSG:2193"}, {"kind": "wellbore", "id": "ID"},
                         [("page-000000", json.dumps(page).encode())])
    assert wfs["geometry"]["coordinates"] == got




def test_arcgis_requests_page_by_object_id(tmp_path):
    from urllib.parse import parse_qs, urlsplit
    _, calls = arcgis_derive(tmp_path)
    assert f"{ARC_URL}?f=json" in calls
    assert any(c.startswith(ARC_URL + "/query?") and "returnCountOnly=true" in c for c in calls)
    pages = [parse_qs(urlsplit(c).query) for c in calls if "resultOffset=" in c]
    assert [q["resultOffset"] for q in pages] == [["0"], ["2"], ["4"]]
    for q in pages:
        assert q["orderByFields"] == ["OBJECTID ASC"] and q["resultRecordCount"] == ["2"] and q["f"] == ["json"]
        assert q["outFields"] == ["OBJECTID,UWI,Title,Start_Date,End_Date"] and "outSR" not in q
    for rid, r in RULES.items():   # every ArcGIS input of the catalogue asks for the fields its rule reads
        for name, rule in (r.get("inputs") or {}).items() if rid != "defaults" else ():
            if rule["extractor"] == "register-arcgis":
                from osd.outlines.extractors import arcgis_out_fields
                asked = arcgis_out_fields(rule, "OID").split(",")
                assert set((rule.get("period_fields") or {}).values()) <= set(asked), (rid, name)
                assert [i["format"] for i in RECS[rid]["inputs"] if i["name"] == name] == ["arcgis"]


def test_refused_arcgis_input_demotes_an_l3_record(tmp_path):
    fc, _ = arcgis_derive(tmp_path / "in")
    rec, opener, sample = l2_passing(tmp_path, ARC_REC)
    kw = {"now": NOW, "opener": opener, "sample": sample, "outline_rule": {"min_features": 5}, "stored": stored_of(fc)}
    v = verify_record(rec, fetch_ok, fc, **kw)
    assert v["level"] == "L3"
    today = verify_record(rec, fetch_ok, fc, previous=v, refused="wells: the layer counts 7 features, the pages served 6", **kw)
    assert outcome(today, "outline-derived")["outcome"] == "fail" and today["level"] == "L2"


def test_multilinestring_parts_follow_linestring_rules():
    from osd.records import geometry_problems
    assert geometry_problems({"type": "MultiLineString", "coordinates": [[[174, -39], [175, -40]], [[176, -41], [177, -41]]]}) == []
    assert geometry_problems({"type": "MultiLineString", "coordinates": [[[174, -39], [175, -40]], [[176, -41]]]}) == \
        ["line has fewer than 2 positions"]
    assert geometry_problems({"type": "MultiLineString", "coordinates": [[[174, -39], [1750000, -40]]]})
    assert geometry_problems({"type": "MultiLineString", "coordinates": []}) == ["multilinestring has no lines"]


def test_multipoint_parts_follow_point_rules():
    from osd.records import geometry_problems
    assert geometry_problems({"type": "MultiPoint", "coordinates": [[174, -39], [175, -40]]}) == []
    assert geometry_problems({"type": "MultiPoint", "coordinates": [[174, -39], [1638611.12, 5621550.6]]}) == \
        ["position [1638611.12, 5621550.6] outside WGS84 lon/lat"]
    assert geometry_problems({"type": "MultiPoint", "coordinates": []}) == ["multipoint has no positions"]
