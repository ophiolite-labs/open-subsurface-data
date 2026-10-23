"""E04: the static STAC catalogue (charter docs/program/charters/E04-stac-catalogue.md)."""

import copy
import json
import random
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
# `full_build` (tests/conftest.py) is the real catalogue, built once per session (E32); `staged` is a
# small build of three real records with this module's own verification inputs.

@pytest.fixture(scope="module")
def staged(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("staged")
    records = tmp / "records"
    for rid in ("equinor/volve", "nlog/nlog", "seg/open-data-wiki"):   # L2, L1, L0
        (records / rid.split("/")[0]).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "records" / f"{rid}.yaml", records / f"{rid}.yaml")
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
    build(catalog, vdir, records_dir=records)
    site_data = tmp / "site" / "data"
    shutil.copytree(catalog, site_data, dirs_exist_ok=True)   # the Makefile's `cp -R build/catalog/.`
    return site_data


def test_makefile_copies_catalog_recursively():
    recipe = re.search(r"^build:.*?\n((?:\t.*\n)+)", (ROOT / "Makefile").read_text(), re.MULTILINE).group(1)
    assert "cp -R build/catalog/. site/data/" in recipe


ITEM_SAMPLE, ITEM_SEED = 20, 18   # OSD-D18: the gate samples Items; `make check-full` validates them all


def item_sample(collection_dir: Path) -> list[Path]:
    """First and last Item by file name, plus up to ITEM_SAMPLE between them chosen by a fixed seed,
    from the Items the Collection links, its child shards' included (E32)."""
    items = sorted(stac.collection_items(collection_dir / "collection.json"))
    if len(items) <= 2:
        return items
    middle = items[1:-1]
    picked = random.Random(ITEM_SEED).sample(middle, min(ITEM_SAMPLE, len(middle)))
    return [items[0], *sorted(picked), items[-1]]


def _linked_collection(c: Path, names: list[str]) -> None:
    (c / "items").mkdir(parents=True, exist_ok=True)
    for n in names:
        (c / "items" / n).write_text("{}")
    (c / "collection.json").write_text(json.dumps({"links": [{"rel": "item", "href": f"./items/{n}"} for n in names]}))


def test_item_sample_is_bounded_and_fixed(tmp_path):
    _linked_collection(tmp_path / "c", [f"{i:03}.json" for i in range(100)])
    s = item_sample(tmp_path / "c")
    assert len(s) == ITEM_SAMPLE + 2 and s[0].name == "000.json" and s[-1].name == "099.json"
    assert s == item_sample(tmp_path / "c") and len(set(s)) == len(s)
    _linked_collection(tmp_path / "c", ["000.json", "050.json", "099.json"])
    assert len(item_sample(tmp_path / "c")) == 3


def test_staged_catalog_collections_and_item_sample_validate_offline(full_build, no_network):
    """OSD-D18: the catalog, every Collection, and per Collection first, last and a seeded sample of Items."""
    stac_dir = full_build / "stac"
    cols = sorted(stac_dir.glob("*/collection.json"))
    assert len(cols) == len(load_records())
    targets = [stac_dir / "catalog.json", *cols, *(i for c in cols for i in item_sample(c.parent))]
    assert any("/items/" in str(t) for t in targets)   # records with a period put Items in the sample
    for t in targets:
        ok, messages = stac.validate(t, recursive=False)
        assert ok and len(messages) == 1, (t, messages)


def test_makefile_check_full_validates_whole_tree_and_verify_runs_it_on_main_only():
    mk = (ROOT / "Makefile").read_text()
    recipe = re.search(r"^check-full:.*?\n((?:\t.*\n)+)", mk, re.MULTILINE).group(1)
    assert "stac.validate" in recipe and "site/data/stac/catalog.json" in recipe
    assert not re.search(r"^check:.*check-full", mk, re.MULTILINE)   # never part of the gate
    wf = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
    step = re.search(r"- name: full STAC tree.*?\n((?:        .*\n)+)", wf).group(0)
    assert "make check-full" in step
    assert "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'" in step


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
    ids = [r["id"] for r in json.loads((staged / "records.json").read_text())["records"]]
    assert reached["collections"] == {stac.collection_id(rid) for rid in ids} and len(ids) == 3
    assert len([i for i in reached["items"] if i.startswith("nlog/nlog#")]) > stac.SHARD_SIZE   # through shards


def test_collection_levels_equal_records_json(staged):
    levels = {r["id"]: r["level"] for r in json.loads((staged / "records.json").read_text())["records"]}
    assert {"L0", "L1", "L2"} <= set(levels.values())
    for rid, level in levels.items():
        col = json.loads((staged / "stac" / stac.collection_id(rid) / "collection.json").read_text())
        assert col["osd:level"] == level, rid


