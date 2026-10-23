"""Extractors: pure functions from an input's stored parts to WGS84 features.

Each takes (record input, input rule, parts) where parts is the ordered list of (name, bytes)
the fetch stored, and returns features carrying geometry plus kind, name and the publisher's
identifiers, and the dates a register states for it when the rule names period_fields (E18).
derive() adds the identity every derived feature carries.
"""

from __future__ import annotations

import csv
import html
import io
import itertools
import json
import math
import re
import struct
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .codecs import blosc_decode
from .geometry import Refused, closed_ring, convex_hull, map_positions, to_wgs84

GEOMETRY_TYPES = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}


def _kind(rule: dict, props: dict) -> str:
    k = rule["kind"]
    if isinstance(k, str):
        return k
    return k.get("map", {}).get(str(props.get(k["field"])), k["default"])


def _ident(rule: dict, props: dict) -> dict:
    out = {}
    for key in ("publisher_id", "uwi"):
        field = rule.get("id" if key == "publisher_id" else "uwi")
        if field and props.get(field) not in (None, ""):
            out[key] = str(props[field])
    if "publisher_id" not in out and "uwi" not in out:
        raise Refused(f"a feature has no {rule.get('id')!r} and no {rule.get('uwi')!r}: no identity")
    name = props.get(rule.get("name", ""))
    out["name"] = str(name if name not in (None, "") else out.get("publisher_id") or out["uwi"])
    return out


ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
ISO_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?")
MDY = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})(?: (\d{1,2}):(\d{2}):(\d{2}) ([AP]M))?")


def period_instant(raw: str, bound: str, form: str = "iso") -> str | None:
    """A publisher's date or timestamp as an RFC 3339 UTC instant, or None when it is not in the
    form the rule names. A date is its first second for a start and its last for an end; a
    timestamp without a zone is read as UTC. form: iso (YYYY-MM-DD, YYYY-MM-DDThh:mm:ss[.f][zone])
    or m/d/y (FactMaps GeoJSON: M/D/YYYY[ h:mm:ss AM|PM])."""
    try:
        if form == "m/d/y":
            m = MDY.fullmatch(raw)
            if not m:
                return None
            mo, d, y, h, mi, sec, ampm = m.groups()
            if h is None:
                when, is_date = datetime(int(y), int(mo), int(d)), True
            else:
                if not 1 <= int(h) <= 12:
                    return None
                hour = int(h) % 12 + (12 if ampm == "PM" else 0)
                when, is_date = datetime(int(y), int(mo), int(d), hour, int(mi), int(sec)), False
        elif ISO_DATE.fullmatch(raw):
            when, is_date = datetime.strptime(raw, "%Y-%m-%d"), True
        elif ISO_TIME.fullmatch(raw):
            when, is_date = datetime.fromisoformat(raw), False
        else:
            return None
    except ValueError:
        return None
    if is_date:
        return when.strftime("%Y-%m-%dT23:59:59Z" if bound == "end" else "%Y-%m-%dT00:00:00Z")
    if when.tzinfo is not None:
        when = when.astimezone(UTC)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _period(rule: dict, props: dict) -> dict:
    """The feature's own start and end as the service states them (osd:period_*_raw, verbatim)
    and normalised (osd:period_*), from the rule's period_fields; a value the rule lists in
    period_placeholders, or one not in its period_format, keeps its raw string only."""
    out = {}
    for bound, field in (rule.get("period_fields") or {}).items():
        raw = props.get(field)
        if raw in (None, ""):
            continue
        out[f"osd:period_{bound}_raw"] = str(raw)
        if str(raw) in [str(x) for x in rule.get("period_placeholders") or []]:
            continue
        instant = period_instant(str(raw), bound, rule.get("period_format", "iso"))
        if instant:
            out[f"osd:period_{bound}"] = instant
    return out


def _epsg(name: str) -> str | None:
    m = re.search(r"EPSG:+(\d+)$", name or "")
    return f"EPSG:{m.group(1)}" if m else None


