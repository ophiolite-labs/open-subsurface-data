"""E19: vocabulary from the records lanes (charter docs/program/charters/E19-vocabulary-from-the-records-lanes.md,
strategy E19-vocabulary-from-the-records-lanes-STRATEGY.md): record/3, the stac-osd v2 access value, the
status expiry note, the scaffold's comment lists and the six record edits. E26 (charter
E26-vocabulary-kinds-the-records-lanes-asked-for.md): record/4's five kinds, record/3 compatibility and the
scaffold's kinds comment. E29 (charter E29-outlines-from-the-map-services.md): record/5's `arcgis` input
format and record/4 compatibility."""

import copy
import gzip
import hashlib
import json
import socket
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator, Draft202012Validator, FormatChecker, ValidationError

from osd import cli, new, paths, stac
from osd.records import load_record, load_records, record_files, validate_records
from osd.verify import Fetched, verify_record

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "tests" / "fixtures" / "schema"
NOW = datetime(2026, 10, 23, 12, tzinfo=UTC)
TERMS = {"stated": "a purchase is a licence to use the data for at most 10 years",
         "duration": "at most 10 years from purchase", "review_before_publication": True, "expires": None}
V1_URL = "https://raw.githubusercontent.com/ophiolite-labs/open-subsurface-data/main/schema/stac-osd.json"


def _v(schema: dict) -> Draft202012Validator:
    return Draft202012Validator(schema, format_checker=FormatChecker())


RECORD = _v(json.loads((paths.SCHEMA_DIR / "record.schema.json").read_text()))   # the live schema, record/5 (E29)
RECORD_4 = _v(json.loads((FROZEN / "record-4.schema.json").read_text()))
RECORD_3 = _v(json.loads((FROZEN / "record-3.schema.json").read_text()))
RECORD_2 = _v(json.loads((FROZEN / "record-2.schema.json").read_text()))
NEW_KINDS = ["velocity-model", "geological-model", "airborne-em", "radiometrics", "stress"]   # E26, literal


def _base(**kw) -> dict:
    rec = {"id": "acme/demo", "title": "Demo set", "publisher": {"name": "Acme", "url": "https://acme.example"},
           "origin": {"url": "https://acme.example/demo", "access": "anonymous"},
           "licence": {"name": "Acme terms", "spdx": None, "redistribution": "forbidden", "attribution": "unknown"},
           "kinds": ["seismic-3d"], "region": {"country": "NL"}, "listed_by": ["publisher"], "added": "2026-10-23"}
    for k, x in kw.items():
        if k == "access":
            rec["origin"]["access"] = x
        elif k == "terms":
            rec["licence"]["terms"] = x
        else:
            rec[k] = x
    return rec


def _errors(rec: dict) -> list:
    return list(RECORD.iter_errors(rec))


# --- record/3 --------------------------------------------------------------------------------------

def test_record_ids_are_versioned():
    assert RECORD.schema["$id"].endswith("/record/5") and RECORD_4.schema["$id"].endswith("/record/4")
    assert RECORD_3.schema["$id"].endswith("/record/3")
    assert RECORD_2.schema["$id"].endswith("/record/2")


def test_record_3_admits_the_new_values():
    assert _errors(_base(kinds=["potential-fields"])) == []
    assert _errors(_base(access="purchase")) == []
    assert _errors(_base(access="purchase", terms=TERMS)) == []
    assert _errors(_base(terms={"stated": "Licence runs until 31 December 2030.", "expires": "2030-12-31"})) == []
    assert _errors(_base(terms={"stated": "Terms as published.", "duration": None,
                                "review_before_publication": None, "expires": None})) == []
    assert _errors(_base(terms={"stated": "Only the words."})) == []


def test_terms_without_stated_refused():
    assert _errors(_base(terms={k: x for k, x in TERMS.items() if k != "stated"}))
    assert _errors(_base(terms={"stated": ""}))


@pytest.mark.parametrize("expires", ["2027-13-01", "2027-02-30", "soon", "2027", "27-01-01", "2027-01-01T00:00:00Z",
                                     20270101, True, date(2027, 1, 1)],
                         ids=["month-13", "feb-30", "word", "year", "short-year", "datetime", "int", "bool", "yaml-date"])
