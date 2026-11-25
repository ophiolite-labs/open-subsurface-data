"""Areas that hold data (E46): which country, province and basin each dataset sits in.

Inputs: the committed area files under areas/ (schema area/1: areas/<kind>.geojson, or
areas/<kind>/<name>.geojson when a kind has one file per source), the records and their committed
outlines. Outputs (written by osd build): build/catalog/areas.json (`#/$defs/index`),
build/catalog/areas-<kind>.geojson (`#/$defs/drawn`) and records[].areas.

The count (R-S3, the charter's design 4 with its dispositions):
- A record's positions are its committed outline features; when it has none, the middle of
  `region.bbox` (never for a `national` record); otherwise none.
- A record sits in an area when one of its positions intersects the area, exactly, on the committed
  geometry: a point inside a part (even-odd over all rings, so a hole is outside; a point on an edge
  is decided by the half-open rule), a line or ring edge that touches or crosses a part's edge, or a
  part whose first vertex lies inside a polygon feature. Edges that step more than 180 degrees of
  longitude are cut at +-180 as the committed outlines cut lines (RFC 7946 3.1.9).
- `national`: the record also sits in `region.country`. Not national: when none of its positions
  lies in any country, it sits in `region.country` (offshore registers; no position at all likewise).
  A country that is not an area is never added.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from . import paths
from .records import Problem, geometry_problems

KINDS = ("country", "province", "basin", "licence")
CORE = ("country", "province", "basin")
VERSION = "areas/1"
DECIMALS = 6
CELL = 1.0   # degrees: the cell of the part index


def schema() -> dict:
    return json.loads((paths.SCHEMA_DIR / "area.schema.json").read_text())


def validator(defn: str | None = None) -> Draft202012Validator:
    s = schema()
    if defn:
        s = {"$schema": s["$schema"], "$id": s["$id"], "$defs": s["$defs"], "$ref": f"#/$defs/{defn}"}
    return Draft202012Validator(s, format_checker=FormatChecker())


def area_files(areas_dir: Path = paths.AREAS_DIR) -> list[Path]:
    """areas/<kind>.geojson and areas/<kind>/<name>.geojson, sorted by their path under areas/."""
    if not areas_dir.is_dir():
        return []
    return sorted([*areas_dir.glob("*.geojson"), *areas_dir.glob("*/*.geojson")],
                  key=lambda p: p.relative_to(areas_dir).as_posix())


def file_kind(rel: str) -> str:
    """The kind a path under areas/ must hold: its stem at the top, its directory below."""
    return rel.split("/")[0].removesuffix(".geojson")


def polygons(g: dict) -> list:
    return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]


def wide_edges(g: dict) -> int:
    """Edges that step more than 180 degrees of longitude (not cut at the antimeridian)."""
    return sum(abs(b[0] - a[0]) > 180 for poly in polygons(g) for ring in poly for a, b in itertools.pairwise(ring))


def _geometry_fast(g: dict) -> tuple[bool, int]:
    """(rings closed, positions numeric WGS84 lon/lat; edges over 180 degrees) in one pass over flat lists;
    (False, 0) sends the caller to records.geometry_problems for the words."""
    import operator

    wide = 0
    try:
        for poly in polygons(g):
            if not poly:
                return False, 0
            for ring in poly:
                if len(ring) < 4 or ring[0] != ring[-1] or not set(map(len, ring)) <= {2, 3}:
                    return False, 0
                xs, ys = [p[0] for p in ring], [p[1] for p in ring]
                lo, hi, south, north = min(xs), max(xs), min(ys), max(ys)
                if not all(type(v) in (int, float) for v in (lo, hi, south, north)):
                    return False, 0
                if not (-180 <= lo and hi <= 180 and -90 <= south and north <= 90):
                    return False, 0
                wide += sum(d > 180 for d in map(abs, map(operator.sub, xs[1:], xs[:-1])))
    except (TypeError, KeyError, IndexError):
        return False, 0
    return True, wide


_CHECKED: dict[tuple, tuple] = {}   # (path, size, mtime) -> one file's findings, for repeated validate calls


def _check_file(p: Path, rel: str) -> tuple[list[Problem], str | None, list[tuple[int, str]], list[tuple[int, str]]]:
    """One area file: (problems, kind when valid, [(feature, area_id)], [(feature, country)])."""
    st = p.stat()
    key = (str(p), st.st_size, st.st_mtime_ns)
    if key in _CHECKED:
        return _CHECKED[key]
    problems: list[Problem] = []
    try:
        doc = json.loads(p.read_text())
    except (OSError, ValueError) as e:
        return [Problem(rel, f"unreadable: {e}")], None, [], []
    errs = sorted(validator().iter_errors(doc), key=lambda e: list(e.path))
    for err in errs:
        where = "/".join(str(x) for x in err.path) or "<root>"
        problems.append(Problem(rel, f"{where}: {err.message}"))
    kind = doc.get("kind") if isinstance(doc, dict) else None
    if file_kind(rel) != kind:
        problems.append(Problem(rel, f"kind {kind!r} does not match the file path (areas/<kind>.geojson "
                                     "or areas/<kind>/<name>.geojson)"))
    if errs:
        return problems, None, [], []
    ids, owners = [], []
    for i, f in enumerate(doc["features"]):
        aid = f["properties"]["area_id"]
        ok, wide = _geometry_fast(f["geometry"])
        if not ok:
            problems += [Problem(rel, f"feature {i} ({aid}): {m}") for m in geometry_problems(f["geometry"])]
        elif wide:
            problems.append(Problem(rel, f"feature {i} ({aid}): an edge steps more than 180 degrees of "
                                         "longitude; cut it at +-180 (RFC 7946 3.1.9)"))
        ids.append((i, aid))
        if "country" in f["properties"]:
            owners.append((i, f["properties"]["country"]))
    _CHECKED[key] = (problems, kind, ids, owners)
    return _CHECKED[key]


def validate_areas(areas_dir: Path = paths.AREAS_DIR) -> list[Problem]:
    """Each area file against area/1, in the place its kind says, with valid WGS84 rings cut at +-180;
    area_id unique within a kind across its files; a province's or licence's country is a country area
    when countries are committed."""
    problems: list[Problem] = []
    seen: dict[tuple[str, str], str] = {}
    countries: set[str] | None = None
    owners: list[tuple[str, int, str]] = []
    for p in area_files(areas_dir):
        rel = p.relative_to(areas_dir).as_posix()
        found, kind, ids, own = _check_file(p, rel)
        problems += found
        if kind == "country":
            countries = (countries or set()) | {aid for _, aid in ids}
        for i, aid in ids:
            if (kind, aid) in seen:
                problems.append(Problem(rel, f"feature {i}: area_id '{aid}' repeated in kind {kind} "
                                             f"(also {seen[(kind, aid)]})"))
            seen.setdefault((kind, aid), rel)
        owners += [(rel, i, c) for i, c in own]
        if kind == "licence":
            problems += _terms_problems(p, rel, areas_dir)
    if countries is not None:
        for rel, i, c in owners:
            if c not in countries:
                problems.append(Problem(rel, f"feature {i}: country '{c}' is not a country area"))
    return problems


def _terms_problems(p: Path, rel: str, areas_dir: Path) -> list[Problem]:
    """E51 (F15): a licence file is drawn only when areas/SOURCES.md, where the terms are quoted, names its
    source address and its credit line word for word."""
    sources = areas_dir / "SOURCES.md"
    text = " ".join(sources.read_text().split()) if sources.exists() else ""
    src = json.loads(p.read_text())["source"]
    return [Problem(rel, f"source/{k} is not written in areas/SOURCES.md, where the terms are quoted: {src[k]!r}")
            for k in ("url", "credit") if " ".join(src[k].split()) not in text]


# --- geometry ---------------------------------------------------------------------------------------

Edge = tuple[float, float, float, float]


def cut_edges(ring: list) -> list[Edge]:
    """A ring's or line's edges; an edge that steps more than 180 degrees is taken the short way round
    and cut at +-180 into two edges (the committed outlines' rule for lines, geometry.split_antimeridian)."""
    out: list[Edge] = []
    for a, b in itertools.pairwise(ring):
        ax, ay, bx, by = a[0], a[1], b[0], b[1]
        if abs(bx - ax) > 180:
            edge = 180.0 if ax > 0 else -180.0
            bxw = bx + 2 * edge
            lat = ay + (by - ay) * (edge - ax) / (bxw - ax)
            out += [(ax, ay, edge, lat), (-edge, lat, bx, by)]
        else:
            out.append((ax, ay, bx, by))
    return out


def unwrap(ring: list) -> list[tuple[float, float]]:
    """The ring with each step taken the short way round, so it is continuous across the antimeridian."""
    out = [(ring[0][0], ring[0][1])]
    for b in ring[1:]:
        x = b[0]
        while x - out[-1][0] > 180:
            x -= 360
        while x - out[-1][0] < -180:
            x += 360
        out.append((x, b[1]))
    return out


def parity(x: float, y: float, edges: Iterable[Edge]) -> bool:
    """Even-odd: True when a ray to +x crosses the edges an odd number of times (half-open in y)."""
    inside = False
    for x1, y1, x2, y2 in edges:
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _orient(ax, ay, bx, by, cx, cy) -> int:
    v = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    return (v > 0) - (v < 0)


def _on(ax, ay, bx, by, cx, cy) -> bool:
    return min(ax, bx) <= cx <= max(ax, bx) and min(ay, by) <= cy <= max(ay, by)


def segments_meet(e: Edge, f: Edge) -> bool:
    """Closed segments touch or cross."""
    ax, ay, bx, by = e
    cx, cy, dx, dy = f
    d1, d2 = _orient(cx, cy, dx, dy, ax, ay), _orient(cx, cy, dx, dy, bx, by)
    d3, d4 = _orient(ax, ay, bx, by, cx, cy), _orient(ax, ay, bx, by, dx, dy)
    if d1 != d2 and d3 != d4 and (d1 or d2) and (d3 or d4):
        return True
    return ((d1 == 0 and _on(cx, cy, dx, dy, ax, ay)) or (d2 == 0 and _on(cx, cy, dx, dy, bx, by))
            or (d3 == 0 and _on(ax, ay, bx, by, cx, cy)) or (d4 == 0 and _on(ax, ay, bx, by, dx, dy)))


def ring_area(ring: list) -> float:
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in itertools.pairwise(ring)) / 2


