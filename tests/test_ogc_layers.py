"""E38: WFS 2.0.0 feature types and OGC API Features collections read whole (verification/6).

Two fake servers page tests/fixtures/ogc_layers/features.json: a GeoServer-like WFS (capabilities,
resultType=hits, startIndex/count/sortBy pages) and an OGC API Features collection (a description
with an items link, pages linked by `next`). Every knob is one failing case.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from jsonschema import Draft202012Validator

from osd import paths, stac
from osd.records import load_record
from osd.verifier import layers
from osd.verifier.listings import OgcService, ogc_service
from osd.verify import ByteBudget, Fetched, FetchError, Pacer, check_files, paced, verify_record

FIX = paths.ROOT / "tests" / "fixtures" / "ogc_layers"
DOC = json.loads((FIX / "features.json").read_text())
FEATURES, CRS = DOC["features"], DOC["crs"]
CAPS = (FIX / "capabilities.xml").read_text()
EXCEPTION = (FIX / "exception.xml").read_bytes()
WFS = "https://fixture.test/geoserver/wfs"
WFS_MANIFEST = (f"{WFS}?service=WFS&version=2.0.0&request=GetFeature&typeNames=ns:wells&count=1000"
                f"&outputFormat=application/json")
WFS_LAYER = f"{WFS}?service=WFS&typeNames=ns%3Awells"
OGC = "https://fixture.test/ogc/collections/wells"
LICENCE = "https://fixture.test/licence.html"
V6 = Draft202012Validator(json.loads((paths.SCHEMA_DIR / "verification.schema.json").read_text()))

# The canonical GeoJSON of the fixture layer, literal: features by id, keys sorted, no whitespace
FEATURES_BYTES = (
    b'"features":['
    b'{"geometry":{"coordinates":[176878.25,200476.5],"type":"Point"},"geometry_name":"geom","id":"wells.1",'
    b'"properties":{"depth_m":1200.5,"id":"5007142","name":"Alpha-1","spud":"2017-01-20"},"type":"Feature"},'
    b'{"geometry":{"coordinates":[176900,200500.125],"type":"Point"},"geometry_name":"geom","id":"wells.2",'
    b'"properties":{"depth_m":980,"id":"5007143","name":"Bravo-1","spud":null},"type":"Feature"},'
    b'{"geometry":{"coordinates":[177000.0,200600.75],"type":"Point"},"geometry_name":"geom","id":"wells.3",'
    b'"properties":{"depth_m":2210.25,"id":"5007144","name":"Charlie-1","spud":"1990-01-01"},"type":"Feature"},'
    b'{"geometry":null,"geometry_name":"geom","id":"wells.4",'
    b'"properties":{"depth_m":15.0,"id":"5007145","name":"Delta-1 \xc3\xa9","spud":"2000-01-01"},"type":"Feature"},'
    b'{"geometry":{"coordinates":[177100.5,200700.25],"type":"Point"},"geometry_name":"geom","id":"wells.5",'
    b'"properties":{"depth_m":3005.0,"id":"5007146","name":"Echo-1","spud":"2010-01-01"},"type":"Feature"}],'
)
WFS_CANONICAL = (b'{"crs":{"properties":{"name":"urn:ogc:def:crs:EPSG::31370"},"type":"name"},' + FEATURES_BYTES
                 + b'"type":"FeatureCollection"}')
OGC_CANONICAL = b'{' + FEATURES_BYTES + b'"type":"FeatureCollection"}'


class Body:
    """One response, streamed in chunks; HTTP errors raise as the real opener does."""

    def __init__(self, url, data=b"", status=200, chunk=1 << 20, content_type="application/json", disposition=""):
        self.url, self.data, self.status, self.chunk = url, data, status, chunk
        self.content_type, self.content_disposition, self.content_length = content_type, disposition, None

    def __iter__(self):
        if self.status != 200:
            raise FetchError(self.url, self.status)
        for i in range(0, len(self.data), self.chunk):
            yield self.data[i:i + self.chunk]


def _common(url, robots):
    u = urlsplit(url)
    if u.path == "/robots.txt":
        return Body(url, robots.encode()) if robots else Body(url, status=404)
    if url == LICENCE:
        return Body(url, b"<html><body>Open licence text</body></html>", content_type="text/html")
    return None


class Wfs:
    """A GeoServer-like WFS 2.0.0 for ns:wells."""

    def __init__(self, features=None, size=2, hits=None, pages=None, version="2.0.0", paging="TRUE",
                 sorting="TRUE", json_format="application/json", exception_at=None, http_error_at=None,
                 robots=None, chunk=1 << 20, crs_at=None, attachment=False):
        self.features = copy.deepcopy(features if features is not None else FEATURES)
        self.size, self.hits, self.pages, self.version = size, hits, pages, version
        self.paging, self.sorting, self.json_format = paging, sorting, json_format
        self.exception_at, self.http_error_at, self.robots, self.chunk = exception_at, http_error_at, robots, chunk
        self.crs_at, self.attachment = crs_at or {}, attachment
        self.calls: list[str] = []

    def capabilities(self) -> bytes:
        t = (CAPS.replace("@PAGING@", self.paging).replace("@SORTING@", self.sorting)
             .replace("@COUNT_DEFAULT@", str(self.size)).replace("@JSON@", self.json_format or "GML3"))
        return t.replace('version="2.0.0"', f'version="{self.version}"', 1).encode()

    def page(self, start: int) -> dict:
        if self.pages is not None:
            feats = self.pages[start]
        else:
            feats = sorted(self.features, key=lambda f: f["properties"]["id"])[start:start + self.size]
        return {"type": "FeatureCollection", "features": copy.deepcopy(feats), "totalFeatures": len(self.features),
                "numberMatched": len(self.features), "numberReturned": len(feats), "timeStamp": f"2026-10-24T0{start}:00Z",
                "links": [{"rel": "next", "href": f"{WFS}?startIndex={start + self.size}"}], "bbox": [start, 0, 1, 1],
                "crs": self.crs_at.get(start, CRS)}

    def __call__(self, url):
        self.calls.append(url)
        if (b := _common(url, self.robots)) is not None:
            return b
        u = urlsplit(url)
        assert u.path == urlsplit(WFS).path, url
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        xml = lambda data: Body(url, data, chunk=self.chunk, content_type="application/xml")
        if q["request"] == "GetCapabilities":
            return xml(self.capabilities())
        assert (q["service"], q["version"], q["request"], q["typeNames"]) == ("WFS", "2.0.0", "GetFeature", "ns:wells")
        if q.get("resultType") == "hits":
            n = self.hits if self.hits is not None else len(self.features)
            return xml(f'<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" numberMatched="{n}" '
                       f'numberReturned="0" timeStamp="2026-10-24T03:14:18Z"/>'.encode())
        disposition = "attachment; filename=wells.json" if self.attachment else "inline; filename=wells.json"
        if "startIndex" not in q:   # the manifest's own one-page export
            return Body(url, json.dumps(self.page(0)).encode(), chunk=self.chunk, disposition=disposition)
        assert (q["sortBy"], q["outputFormat"], q["count"]) == ("id ASC", self.json_format, str(self.size)), url
        start = int(q["startIndex"])
        if start == self.http_error_at:
            return Body(url, status=500)
        if start == self.exception_at:
            return xml(EXCEPTION)
        return Body(url, json.dumps(self.page(start)).encode(), chunk=self.chunk, disposition=disposition)


class Ogc:
    """An OGC API Features collection; pages by `offset`, each linking the next."""

    def __init__(self, features=None, size=2, matched="count", pages=None, next_of=None, exception_at=None,
                 robots=None, chunk=1 << 20, items_link=True):
        self.features = copy.deepcopy(features if features is not None else FEATURES)
        self.size, self.matched, self.pages, self.next_of = size, matched, pages, next_of or {}
        self.exception_at, self.robots, self.chunk, self.items_link = exception_at, robots, chunk, items_link
        self.calls: list[str] = []

    def url(self, offset: int) -> str:
        return f"{OGC}/items?f=json&limit={self.size}&offset={offset}"

    def __call__(self, url):
        self.calls.append(url)
        if (b := _common(url, self.robots)) is not None:
            return b
        u = urlsplit(url)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        body = lambda d: Body(url, json.dumps(d).encode(), chunk=self.chunk, content_type="application/geo+json")
        if u.path == urlsplit(OGC).path:
            links = [{"rel": "self", "type": "application/json", "href": f"{OGC}?f=json"},
                     {"rel": "items", "type": "text/html", "href": f"{OGC}/items?f=html"}]
            if self.items_link:
                links.append({"rel": "items", "type": "application/geo+json", "href": f"{OGC}/items?f=json"})
            return body({"id": "wells", "title": "Wells", "links": links})
        assert u.path == urlsplit(OGC).path + "/items", url
        assert q["f"] == "json", url
        offset = int(q.get("offset", 0))
        if offset == self.exception_at:
            return body({"code": "InvalidParameterValue", "description": "offset beyond the collection"})
        if self.pages is not None:
            feats = self.pages[offset]
        else:
            feats = self.features[offset:offset + self.size]
        page = {"type": "FeatureCollection", "features": copy.deepcopy(feats), "numberReturned": len(feats),
                "timeStamp": f"2026-10-24T03:1{offset}:00Z",
                "links": [{"rel": "self", "type": "application/geo+json", "href": url},
                          {"rel": "alternate", "type": "text/html", "href": url + "&f=html"}]}
        if self.matched == "count":
            page["numberMatched"] = len(self.features)
        elif self.matched is not None:
            page["numberMatched"] = self.matched
        nxt = self.next_of.get(offset, offset + self.size if offset + self.size < len(self.features) else None)
        if nxt is not None:
            page["links"].append({"rel": "next", "type": "application/geo+json", "href": self.url(nxt)})
        return body(page)


def record(manifest):
    rec = copy.deepcopy(load_record(paths.RECORDS_DIR / "terranubis" / "f3-demo-2020.yaml"))
    rec["origin"]["manifest_url"] = manifest
    rec["licence"]["url"] = LICENCE
    return rec


def fetch_ok(url):
    return Fetched(200, url, "text/html", 5, b"<html></html>")


WFS_SAMPLE = {"sort": "id"}


def run(server, manifest=WFS_MANIFEST, sample=None, budget=None):
    sample = sample if sample is not None else (WFS_SAMPLE if manifest == WFS_MANIFEST else ["*"])
    v = verify_record(record(manifest), fetch_ok, None, opener=server, sample=sample, budget=budget)
    V6.validate(v)
    return v


def files_check(v):
    return next(c for c in v["checks"] if c["name"] == "files-checksummed")


def get_of(server):
    return lambda u: b"".join(server(u))


def wfs_out(server, sort="id") -> layers.Outcome:
    return layers.export_wfs(WFS, "ns:wells", sort, WFS_MANIFEST, get_of(server))


def ogc_out(server) -> layers.Outcome:
    return layers.export_ogcapi(OGC, "f=json", get_of(server))


# --- recognition (design 3) ------------------------------------------------------------------------

@pytest.mark.parametrize("url,want", [
    (WFS_MANIFEST, OgcService("wfs", WFS, "ns:wells")),
    ("https://h.test/ows?SERVICE=wfs&REQUEST=GetFeature&TYPENAME=a:b", OgcService("wfs", "https://h.test/ows", "a:b")),
    (OGC, OgcService("ogcapi", OGC, "")),
    (OGC + "/items?f=json&limit=10&offset=20", OgcService("ogcapi", OGC, "f=json")),
    ("https://api.sgu.se/oppnadata/borrhal/ogc/features/v1/collections/borrhal/items?f=application%2Fgeo%2Bjson",
     OgcService("ogcapi", "https://api.sgu.se/oppnadata/borrhal/ogc/features/v1/collections/borrhal",
                "f=application%2Fgeo%2Bjson")),
    ("https://data.geo.admin.ch/api/stac/v1/collections/ch.x/items/x", None),   # a STAC item, not a collection
    ("https://h.test/geoserver/wms?service=WMS&layers=a:b", None),
    ("https://h.test/geoserver/wfs?service=WFS&request=GetCapabilities", None),   # no feature type named
    ("https://h.test/data/wells.zip", None),
])
def test_ogc_service_is_recognised_from_the_url(url, want):
    assert ogc_service(url) == want


# --- canonical bytes (design 6) ---------------------------------------------------------------------

def test_canonical_bytes_are_exact_for_both_protocols():
    w, o = wfs_out(Wfs()), ogc_out(Ogc())
    assert (w.status, o.status) == ("complete", "complete"), (w, o)
    assert w.body == WFS_CANONICAL and o.body == OGC_CANONICAL
    assert w.entry == {"layer": WFS_LAYER, "format": "wfs-geojson", "features": 5, "count": 5,
                       "completeness": "complete", "bytes": len(WFS_CANONICAL),
                       "sha256": hashlib.sha256(WFS_CANONICAL).hexdigest()}
    assert o.entry == {"layer": OGC, "format": "ogcapi-geojson", "features": 5, "count": 5,
                       "completeness": "complete", "bytes": len(OGC_CANONICAL),
                       "sha256": hashlib.sha256(OGC_CANONICAL).hexdigest()}


def _shuffled():
    rng = random.Random(38)
    feats = copy.deepcopy(FEATURES)
    rng.shuffle(feats)
    for f in feats:   # keys reordered within each feature, as another node might serve them
        f["properties"] = dict(reversed(list(f["properties"].items())))
        for k in list(f):
            f[k] = f.pop(k)
    assert [f["id"] for f in feats] != sorted(f["id"] for f in feats)
    return feats


def test_shuffled_pages_and_features_within_pages_give_identical_bytes():
    feats = _shuffled()
    w = wfs_out(Wfs(pages={0: feats[0:2], 2: feats[2:4], 4: feats[4:5]}))
    o = ogc_out(Ogc(pages={0: feats[0:2], 2: feats[2:4], 4: feats[4:5]}))
    assert (w.body, o.body) == (WFS_CANONICAL, OGC_CANONICAL)


def test_numeric_ids_sort_as_numbers():
    feats = copy.deepcopy(FEATURES)
    for f, i in zip(feats, (10.0, 9.0, 2.0, 1.0, 100.0), strict=True):
        f["id"] = i
    out = ogc_out(Ogc(features=feats))
    assert [f["id"] for f in json.loads(out.body)["features"]] == [1.0, 2.0, 9.0, 10.0, 100.0]


@pytest.mark.parametrize("reader", [wfs_out, ogc_out], ids=["wfs", "ogcapi"])
def test_an_attribute_a_geometry_and_a_coordinate_each_change_the_digest(reader):
    server = Wfs if reader is wfs_out else Ogc
    digest = lambda feats: reader(server(features=feats)).entry["sha256"]
    attr, geom, coord = (copy.deepcopy(FEATURES) for _ in range(3))
    attr[2]["properties"]["depth_m"] = 2210.26
    geom[0]["geometry"] = None
    coord[4]["geometry"]["coordinates"][0] = 177100.51
    assert len({digest(FEATURES), digest(attr), digest(geom), digest(coord)}) == 4


# --- the check, end to end through verify_record with an injected opener ------------------------------

@pytest.mark.parametrize("server,manifest,fmt", [(Wfs, WFS_MANIFEST, "wfs-geojson"), (Ogc, OGC, "ogcapi-geojson")],
                         ids=["wfs", "ogcapi"])
def test_a_complete_layer_passes_l2_as_evidence_never_a_file_or_asset(server, manifest, fmt):
    v = run(server(), manifest)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("pass", "L2"), c
    assert c["detail"].startswith(f"whole layer checked (5 features, {fmt}), not a downloadable file; stability unknown")
    (x,) = v["layer_exports"]
    assert (x["format"], x["completeness"], x["count"]) == (fmt, "complete", 5)
    assert "files" not in v and "partial_exports" not in v
    assert stac._assets(v) == {}


def test_the_wfs_reader_takes_the_manifest_over_file_true_and_an_attachment_header():
    server = Wfs(attachment=True)
    v = run(server, sample={"file": True, "sort": "id", "sample": ["*"]})
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("pass", "L2"), c
    assert "whole layer checked (5 features, wfs-geojson)" in c["detail"]
    assert "the manifest_url is the file itself" not in c["detail"] and "files" not in v
    assert WFS_MANIFEST not in server.calls   # never opened as a file: the reader asks for its own pages
    assert [urlsplit(u).path for u in server.calls][:2] == ["/robots.txt", "/geoserver/wfs"]


def test_the_ogc_reader_takes_the_manifest_over_file_true():
    v = run(Ogc(), OGC, sample={"file": True})
    assert files_check(v)["outcome"] == "pass" and "files" not in v and v["layer_exports"]


def _fails(server, manifest, reason):
    v = run(server, manifest)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("fail", "L1"), c
    assert reason in c["detail"], c["detail"]
    assert not {"layer_exports", "files", "partial_exports"} & set(v)


def test_hits_mismatch_fails_with_unique_ids_and_valid_pages():
    # hits 4, page size 3: a full first page and a last page of 2: ids unique, pages valid, only the count disagrees
    _fails(Wfs(size=3, hits=4), WFS_MANIFEST, "the feature type ns:wells counts 4 features, the pages served 5")


def test_number_matched_mismatch_fails_with_unique_ids_and_valid_pages():
    _fails(Ogc(matched=6), OGC, f"the collection {OGC} counts 6 features, the pages served 5")


def test_a_duplicate_id_fails():
    _fails(Wfs(pages={0: FEATURES[0:2], 2: [FEATURES[2], FEATURES[1]], 4: FEATURES[4:5]}), WFS_MANIFEST,
           "the feature type ns:wells: feature id 'wells.2' served twice")
    _fails(Ogc(pages={0: FEATURES[0:2], 2: [FEATURES[2], FEATURES[1]], 4: FEATURES[4:5]}), OGC,
           f"the collection {OGC}: feature id 'wells.2' served twice")


def test_a_paging_loop_fails():
    # page 3's next link is page 2 again: refused before it is fetched a second time
    _fails(Ogc(next_of={4: 2}, pages={0: FEATURES[0:2], 2: FEATURES[2:4], 4: FEATURES[4:5]}), OGC,
           "paging loop: the next link https://fixture.test/ogc/collections/wells/items?f=json&limit=2&offset=2 "
           "was served before")


def test_an_empty_page_that_links_a_next_page_fails():
    _fails(Ogc(pages={0: FEATURES[0:2], 2: [], 4: FEATURES[2:5]}, next_of={2: 4, 4: None}), OGC,
           "served no features and links a next page")


def test_a_short_wfs_page_before_the_end_fails():
    _fails(Wfs(pages={0: FEATURES[0:1], 2: FEATURES[1:3], 4: FEATURES[3:5]}), WFS_MANIFEST,
           "page at startIndex 0 served 1 features, the page size is 2")


def test_a_feature_without_an_id_fails():
    feats = copy.deepcopy(FEATURES)
    del feats[3]["id"]
    _fails(Ogc(features=feats), OGC, "a feature has no id")


def test_a_crs_differing_between_pages_fails():
    other = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}}
    _fails(Wfs(crs_at={2: other}), WFS_MANIFEST, "page at startIndex 2 states crs")


def test_exception_responses_fail_with_the_publishers_message():
    _fails(Wfs(exception_at=2), WFS_MANIFEST, "page at startIndex 2 answered an exception: InvalidParameterValue "
                                              "Illegal property name: id for feature type ns:wells")
    _fails(Ogc(exception_at=2), OGC, "answered an exception: InvalidParameterValue offset beyond the collection")
    _fails(Wfs(http_error_at=2), WFS_MANIFEST, "page error: HTTP 500 from")


def test_a_missing_count_is_unconfirmed_and_earns_no_l2():
    v = run(Ogc(matched=None), OGC)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1"), c
    assert c["detail"] == ("whole layer read (5 features, ogcapi-geojson) but its count is unconfirmed "
                           "(the server states no numberMatched): no L2")
    (x,) = v["layer_exports"]
    assert (x["count"], x["completeness"], x["features"]) == (None, "unconfirmed", 5)
    assert "files" not in v and stac._assets(v) == {}


def test_hits_unknown_is_unconfirmed_too():
    out = wfs_out(Wfs(hits="unknown"))
    assert (out.status, out.entry["count"], out.entry["completeness"]) == ("unconfirmed", None, "unconfirmed")
    assert out.body == WFS_CANONICAL


def test_above_the_cap_a_wfs_layer_is_partial_with_the_manifests_export_as_evidence():
    server = Wfs(hits=50_001)
    v = run(server)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1"), c
    assert c["detail"] == ("not read whole: the feature type counts 50001 features, above the 50000 a whole layer "
                           "is read to; the one-page export kept as a partial export, not a hashed file")
    (p,) = v["partial_exports"]
    body = b"".join(Wfs()(WFS_MANIFEST))
    assert p == {"path": "GetFeature export (at most 1000 of 50001 features)", "url": WFS_MANIFEST,
                 "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "partial": True}
    assert "files" not in v and "layer_exports" not in v and stac._assets(v) == {}
    assert not [u for u in server.calls if "startIndex" in u]


def test_above_the_cap_an_ogc_collection_keeps_its_first_page_as_evidence():
    v = run(Ogc(matched=50_001), OGC)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1"), c
    assert c["detail"].startswith("not read whole: the collection counts 50001 features, above the 50000")
    (p,) = v["partial_exports"]
    assert (p["path"], p["url"]) == ("first page (ogcapi-geojson, 2 of 50001 features)", f"{OGC}/items?f=json&limit=1000")
    assert "files" not in v and "layer_exports" not in v and stac._assets(v) == {}


@pytest.mark.parametrize("server,sort,reason", [
    (Wfs(sorting="FALSE"), "id", "unsortable: the capabilities do not state ImplementsSorting TRUE"),
    (Wfs(), None, "unsortable: no sort property for ns:wells in verifier/samples.yaml"),
    (Wfs(paging="FALSE"), "id", "unpageable: the capabilities do not state ImplementsResultPaging TRUE"),
    (Wfs(version="1.1.0"), "id", "WFS 1.1.0: only 2.0.0 is read whole (deferred)"),
    (Wfs(json_format=None), "id", "GetFeature offers no GeoJSON output (GML only: deferred)"),
], ids=["sorting-false", "no-sort-property", "paging-false", "wfs-1.1", "gml-only"])
def test_a_wfs_that_cannot_be_read_whole_is_partial_and_not_hashed(server, sort, reason):
    v = run(server, sample={"sort": sort} if sort else ["*"])
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1"), c
    assert c["detail"] == f"not read whole: {reason}"
    assert not {"layer_exports", "files", "partial_exports"} & set(v)
    assert not [u for u in server.calls if "startIndex" in u]


def test_robots_refusal_on_a_later_page_declines_the_layer():
    server = Ogc(robots="User-agent: *\nDisallow: /ogc/collections/wells/items?f=json&limit=2&offset=4\n")
    v = run(server, OGC)
    c = files_check(v)
    assert (c["outcome"], v["level"]) == ("skip", "L1"), c
    assert c["detail"] == (f"robots.txt disallows the layer query {OGC}/items?f=json&limit=2&offset=4")
    assert [u for u in server.calls if "offset=2" in u] and not [u for u in server.calls if "offset=4" in u]
    assert not {"layer_exports", "files"} & set(v)


def test_a_page_over_the_budget_share_is_abandoned_and_counted():
    server = Wfs(chunk=64)
    first = [WFS + "?service=WFS&version=2.0.0&request=GetCapabilities",
             WFS + "?" + urlencode({"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                                    "typeNames": "ns:wells", "resultType": "hits"})]
    size = lambda u: len(b"".join(Wfs()(u)))
    page = len(json.dumps(server.page(0)).encode())
    run_budget = ByteBudget(limit=sum(size(u) for u in first) + page + page // 2)
    c, files, members = check_files(record(WFS_MANIFEST), WFS_SAMPLE, server, run_budget.share(512 * 1024**2))
    assert c["outcome"] == "skip" and "whole layer cut at the budget" in c["detail"], c
    assert "startIndex=2&" in c["detail"] and "abandoned mid-stream after" in c["detail"], c["detail"]
    assert run_budget.used == run_budget.limit   # the abandoned read counts: the run has no room left
    assert not files and not members


def test_every_layer_request_is_paced_per_host():
    server = Ogc()
    sleeps: list[float] = []
    fetch, opener = paced(fetch_ok, server, Pacer(clock=lambda: 0.0, sleep=sleeps.append))   # time stands still
    verify_record(record(OGC), fetch, None, opener=opener, sample=["*"])
    assert len([u for u in server.calls if u.startswith(OGC)]) == 4   # description, three pages
    assert len(sleeps) == len(server.calls) - 1 and set(sleeps) == {2.0}


def test_without_an_items_link_the_collections_items_path_is_paged():
    server = Ogc(items_link=False)
    assert ogc_out(server).status == "complete"
    assert f"{OGC}/items?f=json&limit=1000" in server.calls
