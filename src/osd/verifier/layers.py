"""Whole layers (E35): an ArcGIS layer read in full as evidence for files-checksummed, never a file.

The layer is paged by object id with E29's shared paging (osd.outlines.extractors: the page query
and the page checks), asking for every field in native Esri JSON (`outFields=*`, `f=json`, no
`outSR`), so nothing is reprojected. The expected id set is read independently (`returnIdsOnly`) and
the assembled ids must equal it exactly; `editingInfo.lastEditDate` is read before and after paging.

Canonical bytes (`esri-json`): one JSON object with the features sorted by object id, every key
sorted, no whitespace; attributes and coordinates are the values the server returned (a number is
written back in the shortest form that reads as the same number: no rounding). Page metadata
(`fields`, aliases, `exceededTransferLimit`) is left out; every page must state the same geometry
type and spatial reference, which the bytes carry.

`export_layer` is pure over an injected `get(url) -> bytes`: the verifier's get obeys robots.txt,
goes through the paced opener and counts every byte against the record's share before decoding.

E38 adds two readers over the same get, each answering an `Outcome` (complete, unconfirmed, partial,
failed, declined): `export_wfs` (WFS 2.0.0, startIndex and sortBy, GeoJSON only, the count from
resultType=hits) and `export_ogcapi` (OGC API Features, the next links only, the count from
numberMatched). Their canonical bytes (`wfs-geojson`, `ogcapi-geojson`) are a GeoJSON
FeatureCollection with the features sorted by id, as `geojson_canonical` writes it.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree

from ..outlines.extractors import (
    ARCGIS_MAX_FEATURES,
    _arcgis_error,
    _json,
    arcgis_assemble,
    arcgis_count,
    arcgis_layer,
    arcgis_page_query,
    page_offsets,
)
from ..outlines.geometry import Refused

FORMAT = "esri-json"


class Incomplete(Exception):
    """The layer was not read in full. `outcome` is the check's: "fail" for a guard the server's
    answers broke, "skip" for what this run declined (robots.txt, the budget)."""

    def __init__(self, reason: str, outcome: str = "fail"):
        super().__init__(reason)
        self.reason, self.outcome = reason, outcome


class NotWhole(Exception):
    """The layer is not read whole, by design: it counts more features than the E29 cap, or its
    description does not let it be paged (no supportsPagination, object id field or maxRecordCount).
    The verifier falls back to the one-page export, a partial export when the server says so."""


def _q(layer: str, params: dict) -> str:
    return f"{layer}/query?{urlencode(params)}"


def _edit_date(desc: dict) -> int | None:
    v = (desc.get("editingInfo") or {}).get("lastEditDate")
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _description(b: bytes) -> dict:
    d = _json(b, "the layer description")
    _arcgis_error(d, "the layer description")
    return d


def canonical(features: list[dict], oid: str, geometry_type, spatial_reference) -> bytes:
    """The esri-json bytes of a whole layer: features sorted by object id, keys sorted, no whitespace."""
    doc = {"objectIdFieldName": oid, "geometryType": geometry_type, "spatialReference": spatial_reference,
           "features": sorted(features, key=lambda f: f["attributes"][oid])}
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def export_layer(layer: str, get: Callable[[str], bytes]) -> tuple[dict, bytes]:
    """(the layer_exports entry, the canonical bytes). Raises NotWhole above the feature cap or for a
    layer that cannot be paged, and
    Incomplete for every guard that fails."""
    layer = layer.rstrip("/")
    try:
        first = get(f"{layer}?f=json")
        before = _edit_date(_description(first))
        try:
            oid, size = arcgis_layer(first)
        except Refused as e:
            raise NotWhole(str(e)) from None
        counted = get(_q(layer, {"where": "1=1", "returnCountOnly": "true", "f": "json"}))
        n = _json(counted, "the count")
        if isinstance(n, dict) and isinstance(n.get("count"), int) and n["count"] > ARCGIS_MAX_FEATURES:
            raise NotWhole(f"the layer counts {n['count']} features, above the {ARCGIS_MAX_FEATURES} a whole "
                           f"layer is read to")
        count = arcgis_count(counted)
        listed = _json(get(_q(layer, {"where": "1=1", "returnIdsOnly": "true", "f": "json"})), "the id list")
        _arcgis_error(listed, "the id list")
        ids = listed.get("objectIds")
        if not isinstance(ids, list):
            raise Refused("the id list (returnIdsOnly) states no objectIds")
        pages = {off: get(_q(layer, arcgis_page_query(oid, size, off, "*")))
                 for off in page_offsets(count, size)}
        stated: dict[str, object] = {}

        def same_frame(page: dict, what: str) -> None:
            for k in ("geometryType", "spatialReference"):
                stated.setdefault(k, page.get(k))
                if page.get(k) != stated[k]:
                    raise Refused(f"{what} states {k} {page.get(k)!r}, the first page {stated[k]!r}")

        features = arcgis_assemble(pages, oid, size, count, "the layer", same_frame)
        got = {f["attributes"][oid] for f in features}
        if got != set(ids) or len(ids) != len(set(ids)):
            extra, missing = sorted(got - set(ids), key=str), sorted(set(ids) - got, key=str)
            raise Refused(f"the pages' object ids differ from returnIdsOnly ({len(ids)} ids listed): "
                          f"{len(extra)} not listed (e.g. {extra[:1]}), {len(missing)} not served (e.g. {missing[:1]})")
        after = _edit_date(_description(get(f"{layer}?f=json")))
    except Refused as e:
        raise Incomplete(str(e)) from None
    body = canonical(features, oid, stated.get("geometryType"), stated.get("spatialReference"))
    entry = {"layer": layer, "format": FORMAT, "features": len(features), "count": count, "bytes": len(body),
             "sha256": hashlib.sha256(body).hexdigest(), "edit_date_before": before, "edit_date_after": after}
    return entry, body


# --- E38: WFS 2.0.0 feature types and OGC API Features collections ----------------------------------
# Both are read to GeoJSON and answer an Outcome; the expected count is the protocol's own (WFS
# resultType=hits, OGC API numberMatched), never a page's truncation flag or numberReturned. Neither
# protocol states a revision for one feature type or collection, so stability is always unknown.

WFS_FORMAT, OGC_FORMAT = "wfs-geojson", "ogcapi-geojson"
WFS_PAGE, WFS_PAGE_UNSTATED, OGC_PAGE = 5000, 1000, 1000
WFS_JSON = ("application/json", "application/geo+json", "json")   # outputFormat, first offered wins (DOV offers geo+json and refuses it, 24 Oct)
GEOJSON_TYPES = ("application/geo+json", "application/json")
UNKNOWN_REVISION = {WFS_FORMAT: "stability unknown (WFS 2.0 states no revision for a feature type)",
                    OGC_FORMAT: "stability unknown (OGC API Features states no revision for a collection)"}
XML_EXCEPTION = re.compile(r"<(?:\w+:)?ExceptionText>\s*(.*?)\s*</", re.DOTALL)
XML_CODE = re.compile(r'exceptionCode="([^"]*)"')


class Partial(Exception):
    """Not read whole by design (the cap, a service that cannot be paged or sorted, a deferred version
    or format); `evidence` is the one-page export kept as a partial export, at the cap only."""

    def __init__(self, reason: str, evidence: dict | None = None):
        super().__init__(reason)
        self.reason, self.evidence = reason, evidence


@dataclass(frozen=True)
class Outcome:
    """What a WFS or OGC API reader established. complete: the pages assembled exactly the expected
    count of distinct ids (the only status that earns L2); unconfirmed: read to the end but the server
    states no count; partial: not read whole, with the reason; failed: a guard the server's answers
    broke; declined: robots.txt or the budget stopped this run."""
    status: str
    reason: str = ""
    entry: dict | None = None
    body: bytes = b""
    evidence: dict | None = None


def _fid(f) -> tuple:
    i = f.get("id") if isinstance(f, dict) else None
    if isinstance(i, bool) or not isinstance(i, (str, int, float)):
        raise Refused(f"a feature has no id ({json.dumps(f)[:120]})")
    return isinstance(i, str), i   # strings and numbers never compare


def geojson_canonical(features: list[dict], crs=None) -> bytes:
    """The bytes of a whole WFS or OGC API layer: features sorted by id, keys sorted, no whitespace;
    the pages' crs when they state one; page members (counts, links, timestamps, bbox) left out."""
    doc = {"type": "FeatureCollection", "features": sorted(features, key=_fid)}
    if crs is not None:
        doc["crs"] = crs
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _doc(b: bytes, where: str):
    """A JSON answer, or Refused naming the publisher's exception (OWS XML or OGC API JSON)."""
    text = b.decode("utf-8", "replace").lstrip("﻿").lstrip()
    if text.startswith("<"):
        if "ExceptionReport" in text[:2000]:
            code, said = XML_CODE.search(text), XML_EXCEPTION.search(text)
            raise Refused(f"{where} answered an exception: {code.group(1) if code else ''} "
                          f"{html.unescape(said.group(1)) if said else ''}".strip()[:300])
        raise Refused(f"{where} is XML, not GeoJSON: {b[:80]!r}")
    try:
        d = json.loads(text)
    except ValueError:
        raise Refused(f"{where} is not JSON: {b[:80]!r}") from None
    if isinstance(d, dict) and "code" in d and "description" in d and "features" not in d:
        raise Refused(f"{where} answered an exception: {d['code']} {d['description']}"[:300])
    return d