def _keep(rule: dict, props: dict) -> bool:
    return all(str(props.get(k)) == str(v) for k, v in (rule.get("keep") or {}).items())


def _features(rec_input: dict, rule: dict, collections: list[dict]) -> list[dict]:
    f = to_wgs84(rec_input.get("crs"), rec_input.get("units"))
    out = []
    for fc in collections:
        served = _epsg(((fc.get("crs") or {}).get("properties") or {}).get("name", ""))
        if served and served != rec_input.get("crs"):
            raise Refused(f"{rec_input['name']}: the response declares {served}, the record {rec_input.get('crs')}")
        for feat in fc.get("features") or []:
            props = feat.get("properties") or {}
            if not _keep(rule, props):
                continue
            g = feat.get("geometry") or {}
            if not g.get("coordinates") and rule.get("unplaced") == "report":
                out.append({"kind": _kind(rule, props), **_ident(rule, props), **_period(rule, props),
                            "geometry": None})
                continue
            if g.get("type") not in GEOMETRY_TYPES or not g.get("coordinates"):
                raise Refused(f"{rec_input['name']}: a feature has geometry {g.get('type')!r}")
            out.append({"kind": _kind(rule, props), **_ident(rule, props), **_period(rule, props),
                        "geometry": {"type": g["type"], "coordinates": map_positions(g["coordinates"], f)}})
    return out


NAN_POSITION = re.compile(rb"\[\s*nan\s*,\s*nan\s*\]")
EMPTY_GEOMETRY = re.compile(rb'\{"type":"(\w+)",\}')


def geojson_page(b: bytes) -> dict:
    """A GeoJSON page. FactMaps writes two things that are not JSON: `[nan,nan]` for a wellbore
    without a position and `{"type":"MultiPolygon",}` for a survey without an area; both read as
    a geometry without coordinates (the rule decides: unplaced: report, or refuse)."""
    return json.loads(EMPTY_GEOMETRY.sub(rb'{"type":"\1","coordinates":null}', NAN_POSITION.sub(b"null", b)))


def register_wfs(rec_input: dict, rule: dict, parts: list[tuple[str, bytes]]) -> list[dict]:
    """GeoJSON pages of a WFS GetFeature; a stored hit count must equal the features served."""
    pages = [geojson_page(b) for n, b in parts if n.startswith("page-")]
    served = sum(len(p.get("features") or []) for p in pages)
    hits = dict(parts).get("hits")
    if hits is not None:
        m = re.search(rb'numberMatched="(\d+)"', hits)
        if m and int(m.group(1)) != served:
            raise Refused(f"{rec_input['name']}: the service counts {int(m.group(1))} features, the pages "
                          f"served {served}")
    if not served:
        raise Refused(f"{rec_input['name']}: empty response")
    return _features(rec_input, rule, pages)


# --- ArcGIS Map/Feature Server layers (E29) ------------------------------------------------------

ARCGIS_MAX_FEATURES = 50_000   # charter design 4: a layer is read in full or refused; larger ones get no input
ARCGIS_MAX_PAGES = 200


def _json(b: bytes, what: str):
    try:
        return json.loads(b)
    except ValueError:
        raise Refused(f"{what} is not JSON: {b[:120]!r}") from None


def _arcgis_error(doc, what: str) -> None:
    if not isinstance(doc, dict):
        raise Refused(f"{what} is not a JSON object")
    if "error" in doc:
        e = doc["error"] if isinstance(doc["error"], dict) else {"message": doc["error"]}
        raise Refused(f"{what} answered an error: {e.get('code', '')} {e.get('message', '')}".strip())