def label_point(g: dict) -> list[float]:
    """[lon, lat] inside the largest part: the exterior ring's centroid when inside, else the middle of
    the widest inside span of the horizontal line through it."""
    poly = max(polygons(g), key=lambda p: abs(ring_area(p[0])) - sum(abs(ring_area(r)) for r in p[1:]))
    ext = poly[0]
    a = ring_area(ext)
    if a:
        cx = sum((p[0] + q[0]) * (p[0] * q[1] - q[0] * p[1]) for p, q in itertools.pairwise(ext)) / (6 * a)
        cy = sum((p[1] + q[1]) * (p[0] * q[1] - q[0] * p[1]) for p, q in itertools.pairwise(ext)) / (6 * a)
    else:
        cx, cy = sum(p[0] for p in ext) / len(ext), sum(p[1] for p in ext) / len(ext)
    edges = [e for r in poly for e in cut_edges(r)]
    if not parity(cx, cy, edges):
        xs = sorted(x1 + (cy - y1) * (x2 - x1) / (y2 - y1) for x1, y1, x2, y2 in edges if (y1 > cy) != (y2 > cy))
        spans = [(xs[i + 1] - xs[i], xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]
        if spans:
            _, x0, x1 = max(spans)
            cx = (x0 + x1) / 2
        else:
            cx, cy = ext[0][0], ext[0][1]
    return [round(cx, DECIMALS), round(cy, DECIMALS)]


def area_bbox(g: dict) -> list[float]:
    xs = [p[0] for poly in polygons(g) for p in poly[0]]
    ys = [p[1] for poly in polygons(g) for p in poly[0]]
    return [min(xs), min(ys), max(xs), max(ys)]


@dataclass
class Part:
    """One polygon of an area, its edges in latitude bands."""
    key: str                     # area_id
    edges: list[Edge]
    bbox: tuple[float, float, float, float]
    first: tuple[float, float]
    bands: list[list[Edge]] = field(default_factory=list)
    y0: float = 0.0
    h: float = 1.0

    def __post_init__(self):
        _, s, _, n = self.bbox
        nb = max(1, min(512, len(self.edges) // 8))
        self.y0, self.h = s, ((n - s) / nb) or 1.0
        self.bands = [[] for _ in range(nb)]
        for ed in self.edges:
            for b in range(self.band(min(ed[1], ed[3])), self.band(max(ed[1], ed[3])) + 1):
                self.bands[b].append(ed)

    def band(self, y: float) -> int:
        return min(len(self.bands) - 1, max(0, int((y - self.y0) / self.h)))

    def contains(self, x: float, y: float) -> bool:
        w, s, e, n = self.bbox
        return w <= x <= e and s <= y <= n and parity(x, y, self.bands[self.band(y)])

    def meets(self, ed: Edge) -> bool:
        ys0, ys1 = min(ed[1], ed[3]), max(ed[1], ed[3])
        xs0, xs1 = min(ed[0], ed[2]), max(ed[0], ed[2])
        w, s, e, n = self.bbox
        if xs1 < w or xs0 > e or ys1 < s or ys0 > n:
            return False
        seen = set()
        for b in range(self.band(ys0), self.band(ys1) + 1):
            for f in self.bands[b]:
                if f in seen:
                    continue
                seen.add(f)
                if (max(f[0], f[2]) >= xs0 and min(f[0], f[2]) <= xs1 and max(f[1], f[3]) >= ys0
                        and min(f[1], f[3]) <= ys1 and segments_meet(ed, f)):
                    return True
        return False


def _cells(w: float, s: float, e: float, n: float) -> Iterable[tuple[int, int]]:
    for i in range(math.floor(w / CELL), math.floor(e / CELL) + 1):
        for j in range(math.floor(s / CELL), math.floor(n / CELL) + 1):
            yield i, j


class KindIndex:
    """The parts of every area of one kind, found by 1-degree cell."""

    def __init__(self, features: list[dict]):
        self.parts: list[Part] = []
        self.cells: dict[tuple[int, int], list[int]] = {}
        for f in features:
            for poly in polygons(f["geometry"]):
                xs = [p[0] for p in poly[0]]
                ys = [p[1] for p in poly[0]]
                part = Part(f["properties"]["area_id"], [e for r in poly for e in cut_edges(r)],
                            (min(xs), min(ys), max(xs), max(ys)), (poly[0][0][0], poly[0][0][1]))
                for c in _cells(*part.bbox):
                    self.cells.setdefault(c, []).append(len(self.parts))
                self.parts.append(part)

    def candidates(self, w: float, s: float, e: float, n: float, found: set[str]) -> list[Part]:
        idx = sorted({i for c in _cells(w, s, e, n) for i in self.cells.get(c, ())})
        return [self.parts[i] for i in idx if self.parts[i].key not in found]

    def hits(self, shapes: Shapes) -> set[str]:
        found: set[str] = set()
        for x, y in shapes.points:
            for part in self.candidates(x, y, x, y, found):
                if part.contains(x, y):
                    found.add(part.key)
        for ed in shapes.edges:
            box = (min(ed[0], ed[2]), min(ed[1], ed[3]), max(ed[0], ed[2]), max(ed[1], ed[3]))
            for part in self.candidates(*box, found):
                if part.meets(ed):
                    found.add(part.key)
        for ring_set, (w, s, e, n) in shapes.polygons:
            for shift in {0.0, *([360.0] if e > 180 else []), *([-360.0] if w < -180 else [])}:
                box = (max(-180.0, w - shift), s, min(180.0, e - shift), n)
                if box[0] > box[2]:
                    continue
                for part in self.candidates(*box, found):
                    if parity(part.first[0] + shift, part.first[1], ring_set):
                        found.add(part.key)
        return found


@dataclass
class Shapes:
    """A record's positions: points, edges (cut at +-180), and polygon features as unwrapped edge sets."""
    points: list[tuple[float, float]] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    polygons: list[tuple[list[Edge], tuple[float, float, float, float]]] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.points or self.edges or self.polygons)

    def add(self, g: dict) -> None:
        t, c = g["type"], g["coordinates"]
        if t == "Point":
            self.points.append((c[0], c[1]))
        elif t == "MultiPoint":
            self.points += [(p[0], p[1]) for p in c]
        elif t in ("LineString", "MultiLineString"):
            for line in [c] if t == "LineString" else c:
                self.points += [(p[0], p[1]) for p in line]
                self.edges += cut_edges(line)
        elif t in ("Polygon", "MultiPolygon"):
            for poly in [c] if t == "Polygon" else c:
                for ring in poly:
                    self.points += [(p[0], p[1]) for p in ring]
                    self.edges += cut_edges(ring)
                rings = [unwrap(r) for r in poly]
                xs = [p[0] for p in rings[0]]
                ys = [p[1] for p in rings[0]]
                self.polygons.append(([(a[0], a[1], b[0], b[1]) for r in rings for a, b in itertools.pairwise(r)],
                                      (min(xs), min(ys), max(xs), max(ys))))


def bbox_middle(b: list[float]) -> tuple[float, float]:
    w, s, e, n = b
    x = (w + e) / 2 if w <= e else (w + e + 360) / 2
    return (x - 360 if x > 180 else x), (s + n) / 2


def record_shapes(rec: dict, outline: dict | None) -> Shapes:
    """The record's positions: its outline features; else its bbox middle unless it is national."""
    sh = Shapes()
    for f in (outline or {}).get("features", []):
        sh.add(f["geometry"])
    region = rec.get("region") or {}
    if not sh and not region.get("national") and region.get("bbox"):
        sh.points.append(bbox_middle(region["bbox"]))
    return sh


# --- the count and the outputs ---------------------------------------------------------------------

@dataclass
class AreaSet:
    """The committed area files, by kind."""
    files: list[tuple[str, dict]]

    @classmethod
    def load(cls, areas_dir: Path = paths.AREAS_DIR) -> AreaSet:
        return cls([(p.relative_to(areas_dir).as_posix(), json.loads(p.read_text())) for p in area_files(areas_dir)])

    def kinds(self) -> list[str]:
        present = {doc["kind"] for _, doc in self.files}
        return [k for k in KINDS if k in CORE or k in present]

    def features(self, kind: str) -> list[tuple[str, dict]]:
        return [(rel, f) for rel, doc in self.files if doc["kind"] == kind for f in doc["features"]]


def count(records: dict[str, dict], outlines: dict[str, dict | None], areas: AreaSet) -> dict[str, dict[str, list[str]]]:
    """records[id] -> {kind: sorted area ids}, for every kind of the index."""
    kinds = areas.kinds()
    index = {k: KindIndex([f for _, f in areas.features(k)]) for k in kinds}
    countries = {f["properties"]["area_id"] for _, f in areas.features("country")}
    out = {}
    for rid, rec in records.items():
        sh = record_shapes(rec, outlines.get(rid))
        got = {k: index[k].hits(sh) if sh else set() for k in kinds}
        region = rec.get("region") or {}
        c = region.get("country")
        if c in countries and (region.get("national") or not got["country"]):
            got["country"].add(c)
        out[rid] = {k: sorted(got[k]) for k in kinds}
    return out


def record_blocks(licences: list[str], held: dict[str, list[str]]) -> list[str]:
    """records[].blocks (E51 design 4): the block names of the record's licences, natural order, when it sits
    in 1 to BLOCKS_MAX licences; otherwise none (the row shows the number of areas.licence)."""
    if not 0 < len(licences) <= BLOCKS_MAX:
        return []
    return sorted({b for aid in licences for b in held.get(aid, [])}, key=natural)


def drawn_id(kind: str, area_id: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{kind}:{area_id}".encode()).digest()[:6], "big")


def index_and_drawn(areas: AreaSet, placed: dict[str, dict[str, list[str]]]) -> tuple[dict, dict[str, dict]]:
    """areas.json, and per kind the drawn FeatureCollection: only areas that hold a dataset."""
    kinds_out: dict[str, dict] = {}
    drawn: dict[str, dict] = {}
    for k in areas.kinds():
        ids_by_area: dict[str, list[str]] = {}
        for rid in sorted(placed):
            for aid in placed[rid][k]:
                ids_by_area.setdefault(aid, []).append(rid)
        entries, feats = [], []
        for rel, f in sorted(areas.features(k), key=lambda x: x[1]["properties"]["area_id"]):
            pr = f["properties"]
            ids = ids_by_area.get(pr["area_id"])
            if not ids:
                continue
            e = {"area_id": pr["area_id"], "name": pr["name"]}
            if "country" in pr:
                e["country"] = pr["country"]
            e.update(source=rel, label=label_point(f["geometry"]), bbox=area_bbox(f["geometry"]), n=len(ids), ids=ids)
            entries.append(e)
            feats.append({"type": "Feature", "id": drawn_id(k, pr["area_id"]),
                          "properties": {"area_id": pr["area_id"], "name": pr["name"], "n": len(ids)},
                          "geometry": f["geometry"]})
        sources = [{"file": rel, **doc["source"]} for rel, doc in areas.files if doc["kind"] == k]
        kinds_out[k] = {"sources": sources, "areas": entries}
        if areas.features(k):
            drawn[k] = {"type": "FeatureCollection", "kind": k, "features": feats}
    return {"version": VERSION, "kinds": kinds_out}, drawn


NUMBERS = re.compile(r"\[\s+(-?[0-9][-0-9.e+,\s]*?)\s+\]")


def dumps_index(doc: dict) -> str:
    """areas.json as written: two-space indent, each label and bbox on one line."""
    text = json.dumps(doc, indent=2, ensure_ascii=False)
    return NUMBERS.sub(lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", text) + "\n"


COUNT_RULE = "e46-count-1"   # change when the count changes: every cached result is then stale


def area_set_digest(areas_dir: Path) -> str:
    h = hashlib.sha256(COUNT_RULE.encode())
    for p in area_files(areas_dir):
        h.update(p.relative_to(areas_dir).as_posix().encode() + b"\0" + hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def record_key(rec: dict, outline_bytes: bytes | None) -> str:
    """What a record's areas depend on besides the area files: its region and its committed outline."""
    h = hashlib.sha256(json.dumps(rec.get("region") or {}, sort_keys=True).encode())
    h.update(b"\0" + (hashlib.sha256(outline_bytes).digest() if outline_bytes is not None else b"none"))
    return h.hexdigest()


def write(out_dir: Path, records_out: list[dict], records: dict[str, dict], outlines_dir: Path,
          areas_dir: Path = paths.AREAS_DIR, cache_dir: Path | None = None) -> dict:
    """Write areas.json and areas-<kind>.geojson into out_dir and set records_out[].areas (every index
    kind) when any area file is committed. Returns {kind: number of areas that hold a dataset}.
    cache_dir: per area-set digest one file {record key: areas}; a record whose region or outline changed,
    or any area file, is counted again. Written whole by rename; never published."""
    import sys
    import tempfile

    areas = AreaSet.load(areas_dir)
    for old in out_dir.glob("areas-*.geojson"):
        old.unlink()
    if areas.files:
        keys, outlines = {}, {}
        for rid, rec in records.items():
            op = paths.outline_path(rid, outlines_dir)
            raw = op.read_bytes() if op.exists() else None
            keys[rid] = record_key(rec, raw)
            outlines[rid] = json.loads(raw) if raw is not None else None
        cached: dict = {}
        cfile = cache_dir / f"areas-{area_set_digest(areas_dir)[:16]}.json" if cache_dir else None
        if cfile and cfile.exists():
            try:
                cached = json.loads(cfile.read_text())
            except ValueError:
                cached = {}
        todo = {rid: rec for rid, rec in records.items() if keys[rid] not in cached}
        fresh = count(todo, outlines, areas) if todo else {}
        placed = {rid: fresh[rid] if rid in fresh else cached[keys[rid]] for rid in records}
        if cfile and todo:
            cache_dir.mkdir(parents=True, exist_ok=True)
            for old in cache_dir.glob("areas-*.json"):
                old.unlink(missing_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=cache_dir, delete=False, suffix=".tmp") as t:
                json.dump({keys[rid]: placed[rid] for rid in records}, t)
            Path(t.name).replace(cfile)
        held = {f["properties"]["area_id"]: f["properties"].get("blocks", []) for _, f in areas.features("licence")}
        for r in records_out:
            r["areas"] = placed[r["id"]]
            if b := record_blocks(placed[r["id"]].get("licence", []), held):
                r["blocks"] = b
        print(f"areas: {len(todo)} records counted, {len(records) - len(todo)} from the cache", file=sys.stderr)
    else:
        placed = {rid: {k: [] for k in CORE} for rid in records}
    doc, drawn = index_and_drawn(areas, placed)
    (out_dir / "areas.json").write_text(dumps_index(doc))
    for k, fc in drawn.items():
        (out_dir / f"areas-{k}.geojson").write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n")
    for k, v in doc["kinds"].items():
        print(f"areas: {k} {len(v['areas'])} areas hold data, "
              f"{sum(1 for x in placed.values() if x.get(k))} datasets placed", file=sys.stderr)
    return {k: len(v["areas"]) for k, v in doc["kinds"].items()}


# Tiles (E46 design 5): areas.pmtiles, one layer per kind, the drawn areas only, z0-8 (the area files are
# simplified for zoom 8; the page overzooms). Feature id is the drawn id; properties area_id, name, n.
AREA_TILE_ARGS = ["-q", "-f", "-Z0", "-z8", "--no-feature-limit", "--no-tile-size-limit",
                  "--no-tiny-polygon-reduction", "--detect-shared-borders"]


def write_tiles(out_dir: Path, cache_dir: Path = paths.BUILD_DIR / "tiles") -> Path | None:
    """out_dir/areas.pmtiles from out_dir/areas-<kind>.geojson, cached by input and tool version like the
    outline tiles; None when tippecanoe is absent or no kind has a drawn area (the page reads the GeoJSON)."""
    import shutil
    import subprocess
    import sys

    dst = out_dir / "areas.pmtiles"
    dst.unlink(missing_ok=True)
    layers = [(f"areas_{p.stem.removeprefix('areas-')}", p) for p in sorted(out_dir.glob("areas-*.geojson"))
              if json.loads(p.read_text())["features"]]
    if not layers or not shutil.which("tippecanoe"):
        return None
    version = subprocess.run(["tippecanoe", "--version"], capture_output=True, text=True, check=False).stderr.strip()
    key = hashlib.sha256(json.dumps([version, AREA_TILE_ARGS, [n for n, _ in layers]]).encode())
    for _, p in layers:
        key.update(p.read_bytes())
    cached = cache_dir / f"areas-{key.hexdigest()[:16]}.pmtiles"
    if not cached.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_dir / f"tmp-{os.getpid()}-{cached.name}"   # tippecanoe writes PMTiles for a .pmtiles name
        args = [a for n, p in layers for a in ("-L", f"{n}:{p}")]
        r = subprocess.run(["tippecanoe", *AREA_TILE_ARGS, "-o", str(tmp), *args], capture_output=True, text=True, check=False)
        if r.returncode:
            raise RuntimeError(f"tippecanoe failed: {r.stderr}")
        for old in cache_dir.glob("areas-*.pmtiles"):
            old.unlink(missing_ok=True)
        tmp.replace(cached)
    shutil.copyfile(cached, dst)
    print(f"tiles: {dst.name} {dst.stat().st_size / 1e6:.1f} MB, z0-8, layers {', '.join(n for n, _ in layers)}", file=sys.stderr)
    return dst


# --- preparation (osd areas prepare): a publisher's file on this machine to a committed area file ----
# Read as data, never executed; reaches no network. GeoJSON, or an ESRI Shapefile of polygons (a .zip
# holding one, or the .shp with its .dbf beside it) in geographic WGS84 coordinates.

class Refused(ValueError):
    pass


def _dbf(b: bytes, encoding: str) -> list[dict]:
    import struct

    n, header, size = struct.unpack("<IHH", b[4:12])
    fields, i = [], 32
    while b[i] != 0x0D:
        fields.append((b[i:i + 11].split(b"\0")[0].decode("ascii"), chr(b[i + 11]), b[i + 16]))
        i += 32
    rows = []
    for r in range(n):
        rec, at, row = b[header + r * size: header + (r + 1) * size], 1, {}
        for name, t, width in fields:
            raw = rec[at:at + width].split(b"\0")[0].decode(encoding, "replace").strip()
            at += width
            if t in "NF":
                row[name] = None if not raw or raw.startswith("*") else (float(raw) if "." in raw or "e" in raw.lower() else int(raw))
            else:
                row[name] = raw
        rows.append(row)
    return rows


def _shp_polygons(b: bytes) -> list[list[list[list[float]]] | None]:
    """Each record's rings (shape type 5 Polygon, 15 PolygonZ, 25 PolygonM; 0 Null gives None)."""
    import struct

    if struct.unpack(">I", b[:4])[0] != 9994:
        raise Refused("not a shapefile (.shp file code)")
    out, i = [], 100
    while i + 8 <= len(b):
        length = struct.unpack(">I", b[i + 4:i + 8])[0] * 2
        rec = b[i + 8:i + 8 + length]
        i += 8 + length
        t = struct.unpack("<i", rec[:4])[0]
        if t == 0:
            out.append(None)
            continue
        if t not in (5, 15, 25):
            raise Refused(f"shape type {t} is not a polygon")
        nparts, npts = struct.unpack("<ii", rec[36:44])
        parts = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])) + [npts]
        at = 44 + 4 * nparts
        xy = struct.unpack(f"<{2 * npts}d", rec[at:at + 16 * npts])
        out.append([[[xy[2 * k], xy[2 * k + 1]] for k in range(parts[p], parts[p + 1])] for p in range(nparts)])
    return out


def _nest(rings: list[list[list[float]]]) -> dict:
    """Shapefile rings to GeoJSON: clockwise rings are exteriors, the others holes of the smallest
    exterior holding their first vertex."""
    outer = [r for r in rings if ring_area(r) < 0]
    holes = [r for r in rings if ring_area(r) >= 0]
    if not outer:
        outer, holes = holes, []
    polys = [[o] for o in outer]
    for h in holes:
        hold = [p for p in polys if parity(h[0][0], h[0][1], cut_edges(p[0]))]
        (min(hold, key=lambda p: abs(ring_area(p[0]))) if hold else polys[0]).append(h)
    for p in polys:   # GeoJSON: exterior counterclockwise, holes clockwise (RFC 7946 3.1.6)
        p[0] = p[0][::-1]
        p[1:] = [h[::-1] for h in p[1:]]
    return {"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1 else {"type": "MultiPolygon", "coordinates": polys}


def read_features(path: Path) -> list[tuple[dict, dict | None]]:
    """[(attributes, geometry)] from a GeoJSON file, a .shp (with .dbf, .prj, .cpg beside it) or a .zip
    holding one .shp. Coordinates must be geographic WGS84 (the .prj says GCS WGS 1984)."""
    import zipfile

    if path.suffix.lower() in (".geojson", ".json"):
        fc = json.loads(path.read_text())
        return [(f.get("properties") or {}, f.get("geometry")) for f in fc.get("features", [])]
    if path.suffix.lower() == ".zip":
        z = zipfile.ZipFile(path)
        shps = [n for n in z.namelist() if n.lower().endswith(".shp")]
        if len(shps) != 1:
            raise Refused(f"{path.name}: {len(shps)} .shp files inside, need one")
        names = {n.lower(): n for n in z.namelist()}

        def part(ext):
            n = names.get(shps[0][:-4].lower() + ext)
            return z.read(n) if n else None
    elif path.suffix.lower() == ".shp":
        sibs = {p.suffix.lower(): p for p in path.parent.glob(path.stem + ".*")}

        def part(ext):
            return sibs[ext].read_bytes() if ext in sibs else None
    else:
        raise Refused(f"{path.name}: not GeoJSON, .shp or .zip")
    prj = (part(".prj") or b"").decode("latin-1")
    if not (prj.startswith("GEOGCS") and "WGS_1984" in prj.replace(" ", "_")):
        raise Refused(f"{path.name}: the .prj does not say geographic WGS 84: {prj[:80]!r}")
    cpg = (part(".cpg") or b"").decode("ascii", "replace").strip().lower()
    encoding = "utf-8" if cpg in ("utf-8", "utf8", "65001") else "latin-1"
    rows = _dbf(part(".dbf") or b"", encoding)
    shapes = _shp_polygons(part(".shp"))
    if len(rows) != len(shapes):
        raise Refused(f"{path.name}: {len(rows)} attribute rows for {len(shapes)} shapes")
    return [(r, _nest(s) if s else None) for r, s in zip(rows, shapes)]


ID_PATTERNS = {"country": r"^[A-Z]{2}$", "province": r"^([A-Z]{2}-[A-Z0-9]{1,3}|[A-Z]{3}-[0-9]+)$",
               "basin": r"^usgs-[0-9]+$", "licence": r"^[A-Z]{2}:\S+$"}   # area/1 allOf (tests/test_areas.py)


def _value(attrs: dict, f: str, prefix: str = "") -> str | None:
    v = attrs.get(f)
    if v is None or v == "":
        return None
    return prefix + (str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)).strip()


def _area_id(attrs: dict, rule: dict, kind: str, taken: dict[str, dict]) -> str | None:
    """The first of the rule's id fields whose value (with the rule's prefix) fits the kind's pattern and,
    for a field the rule lists under `unique`, is not repeated in the file."""
    import re as _re

    for f in rule["id"]:
        v = _value(attrs, f, rule.get("prefix", ""))
        if v and _re.fullmatch(ID_PATTERNS[kind], v) and taken.get(f, {}).get(v, 1) == 1:
            return v
    return None


def densify_wide(g: dict) -> dict:
    """Edges longer than 180 degrees of longitude halved (planar midpoints) until none is: the publisher's
    straight edge along a parallel, such as Antarctica's along -90, kept as drawn, which simplification
    can leave as one edge from 180 to -180 (area/1 refuses an edge over 180 degrees)."""
    def ring(r):
        out = [r[0]]
        for b in r[1:]:
            a = out[-1]
            n = 1
            while abs(b[0] - a[0]) / n > 180:
                n *= 2
            out += [[a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n] for k in range(1, n)] + [b]
        return out
    polys = [[ring(r) for r in poly] for poly in polygons(g)]
    return {"type": g["type"], "coordinates": polys[0] if g["type"] == "Polygon" else polys}


def _merge(geoms: list[dict]) -> dict:
    polys = [p for g in geoms for p in polygons(g)]
    return {"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1 else {"type": "MultiPolygon", "coordinates": polys}


def prepare(kind: str, path: Path, rule: dict, countries: set[str] | None = None) -> tuple[dict, list[str]]:
    """The area file for kind from the publisher's file at path, by its rule in areas/prepare.yaml: ids,
    names and (provinces) countries from the named attributes, parts of one id merged, simplified to
    `tolerance_m` (zoom 8) with positions rounded to `decimals`. Returns (area file, notes on what was left
    out and why)."""
    import collections

    from .outlines.geometry import simplify

    notes: list[str] = []
    by_id: dict[str, list] = {}
    rows = read_features(path)
    taken = {f: collections.Counter(_value(a, f, rule.get("prefix", "")) for a, _ in rows) for f in rule.get("unique", [])}
    for attrs, g in rows:
        if any(_value(attrs, f) in map(str, vs) for f, vs in rule.get("exclude", {}).items()):
            continue
        aid = _area_id(attrs, rule, kind, taken)
        name = str(attrs.get(rule["name"]) or "").strip()
        if g is None or not aid or not name:
            notes.append(f"left out: no geometry, id or name: {rule['name']}={name!r} "
                         + " ".join(f"{f}={attrs.get(f)!r}" for f in rule["id"]))
            continue
        country = attrs.get(rule["country"]) if "country" in rule else None
        if "country" in rule and (not isinstance(country, str) or (countries is not None and country not in countries)):
            notes.append(f"left out: {aid} {name}: country {country!r} is not a country area")
            continue
        by_id.setdefault(aid, []).append((name, country, g))
    features = []
    for aid in sorted(by_id):
        parts = by_id[aid]
        big = max(parts, key=lambda p: max(abs(ring_area(q[0])) for q in polygons(p[2])))
        names = sorted({n for n, _, _ in parts})
        if len(names) > 1:
            notes.append(f"{aid}: {len(parts)} rows named {names}; the largest part's name kept: {big[0]}")
        g = densify_wide(simplify(_merge([p[2] for p in parts]), rule["tolerance_m"], decimals=rule["decimals"])[0])
        props = {"area_id": aid, "name": big[0]}
        if "country" in rule:
            props["country"] = big[1]
        features.append({"type": "Feature", "properties": props, "geometry": g})
    source = dict(rule["source"], sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return {"type": "FeatureCollection", "kind": kind, "source": source, "features": features}, notes


def prepare_to_file(kind: str, path: Path, areas_dir: Path = paths.AREAS_DIR) -> tuple[Path, list[str]]:
    """areas/<kind>.geojson from the publisher's file by its rule in areas/prepare.yaml; returns (path,
    notes). Provinces keep only countries in the committed areas/country.geojson."""
    import yaml

    rules = yaml.safe_load((areas_dir / "prepare.yaml").read_text())
    if kind not in rules:
        raise Refused(f"no rule for kind {kind!r} in {areas_dir / 'prepare.yaml'}")
    rule = rules[kind]
    if path.name != rule["file"]:
        raise Refused(f"{path.name} is not the file the rule names ({rule['file']})")
    countries = None
    if "country" in rule:
        cp = areas_dir / "country.geojson"
        if not cp.exists():
            raise Refused("prepare countries first: provinces keep only committed countries")
        countries = {f["properties"]["area_id"] for f in json.loads(cp.read_text())["features"]}
    doc, notes = prepare(kind, path, rule, countries)
    errs = list(validator().iter_errors(doc))
    if errs:
        raise Refused(f"the prepared file is not area/1: {errs[0].message}")
    out = areas_dir / f"{kind}.geojson"
    out.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    return out, notes


# --- E51: osd areas read <cc>: a regulator's licence layers to areas/licence/<cc>.geojson ---------------
# The one network command of this module, run by the `areas` workflow or a maintainer; tests inject `get`.
# areas/licence/<cc>.yaml names the service, the layers, the "current" filter, the block join and the terms
# (strategy E51-licences-per-country-STRATEGY.md). Every layer is read whole by the verifier's ArcGIS
# reader (E35). A read that fails any guard writes nothing: the committed file stays, with its date.

READ_AGENT = "areas-reader/1"   # a generic client name (no project or person in requests to regulators)
SHRINK = 0.2                    # more than this share of the committed licences missing: the read is refused
BLOCKS_MAX = 25                 # records[].blocks only for a record in at most this many licences
CONFIG_KEYS = {"country": str, "service": str, "licences": dict, "blocks": dict, "block_layer": dict,
               "tolerance_m": (int, float), "decimals": int, "source": dict}
SUB_KEYS = {"licences": ("layer", "id", "name", "join", "current", "edition"),
            "blocks": ("layer", "licence", "block"), "block_layer": ("layer", "id", "name"),
            "source": ("name", "url", "licence", "credit")}


class ReadRefused(Exception):
    """The read is not taken: the reason is the finding."""


def natural(s: str) -> list:
    """Sort key: digits as numbers ("15/9" before "15/12")."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def read_config(cc: str, areas_dir: Path = paths.AREAS_DIR) -> dict:
    """areas/licence/<cc>.yaml, its shape checked (strategy: the contract)."""
    import yaml

    p = areas_dir / "licence" / f"{cc.lower()}.yaml"
    if not p.exists():
        raise ReadRefused(f"no {p}: a country is read only when its file names the service and the terms")
    cfg = yaml.safe_load(p.read_text()) or {}
    for k, t in CONFIG_KEYS.items():
        if not isinstance(cfg.get(k), t):
            raise ReadRefused(f"{p.name}: `{k}` missing or not a {getattr(t, '__name__', t)}")
    for k, subs in SUB_KEYS.items():
        for s in subs:
            if cfg[k].get(s) in (None, ""):
                raise ReadRefused(f"{p.name}: `{k}.{s}` missing")
    cur = cfg["licences"]["current"]
    if not (isinstance(cur, dict) and cur.get("field") and cur.get("op") in ("=", "in") and "value" in cur):
        raise ReadRefused(f"{p.name}: `licences.current` is {{field, op (= or in), value}}")
    if cfg["country"] != cc.upper():
        raise ReadRefused(f"{p.name}: country {cfg['country']!r} is not {cc.upper()!r}")
    return cfg


def _layer(cfg: dict, which: str, get) -> list[dict]:
    """The attributes and geometry of every feature of one layer, read whole; WGS84 required."""
    from .verifier import layers

    url = f"{cfg['service'].rstrip('/')}/{cfg[which]['layer']}"
    try:
        _, body = layers.export_layer(url, get)
    except (layers.Incomplete, layers.NotWhole) as e:
        raise ReadRefused(f"layer {cfg[which]['layer']} not read whole: {getattr(e, 'reason', e)}") from None
    doc = json.loads(body)
    sr = doc.get("spatialReference") or {}
    if 4326 not in (sr.get("wkid"), sr.get("latestWkid")):
        raise ReadRefused(f"layer {cfg[which]['layer']} is not in WGS84 (spatialReference {sr})")
    return doc["features"]


def _current(attrs: dict, cur: dict, layer) -> bool:
    if cur["field"] not in attrs:
        raise ReadRefused(f"layer {layer}: the current filter's field {cur['field']!r} is not in the layer")
    v = attrs[cur["field"]]
    return v == cur["value"] if cur["op"] == "=" else v in cur["value"]


def read_licences(cfg: dict, get, today: str) -> dict:
    """The area file for one country from its regulator: one feature per current licence, its geometry
    simplified, its blocks from the join. Raises ReadRefused for every guard."""
    from .outlines.extractors import esri_geometry
    from .outlines.geometry import Refused as GeometryRefused
    from .outlines.geometry import simplify

    lc, bc, kc, cc = cfg["licences"], cfg["blocks"], cfg["block_layer"], cfg["country"]
    lic = _layer(cfg, "licences", get)
    rows = _layer(cfg, "blocks", get)
    blk = _layer(cfg, "block_layer", get)
    names: dict = {}
    for f in blk:
        a = f["attributes"]
        if a.get(kc["id"]) is None or not a.get(kc["name"]):
            raise ReadRefused(f"block layer {kc['layer']}: a block without {kc['id']} or {kc['name']}")
        if names.setdefault(a[kc["id"]], a[kc["name"]]) != a[kc["name"]]:
            raise ReadRefused(f"block layer {kc['layer']}: block {a[kc['id']]} named "
                              f"{names[a[kc['id']]]!r} and {a[kc['name']]!r}")
    current: dict = {}   # join value -> (id, name, geometry, edition)
    seen: set = set()
    for f in lic:
        a = f["attributes"]
        if not _current(a, lc["current"], lc["layer"]):
            continue
        aid, name, key = a.get(lc["id"]), a.get(lc["name"]), a.get(lc["join"])
        if aid in (None, "") or not name or key in (None, ""):
            raise ReadRefused(f"licence layer {lc['layer']}: a current licence without {lc['id']}, {lc['name']} "
                              f"or {lc['join']}: {aid!r} {name!r}")
        if aid in seen or key in current:
            raise ReadRefused(f"licence layer {lc['layer']}: licence {aid!r} ({name}) read twice")
        seen.add(aid)
        try:
            g = esri_geometry(f.get("geometry"))
        except GeometryRefused as e:
            raise ReadRefused(f"licence {name}: {e}") from None
        if not g or g["type"] not in ("Polygon", "MultiPolygon"):
            raise ReadRefused(f"licence {name}: no polygon")
        current[key] = (aid, name, g, a.get(lc["edition"]))
    if not current:
        raise ReadRefused(f"licence layer {lc['layer']}: no current licence read")
    blocks: dict = {k: set() for k in current}
    for f in rows:
        a = f["attributes"]
        key, bid = a.get(bc["licence"]), a.get(bc["block"])
        if key not in current:
            raise ReadRefused(f"block rows (layer {bc['layer']}): licence {key!r} is not a current licence")
        if bid not in names:
            raise ReadRefused(f"block rows (layer {bc['layer']}): block {bid!r} of licence {key!r} is not in "
                              f"block layer {kc['layer']}")
        blocks[key].add(names[bid])
    if empty := sorted(k for k, b in blocks.items() if not b):
        raise ReadRefused(f"{len(empty)} current licences have no block rows (layer {bc['layer']}), "
                          f"e.g. {empty[0]!r}")
    features = []
    for key, (aid, name, g, _) in current.items():
        try:
            sg = densify_wide(simplify(g, cfg["tolerance_m"], decimals=cfg["decimals"])[0])
        except (GeometryRefused, ValueError, IndexError) as e:
            raise ReadRefused(f"licence {name}: simplification failed: {e}") from None
        if bad := geometry_problems(sg):
            raise ReadRefused(f"licence {name}: {bad[0]}")
        features.append({"type": "Feature", "properties": {
            "area_id": f"{cc}:{aid}", "name": f"{cfg['licences'].get('name_prefix', '')}{name}", "country": cc,
            "blocks": sorted(blocks[key], key=natural)}, "geometry": sg})
    features.sort(key=lambda f: natural(f["properties"]["area_id"]))
    eds = [e for *_, e in current.values() if isinstance(e, int) and not isinstance(e, bool)]
    from datetime import UTC, datetime
    edition = datetime.fromtimestamp(max(eds) / 1000, UTC).date().isoformat() if eds else today
    canon = json.dumps(features, sort_keys=True, separators=(",", ":")).encode()
    source = {**{k: cfg["source"][k] for k in ("name", "url", "licence", "credit")}, "edition": edition,
              "retrieved": today, "sha256": hashlib.sha256(canon).hexdigest()}
    doc = {"type": "FeatureCollection", "kind": "licence", "source": source, "features": features}
    if errs := list(validator().iter_errors(doc)):
        raise ReadRefused(f"the read is not area/1: {errs[0].message}")
    return doc


def _content(doc: dict) -> tuple:
    """What a read changes: the licences and the configured terms, not the read's date or edition."""
    s = doc["source"]
    return (s["name"], s["url"], s["licence"], s["credit"], s["sha256"])


def read_to_file(cc: str, get, today: str, areas_dir: Path = paths.AREAS_DIR) -> dict:
    """Read one country and write areas/licence/<cc>.geojson unless a guard refuses or nothing changed.
    Returns the summary {country, status: written|unchanged|refused, before, after, added, removed, retrieved,
    finding}; a refused read leaves the committed file byte-identical."""
    out = areas_dir / "licence" / f"{cc.lower()}.geojson"
    old = json.loads(out.read_text()) if out.exists() else None
    before = {f["properties"]["area_id"] for f in old["features"]} if old else set()
    summary = {"country": cc.upper(), "file": out.relative_to(areas_dir).as_posix() if out.is_relative_to(areas_dir)
               else str(out), "before": len(before), "after": len(before), "added": 0, "removed": 0,
               "retrieved": old["source"]["retrieved"] if old else None, "finding": None}
    try:
        cfg = read_config(cc, areas_dir)
        doc = read_licences(cfg, get, today)
        after = {f["properties"]["area_id"] for f in doc["features"]}
        missing = before - after
        if len(missing) > SHRINK * len(before):
            raise ReadRefused(f"{len(missing)} of the {len(before)} committed licences are missing from the read "
                              f"(more than a fifth), e.g. {min(missing, key=natural)}; read {len(after)}")
    except ReadRefused as e:
        return {**summary, "status": "refused", "finding": str(e)}
    summary.update(after=len(after), added=len(after - before), removed=len(missing))
    if old and _content(old) == _content(doc):
        return {**summary, "status": "unchanged"}
    out.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {**summary, "status": "written", "retrieved": today}


def pr_text(summaries: list[dict], today: str) -> tuple[str, str]:
    """The `areas` workflow's pull request: title and body, the count before and after per country."""
    rows = [f"| {s['country']} | {s['status']} | {s['before']} | {s['after']} | +{s['added']} -{s['removed']} | "
            f"{s['retrieved'] or '-'} |" for s in summaries]
    body = ("What a user can do after this merges: see the licences as the regulators state them on "
            f"{today}.\n\nWritten by the `areas` workflow (`osd areas read`); `check` gates it like any change. "
            "A pull request opened by the workflow does not start `check` by itself: close and reopen it.\n\n"
            "| Country | Read | Licences before | After | Change | Retrieved |\n|---|---|---|---|---|---|\n"
            + "\n".join(rows) + "\n")
    return f"Licences read {today}", body


def issue_text(s: dict, today: str) -> tuple[str, str]:
    """The standing issue of a country whose read was refused, and the comment for this run."""
    comment = (f"{today}: the read of {s['country']} was refused; `{s['file']}` stays as read on "
               f"{s['retrieved'] or 'never'}.\n\nFinding: {s['finding']}\n")
    return f"Licences: {s['country']} read refused", comment


def http_get(pause: float = 1.0, retries: int = 2, wait: float = 15.0, opener=None, sleep=None):
    """`get` for osd areas read: GET with a generic client name, robots.txt obeyed (RFC 9309; 4xx allows,
    anything else unreadable refuses), one request at a time with a pause per request. A request with no
    answer or a 5xx is tried again `retries` times after `wait` seconds (Sodir closed a page's connection
    on the first workflow run, 25 Nov); a 4xx is final."""
    import time
    import urllib.error
    import urllib.request
    from urllib.parse import urlsplit

    from .verifier import layers
    from .verifier import robots as robots_txt

    rules: dict = {}

    sleep = sleep or time.sleep

    def fetch(url: str) -> bytes:
        if opener:
            return opener(url)
        req = urllib.request.Request(url, headers={"User-Agent": READ_AGENT})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()

    def again(url: str) -> bytes:
        for k in range(retries + 1):
            try:
                return fetch(url)
            except urllib.error.HTTPError as e:
                if e.code < 500 or k == retries:
                    raise
            except (urllib.error.URLError, OSError):
                if k == retries:
                    raise
            sleep(wait)
        raise AssertionError("unreachable")

    def get(url: str) -> bytes:
        u = urlsplit(url)
        host = f"{u.scheme}://{u.netloc}"
        if host not in rules:
            try:
                rules[host] = robots_txt.parse(fetch(host + "/robots.txt").decode("utf-8", "replace"),
                                               READ_AGENT.split("/")[0])
            except urllib.error.HTTPError as e:
                rules[host] = robots_txt.Rules() if 400 <= e.code < 500 else robots_txt.Rules.disallow_all()
            except (urllib.error.URLError, OSError):
                rules[host] = robots_txt.Rules.disallow_all()
        if not rules[host].allowed(url):
            raise layers.Incomplete(f"robots.txt does not allow {url}")
        sleep(pause)
        try:
            return again(url)
        except urllib.error.HTTPError as e:
            raise layers.Incomplete(f"HTTP {e.code} for {url}") from None
        except (urllib.error.URLError, OSError) as e:
            raise layers.Incomplete(f"no answer for {url}: {e}") from None

    return get
