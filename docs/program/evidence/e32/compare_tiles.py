"""Compare every feature of outlines.pmtiles at z12 with outlines.geojson, both directions (E32).

    uv run python docs/program/evidence/e32/compare_tiles.py site/data/outlines.geojson site/data/outlines.pmtiles

For each GeoJSON feature (identity: `feature_id`, else record_id, kind, name) the z12 tiles must hold
it with the same id, kind, title and every other property (arrays come back as JSON text: MVT has
no array value), the same geometry type, and:
  - a point: the decoded position equal to the GeoJSON position on the z12 tile grid, exactly, as
    tippecanoe rounds it (world units of 2^12 tiles x extent 4096; one unit is 360 / 2^24 = 2.1e-5
    degrees of longitude, so MVT at z12 cannot hold 1e-6 degrees; the script reports the largest
    difference in degrees as well);
  - a line or polygon: the union of its pieces' extents equal to the GeoJSON extent within one grid
    unit (pieces are clipped at tile buffers, so vertices differ; the extent does not).
Every tile feature must be a GeoJSON feature (no feature the GeoJSON lacks, no altered identity).
Prints the counts and every difference; exit status 1 when there is one.
"""

from __future__ import annotations

import gzip
import json
import math
import struct
import sys
from collections import defaultdict
from pathlib import Path

Z = 12
TYPES = {1: "Point", 2: "LineString", 3: "Polygon"}
GEO = {"Point": "Point", "MultiPoint": "Point", "LineString": "LineString", "MultiLineString": "LineString",
       "Polygon": "Polygon", "MultiPolygon": "Polygon"}


def varint(b, i):
    n = shift = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 0x7F) << shift
        if c < 0x80:
            return n, i
        shift += 7


def fields(b):
    i, end = 0, len(b)
    while i < end:
        key, i = varint(b, i)
        f, wire = key >> 3, key & 7
        if wire == 0:
            v, i = varint(b, i)
        elif wire == 2:
            n, i = varint(b, i)
            v, i = b[i:i + n], i + n
        elif wire == 5:
            v, i = b[i:i + 4], i + 4
        elif wire == 1:
            v, i = b[i:i + 8], i + 8
        else:
            raise ValueError(f"wire type {wire}")
        yield f, v


def value(b):
    for f, v in fields(b):
        if f == 1:
            return v.decode()
        if f == 2:
            return struct.unpack("<f", v)[0]
        if f == 3:
            return struct.unpack("<d", v)[0]
        if f in (4, 5):
            return v
        if f == 6:
            return (v >> 1) ^ -(v & 1)
        if f == 7:
            return bool(v)


def zxy(tid):
    """PMTiles v3 tile id (Hilbert order per zoom) to (z, x, y)."""
    acc, z = 0, 0
    while acc + 4 ** z <= tid:
        acc += 4 ** z
        z += 1
    t, n, x, y, s = tid - acc, 2 ** z, 0, 0, 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x, y = s - 1 - x, s - 1 - y
            x, y = y, x
        x, y = x + s * rx, y + s * ry
        t //= 4
        s *= 2
    return z, x, y


def tiles(path: Path, z: int):
    """(x, y, tile bytes) for every tile at zoom z, run-length entries expanded."""
    data = path.read_bytes()
    assert data[:7] == b"PMTiles" and data[7] == 3
    root_off, root_len, _, _, leaf_off, _, tile_off = struct.unpack_from("<7Q", data, 8)
    internal, tile_comp = data[97], data[98]
    unz = gzip.decompress if internal == 2 else (lambda x: x)
    tunz = gzip.decompress if tile_comp == 2 else (lambda x: x)
    lo, hi = sum(4 ** k for k in range(z)), sum(4 ** k for k in range(z + 1))

    def walk(off, length):
        d = unz(data[off:off + length])
        n, i = varint(d, 0)
        cols = []
        for _ in range(4):
            col = []
            for _ in range(n):
                v, i = varint(d, i)
                col.append(v)
            cols.append(col)
        tid, prev = 0, None
        for k in range(n):
            tid += cols[0][k]
            run, length_k, o = cols[1][k], cols[2][k], cols[3][k]
            o = prev[0] + prev[1] if o == 0 and k > 0 else o - 1
            prev = (o, length_k)
            if run == 0:
                yield from walk(leaf_off + o, length_k)
            elif tid < hi and tid + run > lo:
                body = tunz(data[tile_off + o:tile_off + o + length_k])
                for t in range(max(tid, lo), min(tid + run, hi)):
                    _, x, y = zxy(t)
                    yield x, y, body

    yield from walk(root_off, root_len)


def geometry(cmds):
    """MVT geometry commands to a flat list of (x, y) tile-local positions."""
    out, i, cx, cy = [], 0, 0, 0
    while i < len(cmds):
        cmd, count = cmds[i] & 7, cmds[i] >> 3
        i += 1
        if cmd == 7:
            continue
        for _ in range(count):
            dx, dy = cmds[i], cmds[i + 1]
            i += 2
            cx += (dx >> 1) ^ -(dx & 1)
            cy += (dy >> 1) ^ -(dy & 1)
            out.append((cx, cy))
    return out