def arcgis_layer(b: bytes) -> tuple[str, int]:
    """(object id field, maxRecordCount) from a layer description (?f=json); refused unless the
    layer pages (supportsPagination) and names its object id field (objectIdField, else the one
    field of type esriFieldTypeOID)."""
    d = _json(b, "the layer description")
    _arcgis_error(d, "the layer description")
    pages = (d.get("advancedQueryCapabilities") or {}).get("supportsPagination", d.get("supportsPagination"))
    if pages is not True:
        raise Refused("the layer does not state supportsPagination: true; it cannot be read in full")
    oid = d.get("objectIdField")
    if not oid:
        oids = [f.get("name") for f in d.get("fields") or [] if f.get("type") == "esriFieldTypeOID"]
        oid = oids[0] if len(oids) == 1 else None
    if not oid:
        raise Refused("the layer names no object id field (objectIdField or one esriFieldTypeOID field)")
    size = d.get("maxRecordCount")
    if not isinstance(size, int) or isinstance(size, bool) or size < 1:
        raise Refused(f"the layer states no maxRecordCount ({size!r})")
    return oid, size


def arcgis_count(b: bytes) -> int:
    """The layer's feature count on the day (returnCountOnly=true), within the cap."""
    d = _json(b, "the count")
    _arcgis_error(d, "the count")
    n = d.get("count")
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise Refused(f"the count response states no count: {b[:120]!r}")
    if n == 0:
        raise Refused("empty response: the layer counts 0 features")
    if n > ARCGIS_MAX_FEATURES:
        raise Refused(f"the layer counts {n} features, above the {ARCGIS_MAX_FEATURES} an input is read in full to")
    return n


def arcgis_out_fields(rule: dict, oid: str) -> str:
    """The fields a page asks for: the object id and every field the rule reads, in that order."""
    kind = rule.get("kind")
    names = [oid, rule.get("uwi"), rule.get("name"), kind.get("field") if isinstance(kind, dict) else None,
             *(rule.get("period_fields") or {}).values(), *(rule.get("keep") or {})]
    return ",".join(dict.fromkeys(n for n in names if n))


def page_offsets(count: int, size: int) -> list[int]:
    offsets = list(range(0, count, size))
    if len(offsets) > ARCGIS_MAX_PAGES:
        raise Refused(f"{count} features at {size} per page is more than {ARCGIS_MAX_PAGES} pages")
    return offsets


def _signed_area(ring: list) -> float:
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in itertools.pairwise(ring)) / 2


def _inside(p: list, ring: list) -> bool:
    x, y, hit = p[0], p[1], False
    for a, b in itertools.pairwise(ring):
        if (a[1] > y) != (b[1] > y) and x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            hit = not hit
    return hit


def _number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(v)


def esri_geometry(g: dict | None) -> dict | None:
    """An Esri JSON geometry as a GeoJSON geometry in the same (native) coordinates; None when the
    feature has no position. Polygons: Esri writes exterior rings clockwise and holes
    counter-clockwise; each hole belongs to the exterior that contains it, and GeoJSON (RFC 7946)
    gets exteriors counter-clockwise and holes clockwise."""
    if not g:
        return None
    if "x" in g:
        if not (_number(g.get("x")) and _number(g.get("y"))):
            return None
        return {"type": "Point", "coordinates": [g["x"], g["y"]]}
    if "points" in g:
        pts = [p[:2] for p in g.get("points") or []]
        return {"type": "MultiPoint", "coordinates": pts} if pts else None
    if "paths" in g:
        paths = [[p[:2] for p in path] for path in g.get("paths") or [] if path]
        if not paths:
            return None
        return ({"type": "LineString", "coordinates": paths[0]} if len(paths) == 1
                else {"type": "MultiLineString", "coordinates": paths})
    if "rings" in g:
        rings = [[p[:2] for p in r] for r in g.get("rings") or [] if r]
        if not rings:
            return None
        exteriors = [[r[::-1]] for r in rings if _signed_area(r) < 0]   # clockwise: an exterior
        for h in (r for r in rings if _signed_area(r) >= 0):
            owner = [poly for poly in exteriors if _inside(h[0], poly[0])]
            if not owner:
                raise Refused("a polygon hole (counter-clockwise ring) lies inside no exterior ring")
            min(owner, key=lambda poly: abs(_signed_area(poly[0]))).append(h[::-1])   # the innermost exterior
        if not exteriors:
            raise Refused("a polygon has no exterior (clockwise) ring")
        return ({"type": "Polygon", "coordinates": exteriors[0]} if len(exteriors) == 1
                else {"type": "MultiPolygon", "coordinates": exteriors})
    raise Refused(f"an Esri geometry of no known type: {sorted(g)}")


