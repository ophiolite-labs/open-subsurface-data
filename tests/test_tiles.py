"""E50 (R-S7, the speed practices of Shop 06): what the built tile archives must hold so the map
stays quick. Practice 1: every tile under 500 KB, the cap tippecanoe's `--drop-densest-as-needed`
works to. Practice 6: one file with its index at the front: the root directory inside the first
16,384 bytes, tile data clustered by TileID, at most one level of leaf directories (PMTiles v3
spec). Read from the header and the directories only: a tile's size is its directory entry, so no
tile is decompressed. The gate checks the reader on the fixture outlines; the real archives in
site/data/ are read by `make check-full` (it builds them first), as the E36 tile comparison is."""
import gzip
import json
import os
import shutil
import struct
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "site" / "data"
ARCHIVES = ("outlines.pmtiles", "areas.pmtiles")  # areas.pmtiles from E46; read when the build writes it
TILE_CAP = 500 * 1024  # tippecanoe's default: "reduce it to under 500K"
ROOT_DIR_CAP = 16_384  # PMTiles v3: the root directory "MUST be contained in the first 16,384 bytes"


def _varint(b: bytes, i: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 0x7F) << shift
        if c < 0x80:
            return n, i
        shift += 7


def _zxy(tid: int) -> int:
    """The zoom of a Hilbert TileID."""
    z, acc = 0, 0
    while tid >= acc + 4 ** z:
        acc += 4 ** z
        z += 1
    return z


@dataclass
class Layout:
    root_end: int
    clustered: bool
    min_zoom: int
    max_zoom: int
    leaf_depth: int = 0
    tiles: int = 0
    largest: dict[int, int] = field(default_factory=dict)  # zoom -> largest tile bytes
    over_cap: list[tuple[int, int]] = field(default_factory=list)  # (zoom, bytes)


def read_layout(path: Path) -> Layout:
    """The header and every directory of a PMTiles v3 archive (no tile data is read)."""
    with path.open("rb") as fh:
        head = fh.read(127)
        assert head[:7] == b"PMTiles" and head[7] == 3, f"{path.name}: not PMTiles v3"
        root_off, root_len, _, _, leaf_off, leaf_len = struct.unpack_from("<6Q", head, 8)
        clustered, internal = head[96], head[97]
        min_zoom, max_zoom = head[100], head[101]
        unz = gzip.decompress if internal == 2 else (lambda x: x)
        assert internal in (1, 2), f"{path.name}: internal compression {internal} not read here"
        fh.seek(leaf_off)
        leaves = fh.read(leaf_len)
        fh.seek(root_off)
        root = fh.read(root_len)
    out = Layout(root_end=root_off + root_len, clustered=clustered == 1, min_zoom=min_zoom, max_zoom=max_zoom)

    def walk(raw: bytes, depth: int) -> None:
        d = unz(raw)
        n, i = _varint(d, 0)
        cols = []
        for _ in range(4):
            col = []
            for _ in range(n):
                v, i = _varint(d, i)
                col.append(v)
            cols.append(col)
        tid, prev = 0, None
        for k in range(n):
            tid += cols[0][k]
            run, length, o = cols[1][k], cols[2][k], cols[3][k]
            o = prev[0] + prev[1] if o == 0 and k > 0 else o - 1
            prev = (o, length)
            if run == 0:
                out.leaf_depth = max(out.leaf_depth, depth + 1)
                walk(leaves[o:o + length], depth + 1)
                continue
            z = _zxy(tid)
            out.tiles += run
            out.largest[z] = max(out.largest.get(z, 0), length)
            if length >= TILE_CAP:
                out.over_cap.append((z, length))

    walk(root, 0)
    return out


def report(name: str, lay: Layout) -> str:
    sizes = ", ".join(f"z{z} {b / 1024:.0f} KB" for z, b in sorted(lay.largest.items()))
    return (f"{name}: {lay.tiles} tiles z{lay.min_zoom}-{lay.max_zoom}, clustered={lay.clustered}, "
            f"leaf levels {lay.leaf_depth}, root directory ends at byte {lay.root_end}, "
            f"{len(lay.over_cap)} tiles >= 500 KB; largest per zoom: {sizes}")


