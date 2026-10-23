"""E03: outlines from the data. Every test runs offline over frozen responses in
tests/fixtures/outlines/ (see its README for what was truncated)."""
import copy
import json
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
    import struct
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
    assert [122.223263, -14.041063] in ring  # inline 983, crossline 504: x 416132.23, y 8447594.37 (MGA 51)


# --- publisher-file and register-csv ------------------------------------------------------

def test_publisher_page_extent(tmp_path):
    inputs = stage(tmp_path, "nzpam/parihaka", "survey-extent")
    [f] = derive(RECS["nzpam/parihaka"], RULES, inputs)["features"]
    assert f["properties"]["publisher_id"] == "927165623" and f["properties"]["name"] == "PARIHAKA-3D : PR3460"
    assert f["geometry"]["type"] == "Polygon" and len(f["geometry"]["coordinates"][0]) == 152


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
    import hashlib
    for f in fc["features"]:
        p = f["properties"]
        assert p["approximate"] is False and p["source"] == "register-wfs (wellbores)"
        assert p["feature_id"] == f"sodir/factpages#{p['publisher_id']}"
        assert p["input_url"] == RECS["sodir/factpages"]["inputs"][0]["url"]
        assert p["input_sha256"] == hashlib.sha256(sums).hexdigest()
        assert p["licence"] == "Norwegian Licence for Open Government Data 2.0"  # OSD-D13
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
    p.write_text(p.read_text().replace('"input_sha256"', '"input_sha"'))
    assert any("input_sha256" in str(m) for m in validate_outlines(tmp_outlines, tmp_records))


# --- fetching through the injected opener ------------------------------------------------

def wfs_opener(d: Path, calls: list):
    """Serve a frozen WFS fixture: resultType=hits -> hits, startIndex=N -> page-N."""
    from urllib.parse import parse_qs, urlsplit

    def open_(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            raise FetchError(url, 404)
        q = parse_qs(urlsplit(url).query)
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
    o, d = check(rec, fc, {"min_features": 1}, {f["properties"]["input_url"]: f["properties"]["input_sha256"]
                                                 for f in fc["features"]})
    assert (o, d) == ("fail", "the record declares no inputs")


def test_approximate_feature_never_passes():
    outline = json.loads(paths.outline_path("terranubis/f3-demo-2020").read_text())
    rec = {**RECS["terranubis/f3-demo-2020"], "inputs": [SEGY_INPUT]}
    assert check(rec, outline, {"min_features": 1}, {})[0] == "fail"


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
    stored = {f["properties"]["input_url"]: f["properties"]["input_sha256"] for f in fc["features"]}
    o, d = check(rec, fc, {"min_features": 1}, stored)
    assert o == "fail" and "duplicate feature_id" in d


# --- the L3 check in the verifier ----------------------------------------------------------

def derived_sodir(tmp_path):
    rec = only(RECS["sodir/factpages"], "wellbores")
    inputs = stage(tmp_path, "sodir/factpages", "wellbores")
    fc = derive(rec, RULES, inputs)
    stored = {rec["inputs"][0]["url"]: fc["features"][0]["properties"]["input_sha256"]}
    return rec, fc, stored


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
    assert v2.schema["$id"].endswith("/record/2") and v1.schema["$id"].endswith("/record/1")
    for p in record_files():
        rec = load_record(p)
        rec.pop("inputs", None)  # the only version-2 addition: what remains is a version-1 file
        assert not list(v1.iter_errors(rec)), p
        assert not list(v2.iter_errors(rec)), p


def test_every_version_1_outline_validates_under_outline_2():
    v1 = Draft202012Validator(json.loads((FIX / "schema" / "outline-1.schema.json").read_text()))
    v2 = Draft202012Validator(json.loads((paths.SCHEMA_DIR / "outline.schema.json").read_text()))
    assert v2.schema["$id"].endswith("/outline/2")
    placeholders = [f for p in sorted(paths.OUTLINES_DIR.glob("*.geojson"))
                    for f in json.loads(p.read_text())["features"] if f["properties"]["approximate"]]
    assert placeholders
    for f in placeholders:
        assert not list(v1.iter_errors(f["properties"])) and not list(v2.iter_errors(f["properties"]))


def test_rules_name_records_with_inputs():
    for rid, rule in RULES.items():
        names = {i["name"] for i in RECS[rid].get("inputs", [])}
        assert rule["inputs"] and set(rule["inputs"]) <= names, rid
        assert isinstance(rule["min_features"], int) and rule["min_features"] >= 1, rid
        for r in rule["inputs"].values():
            assert r["extractor"] in outlines.EXTRACTORS, rid


def test_record_schema_has_no_outline_policy():
    props = json.loads((paths.SCHEMA_DIR / "record.schema.json").read_text())["properties"]["inputs"]
    assert set(props["items"]["properties"]) == {"name", "url", "format", "crs", "units", "stated"}  # OSD-D11