def _wkids(sr: dict | None) -> set[str]:
    return {f"EPSG:{sr[k]}" for k in ("wkid", "latestWkid") if isinstance(sr, dict) and isinstance(sr.get(k), int)}


def register_arcgis(rec_input: dict, rule: dict, parts: list[tuple[str, bytes]]) -> list[dict]:
    """The pages of an ArcGIS layer query, reassembled: every page the count calls for is there,
    none short but the last, none answered an error, each states the record's CRS, the object ids
    are unique and as many as the layer counted. Positions are native and transformed from the
    record's crs as the WFS path does; the object id is the feature's key."""
    by = dict(parts)
    name = rec_input["name"]
    if "layer" not in by or "count" not in by:
        raise Refused(f"{name}: the layer description or the count was not fetched")
    oid, size = arcgis_layer(by["layer"])
    count = arcgis_count(by["count"])
    feats, seen = [], set()
    offsets = page_offsets(count, size)
    for k, off in enumerate(offsets):
        what = f"{name}: page at offset {off}"
        if f"page-{off:06d}" not in by:
            raise Refused(f"{what} is missing")
        page = _json(by[f"page-{off:06d}"], what)
        _arcgis_error(page, what)
        served = _wkids(page.get("spatialReference"))
        if rec_input.get("crs") not in served:
            raise Refused(f"{what} states spatialReference {sorted(served) or 'none'}, the record {rec_input.get('crs')}")
        got = page.get("features") or []
        if k < len(offsets) - 1 and len(got) != size:
            raise Refused(f"{what} served {len(got)} features, not the {size} a full page holds")
        for f in got:
            a = f.get("attributes") or {}
            if a.get(oid) in (None, ""):
                raise Refused(f"{what}: a feature has no {oid}")
            if a[oid] in seen:
                raise Refused(f"{name}: object id {a[oid]} served twice")
            seen.add(a[oid])
            feats.append({"properties": a, "geometry": esri_geometry(f.get("geometry"))})
    if len(seen) != count:
        raise Refused(f"{name}: the layer counts {count} features, the pages served {len(seen)}")
    rule = {**rule, "id": oid, "unplaced": "report"}   # a feature the register lists without a position
    return _features(rec_input, rule, [{"features": feats}])


def register_csv(rec_input: dict, rule: dict, parts: list[tuple[str, bytes]]) -> list[dict]:
    """A register table with one row per wellbore and its coordinate columns named in the rule."""
    text = parts[0][1].decode(rule.get("encoding", "utf-8-sig"))
    rows = list(csv.DictReader(io.StringIO(text), delimiter=rule.get("delimiter", ",")))
    if not rows:
        raise Refused(f"{rec_input['name']}: empty response")
    feats = []
    for i, row in enumerate(rows):
        try:
            x, y = float(row[rule["x"]]), float(row[rule["y"]])
        except (KeyError, TypeError, ValueError):
            raise Refused(f"{rec_input['name']}: row {i + 1} has no {rule['x']}/{rule['y']} coordinate") from None
        feats.append({"type": "Feature", "properties": row, "geometry": {"type": "Point", "coordinates": [x, y]}})
    return _features(rec_input, rule, [{"features": feats}])


