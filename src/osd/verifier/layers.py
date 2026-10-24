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
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from urllib.parse import urlencode

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
