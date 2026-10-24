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

from osd import paths
from osd.records import load_record
from osd.verify import Fetched, FetchError, verify_record

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