def test_expires_not_a_date_refused(expires):
    assert _errors(_base(terms=dict(TERMS, expires=expires)))


@pytest.mark.parametrize("rec", [
    _base(kinds=["gravity"]), _base(access="paid"), _base(access="Purchase"),
    _base(terms=dict(TERMS, price="40 USD")), _base(terms="at most 10 years"),
    _base(terms=dict(TERMS, review_before_publication="yes")), _base(terms=dict(TERMS, duration=10)),
], ids=["kind", "access", "access-case", "terms-closed", "terms-string", "review-string", "duration-int"])
def test_unknown_values_refused(rec):
    assert _errors(rec)


def test_record_2_files_validate_under_record_2():
    """Every record/2 file is a record/3 file; every current record without its record/3 values is a
    record/2 file under the frozen record/2 schema."""
    assert not list(RECORD_2.iter_errors(_base())) and not _errors(_base())
    assert list(RECORD_2.iter_errors(_base(access="purchase")))     # the frozen copy is the old contract
    old = 0
    for p in record_files():
        rec = load_record(p)
        assert not list(RECORD.iter_errors(rec)), p
        if (rec["origin"]["access"] == "purchase" or "potential-fields" in rec["kinds"]
                or set(NEW_KINDS) & set(rec["kinds"]) or "terms" in rec["licence"]
                or any(i["format"] == "arcgis" for i in rec.get("inputs") or [])):   # record/5 (E29)
            continue
        assert not list(RECORD_2.iter_errors(rec)), p
        old += 1
    assert old >= 89   # at least 96 records (E20), seven carry record/3 values


def test_the_six_records_state_the_new_values():
    recs = load_records()
    for rid in ("prime/national-oil-gas-database", "eug/national-data-repository", "namcor/exploration-production-data"):
        assert "potential-fields" in recs[rid]["kinds"], rid
    for rid in ("namcor/exploration-production-data", "beg/stratton-3d", "dgh/national-data-repository",
                "pasa/national-petroleum-exploration-database"):
        assert recs[rid]["origin"]["access"] == "purchase", rid
    assert not any("Want" in k for k in recs["beg/stratton-3d"]["known_issues"])
    terms = recs["pasa/national-petroleum-exploration-database"]["licence"]["terms"]
    assert terms["duration"] == "a maximum period of 10 years"   # the publisher's words (E20)
    assert terms["review_before_publication"] is True and terms["expires"] is None
    assert "maximum period of 10 years" in terms["stated"] and "review prior to publication" in terms["stated"]
    assert {"dgh/national-data-repository", "pasa/national-petroleum-exploration-database"} <= {
        k for k, r in recs.items() if "terms" in r["licence"]}   # a subset: later records may state terms (E22)
    assert validate_records() == [] and len(recs) >= 96


# --- record/4 (E26): the kinds the records lanes asked for ----------------------------------------

RECORD_3_KINDS = [   # every record/3 kind, a fixed list: the compatibility fixtures, one record each
    "wellbore-headers", "wellbore-logs", "wellbore-paths", "tops", "core", "time-depth",
    "seismic-3d", "seismic-2d", "seismic-4d", "horizons", "surfaces", "faults",
    "reservoir-model", "production", "pressure", "geochemistry", "reports", "source-list",
    "potential-fields"]


@pytest.mark.parametrize("kind", NEW_KINDS)
def test_record_4_admits_each_new_kind(kind):
    assert _errors(_base(kinds=[kind])) == []
    assert _errors(_base(kinds=["seismic-3d", kind])) == []


@pytest.mark.parametrize("kind", ["velocity_model", "Velocity-model", "velocity", "geologic-model", "aem",
                                  "radiometric", "in-situ-stress"])
def test_record_4_refuses_an_unknown_kind(kind):
    assert _errors(_base(kinds=[kind]))


