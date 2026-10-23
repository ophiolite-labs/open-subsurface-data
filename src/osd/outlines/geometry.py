"""Hulls, CRS transforms and coordinate units for derived outlines."""

from __future__ import annotations

import itertools
import math
from functools import cache

from pyproj import CRS, Transformer

DECIMALS = 6  # 0.11 m at the equator: below any publisher's stated precision
UNIT_NAMES = {"metre": "m", "foot": "ft", "US survey foot": "ftUS", "degree": "degree"}


class Refused(Exception):
    """An input or a derivation the lane will not guess about; the message is the reason."""


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Andrew's monotone chain; counter-clockwise, first vertex not repeated, collinear dropped."""
    pts = sorted(set(points))
    if len(pts) < 3:
        raise Refused(f"a hull needs three distinct positions, got {len(pts)}")

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        raise Refused("every position lies on one line: no area to outline")
    return hull


def crs_units(crs: str) -> str:
    unit = CRS(crs).axis_info[0].unit_name
    return UNIT_NAMES.get(unit, unit)


@cache
def _transformer(crs: str) -> Transformer:
    return Transformer.from_crs(crs, "EPSG:4326", always_xy=True)


def to_wgs84(crs: str | None, units: str | None = None):
    """A function (x, y) -> [lon, lat] for coordinates served as (east, north) in `crs`.

    Refuses an undeclared CRS, and units that disagree with the CRS axis (no conversion is guessed).
    """
    if not crs:
        raise Refused("CRS not declared by the publisher (record input has no crs)")
    want = crs_units(crs)
    if units is not None and units != want:
        raise Refused(f"units {units} disagree with {crs}, whose axes are in {want}")
    t = _transformer(crs)

    def f(x: float, y: float) -> list[float]:
        lon, lat = t.transform(x, y)
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise Refused(f"({x}, {y}) in {crs} transforms outside WGS84: axis order or CRS is wrong")
        return [round(lon, DECIMALS), round(lat, DECIMALS)]

    return f


def map_positions(coords, f):
    """Apply f to every position of a GeoJSON coordinates array, any nesting."""
    if coords and isinstance(coords[0], (int, float)):
        return f(coords[0], coords[1])
    return [map_positions(c, f) for c in coords]


def closed_ring(vertices: list[list[float]]) -> list[list[float]]:
    return vertices + [vertices[0]]


def _dp(pts: list[list[float]], tol: float, kx: float, ky: float) -> list[list[float]]:
    """Douglas-Peucker on lon/lat scaled to metres around the ring (kx, ky metres per degree)."""
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay, bx, by = pts[a][0] * kx, pts[a][1] * ky, pts[b][0] * kx, pts[b][1] * ky
        dx, dy = bx - ax, by - ay
        n2 = dx * dx + dy * dy
        far, at = -1.0, -1
        for k in range(a + 1, b):
            px, py = pts[k][0] * kx - ax, pts[k][1] * ky - ay
            if n2:
                t = max(0.0, min(1.0, (px * dx + py * dy) / n2))
                d = math.hypot(px - t * dx, py - t * dy)
            else:
                d = math.hypot(px, py)
            if d > far:
                far, at = d, k
        if far > tol:
            keep[at] = True
            stack += [(a, at), (at, b)]
    return [p for p, k in zip(pts, keep) if k]


def _scale(ring: list[list[float]]) -> tuple[float, float]:
    lat = sum(p[1] for p in ring) / len(ring)
    return 111320.0 * math.cos(math.radians(lat)), 110540.0


def ring_area_m2(ring: list[list[float]]) -> float:
    """Shoelace area in the ring's local metre scaling."""
    kx, ky = _scale(ring)
    return abs(sum(a[0] * kx * b[1] * ky - b[0] * kx * a[1] * ky for a, b in itertools.pairwise(ring))) / 2


def _ring(ring: list[list[float]], tol: float) -> list[list[float]]:
    kx, ky = _scale(ring)
    # split the closed ring at its farthest vertex from the start so both halves have ends
    far = max(range(len(ring)), key=lambda k: math.hypot((ring[k][0] - ring[0][0]) * kx,
                                                         (ring[k][1] - ring[0][1]) * ky))
    if far == 0:
        return ring
    out = _dp(ring[:far + 1], tol, kx, ky)[:-1] + _dp(ring[far:], tol, kx, ky)
    return out if len(out) >= 4 else ring


def _polygon(rings: list, tol: float, exterior_only: bool) -> tuple[list | None, int]:
    """(simplified rings, rings dropped); None when the exterior itself is below tol²."""
    if tol and ring_area_m2(rings[0]) < tol * tol:
        return None, len(rings)
    holes = [] if exterior_only else [r for r in rings[1:] if not tol or ring_area_m2(r) >= tol * tol]
    return [_ring(r, tol) for r in [rings[0], *holes]], len(rings) - 1 - len(holes)


def _round(c: list, decimals: int) -> list:
    return [_round(x, decimals) for x in c] if isinstance(c[0], list) else [round(v, decimals) for v in c]


def simplify(g: dict, tol_m: float, exterior_only: bool = False, decimals: int = DECIMALS) -> tuple[dict, int]:
    """(geometry, rings dropped): every ring simplified to tol_m metres, rings whose area is
    below tol_m² dropped, every hole dropped when exterior_only, positions rounded to decimals
    (OSD-D16). A polygon whose exterior is dropped goes with its holes; a geometry with nothing
    left above tol_m² keeps its largest polygon's exterior."""
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    kept, dropped = [], 0
    for rings in polys:
        out, n = _polygon(rings, tol_m, exterior_only)
        dropped += n
        if out:
            kept.append(out)
    if not kept:
        big = max(polys, key=lambda rings: ring_area_m2(rings[0]))
        kept, dropped = [[_ring(big[0], tol_m)]], sum(len(r) for r in polys) - 1
    kept = _round(kept, decimals)
    if g["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": kept[0]}, dropped
    return {"type": "MultiPolygon", "coordinates": kept}, dropped