def test_licence_mapping_every_record(full_build):
    for rid, rec in load_records().items():
        col = json.loads((full_build / "stac" / stac.collection_id(rid) / "collection.json").read_text())
        spdx = rec["licence"].get("spdx")
        assert col["license"] == (spdx or "other"), rid
        lic = [x for x in col["links"] if x["rel"] == "license"]
        assert len(lic) == 1 and lic[0]["href"] == rec["licence"].get("url", rec["origin"]["url"]), rid
    for p in full_build.rglob("*.json"):   # Items carry no licence; every other file is read
        if p.parent.name != "items":
            assert '"proprietary"' not in p.read_text(), p


def test_collection_assets_from_verified_files(staged):
    col = json.loads((staged / "stac" / "equinor--volve" / "collection.json").read_text())
    assert col["osd:checked_at"] == "2026-10-23T12:00:00+00:00"
    assert col["assets"] == {"Volve_Well_logs.zip": {
        "href": "https://example.org/Volve_Well_logs.zip", "title": "Volve_Well_logs.zip",
        "roles": ["data"], "file:size": 1234, "file:checksum": "1220" + SHA}}
    assert stac.FILE_EXTENSION in col["stac_extensions"]


def test_outlines_geojson_carries_feature_id(full_build):
    fc = json.loads((full_build / "outlines.geojson").read_text())
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
    assert schema["$id"].endswith("/record/5") and "period" not in schema["required"]
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


# --- E18: Items carry their own dates ------------------------------------------------------------

def _dated_catalog(tmp_path):
    """The fixture register (tests/fixtures/outlines/dates, collection period 1990-2000) built."""
    from test_outlines import DATED_REC, dated_register

    from osd.outlines import write_outline
    od = tmp_path / "outlines"
    od.mkdir()
    write_outline(dated_register(tmp_path), od / "fixture__dated-register.geojson")
    rec = _record(DATED_REC["id"], period=DATED_REC["period"])
    catalog = tmp_path / "catalog"
    stac.write_catalog(catalog, [rec], vdir=tmp_path, outlines_dir=od)
    return catalog / "stac" / "catalog.json"


COLLECTION_1990_2000 = ("1990-01-01T00:00:00Z", "2000-12-31T23:59:59Z")


@pytest.mark.parametrize("local, start, end, source", [
    ("dated", "1993-06-01T00:00:00Z", "1994-02-28T23:59:59Z", "feature"),
    ("timestamp-utc", "1992-07-08T10:11:12Z", "1992-07-09T01:02:03Z", "feature"),
    ("timestamp-zoned", "1992-07-08T08:11:12Z", "1992-07-08T23:00:00Z", "feature"),
    ("undated", *COLLECTION_1990_2000, "collection"),
    ("placeholder", *COLLECTION_1990_2000, "collection"),
    ("reversed", *COLLECTION_1990_2000, "collection"),
    ("open-end", "1998-03-04T00:00:00Z", "2000-12-31T23:59:59Z", "feature-start,collection-end"),
    ("late-start", *COLLECTION_1990_2000, "collection"),
    ("malformed", *COLLECTION_1990_2000, "collection"),
], ids=lambda x: x if isinstance(x, str) and "T" not in x else "")
def test_fixture_register_item_periods(tmp_path, local, start, end, source):
    catalog = _dated_catalog(tmp_path)
    p = _items(catalog)[f"fixture/dated-register#{local}"]["properties"]
    assert (p["start_datetime"], p["end_datetime"], p["osd:period_source"]) == (start, end, source)
    col = json.loads((catalog.parent / "fixture--dated-register" / "collection.json").read_text())
    assert col["extent"]["temporal"]["interval"] == [list(COLLECTION_1990_2000)]   # the record's period


def test_fixture_items_lie_inside_their_collection_and_validate(tmp_path, no_network):
    catalog = _dated_catalog(tmp_path)
    assert len(_items(catalog)) == 9
    assert stac.containment_problems(catalog.parent) == []
    ok, messages = stac.validate(catalog, recursive=True)
    assert ok, messages


def test_item_outside_its_collection_fails_validation(tmp_path, no_network):
    rec = _record("acme/dated", period={"start": "1990", "end": "2000"})
    od = tmp_path / "outlines"
    _outlines(od, "acme/dated", ["early", "inside"])
    p = od / "acme__dated.geojson"
    fc = json.loads(p.read_text())
    fc["features"][0]["properties"].update({"osd:period_start": "1985-01-01T00:00:00Z",
                                            "osd:period_end": "1986-01-01T23:59:59Z"})
    p.write_text(json.dumps(fc))
    stac.write_catalog(tmp_path / "catalog", [rec], vdir=tmp_path, outlines_dir=od)
    root = tmp_path / "catalog" / "stac"
    [problem] = stac.containment_problems(root)
    assert "acme/dated#early" in problem
    ok, messages = stac.validate(root / "catalog.json", recursive=True)
    assert not ok and any("acme/dated#early" in str(m) for m in messages)


