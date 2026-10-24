"""E35: whole ArcGIS layers for the verifier (verification/5 `layer_exports`, never a file).

A fake ArcGIS server answers the description, returnCountOnly, returnIdsOnly and object-id pages
from tests/fixtures/whole_layers/features.json; each failing case has its own server variant.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from urllib.parse import parse_qs, urlsplit

from jsonschema import Draft202012Validator

from osd import paths, stac
from osd.build import build
from osd.records import load_record
from osd.verify import ByteBudget, Fetched, FetchError, Pacer, check_files, paced, verify_record

FIX = paths.ROOT / "tests" / "fixtures" / "whole_layers"
LAYER_DOC = json.loads((FIX / "features.json").read_text())
FEATURES = LAYER_DOC["features"]
LAYER = "https://fixture.test/arcgis/rest/services/W/MapServer/0"
LICENCE = "https://fixture.test/licence.html"
EDITED = 1761213703000
V5 = Draft202012Validator(json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text()))

# The canonical esri-json of the fixture layer, literal: features by object id, keys sorted, no whitespace
CANONICAL = (
    b'{"features":['
    b'{"attributes":{"DEPTH_M":1200.5,"NAME":"Alpha-1","OBJECTID":1,"SPUD":315532800000,"UWI":"W-001"},'
    b'"geometry":{"x":1730000.25,"y":5900000.5}},'
    b'{"attributes":{"DEPTH_M":980,"NAME":"Bravo-1","OBJECTID":2,"SPUD":null,"UWI":"W-002"},'
    b'"geometry":{"x":1731000.125,"y":5901000.0}},'
    b'{"attributes":{"DEPTH_M":2210.25,"NAME":"Charlie-1","OBJECTID":3,"SPUD":631152000000,"UWI":"W-003"},'
    b'"geometry":{"x":1732000.0,"y":5902000.75}},'
    b'{"attributes":{"DEPTH_M":15.0,"NAME":"Delta-1 \xc3\xa9","OBJECTID":4,"SPUD":946684800000,"UWI":"W-004"},'
    b'"geometry":null},'
    b'{"attributes":{"DEPTH_M":3005.0,"NAME":"Echo-1","OBJECTID":5,"SPUD":1262304000000,"UWI":"W-005"},'
    b'"geometry":{"x":1734000.5,"y":5904000.25}}],'
    b'"geometryType":"esriGeometryPoint","objectIdFieldName":"OBJECTID",'
    b'"spatialReference":{"latestWkid":2193,"wkid":2193}}'
)


class Body:
    """One response, streamed in chunks; HTTP errors raise as the real opener does."""

    def __init__(self, url, data=b"", status=200, chunk=1 << 20):
        self.url, self.data, self.status, self.chunk = url, data, status, chunk
        self.content_type, self.content_disposition, self.content_length = "application/json", "", None

    def __iter__(self):
        if self.status != 200:
            raise FetchError(self.url, self.status)
        for i in range(0, len(self.data), self.chunk):
            yield self.data[i:i + self.chunk]


class Server:
    """A fake ArcGIS layer. Every knob is one failing case."""

    def __init__(self, features=None, size=2, count=None, ids=None, pages=None, edit_dates=(EDITED,),
                 error_at=None, http_error_at=None, robots=None, chunk=1 << 20, export=None):
        self.features = copy.deepcopy(features if features is not None else FEATURES)
        self.size, self.count, self.ids, self.pages = size, count, ids, pages
        self.edit_dates, self.described = list(edit_dates), 0
        self.error_at, self.http_error_at, self.robots, self.chunk = error_at, http_error_at, robots, chunk
        self.export = export
        self.calls: list[str] = []

    def description(self) -> dict:
        d = {"type": "Feature Layer", "maxRecordCount": self.size, "objectIdField": "OBJECTID",
             "advancedQueryCapabilities": {"supportsPagination": True}, "geometryType": "esriGeometryPoint",
             "fields": [{"name": "OBJECTID", "type": "esriFieldTypeOID"}]}
        date = self.edit_dates[min(self.described, len(self.edit_dates) - 1)]
        self.described += 1
        if date is not None:
            d["editingInfo"] = {"lastEditDate": date}
        return d

    def page(self, off: int) -> dict:
        if self.pages is not None:   # explicit page contents, by offset
            feats = self.pages[off]
        else:
            ordered = sorted(self.features, key=lambda f: f["attributes"]["OBJECTID"])
            feats = ordered[off:off + self.size]
        return {"objectIdFieldName": "OBJECTID", "geometryType": "esriGeometryPoint",
                "spatialReference": LAYER_DOC["spatialReference"], "fields": [{"name": "OBJECTID"}],
                "exceededTransferLimit": True, "features": copy.deepcopy(feats)}

    def __call__(self, url):
        self.calls.append(url)
        u = urlsplit(url)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        body = lambda d, status=200: Body(url, json.dumps(d).encode(), status, self.chunk)
        if u.path == "/robots.txt":
            return Body(url, self.robots.encode()) if self.robots else Body(url, status=404)
        if url == LICENCE:
            return Body(url, b"<html><body>Open licence text</body></html>")
        if u.path == urlsplit(LAYER).path:
            return body(self.description())
        assert u.path == urlsplit(LAYER).path + "/query", url
        if q.get("f") == "geojson":   # the one-page export of E23
            return Body(url, self.export or b'{"type":"FeatureCollection","features":[],"exceededTransferLimit":true}')
        if q.get("returnCountOnly") == "true":
            return body({"count": self.count if self.count is not None else len(self.features)})
        if q.get("returnIdsOnly") == "true":
            ids = self.ids if self.ids is not None else [f["attributes"]["OBJECTID"] for f in self.features]
            return body({"objectIdFieldName": "OBJECTID", "objectIds": ids})
        assert (q["outFields"], q["f"], q["orderByFields"]) == ("*", "json", "OBJECTID ASC") and "outSR" not in q
        off = int(q["resultOffset"])
        if off == self.http_error_at:
            return body({}, 500)
        if off == self.error_at:
            return body({"error": {"code": 400, "message": "Unable to complete operation."}})
        return body(self.page(off))


def record():
    rec = load_record(paths.RECORDS_DIR / "terranubis" / "f3-demo-2020.yaml")
    rec = copy.deepcopy(rec)
    rec["origin"]["manifest_url"] = LAYER + "?f=json"
    rec["licence"]["url"] = LICENCE
    return rec


def fetch_ok(url):
    return Fetched(200, url, "text/html", 5, b"<html></html>")


def run(server, budget=None):
    v = verify_record(record(), fetch_ok, None, opener=server, sample=["*"], budget=budget)
    V5.validate(v)
    return v


def files_check(v):
    return next(c for c in v["checks"] if c["name"] == "files-checksummed")


def export_bytes(server) -> bytes:
    from osd.verifier.layers import export_layer
    _, body = export_layer(LAYER, lambda u: b"".join(server(u)))
    return body


# --- canonical bytes ---------------------------------------------------------------------------------

def test_whole_layer_canonical_bytes_are_exact():
    assert export_bytes(Server()) == CANONICAL
    assert (FIX / "features.json").exists()


def test_shuffled_pages_and_features_give_identical_bytes():
    rng = random.Random(35)
    feats = copy.deepcopy(FEATURES)
    rng.shuffle(feats)
    for f in feats:   # keys reordered within each feature as another node might serve them
        f["attributes"] = dict(reversed(list(f["attributes"].items())))
    pages = {0: feats[0:2], 2: feats[2:4], 4: feats[4:5]}
    assert [f["attributes"]["OBJECTID"] for f in feats] != [1, 2, 3, 4, 5]
    assert export_bytes(Server(pages=pages)) == CANONICAL


def _digest(features) -> str:
    return hashlib.sha256(export_bytes(Server(features=features))).hexdigest()


def test_attribute_null_geometry_and_moved_coordinate_each_change_the_digest():
    base = _digest(FEATURES)
    attr, null, moved = (copy.deepcopy(FEATURES) for _ in range(3))
    attr[2]["attributes"]["DEPTH_M"] = 2210.26
    null[0]["geometry"] = None
    moved[4]["geometry"]["x"] = 1734000.51
    digests = {base, _digest(attr), _digest(null), _digest(moved)}
    assert len(digests) == 4


def test_the_assembled_id_set_equals_return_ids_only():
    server = Server()
    v = run(server)
    (x,) = v["layer_exports"]
    ids = json.loads(b"".join(server(LAYER + "/query?where=1%3D1&returnIdsOnly=true&f=json")))["objectIds"]
    served = [f["attributes"]["OBJECTID"] for f in json.loads(CANONICAL)["features"]]
    assert served == sorted(ids) and x["features"] == len(ids) == x["count"] == 5
    assert x == {"layer": LAYER, "format": "esri-json", "features": 5, "count": 5, "bytes": len(CANONICAL),
                 "sha256": hashlib.sha256(CANONICAL).hexdigest(), "edit_date_before": EDITED,
                 "edit_date_after": EDITED}


# --- the check -----------------------------------------------------------------------------------------

def test_a_complete_layer_passes_l2_as_evidence_not_a_file():
    v = run(Server())
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("pass", "L2")
    assert c["detail"].startswith("whole layer checked (5 features, esri-json), not a downloadable file; "
                                  "edit date 2025-10-23T10:01:43+00:00 unchanged during paging")
    assert "files" not in v and "partial_exports" not in v


def test_a_layer_export_never_becomes_an_asset():
    v = run(Server())
    assert v["layer_exports"] and "files" not in v
    assert stac._assets(v) == {}   # no STAC asset: osd get, manifests and the mirror read `files` only


def test_a_layer_without_an_edit_date_passes_with_stability_unknown():
    v = run(Server(edit_dates=(None,)))
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("pass", "L2")
    assert "stability unknown (the layer states no edit date)" in c["detail"]
    assert v["layer_exports"][0]["edit_date_before"] is None


def test_an_edit_during_paging_is_incomplete():
    # the listing and the description before paging read EDITED, the description after the next date
    v = run(Server(edit_dates=(EDITED, EDITED, EDITED + 60_000)))
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1")
    assert ("layer edited during paging (lastEditDate 2025-10-23T10:01:43+00:00 before, "
            "2025-10-23T10:02:43+00:00 after): whole layer not a snapshot") in c["detail"]
    (x,) = v["layer_exports"]
    assert (x["edit_date_before"], x["edit_date_after"]) == (EDITED, EDITED + 60_000)


def _fails(server, reason):
    v = run(server)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("fail", "L1"), c
    assert reason in c["detail"], c["detail"]
    assert "layer_exports" not in v and "files" not in v


def test_duplicate_id_fails():
    pages = {0: FEATURES[0:2], 2: [FEATURES[2], FEATURES[1]], 4: FEATURES[4:5]}
    _fails(Server(pages=pages), "the layer: object id 2 served twice")


def test_http_page_error_fails():
    _fails(Server(http_error_at=2), "page error: HTTP 500 from")


def test_error_json_page_fails():
    _fails(Server(error_at=2), "the layer: page at offset 2 answered an error: 400 Unable to complete operation.")


def test_count_guard_alone_catches_an_oversized_final_page():
    # a full first page and a final page larger than the count leaves room for: ids unique, listed by
    # returnIdsOnly; only the count disagrees
    six = copy.deepcopy(FEATURES) + [{"attributes": {"OBJECTID": 6, "UWI": "W-006"}, "geometry": None}]
    pages = {0: six[0:3], 3: six[3:6]}
    _fails(Server(features=six, size=3, count=4, pages=pages),
           "the layer: the layer counts 4 features, the pages served 6")


def test_ids_differing_from_return_ids_only_fail():
    _fails(Server(ids=[1, 2, 3, 4, 99]), "the pages' object ids differ from returnIdsOnly (5 ids listed): "
                                          "1 not listed (e.g. [5]), 1 not served (e.g. [99])")


def test_a_layer_above_the_feature_cap_stays_a_partial_export():
    server = Server(count=50_001, size=1000)   # 51 pages: under the 200-page cap, above the 50,000 features
    v = run(server)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1")
    assert ("not read whole: the layer counts 50001 features, above the 50000 a whole layer is read to; "
            "the one-page export instead") in c["detail"]
    assert "export truncated by the server (exceededTransferLimit)" in c["detail"]
    assert v["partial_exports"] and "layer_exports" not in v
    assert not [u for u in server.calls if "resultOffset" in u]


def test_robots_disallow_skips_the_layer():
    server = Server(robots="User-agent: *\nDisallow: /arcgis/rest/services/W/MapServer/0/query\n")
    v = run(server)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1")
    assert "robots.txt disallows the layer query https://fixture.test/arcgis/rest/services/W/MapServer/0/query?" in c["detail"]
    assert not [u for u in server.calls if "/query?" in u]


def test_a_page_over_the_budget_share_is_abandoned_and_counted():
    server = Server(chunk=64)
    size = lambda u: len(b"".join(Server()(u)))
    before = [LAYER + "?f=json", LAYER + "/query?where=1%3D1&returnCountOnly=true&f=json",
              LAYER + "/query?where=1%3D1&returnIdsOnly=true&f=json"]
    page = len(json.dumps(server.page(0)).encode())
    # the description, count, ids and the first page fit (the listing is not budgeted); the second is cut
    run_budget = ByteBudget(limit=sum(size(u) for u in before) + page + page // 2)
    c, files, members = check_files(record(), ["*"], server, run_budget.share(512 * 1024**2))
    assert c["outcome"] == "skip" and "whole layer cut at the budget" in c["detail"], c
    assert "resultOffset=2&" in c["detail"] and "abandoned mid-stream after 192 bytes" in c["detail"], c["detail"]
    assert run_budget.used == run_budget.limit   # the abandoned read counts: the run has no room left
    assert not files and "layer_exports" not in members


def test_every_layer_request_is_paced_per_host():
    server = Server()
    sleeps: list[float] = []
    fetch, opener = paced(fetch_ok, server, Pacer(clock=lambda: 0.0, sleep=sleeps.append))   # time stands still
    verify_record(record(), fetch, None, opener=opener, sample=["*"])
    layer_calls = [u for u in server.calls if u.startswith(LAYER)]
    assert len(layer_calls) == 8   # listing, description, count, ids, three pages, description again
    assert len(sleeps) == len(server.calls) - 1 and set(sleeps) == {2.0}


# --- the build reads verification/4 and verification/5 -------------------------------------------------

def test_the_build_reads_verification_4_and_5(tmp_path, tmp_records):
    for version, extra in (("4", {}), ("5", {"layer_exports": [{
            "layer": LAYER, "format": "esri-json", "features": 5, "count": 5, "bytes": 10, "sha256": "b" * 64,
            "edit_date_before": None, "edit_date_after": None}]})):
        vdir = tmp_path / f"v{version}"
        vdir.mkdir()
        (vdir / "acme__demo.json").write_text(json.dumps(
            {"record_id": "acme/demo", "checked_at": "2026-10-24T12:00:00+00:00", "tool_version": "t",
             "level": "L2", "checks": [], **extra}))
        out = tmp_path / f"catalog{version}"
        assert build(out, vdir, records_dir=tmp_records)["records"] == 1
        (rec,) = json.loads((out / "records.json").read_text())["records"]
        assert rec["level"] == "L2"
        col = json.loads(next((out / "stac").rglob("collection.json")).read_text())
        assert not col.get("assets")