class _Extent(HTMLParser):
    """The data-extent of the element inside the one marked property="locn:geometry"."""

    def __init__(self):
        super().__init__()
        self.depth, self.extent, self.title, self._in_title = 0, None, "", False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        if self.depth:
            self.depth += 1
            if self.extent is None and a.get("data-extent"):
                self.extent = a["data-extent"]
        elif a.get("property") == "locn:geometry":
            self.depth = 1

    def handle_endtag(self, tag):
        self._in_title = self._in_title and tag != "title"
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def publisher_file(rec_input: dict, rule: dict, parts: list[tuple[str, bytes]]) -> list[dict]:
    """A GeoJSON file, or the GeoJSON extent a publisher's page labels as the dataset's geometry."""
    body = parts[0][1]
    if rec_input["format"] == "geojson":
        fc = json.loads(body)
        if not fc.get("features"):
            raise Refused(f"{rec_input['name']}: empty response")
        return _features(rec_input, rule, [fc])
    p = _Extent()
    p.feed(body.decode("utf-8", "replace"))
    if not p.extent:
        raise Refused(f"{rec_input['name']}: the page carries no locn:geometry extent")
    g = json.loads(html.unescape(p.extent))
    props = {"id": urlsplit(rec_input["url"]).path.rstrip("/").rsplit("/", 1)[-1],
             "name": " ".join(p.title.split(" - ")[0].split())}
    rule = {**rule, "id": "id", "name": "name"}
    return _features(rec_input, rule, [{"features": [{"properties": props, "geometry": g}]}])


# --- trace headers: SEG-Y files and MDIO stores -------------------------------------------------

def _scaled(v: int, scalar: int) -> float:
    """SEG-Y coordinate scalar: negative divides, positive multiplies, zero is one."""
    return v / -scalar if scalar < 0 else v * scalar if scalar > 0 else float(v)


SEGY_UNITS = {1: "m", 2: "ft"}
STRUCT = {"i1": "b", "u1": "B", "i2": "h", "u2": "H", "i4": "i", "u4": "I", "i8": "q", "u8": "Q",
          "f4": "f", "f8": "d"}
SEGY_SAMPLE_BYTES = {1: 4, 2: 4, 3: 2, 5: 4, 6: 8, 8: 1, 9: 8, 10: 4, 11: 2, 12: 8, 16: 1}


def segy_positions(rule: dict, data: bytes) -> tuple[list[tuple[float, float]], str | None]:
    """Every live trace's (x, y) from the header bytes the rule names (1-based, SEG-Y rev 1)."""
    if len(data) < 3600:
        raise Refused("SEG-Y shorter than its file headers")
    samples, fmt = struct.unpack_from(">H", data, 3220)[0], struct.unpack_from(">H", data, 3224)[0]
    if fmt not in SEGY_SAMPLE_BYTES:
        raise Refused(f"SEG-Y sample format code {fmt} not known")
    if struct.unpack_from(">h", data, 3504)[0] != 0:
        raise Refused("SEG-Y extended textual headers not read by this extractor")
    units = SEGY_UNITS.get(struct.unpack_from(">H", data, 3254)[0])
    size = 240 + samples * SEGY_SAMPLE_BYTES[fmt]
    # SEG-Y rev 1 defaults: CDP X at 181, CDP Y at 185, coordinate scalar at 71
    xb, yb, sb = rule.get("x_byte", 181) - 1, rule.get("y_byte", 185) - 1, rule.get("scalar_byte", 71) - 1
    pts = []
    for off in range(3600, len(data) - 239, size):
        if struct.unpack_from(">h", data, off + 28)[0] == 2:  # trace identification code: dead
            continue
        s = struct.unpack_from(">h", data, off + sb)[0]
        pts.append((_scaled(struct.unpack_from(">i", data, off + xb)[0], s),
                    _scaled(struct.unpack_from(">i", data, off + yb)[0], s)))
    if not pts:
        raise Refused("empty response: no live trace")
    return pts, units


def _zarray(meta: dict, name: str) -> dict:
    a = meta.get(f"{name}/.zarray")
    if not a:
        raise Refused(f"MDIO store has no {name} array")
    comp = a.get("compressor") or {}
    if comp and (comp.get("id"), comp.get("cname")) != ("blosc", "lz4"):
        raise Refused(f"MDIO {name}: compressor {comp.get('id')}/{comp.get('cname')} not read")
    return a