class _Pages:
    """Features assembled page by page: every feature with an id, no id twice, one crs."""

    def __init__(self, what: str):
        self.what, self.features, self.seen, self.crs, self.pages = what, [], set(), None, 0

    def add(self, page, where: str) -> int:
        feats = page.get("features") if isinstance(page, dict) else None
        if not (isinstance(page, dict) and page.get("type") == "FeatureCollection" and isinstance(feats, list)):
            raise Refused(f"{where} is not a GeoJSON FeatureCollection")
        if self.pages and page.get("crs") != self.crs:
            raise Refused(f"{where} states crs {page.get('crs')!r}, the first page {self.crs!r}")
        self.crs, self.pages = page.get("crs"), self.pages + 1
        for f in feats:
            k = _fid(f)
            if k in self.seen:
                raise Refused(f"{self.what}: feature id {f['id']!r} served twice")
            self.seen.add(k)
            self.features.append(f)
        return len(feats)


def _outcome(fmt: str, layer: str, pages: _Pages, count: int | None) -> Outcome:
    if count is not None and len(pages.features) != count:
        raise Refused(f"{pages.what} counts {count} features, the pages served {len(pages.features)}")
    body = geojson_canonical(pages.features, pages.crs)
    entry = {"layer": layer, "format": fmt, "features": len(pages.features), "count": count,
             "completeness": "complete" if count is not None else "unconfirmed", "bytes": len(body),
             "sha256": hashlib.sha256(body).hexdigest()}
    if count is None:
        return Outcome("unconfirmed", "the server states no numberMatched", entry, body)
    return Outcome("complete", UNKNOWN_REVISION[fmt], entry, body)