def test_record_3_fixtures_validate_under_record_3_and_record_4():
    """The same record/3 files, one per record/3 kind, are valid under the frozen record/3 and under
    record/4; the frozen copy is the old contract and refuses each new kind."""
    for kind in RECORD_3_KINDS:
        rec = _base(kinds=[kind])
        assert not list(RECORD_3.iter_errors(rec)), kind
        assert not _errors(rec), kind
    for kind in NEW_KINDS:
        assert list(RECORD_3.iter_errors(_base(kinds=[kind]))), kind


# --- record/5 (E29): inputs read from an ArcGIS layer -------------------------------------------

RECORD_4_FORMATS = ["wfs", "csv", "segy", "mdio", "geojson", "html-geojson"]   # every record/4 format, literal


def _with_input(fmt: str) -> dict:
    return _base(inputs=[{"name": "layer", "url": "https://acme.example/arcgis/rest/services/W/MapServer/0",
                          "format": fmt, "crs": "EPSG:2193", "stated": "layer description: wkid 2193"}])


def test_record_4_fixtures_validate_under_record_4_and_record_5():
    """The same record/4 files, one per record/4 input format and one per record/4 kind, are valid under
    the frozen record/4 and under record/5; every stored record is valid under record/5."""
    for fmt in RECORD_4_FORMATS:
        assert not list(RECORD_4.iter_errors(_with_input(fmt))), fmt
        assert not _errors(_with_input(fmt)), fmt
    for kind in RECORD_3_KINDS + NEW_KINDS:
        assert not list(RECORD_4.iter_errors(_base(kinds=[kind]))), kind
        assert not _errors(_base(kinds=[kind])), kind
    for p in record_files():
        assert not _errors(load_record(p)), p


def test_record_5_admits_arcgis_and_record_4_refuses_it():
    assert _errors(_with_input("arcgis")) == []
    assert list(RECORD_4.iter_errors(_with_input("arcgis")))
    assert _errors(_with_input("ArcGIS")) and _errors(_with_input("esri-json"))


# --- osd new: the scaffold's comment lists come from the schema -----------------------------------

def test_new_scaffold_comments_list_the_schema_values():
    props = RECORD.schema["properties"]
    text = new.scaffold("https://acme.example/demo", "Demo", "acme/demo", date(2026, 10, 23))
    lines = {line.split(":")[0].strip(): line.split("#", 1)[1].strip() for line in text.splitlines()
             if "#" in line and not line.startswith("#")}
    assert lines["access"] == "fill: " + " | ".join(props["origin"]["properties"]["access"]["enum"])
    assert "purchase" in lines["access"]
    assert lines["redistribution"] == "fill: " + " | ".join(props["licence"]["properties"]["redistribution"]["enum"])
    assert lines["attribution"] == "fill: " + " | ".join(props["licence"]["properties"]["attribution"]["enum"])
    assert lines["listed_by"] == " | ".join(props["listed_by"]["items"]["enum"])


def test_new_scaffold_kinds_comment_lists_the_schema_kinds():
    text = new.scaffold("https://acme.example/demo", "Demo", "acme/demo", date(2026, 10, 23))
    (line,) = [x for x in text.splitlines() if x.startswith("kinds:")]
    assert line.split("#", 1)[1].strip() == "fill: " + " | ".join(RECORD.schema["properties"]["kinds"]["items"]["enum"])
    listed = line.split("fill: ", 1)[1].split(" | ")
    for kind in NEW_KINDS + RECORD_3_KINDS:
        assert kind in listed, kind


# --- osd status: a stated absolute expiry beside the level ------------------------------------------