def features(x, y, tile):
    """(properties, geometry type, world-unit positions) for every feature of one tile."""
    for f, layer in fields(tile):
        if f != 3:
            continue
        keys, values, feats, extent = [], [], [], 4096
        for lf, v in fields(layer):
            if lf == 2:
                feats.append(v)
            elif lf == 3:
                keys.append(v.decode())
            elif lf == 4:
                values.append(value(v))
            elif lf == 5:
                extent = v
        for feat in feats:
            tags, gtype, cmds = b"", 0, []
            for ff, v in fields(feat):
                if ff == 2:
                    tags = v
                elif ff == 3:
                    gtype = v
                elif ff == 4:
                    j = 0
                    while j < len(v):
                        c, j = varint(v, j)
                        cmds.append(c)
            ix, i = [], 0
            while i < len(tags):
                t, i = varint(tags, i)
                ix.append(t)
            props = {keys[ix[j]]: values[ix[j + 1]] for j in range(0, len(ix), 2)}
            pts = [(x * extent + px, y * extent + py) for px, py in geometry(cmds)]
            yield props, TYPES.get(gtype), pts, extent


def world(lon, lat, scale):
    s = math.sin(math.radians(max(min(lat, 85.0511287798), -85.0511287798)))
    return (lon + 180) / 360 * scale, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * scale


def cround(v):
    """C's round(): halves away from zero."""
    return math.floor(v + 0.5) if v >= 0 else -math.floor(-v + 0.5)


def grid(lon, lat, scale):
    """Where tippecanoe puts a position on the grid: rounded to the 2^32 world (projection.cpp
    lonlat2tile), then rounded to the tile grid (clip.cpp to_tile_scale)."""
    lat_rad = math.radians(lat)
    x32 = cround(2 ** 32 * ((lon + 180) / 360))
    y32 = cround(2 ** 32 * (1 - (math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi)) / 2)
    shift = 2 ** 32 / scale
    return cround(x32 / shift), cround(y32 / shift)


def lonlat(wx, wy, scale):
    return wx / scale * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * wy / scale))))


def positions(c):
    if c and isinstance(c[0], (int, float)):
        yield c
    else:
        for x in c:
            yield from positions(x)


def identity(p):
    return p.get("feature_id") or (p["record_id"], p["kind"], p["name"])


def main(geojson: Path, pmtiles: Path) -> int:
    want = {}
    for f in json.loads(geojson.read_text())["features"]:
        k = identity(f["properties"])
        assert k not in want, f"identity {k} twice in the GeoJSON"
        want[k] = f
    seen_props, seen_type, seen_pts = {}, {}, defaultdict(list)
    problems, extent_seen, pieces = [], set(), 0
    for x, y, tile in tiles(pmtiles, Z):
        for props, gtype, pts, extent in features(x, y, tile):
            pieces += 1
            extent_seen.add(extent)
            k = identity(props)
            if k not in want:
                problems.append(f"tile {Z}/{x}/{y}: feature {k!r} is no GeoJSON feature ({props.get('record_id')})")
                continue
            if k in seen_props and seen_props[k] != props:
                problems.append(f"{k}: two pieces carry different properties")
            seen_props.setdefault(k, props)
            seen_type.setdefault(k, set()).add(gtype)
            seen_pts[k] += pts
    assert len(extent_seen) == 1, extent_seen
    scale = 2 ** Z * extent_seen.pop()
    max_units, max_deg, polys = 0.0, 0.0, 0
    for k, f in want.items():
        p = f["properties"]
        if k not in seen_props:
            problems.append(f"{k}: in the GeoJSON, in no z{Z} tile")
            continue
        got = {a: json.loads(v) if isinstance(p.get(a), list) else v for a, v in seen_props[k].items()}
        for a in ("feature_id", "kind", "title"):
            if got.get(a) != p.get(a):
                problems.append(f"{k}: {a} {got.get(a)!r} in the tile, {p.get(a)!r} in the GeoJSON")
        if got != p:
            diff = sorted(a for a in set(got) | set(p) if got.get(a) != p.get(a))
            problems.append(f"{k}: properties differ in {diff}")
        gtype = GEO[f["geometry"]["type"]]
        if seen_type[k] != {gtype}:
            problems.append(f"{k}: geometry {seen_type[k]} in the tile, {gtype} in the GeoJSON")
            continue
        exp = [world(lon, lat, scale) for lon, lat, *_ in positions(f["geometry"]["coordinates"])]
        pts = seen_pts[k]
        if gtype == "Point":
            for (ex, ey), (lon, lat, *_) in zip(exp, positions(f["geometry"]["coordinates"])):
                gx, gy = min(pts, key=lambda q: (q[0] - ex) ** 2 + (q[1] - ey) ** 2)
                if (gx, gy) != grid(lon, lat, scale):
                    problems.append(f"{k}: point at grid ({gx}, {gy}), GeoJSON on grid {grid(lon, lat, scale)}")
                glon, glat = lonlat(gx, gy, scale)
                max_deg = max(max_deg, abs(glon - lon), abs(glat - lat))
                max_units = max(max_units, abs(gx - ex), abs(gy - ey))
        else:
            polys += 1
            ebox = (min(q[0] for q in exp), min(q[1] for q in exp), max(q[0] for q in exp), max(q[1] for q in exp))
            inside = [q for q in pts if 0 <= q[0] <= scale] or pts   # not the copies past the antimeridian
            gbox = (min(q[0] for q in inside), min(q[1] for q in inside), max(q[0] for q in inside), max(q[1] for q in inside))
            worst = max(abs(a - b) for a, b in zip(ebox, gbox))
            if worst > 1:
                problems.append(f"{k}: extent {gbox} in the tiles, {tuple(round(v, 1) for v in ebox)} in the GeoJSON")
    print(f"geojson features: {len(want)}; z{Z} pieces: {pieces}; features found in tiles: {len(seen_props)}; "
          f"lines and polygons compared by extent: {polys}")
    print(f"points: largest offset from the GeoJSON position {max_units:.3f} grid units, {max_deg:.2e} degrees "
          f"(grid unit {360 / scale:.2e} degrees of longitude)")
    print(f"differences: {len(problems)}")
    for line in problems[:200]:
        print("  " + line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