def _evidence(url: str, b: bytes, name: str) -> dict:
    return {"path": name, "url": url, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "partial": True}


def _read(reader: Callable[[], Outcome]) -> Outcome:
    try:
        return reader()
    except Partial as p:
        return Outcome("partial", p.reason, evidence=p.evidence)
    except Refused as e:
        return Outcome("failed", str(e))
    except Incomplete as i:
        return Outcome("failed" if i.outcome == "fail" else "declined", i.reason)


def _with(url: str, **params) -> str:
    """`url` with these query parameters set (any case of the same name replaced)."""
    u = urlsplit(url)
    names = {k.lower() for k in params}
    q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if k.lower() not in names]
    return urlunsplit(u._replace(query=urlencode(q + [(k, str(v)) for k, v in params.items()])))


def _link(doc: dict, rel: str, base: str) -> str | None:
    """The href of `rel` in a document's links, GeoJSON first, then JSON, then an untyped one."""
    links = [x for x in doc.get("links") or [] if isinstance(x, dict) and x.get("rel") == rel
             and isinstance(x.get("href"), str)]
    for want in (*GEOJSON_TYPES, None):
        for x in links:
            if (x.get("type") or None) == want or (want and str(x.get("type", "")).startswith(want)):
                return urljoin(base, x["href"])
    return None