@pytest.mark.parametrize("terms, note", [
    ({"stated": "Until 22 October 2026.", "expires": "2026-10-22"}, "(terms expired 2026-10-22)"),
    ({"stated": "Until 23 October 2026.", "expires": "2026-10-23"}, "(terms expire 2026-10-23 (today))"),
    ({"stated": "Until 24 October 2026.", "expires": "2026-10-24"}, "(terms expire 2026-10-24)"),
    ({"stated": "At most 10 years.", "duration": "at most 10 years from purchase", "expires": None}, None),
    ({"stated": "At most 10 years."}, None),
    (None, None),
    ({"stated": "Until soon.", "expires": "soon"}, "(terms expire ? ('soon' is not a date))"),
], ids=["past", "today", "future", "null", "absent", "no-terms", "malformed"])
def test_status_terms_expiry(tmp_records, tmp_path, terms, note):
    p = tmp_records / "acme" / "demo.yaml"
    rec = yaml.safe_load(p.read_text())
    if terms is not None:
        rec["licence"]["terms"] = terms
    p.write_text(yaml.safe_dump(rec))
    vdir = tmp_path / "verification"
    vdir.mkdir()
    for at in (NOW, datetime(2026, 10, 23, 23, 59, 59, tzinfo=UTC), datetime(2026, 10, 23, 0, 0, tzinfo=UTC)):
        lines = cli.status_lines(vdir, now=at, records_dir=tmp_records)
        (row,) = lines[1:]
        if note is None:
            assert row.split()[:2] == ["L0", "acme/demo"] and "terms" not in row
        else:
            assert row.startswith(f"L0 {note} acme/demo"), row
        assert row.index("acme/") == lines[0].index(" id ") + 1     # columns stay aligned


def test_status_reads_an_unquoted_yaml_date_as_the_day():
    rec = _base(terms={"stated": "Until 1 Jan 2027.", "expires": date(2027, 1, 1)})
    assert cli.terms_note(rec, NOW) == "terms expire 2027-01-01"


# --- verification does not read access --------------------------------------------------------------

def test_verification_identical_for_request_and_purchase():
    rec = load_record(paths.RECORDS_DIR / "dgh" / "national-data-repository.yaml")
    before = copy.deepcopy(rec)
    before["origin"]["access"] = "request"
    assert rec["origin"]["access"] == "purchase"

    def fetch(url):
        return Fetched(200, url, "text/html", 12)

    a, b = verify_record(before, fetch, None, now=NOW), verify_record(rec, fetch, None, now=NOW)
    assert a["checks"] == b["checks"] and a["level"] == b["level"] == "L1"
    assert a == b


# --- STAC: purchase and the keyword travel; a stac-osd/1 document still validates -----------------

@pytest.fixture
def no_network(monkeypatch):
    def refuse(*a, **k):
        raise OSError("network access denied in tests")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr("stac_validator.utilities.urlopen", refuse)


def _collection(tmp_path) -> dict:
    rec = dict(_base(access="purchase", kinds=["seismic-2d", "potential-fields"], terms=TERMS),
               level="L1", checked_at="2026-10-23T12:00:00+00:00", stale=False, blocked_since=None)
    (tmp_path / "v").mkdir()
    (tmp_path / "o").mkdir()
    (col,) = stac.write_catalog(tmp_path / "catalog", [rec], vdir=tmp_path / "v", outlines_dir=tmp_path / "o")
    return col


def test_stac_collection_carries_purchase_and_keyword(tmp_path, no_network):
    col = _collection(tmp_path)
    assert col["osd:access"] == "purchase" and "potential-fields" in col["keywords"]
    assert stac.OSD_EXTENSION in col["stac_extensions"] and "?v=" in stac.OSD_EXTENSION
    ok, msg = stac.validate(tmp_path / "catalog" / "stac" / "catalog.json")
    assert ok, msg
    v2 = json.loads((paths.SCHEMA_DIR / "stac-osd.json").read_text())
    assert v2["$id"] == stac.OSD_EXTENSION
    assert not list(Draft7Validator(v2).iter_errors(col))
    bad = dict(col, **{"osd:access": "paid"})
    assert list(Draft7Validator(v2).iter_errors(bad))