def _chunk(parts: dict, name: str, a: dict) -> bytes:
    raw = parts.get(name)
    if raw is None:
        raise Refused(f"MDIO chunk {name} was not fetched")
    return blosc_decode(raw) if a.get("compressor") else raw


def mdio_grid_hull(parts: dict) -> list[tuple[int, int]]:
    """Hull of the live traces in (inline index, crossline index) from trace_mask."""
    meta = json.loads(parts[".zmetadata"])["metadata"]
    a = _zarray(meta, "trace_mask")
    (ni, nx), (ci, cx) = a["shape"], a["chunks"]
    pts = []
    for bi in range(-(-ni // ci)):
        for bx in range(-(-nx // cx)):
            m = _chunk(parts, f"trace_mask/{bi}/{bx}", a)
            for r in range(min(ci, ni - bi * ci)):
                row = m[r * cx:r * cx + min(cx, nx - bx * cx)]
                lo = row.find(1)
                if lo >= 0:
                    hi = row.rfind(1)
                    pts += [(bi * ci + r, bx * cx + lo), (bi * ci + r, bx * cx + hi)]
    if not pts:
        raise Refused("empty response: trace_mask has no live trace")
    return convex_hull(pts)


def mdio_header_chunks(parts: dict) -> list[str]:
    meta = json.loads(parts[".zmetadata"])["metadata"]
    ci, cx = _zarray(meta, "headers")["chunks"]
    return sorted({f"headers/{i // ci}/{x // cx}" for i, x in mdio_grid_hull(parts)})


def mdio_positions(rule: dict, parts: dict) -> tuple[list[tuple[float, float]], str | None, str | None]:
    meta = json.loads(parts[".zmetadata"])["metadata"]
    a = _zarray(meta, "headers")
    ci, cx = a["chunks"]
    fields, size = {}, 0
    for fname, ftype in a["dtype"]:
        fmt = (">" if ftype[0] == ">" else "<") + STRUCT[ftype[1:]]
        fields[fname] = (size, fmt)
        size += struct.calcsize(fmt)
    want = (rule["x_field"], rule["y_field"], rule["scalar_field"])
    if any(w not in fields for w in want):
        raise Refused(f"MDIO headers lack one of {want}")
    decoded, pts = {}, []
    for i, x in mdio_grid_hull(parts):
        name = f"headers/{i // ci}/{x // cx}"
        if name not in decoded:
            decoded[name] = _chunk(parts, name, a)
        at = ((i % ci) * cx + x % cx) * size
        xv, yv, sv = (struct.unpack_from(fields[w][1], decoded[name], at + fields[w][0])[0] for w in want)
        pts.append((_scaled(xv, sv), _scaled(yv, sv)))
    units = ((meta.get(f"{rule['x_field']}/.zattrs") or {}).get("unitsV1") or {}).get("length")
    name = (meta.get(".zattrs") or {}).get("name")
    return pts, units, name


def segy_hull(rec_input: dict, rule: dict, parts: list[tuple[str, bytes]]) -> list[dict]:
    """The convex hull of every live trace's coordinates, from SEG-Y headers or an MDIO store."""
    if rec_input["format"] == "mdio":
        pts, units, survey = mdio_positions(rule, dict(parts))
    else:
        pts, units = segy_positions(rule, parts[0][1])
        survey = None
    units = units or rec_input.get("units")
    if units is None:
        raise Refused(f"{rec_input['name']}: coordinate units not declared (data nor record)")
    f = to_wgs84(rec_input.get("crs"), units)
    ring = closed_ring([f(x, y) for x, y in convex_hull(pts)])
    ident = {"publisher_id": survey} if survey else {}
    return [{"kind": rule["kind"], "name": survey or rec_input["name"], **ident,
             "geometry": {"type": "Polygon", "coordinates": [ring]}}]


EXTRACTORS = {"register-wfs": register_wfs, "register-csv": register_csv, "register-arcgis": register_arcgis,
              "segy-hull": segy_hull, "publisher-file": publisher_file}