def test_every_item_states_its_period_source(staged):
    """The published tree: every Item says where its interval comes from."""
    from collections import Counter
    seen = Counter()
    for col in sorted((staged / "stac").glob("*/collection.json")):
        for it in item_sample(col.parent):
            seen[json.loads(it.read_text())["properties"]["osd:period_source"]] += 1
    assert seen and set(seen) <= {"feature", "feature-start,collection-end", "collection"}


def _osd_doc(tmp_path, url, **item_fields):
    _, cols = _write(tmp_path, [_record("acme/demo", level="L1")], {})
    col = dict(cols[0], links=[], stac_extensions=[url])
    item = {"type": "Feature", "stac_version": "1.0.0", "stac_extensions": [url], "id": "acme/demo#a",
            "geometry": {"type": "Point", "coordinates": [4.5, 54.5]}, "bbox": [4.5, 54.5, 4.5, 54.5],
            "links": [], "assets": {},
            "properties": {"datetime": None, "start_datetime": "1990-01-01T00:00:00Z",
                           "end_datetime": "2000-12-31T23:59:59Z", "osd:approximate": False,
                           "osd:derivation": "fixture", **item_fields}}
    return col, item


V1_URL = "https://raw.githubusercontent.com/ophiolite-labs/open-subsurface-data/main/schema/stac-osd.json"


def test_stac_osd_1_and_2_documents_validate_under_their_frozen_schemas(tmp_path, no_network):
    """OSD-D19: documents naming the v1 or v2 identifier (no osd:period_source) validate under their
    frozen copy, under the current schema and through the schema map, which sends every identifier
    to the current file as the host does online; the frozen copies refuse osd:period_source."""
    from jsonschema import Draft7Validator
    m = json.loads(stac.SCHEMA_MAP.read_text())["schemas"]
    current = json.loads((ROOT / "schema/stac-osd.json").read_text())
    assert current["$id"] == stac.OSD_EXTENSION == V1_URL + "?v=3"
    cur = Draft7Validator(current)
    for n, url in ((1, V1_URL), (2, V1_URL + "?v=2")):
        frozen = json.loads((ROOT / f"tests/fixtures/schema/stac-osd-{n}.json").read_text())
        assert frozen["$id"] == url and m[url] == m[stac.OSD_EXTENSION] == "../stac-osd.json"
        col, item = _osd_doc(tmp_path, url)
        for doc in (col, item):
            assert not list(Draft7Validator(frozen).iter_errors(doc)), url
            assert not list(cur.iter_errors(doc)) and _valid(doc, tmp_path), url
        _, dated = _osd_doc(tmp_path, url, **{"osd:period_source": "feature"})
        assert list(Draft7Validator(frozen).iter_errors(dated)), url   # v1 and v2 know no period_source
    for good in ("feature", "feature-start,collection-end", "collection"):
        _, item = _osd_doc(tmp_path, stac.OSD_EXTENSION, **{"osd:period_source": good})
        assert _valid(item, tmp_path) and not list(cur.iter_errors(item)), good
    _, item = _osd_doc(tmp_path, stac.OSD_EXTENSION, **{"osd:period_source": "record"})
    assert not _valid(item, tmp_path)   # closed enum


# --- E32: Collections above SHARD_SIZE Items link child Catalog shards --------------------------

def _walk_item_ids(catalog: Path, collections: set | None = None, broken: list | None = None) -> list[str]:
    """Every Item id reached from the root by `child` and `item` links, once per link (a duplicate
    link shows as a repeated id); the Collection ids passed go into `collections`, every relative link
    of a reached file that names no file into `broken`."""
    ids, todo, seen, exists = [], [stac.link_target(catalog)], set(), {}
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        doc = json.loads(p.read_text())
        if doc["type"] == "Collection" and collections is not None:
            collections.add(doc["id"])
        for x in doc.get("links", []):
            target = stac.link_target(p, x["href"])
            if target not in exists:
                exists[target] = "://" in x["href"] or target.is_file()
            if broken is not None and not exists[target]:
                broken.append(f"{p}: {x['rel']} -> {x['href']}")
            if x["rel"] == "child":
                todo.append(target)
            elif x["rel"] == "item":
                ids.append(json.loads(target.read_text())["id"])
    return ids