def test_stac_osd_1_collection_still_validates(tmp_path, no_network):
    """A Collection written under stac-osd/1 (the v1 URL, a record/2 access value) validates under the
    frozen v1 schema, under the current schema, and through the offline schema map."""
    col = _collection(tmp_path)
    old = dict(col, stac_extensions=[V1_URL if x == stac.OSD_EXTENSION else x for x in col["stac_extensions"]],
               **{"osd:access": "request"})
    v1 = json.loads((FROZEN / "stac-osd-1.json").read_text())
    assert v1["$id"] == V1_URL
    assert not list(Draft7Validator(v1).iter_errors(old))
    assert list(Draft7Validator(v1).iter_errors(col))        # v1 never knew purchase or the v2 URL
    assert not list(Draft7Validator(json.loads((paths.SCHEMA_DIR / "stac-osd.json").read_text())).iter_errors(old))
    p = tmp_path / "catalog" / "stac" / col["id"] / "collection.json"
    p.write_text(json.dumps(old))
    ok, msg = stac.validate(p, recursive=False)
    assert ok, msg
    smap = json.loads(stac.SCHEMA_MAP.read_text())["schemas"]
    assert smap[V1_URL] == smap[stac.OSD_EXTENSION] == "../stac-osd.json"


def test_template_access_comment_lists_the_schema_values():
    line = next(x for x in (paths.RECORDS_DIR / "_template.yaml").read_text().splitlines() if x.strip().startswith("access:"))
    enum = RECORD.schema["properties"]["origin"]["properties"]["access"]["enum"]
    assert line.split("#", 1)[1].strip() == " | ".join(enum) + " (from schema/record.schema.json)"


# --- E35: verification/5 (layer_exports); verification/4 frozen ---------------------------------------

FROZEN_V4 = FROZEN / "verification-4.schema.json"
V5 = Draft202012Validator(json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text()))
V4 = Draft202012Validator(json.loads(FROZEN_V4.read_text()))
LAYER_EXPORT = {"layer": "https://x.test/arcgis/rest/services/W/MapServer/0", "format": "esri-json",
                "features": 3, "count": 3, "bytes": 120, "sha256": "a" * 64,
                "edit_date_before": 1761213703000, "edit_date_after": 1761213703000}
V_BASE = {"record_id": "a/b", "checked_at": "2026-10-24T12:00:00+00:00", "tool_version": "t", "level": "L2",
          "checks": []}


def test_verification_5_identity():
    assert V5.schema["$id"] == "https://open-subsurface-data.org/schema/verification/5"


def test_frozen_4_is_main_8d23039():
    assert hashlib.sha256(FROZEN_V4.read_bytes()).hexdigest() == (
        "20b7cf84692e42b49092852b54940207b58c1e74497feed66e15f05010e7f4f9")
    assert V4.schema["$id"].endswith("/verification/4")


def _verification_fixtures() -> list[Path]:
    out = []
    for p in sorted((ROOT / "tests" / "fixtures").rglob("*.json")):
        try:
            d = json.loads(p.read_text())
        except ValueError:
            continue
        if isinstance(d, dict) and {"record_id", "checked_at", "level", "checks"} <= set(d) and V4.is_valid(d):
            out.append(p)
    return out


def test_every_verification_4_fixture_validates_under_5():
    found = _verification_fixtures()
    assert len(found) >= 10, found   # site, shards, fidelity and mirror fixtures (24 Oct: 15)
    for p in found:
        V5.validate(json.loads(p.read_text()))
    with gzip.open(ROOT / "tests" / "fixtures" / "verification" / "stored-3.jsonl.gz", "rt") as fh:
        docs = [json.loads(line) for line in fh]
    assert len(docs) == 96
    for d in docs:
        V4.validate(d)
        V5.validate(d)


def test_layer_exports_are_verification_5_only():
    doc = {**V_BASE, "layer_exports": [LAYER_EXPORT]}
    V5.validate(doc)
    V5.validate({**V_BASE, "layer_exports": [{**LAYER_EXPORT, "edit_date_before": None, "edit_date_after": None}]})
    assert not V4.is_valid(doc)


@pytest.mark.parametrize("bad", [
    {"format": "geojson"}, {"sha256": "A" * 64}, {"features": -1}, {"extra": 1}, {"edit_date_after": "today"},
], ids=["format", "sha256", "features", "extra-key", "edit-date"])
def test_layer_export_shape_is_closed(bad):
    with pytest.raises(ValidationError):
        V5.validate({**V_BASE, "layer_exports": [{**LAYER_EXPORT, **bad}]})


def test_a_layer_export_is_never_a_file():
    with pytest.raises(ValidationError):
        V5.validate({**V_BASE, "files": [LAYER_EXPORT]})
