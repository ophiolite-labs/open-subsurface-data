"""E04: the static STAC catalogue (charter docs/program/charters/E04-stac-catalogue.md)."""

import copy
import json
import re
import shutil
import socket
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from osd import stac
from osd.build import build
from osd.records import _schema, load_records

ROOT = Path(__file__).resolve().parents[1]
SHA = "ab" * 32


@pytest.fixture
def no_network(monkeypatch):
    """Every way out of this process raises: sockets, DNS, requests and urllib."""
    def refuse(*a, **k):
        raise OSError("network access denied in tests")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    import requests
    monkeypatch.setattr(requests, "get", refuse)
    monkeypatch.setattr("stac_validator.utilities.urlopen", refuse)


def _record(rid, *, period=None, level="L0", spdx="CC-BY-4.0", url=True):
    lic = {"name": "Some licence", "spdx": spdx, "redistribution": "allowed", "attribution": "required"}
    if url:
        lic["url"] = f"https://{rid.split('/')[0]}.example/licence"
    rec = {"id": rid, "title": f"Title of {rid}", "summary": "A dataset.",
           "publisher": {"name": "Acme", "url": "https://acme.example"},
           "origin": {"url": f"https://acme.example/{rid}", "access": "anonymous"},
           "licence": lic, "kinds": ["seismic-3d"], "region": {"bbox": [4, 54, 6, 56]},
           "listed_by": ["community"], "added": "2026-10-23",
           "level": level, "checked_at": None if level == "L0" else "2026-10-23T12:00:00+00:00",
           "stale": True, "blocked_since": None}
    if period:
        rec["period"] = period
    return rec


def _feature(rid, local, *, input_="grid", lon=4.5):
    return {"type": "Feature",
            "properties": {"record_id": rid, "kind": "survey-3d", "name": local, "approximate": False,
                           "source": "segy-bin-grid:grid", "feature_id": f"{rid}#{local}", "input": input_},
            "geometry": {"type": "Polygon",
                         "coordinates": [[[lon, 54], [lon + 0.5, 54], [lon + 0.5, 55], [lon, 55], [lon, 54]]]}}


def _outlines(d: Path, rid: str, locals_: list[str]) -> None:
    d.mkdir(exist_ok=True)
    (d / (rid.replace("/", "__") + ".geojson")).write_text(json.dumps({
        "type": "FeatureCollection", "licence": "Some licence",
        "inputs": {"grid": {"url": "https://acme.example/grid.sgy", "sha256": SHA}},
        "features": [_feature(rid, x, lon=4 + i * 0.1) for i, x in enumerate(locals_)]}))


def _write(tmp_path, records, outlines, verifications=None):
    od, vd = tmp_path / "outlines", tmp_path / "verification"
    od.mkdir(exist_ok=True)
    vd.mkdir(exist_ok=True)
    for rid, locals_ in outlines.items():
        _outlines(od, rid, locals_)
    for rid, v in (verifications or {}).items():
        (vd / (rid.replace("/", "__") + ".json")).write_text(json.dumps(v))
    out = tmp_path / "catalog"
    cols = stac.write_catalog(out, records, vdir=vd, outlines_dir=od)
    return out / "stac" / "catalog.json", cols


def _items(catalog: Path) -> dict[str, dict]:
    items = (json.loads(p.read_text()) for p in catalog.parent.glob("*/items/*.json"))
    return {i["id"]: i for i in items}


# --- the published tree: real records, staged as `make build` stages it -------------------------