# --- OGC API Features ----------------------------------------------------------------------------

def export_ogcapi(collection: str, query: str, get: Callable[[str], bytes]) -> Outcome:
    """A collection paged by its `next` links only (design 4): the expected count is the first page's
    numberMatched (none: unconfirmed); a next link served before is a paging loop."""
    def read() -> Outcome:
        what = f"the collection {collection}"
        desc = _doc(get(f"{collection}?{query}" if query else collection), "the collection description")
        if not isinstance(desc, dict):
            raise Refused("the collection description is not a JSON object")
        items = _link(desc, "items", collection) or (f"{collection}/items?{query}" if query else f"{collection}/items")
        url, seen, count, pages = _with(items, limit=OGC_PAGE), set(), None, _Pages(what)
        while url:
            if url in seen:
                raise Refused(f"paging loop: the next link {url} was served before")
            seen.add(url)
            b = get(url)
            where = f"page {pages.pages + 1} ({url})"
            page = _doc(b, where)
            if not pages.pages and isinstance(page, dict):
                n = page.get("numberMatched")
                count = n if isinstance(n, int) and not isinstance(n, bool) and n >= 0 else None
                if count is not None and count > ARCGIS_MAX_FEATURES:
                    raise Partial(f"the collection counts {count} features, above the {ARCGIS_MAX_FEATURES} a whole "
                                  f"layer is read to", _evidence(url, b, f"first page ({OGC_FORMAT}, "
                                                                 f"{len(page.get('features') or [])} of {count} features)"))
            got = pages.add(page, where)
            url = _link(page, "next", url)
            if url and not got:
                raise Refused(f"{where} served no features and links a next page")
            if count is None and len(pages.features) > ARCGIS_MAX_FEATURES:
                raise Partial(f"the collection states no numberMatched and serves more than {ARCGIS_MAX_FEATURES} features")
        return _outcome(OGC_FORMAT, collection, pages, count)
    return _read(read)


# --- WFS 2.0.0 -----------------------------------------------------------------------------------

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml(b: bytes, where: str) -> ElementTree.Element:
    text = b.decode("utf-8", "replace").lstrip("﻿").lstrip()
    if "ExceptionReport" in text[:2000]:
        _doc(b, where)   # raises with the publisher's message
    try:
        return ElementTree.fromstring(b)
    except ElementTree.ParseError:
        raise Refused(f"{where} is not XML: {b[:80]!r}") from None


@dataclass(frozen=True)
class WfsCapabilities:
    version: str
    types: frozenset
    constraints: dict
    formats: tuple


def wfs_capabilities(b: bytes) -> WfsCapabilities:
    root = _xml(b, "the capabilities")
    if _local(root.tag) != "WFS_Capabilities":
        raise Refused(f"the capabilities are {_local(root.tag)}, not WFS_Capabilities")
    types, constraints, formats = set(), {}, []
    for el in root.iter():
        name = _local(el.tag)
        if name == "FeatureType":
            types |= {(c.text or "").strip() for c in el if _local(c.tag) == "Name"}
        elif name == "Constraint" and el.get("name"):
            value = next((d.text for d in el.iter() if _local(d.tag) == "DefaultValue"), None)
            constraints[el.get("name")] = (value or "").strip()
        elif name == "Operation" and el.get("name") == "GetFeature":
            for p in el.iter():
                if _local(p.tag) == "Parameter" and p.get("name") == "outputFormat":
                    formats += [(v.text or "").strip() for v in p.iter() if _local(v.tag) == "Value"]
    return WfsCapabilities(root.get("version") or "", frozenset(types), constraints, tuple(formats))


