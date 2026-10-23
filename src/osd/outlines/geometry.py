"""Hulls, CRS transforms and coordinate units for derived outlines."""

from __future__ import annotations

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
