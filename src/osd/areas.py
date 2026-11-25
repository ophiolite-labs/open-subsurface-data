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
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from . import paths
from .records import Problem, geometry_problems, load_outline

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


def validate_areas(areas_dir: Path = paths.AREAS_DIR) -> list[Problem]:
    """Each area file against area/1, in the place its kind says, with valid WGS84 rings cut at +-180;
    area_id unique within a kind across its files; a province's or licence's country is a country area
    when countries are committed."""
    problems: list[Problem] = []
    v = validator()
    seen: dict[tuple[str, str], str] = {}
    countries: set[str] | None = None
    owners: list[tuple[str, int, str]] = []
    for p in area_files(areas_dir):
        rel = p.relative_to(areas_dir).as_posix()
        try:
            doc = json.loads(p.read_text())
        except (OSError, ValueError) as e:
            problems.append(Problem(rel, f"unreadable: {e}"))
            continue
        errs = sorted(v.iter_errors(doc), key=lambda e: list(e.path))
        for err in errs:
            where = "/".join(str(x) for x in err.path) or "<root>"
            problems.append(Problem(rel, f"{where}: {err.message}"))
        kind = doc.get("kind") if isinstance(doc, dict) else None
        if file_kind(rel) != kind:
            problems.append(Problem(rel, f"kind {kind!r} does not match the file path (areas/<kind>.geojson "
                                         "or areas/<kind>/<name>.geojson)"))
        if errs:
            continue
        if kind == "country":
            countries = (countries or set()) | {f["properties"]["area_id"] for f in doc["features"]}
        for i, f in enumerate(doc["features"]):
            aid = f["properties"]["area_id"]
            for msg in geometry_problems(f["geometry"]):
                problems.append(Problem(rel, f"feature {i} ({aid}): {msg}"))
            if not geometry_problems(f["geometry"]) and wide_edges(f["geometry"]):
                problems.append(Problem(rel, f"feature {i} ({aid}): an edge steps more than 180 degrees of "
                                             "longitude; cut it at +-180 (RFC 7946 3.1.9)"))
            if (kind, aid) in seen:
                problems.append(Problem(rel, f"feature {i}: area_id '{aid}' repeated in kind {kind} "
                                             f"(also {seen[(kind, aid)]})"))
            seen.setdefault((kind, aid), rel)
            if "country" in f["properties"]:
                owners.append((rel, i, f["properties"]["country"]))
    if countries is not None:
        for rel, i, c in owners:
            if c not in countries:
                problems.append(Problem(rel, f"feature {i}: country '{c}' is not a country area"))
    return problems


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


def write(out_dir: Path, records_out: list[dict], records: dict[str, dict], outlines_dir: Path,
          areas_dir: Path = paths.AREAS_DIR) -> dict:
    """Write areas.json and areas-<kind>.geojson into out_dir and set records_out[].areas (every index
    kind) when any area file is committed. Returns {kind: number of areas that hold a dataset}."""
    areas = AreaSet.load(areas_dir)
    for old in out_dir.glob("areas-*.geojson"):
        old.unlink()
    if areas.files:
        outlines = {}
        for rid in records:
            op = paths.outline_path(rid, outlines_dir)
            outlines[rid] = load_outline(op) if op.exists() else None
        placed = count(records, outlines, areas)
        for r in records_out:
            r["areas"] = placed[r["id"]]
    else:
        placed = {rid: {k: [] for k in CORE} for rid in records}
    doc, drawn = index_and_drawn(areas, placed)
    (out_dir / "areas.json").write_text(dumps_index(doc))
    for k, fc in drawn.items():
        (out_dir / f"areas-{k}.geojson").write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {k: len(v["areas"]) for k, v in doc["kinds"].items()}