def test_reached_items_are_exactly_the_outline_feature_ids(full_build):
    # mutation: a shard's `child` link left out of its Collection -> Items missed, red
    want = []
    for rid, rec in load_records().items():
        op = ROOT / "outlines" / (rid.replace("/", "__") + ".geojson")
        if rec.get("period") and op.exists():
            want += [f["properties"]["feature_id"] for f in json.loads(op.read_text())["features"]
                     if f["properties"].get("feature_id")]
    collections, broken = set(), []
    reached = _walk_item_ids(full_build / "stac" / "catalog.json", collections, broken)
    assert broken == []   # every link of every reached file resolves (link_problems on the whole tree, once)
    assert collections == {stac.collection_id(rid) for rid in load_records()}
    assert len(reached) == len(set(reached)), "an Item is linked twice"
    assert len(want) == len(set(want))
    assert set(reached) == set(want)


def test_collections_stay_small_and_shard_above_the_threshold(full_build):
    sharded = 0
    for col_path in (full_build / "stac").glob("*/collection.json"):
        assert col_path.stat().st_size < 2_000_000, col_path
        links = json.loads(col_path.read_text())["links"]
        items = [x for x in links if x["rel"] == "item"]
        shards = [x for x in links if x["rel"] == "child"]
        assert len(items) <= stac.SHARD_SIZE and not (items and shards), col_path
        sharded += bool(shards)
        for x in shards:
            shard = json.loads((col_path.parent / x["href"]).read_text())
            assert shard["type"] == "Catalog" and 0 < sum(y["rel"] == "item" for y in shard["links"]) <= stac.SHARD_SIZE
    assert sharded, "no register is above the threshold"


def _sharded(tmp_path, monkeypatch, n=5, size=2):
    """acme/many: n Items in shards of `size`, dated register 1990-2000."""
    monkeypatch.setattr(stac, "SHARD_SIZE", size)
    rec = _record("acme/many", period={"start": "1990", "end": "2000"})
    catalog, (col,) = _write(tmp_path, [rec], {"acme/many": [f"w{i}" for i in range(n)]})
    return catalog, col


def test_shards_are_standard_catalogs_and_items_keep_their_collection(tmp_path, monkeypatch, no_network):
    catalog, col = _sharded(tmp_path, monkeypatch)
    assert [x["href"] for x in col["links"] if x["rel"] in ("item", "child")] == [
        "./shards/1/catalog.json", "./shards/2/catalog.json", "./shards/3/catalog.json"]
    shard = json.loads((catalog.parent / "acme--many" / "shards" / "3" / "catalog.json").read_text())
    assert shard["type"] == "Catalog" and [x["href"] for x in shard["links"] if x["rel"] == "item"] == ["../../items/w4.json"]
    item = json.loads((catalog.parent / "acme--many" / "items" / "w4.json").read_text())
    assert item["collection"] == "acme--many"
    assert {x["rel"]: x["href"] for x in item["links"]}["parent"] == "../collection.json"
    assert "\n " not in (catalog.parent / "acme--many" / "collection.json").read_text()   # compact
    assert sorted(_walk_item_ids(catalog)) == [f"acme/many#w{i}" for i in range(5)]
    assert stac.link_problems(catalog.parent) == []
    ok, messages = stac.validate(catalog, recursive=True)
    assert ok, messages
    assert {m["path"].rsplit("/", 1)[-1] for m in messages} >= {"catalog.json", "w4.json"}   # shards walked
    (catalog.parent / "acme--many" / "shards" / "3" / "catalog.json").unlink()
    assert stac.link_problems(catalog.parent) == [
        "acme--many/collection.json: child -> ./shards/3/catalog.json does not exist"]


def test_item_outside_its_interval_on_a_later_shard_fails_check_full(tmp_path, monkeypatch, no_network):
    # mutation: containment_problems reads only the Collection's direct item links -> passes, red
    catalog, _ = _sharded(tmp_path, monkeypatch)
    p = catalog.parent / "acme--many" / "items" / "w4.json"
    item = json.loads(p.read_text())
    item["properties"].update(start_datetime="2005-01-01T00:00:00Z", end_datetime="2006-01-01T00:00:00Z")
    p.write_text(json.dumps(item))
    ok, messages = stac.validate(catalog, recursive=True)
    assert not ok
    assert [m["error_message"] for m in messages if m.get("error_type") == "containment"] == [
        ("acme/many#w4: 2005-01-01T00:00:00Z to 2006-01-01T00:00:00Z is outside its Collection's "
        "1990-01-01T00:00:00Z to 2000-12-31T23:59:59Z")]


def test_item_sample_draws_from_shards(tmp_path, monkeypatch):
    catalog, _ = _sharded(tmp_path, monkeypatch, n=7)
    sample = item_sample(catalog.parent / "acme--many")
    assert [p.name for p in sample] == [f"w{i}.json" for i in range(7)]   # all 7 under the sample size