def _assert_layout(lay: Layout, name: str) -> None:
    assert lay.root_end <= ROOT_DIR_CAP, f"{name}: root directory ends at byte {lay.root_end}"
    assert lay.clustered, f"{name}: tile data not clustered by TileID"
    assert lay.leaf_depth <= 1, f"{name}: {lay.leaf_depth} levels of leaf directories"


# ---- The gate: the reader over a fixture archive written by write_tiles ----------------------------

_needs_tippecanoe = pytest.mark.skipif(not (shutil.which("tippecanoe") or os.environ.get("CI")),
                                       reason="tippecanoe not installed (CI installs it)")


@_needs_tippecanoe
def test_fixture_archive_has_its_index_at_the_front_and_small_tiles(tmp_path):
    from test_build import _fixture_outlines  # tests/ is on the path (rootdir conftest)

    from osd.build import write_tiles

    out = tmp_path / "catalog"
    out.mkdir()
    (out / "outlines.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": _fixture_outlines()}))
    tiles = write_tiles(out, cache_dir=tmp_path / "tiles")
    lay = read_layout(tiles)
    print(report(tiles.name, lay))
    _assert_layout(lay, tiles.name)
    assert lay.tiles > 0 and lay.max_zoom == 12
    assert not lay.over_cap


def test_reader_finds_a_leaf_level_and_an_oversized_tile(tmp_path):
    """A hand-written archive: a root that points to one leaf directory holding two tiles, one of
    them 600 KB, so the reader's leaf depth and size cap are tested without tippecanoe."""
    def enc(n: int) -> bytes:
        b = bytearray()
        while True:
            c, n = n & 0x7F, n >> 7
            b.append(c | (0x80 if n else 0))
            if not n:
                return bytes(b)

    def directory(entries):  # (tile id, run, length, offset)
        cols = [[], [], [], []]
        last = 0
        for tid, run, length, off in entries:
            cols[0].append(tid - last)
            last = tid
            cols[1].append(run)
            cols[2].append(length)
            cols[3].append(off + 1)
        return enc(len(entries)) + b"".join(enc(v) for c in cols for v in c)

    leaf = directory([(1, 1, 10, 0), (2, 1, 600 * 1024, 10)])
    root = directory([(0, 0, len(leaf), 0)])
    head = bytearray(127)
    head[:8] = b"PMTiles\x03"
    struct.pack_into("<6Q", head, 8, 127, len(root), 0, 0, 127 + len(root), len(leaf))
    head[96], head[97], head[100], head[101] = 1, 1, 0, 1
    p = tmp_path / "t.pmtiles"
    p.write_bytes(bytes(head) + root + leaf)
    lay = read_layout(p)
    assert (lay.leaf_depth, lay.tiles, lay.clustered) == (1, 2, True)
    assert lay.over_cap == [(1, 600 * 1024)]
    assert lay.largest == {1: 600 * 1024}


# ---- The real archives, as `make build` stages them (make check-full) -----------------------------

def _built(name: str) -> Path:
    p = SITE_DATA / name
    if not p.exists():
        pytest.skip(f"no site/data/{name} (make build with tippecanoe writes it)")
    return p


@pytest.mark.full
@pytest.mark.parametrize("name", ARCHIVES)
def test_built_archive_has_its_index_at_the_front(name):
    """Practice 6: clustered, one leaf level, the root directory in the first 16 KiB."""
    p = _built(name)
    lay = read_layout(p)
    print(report(name, lay))
    _assert_layout(lay, name)


@pytest.mark.full
@pytest.mark.parametrize("name", ARCHIVES)
def test_built_archive_tiles_are_under_500_kb(name):
    """Practice 1: every tile under 500 KB, thinned where dense."""
    p = _built(name)
    lay = read_layout(p)
    print(report(name, lay))
    assert not lay.over_cap, f"{name}: {len(lay.over_cap)} tiles >= 500 KB, the largest {max(b for _, b in lay.over_cap)} bytes"


if __name__ == "__main__":  # `uv run python tests/test_tiles.py [archive ...]`: the report alone
    import sys

    for a in sys.argv[1:] or [str(SITE_DATA / n) for n in ARCHIVES if (SITE_DATA / n).exists()]:
        print(report(Path(a).name, read_layout(Path(a))))