def wfs_hits(b: bytes) -> int | None:
    """numberMatched of a resultType=hits answer; None when the server says "unknown"."""
    root = _xml(b, "the hits count")
    n = root.get("numberMatched")
    if n is None:
        raise Refused(f"the hits count ({_local(root.tag)}) states no numberMatched")
    if n == "unknown":
        return None
    if not n.isdigit():
        raise Refused(f"the hits count states numberMatched {n!r}")
    return int(n)


def export_wfs(base: str, type_name: str, sort: str | None, manifest: str, get: Callable[[str], bytes]) -> Outcome:
    """A WFS 2.0.0 feature type paged by startIndex and count, sorted by the configured property,
    GeoJSON only (design 5); the expected count from resultType=hits. Above the cap, the manifest's
    own count-bounded GetFeature is kept as the partial export."""
    def kvp(**extra) -> str:
        return f"{base}?" + urlencode({"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                                       "typeNames": type_name, **extra})

    layer = f"{base}?" + urlencode({"service": "WFS", "typeNames": type_name})

    def read() -> Outcome:
        caps = wfs_capabilities(get(f"{base}?service=WFS&version=2.0.0&request=GetCapabilities"))
        if caps.version != "2.0.0":
            raise Partial(f"WFS {caps.version or 'of no stated version'}: only 2.0.0 is read whole (deferred)")
        if "," in type_name:
            raise Partial(f"several typeNames ({type_name}): one feature type is one layer")
        if type_name not in caps.types:
            raise Refused(f"the capabilities do not list the feature type {type_name}")
        fmt = next((f for want in WFS_JSON for f in caps.formats if f.split(";")[0].strip().lower() == want), None)
        if fmt is None:
            raise Partial("GetFeature offers no GeoJSON output (GML only: deferred)")
        if caps.constraints.get("ImplementsResultPaging", "").upper() != "TRUE":
            raise Partial("unpageable: the capabilities do not state ImplementsResultPaging TRUE")
        if caps.constraints.get("ImplementsSorting", "").upper() != "TRUE":
            raise Partial("unsortable: the capabilities do not state ImplementsSorting TRUE")
        count = wfs_hits(get(kvp(resultType="hits")))
        if count is not None and count > ARCGIS_MAX_FEATURES:
            reason = f"the feature type counts {count} features, above the {ARCGIS_MAX_FEATURES} a whole layer is read to"
            stated = {k.lower(): v for k, v in parse_qsl(urlsplit(manifest).query)}.get("count")
            if stated:
                b = get(manifest)
                raise Partial(reason, _evidence(manifest, b, f"GetFeature export (at most {stated} of {count} features)"))
            raise Partial(reason)
        if not sort:
            raise Partial(f"unsortable: no sort property for {type_name} in verifier/samples.yaml")
        default = caps.constraints.get("CountDefault", "")
        size = min(int(default), WFS_PAGE) if default.isdigit() and int(default) > 0 else WFS_PAGE_UNSTATED
        pages, start = _Pages(f"the feature type {type_name}"), 0
        while count is None or start < count:
            url = kvp(count=size, startIndex=start, sortBy=f"{sort} ASC", outputFormat=fmt)
            where = f"page at startIndex {start}"
            got = pages.add(_doc(get(url), where), where)
            last = got < size if count is None else start + size >= count
            if not last and got != size:
                raise Refused(f"{where} served {got} features, the page size is {size}")
            if last:
                break
            if count is None and len(pages.features) > ARCGIS_MAX_FEATURES:
                raise Partial(f"hits states numberMatched unknown and the pages serve more than {ARCGIS_MAX_FEATURES} features")
            start += size
        return _outcome(WFS_FORMAT, layer, pages, count)
    return _read(read)