@pytest.fixture(scope="module")
def staged(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("staged")
    vdir = tmp / "verification"
    vdir.mkdir()
    (vdir / "equinor__volve.json").write_text(json.dumps(
        {"record_id": "equinor/volve", "checked_at": "2026-10-23T12:00:00+00:00", "tool_version": "t",
         "level": "L2", "checks": [], "files": [
             {"path": "Volve_Well_logs.zip", "url": "https://example.org/Volve_Well_logs.zip",
              "bytes": 1234, "sha256": SHA}]}))
    (vdir / "nlog__nlog.json").write_text(json.dumps(
        {"record_id": "nlog/nlog", "checked_at": "2026-10-23T12:00:00+00:00", "tool_version": "t",
         "level": "L1", "checks": []}))
    catalog = tmp / "build" / "catalog"
    build(catalog, vdir)
    site_data = tmp / "site" / "data"
    shutil.copytree(catalog, site_data, dirs_exist_ok=True)   # the Makefile's `cp -R build/catalog/.`
    return site_data


def test_makefile_copies_catalog_recursively():
    recipe = re.search(r"^build:.*?\n((?:\t.*\n)+)", (ROOT / "Makefile").read_text(), re.MULTILINE).group(1)
    assert "cp -R build/catalog/. site/data/" in recipe


def test_staged_tree_validates_recursively_offline(staged, no_network):
    ok, messages = stac.validate(staged / "stac" / "catalog.json", recursive=True)
    assert ok, [m for m in messages if not m.get("valid_stac")]
    assert len(messages) == 1 + len(load_records()) + len(list(staged.glob("stac/*/items/*.json")))
    assert all(m["valid_stac"] for m in messages)


def test_validator_needs_the_bundled_schemas(staged, no_network, tmp_path):
    """The schema map is what keeps the validator offline: without it, validation cannot pass."""
    broken = tmp_path / "map.json"
    m = json.loads(stac.SCHEMA_MAP.read_text())["schemas"]
    m = {k: str(stac.SCHEMA_MAP.parent / v) for k, v in m.items() if "collection.json" not in k}
    broken.write_text(json.dumps({"schemas": m}))
    ok, _ = stac.validate(staged / "stac" / "catalog.json", recursive=True, schema_config=broken)
    assert not ok


def test_staged_links_resolve(staged):
    assert stac.link_problems(staged / "stac") == []


def test_reachable_collections_equal_record_ids(staged):
    reached = stac.reachable(staged / "stac" / "catalog.json")
    assert reached["collections"] == {stac.collection_id(rid) for rid in load_records()}


def test_collection_levels_equal_records_json(staged):
    levels = {r["id"]: r["level"] for r in json.loads((staged / "records.json").read_text())["records"]}
    assert {"L0", "L1", "L2"} <= set(levels.values())
    for rid, level in levels.items():
        col = json.loads((staged / "stac" / stac.collection_id(rid) / "collection.json").read_text())
        assert col["osd:level"] == level, rid


def test_licence_mapping_every_record(staged):
    for rid, rec in load_records().items():
        col = json.loads((staged / "stac" / stac.collection_id(rid) / "collection.json").read_text())
        spdx = rec["licence"].get("spdx")
        assert col["license"] == (spdx or "other"), rid
        lic = [x for x in col["links"] if x["rel"] == "license"]
        assert len(lic) == 1 and lic[0]["href"] == rec["licence"].get("url", rec["origin"]["url"]), rid
    for p in staged.rglob("*.json"):
        assert '"proprietary"' not in p.read_text(), p


def test_collection_assets_from_verified_files(staged):
    col = json.loads((staged / "stac" / "equinor--volve" / "collection.json").read_text())
    assert col["osd:checked_at"] == "2026-10-23T12:00:00+00:00"
    assert col["assets"] == {"Volve_Well_logs.zip": {
        "href": "https://example.org/Volve_Well_logs.zip", "title": "Volve_Well_logs.zip",
        "roles": ["data"], "file:size": 1234, "file:checksum": "1220" + SHA}}
    assert stac.FILE_EXTENSION in col["stac_extensions"]


def test_outlines_geojson_carries_feature_id(staged):
    fc = json.loads((staged / "outlines.geojson").read_text())
    with_id = [f for f in fc["features"] if "feature_id" in f["properties"]]
    assert with_id and all(f["id"] == f["properties"]["feature_id"] for f in with_id)
    assert all("id" not in f for f in fc["features"] if "feature_id" not in f["properties"])


# --- Items from fixtures -------------------------------------------------------------------------

def test_item_ids_equal_feature_ids_with_period(tmp_path, no_network):
    recs = [_record("acme/dated", period={"start": "1993", "end": "1994-06"}), _record("acme/undated")]
    catalog, _ = _write(tmp_path, recs, {"acme/dated": ["a", "b", "c"], "acme/undated": ["d", "e"]})
    assert set(_items(catalog)) == {"acme/dated#a", "acme/dated#b", "acme/dated#c"}
    assert stac.reachable(catalog)["items"] == {"acme/dated#a", "acme/dated#b", "acme/dated#c"}
    ok, messages = stac.validate(catalog, recursive=True)
    assert ok, messages
    assert len(messages) == 1 + 2 + 3


@pytest.mark.parametrize("outlines, expected", [
    (["a", "b"], {"acme/l0#a", "acme/l0#b"}),
    ([], set()),
], ids=["l0-with-outlines", "no-outlines"])
def test_items_independent_of_level(tmp_path, outlines, expected):
    rec = _record("acme/l0", period={"start": "2001-02-03", "end": "2001-02-03"}, level="L0")
    catalog, cols = _write(tmp_path, [rec], {"acme/l0": outlines} if outlines else {})
    assert cols[0]["osd:level"] == "L0"
    assert set(_items(catalog)) == expected
    assert {x["href"] for x in cols[0]["links"] if x["rel"] == "item"} == {
        f"./items/{fid.split('#')[1]}.json" for fid in expected}


def test_item_time_and_provenance(tmp_path):
    rec = _record("acme/dated", period={"start": "1993", "end": "1994-02", "stated": "acquired 1993-94"})
    catalog, cols = _write(tmp_path, [rec], {"acme/dated": ["a"]})
    item = _items(catalog)["acme/dated#a"]
    p = item["properties"]
    assert p["datetime"] is None
    assert (p["start_datetime"], p["end_datetime"]) == ("1993-01-01T00:00:00Z", "1994-02-28T23:59:59Z")
    assert (p["osd:approximate"], p["osd:derivation"], p["osd:input_sha256"]) == (
        False, "segy-bin-grid:grid", SHA)
    assert item["bbox"] == [4.0, 54, 4.5, 55]
    assert item["collection"] == "acme--dated" and item["assets"] == {}
    assert cols[0]["extent"]["temporal"]["interval"] == [["1993-01-01T00:00:00Z", "1994-02-28T23:59:59Z"]]


def test_period_end_before_start_fails(tmp_path):
    rec = _record("acme/dated", period={"start": "1995", "end": "1994"})
    with pytest.raises(ValueError, match="period"):
        _write(tmp_path, [rec], {"acme/dated": ["a"]})


def test_undated_collection_has_open_interval_and_no_items(tmp_path):
    catalog, cols = _write(tmp_path, [_record("acme/undated", spdx=None)], {"acme/undated": ["a"]})
    assert cols[0]["extent"]["temporal"]["interval"] == [[None, None]]
    assert cols[0]["license"] == "other"
    assert _items(catalog) == {}


def test_duplicate_feature_id_fails_build(tmp_path):
    recs = [_record("acme/one", period={"start": "2000", "end": "2000"})]
    od = tmp_path / "outlines"
    _outlines(od, "acme/one", ["a", "a"])
    with pytest.raises(ValueError, match="duplicate feature_id 'acme/one#a'"):
        stac.write_catalog(tmp_path / "catalog", recs, vdir=tmp_path, outlines_dir=od)


def test_item_file_names_are_path_safe_and_distinct(tmp_path):
    recs = [_record("acme/one", period={"start": "2000", "end": "2000"})]
    catalog, _ = _write(tmp_path, recs, {"acme/one": ["x/1", "x_1", "B 7"]})
    names = sorted(p.name for p in catalog.parent.glob("acme--one/items/*.json"))
    assert len(names) == 3 and all(re.fullmatch(r"[A-Za-z0-9._-]+\.json", n) for n in names)
    assert set(_items(catalog)) == {"acme/one#x/1", "acme/one#x_1", "acme/one#B 7"}


# --- the osd extension ---------------------------------------------------------------------------

@pytest.fixture
def one_collection(tmp_path):
    _, cols = _write(tmp_path, [_record("acme/demo", level="L1")], {})
    return dict(cols[0], links=[])


def _valid(obj, tmp_path) -> bool:
    p = tmp_path / "obj.json"
    p.write_text(json.dumps(obj))
    ok, _ = stac.validate(p, recursive=False)
    return ok


@pytest.mark.parametrize("mutate", [
    lambda c: c.pop("osd:level"),
    lambda c: c.update({"osd:level": "L9"}),
    lambda c: c.update({"osd:access": "paid"}),
    lambda c: c.update({"osd:redistribution": "maybe"}),
    lambda c: c.update({"osd:verified": True}),
], ids=["missing-level", "l9", "access-enum", "redistribution-enum", "unknown-osd-field"])
def test_osd_extension_rejects(one_collection, tmp_path, no_network, mutate):
    assert _valid(one_collection, tmp_path)
    bad = copy.deepcopy(one_collection)
    mutate(bad)
    assert not _valid(bad, tmp_path)


# --- record/2: period ----------------------------------------------------------------------------

def test_period_is_additive_to_record_2():
    from osd.records import validate_records
    assert validate_records() == []                       # every current record still validates
    schema = _schema("record")
    assert schema["$id"].endswith("/record/2") and "period" not in schema["required"]
    v = Draft202012Validator(schema, format_checker=FormatChecker())
    base = {k: x for k, x in _record("acme/demo").items()
            if k not in ("level", "checked_at", "stale", "blocked_since")}
    assert not list(v.iter_errors(dict(base, period={"start": "1993", "end": "1994-06-30"})))
    for bad in ({"start": "1993"}, {"start": "93", "end": "1994"}, {"start": "1993", "end": "1994", "x": 1}):
        assert list(v.iter_errors(dict(base, period=bad))), bad


def test_unquoted_yaml_period_reads_as_strings(tmp_records):
    from osd.records import load_record, validate_records
    p = tmp_records / "acme" / "demo.yaml"
    p.write_text(p.read_text() + "period: {start: 1993, end: 1994-06-30, stated: acquired 1993-94}\n")
    assert load_record(p)["period"] == {"start": "1993", "end": "1994-06-30", "stated": "acquired 1993-94"}
    assert validate_records(tmp_records) == []
