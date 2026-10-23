import collections
import json
import os
import shutil

import pytest

from osd.build import build, write_tiles
from osd.records import load_records


def test_build_joins_records_outlines_and_levels(tmp_path):
    vdir = tmp_path / "verification"
    vdir.mkdir()
    (vdir / "equinor__volve.json").write_text(json.dumps(
        {"record_id": "equinor/volve", "checked_at": "2026-10-23T12:00:00+00:00",
         "tool_version": "t", "level": "L1", "checks": []}))
    out = tmp_path / "catalog"
    n = build(out, vdir)
    assert n["records"] == len(load_records())
    recs = {r["id"]: r for r in json.loads((out / "records.json").read_text())["records"]}
    assert recs["equinor/volve"]["level"] == "L1"
    assert recs["nlog/nlog"]["level"] == "L0"
    fc = json.loads((out / "outlines.geojson").read_text())
    volve = [f for f in fc["features"] if f["properties"]["record_id"] == "equinor/volve"]
    assert volve and volve[0]["properties"]["level"] == "L1"
    assert volve[0]["properties"]["licence"] == "Equinor Open Data Licence"
    cols = json.loads((out / "collections.json").read_text())["collections"]
    assert any(c["license"] == "CC-BY-SA-4.0" for c in cols)


# E15: tiles. A minimal PMTiles v3 and Mapbox Vector Tile reader, enough to count features and read
# their properties at one zoom; geometry is skipped.

def _varint(b, i):
    n = shift = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 0x7F) << shift
        if c < 0x80:
            return n, i
        shift += 7


def _fields(b):
    """(field number, value) for every field of one protobuf message; length-delimited as bytes."""
    i, end = 0, len(b)
    while i < end:
        key, i = _varint(b, i)
        f, wire = key >> 3, key & 7
        if wire == 0:
            v, i = _varint(b, i)
        elif wire == 2:
            n, i = _varint(b, i)
            v, i = b[i:i + n], i + n
        elif wire == 5:
            v, i = b[i:i + 4], i + 4
        elif wire == 1:
            v, i = b[i:i + 8], i + 8
        else:
            raise ValueError(f"wire type {wire}")
        yield f, v


def _value(b):
    import struct
    for f, v in _fields(b):
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


def _tiles_at(path, z):
    """Decoded tile bytes for every tile at zoom z."""
    import gzip
    import struct
    data = path.read_bytes()
    assert data[:7] == b"PMTiles" and data[7] == 3
    root_off, root_len, _, _, leaf_off, _, tile_off = struct.unpack_from("<7Q", data, 8)
    internal, tile_comp = data[97], data[98]
    unz = (lambda x: gzip.decompress(x)) if internal == 2 else (lambda x: x)
    tunz = (lambda x: gzip.decompress(x)) if tile_comp == 2 else (lambda x: x)
    lo = sum(4 ** k for k in range(z))
    hi = lo + 4 ** z

    def walk(off, length):
        d = unz(data[off:off + length])
        n, i = _varint(d, 0)
        cols = []
        for _ in range(4):
            col = []
            for _ in range(n):
                v, i = _varint(d, i)
                col.append(v)
            cols.append(col)
        tid = 0
        prev = None
        for k in range(n):
            tid += cols[0][k]
            run, length_k, o = cols[1][k], cols[2][k], cols[3][k]
            o = prev[0] + prev[1] if o == 0 and k > 0 else o - 1
            prev = (o, length_k)
            if run == 0:
                yield from walk(leaf_off + o, length_k)
            elif tid < hi and tid + run > lo:
                yield tunz(data[tile_off + o:tile_off + o + length_k])

    yield from walk(root_off, root_len)


def _features(tile):
    """(layer name, properties) for every feature in one tile."""
    for f, layer in _fields(tile):
        if f != 3:
            continue
        name, keys, values, feats = None, [], [], []
        for lf, v in _fields(layer):
            if lf == 1:
                name = v.decode()
            elif lf == 2:
                feats.append(v)
            elif lf == 3:
                keys.append(v.decode())
            elif lf == 4:
                values.append(_value(v))
        for feat in feats:
            tags = next((v for ff, v in _fields(feat) if ff == 2), b"")
            ix, i = [], 0
            while i < len(tags):
                t, i = _varint(tags, i)
                ix.append(t)
            yield name, {keys[ix[j]]: values[ix[j + 1]] for j in range(0, len(ix), 2)}


def _identity(p):
    return p.get("feature_id") or (p["record_id"], p["kind"], p["name"])


_needs_tippecanoe = pytest.mark.skipif(not (shutil.which("tippecanoe") or os.environ.get("CI")),
                                       reason="tippecanoe not installed (CI installs it)")


@_needs_tippecanoe
def test_tiles_hold_every_feature_with_its_properties_at_max_zoom(tmp_path):
    out = tmp_path / "catalog"
    build(out)  # the real catalogue, as `make build` writes it; tiling is cached by content
    tiles = write_tiles(out)
    assert tiles is not None, "tippecanoe must be installed where CI is set"
    want = {}
    for f in json.loads((out / "outlines.geojson").read_text())["features"]:
        want[_identity(f["properties"])] = f["properties"]
    assert len(want) == len(json.loads((out / "outlines.geojson").read_text())["features"]), "identities are unique"
    seen = {}
    for tile in _tiles_at(tiles, 12):
        for layer, props in _features(tile):
            assert layer == "outlines"
            seen.setdefault(_identity(props), props)
    def by_kind(d):
        return collections.Counter(p["kind"] for p in d.values())
    print("features at z12 per kind:", dict(by_kind(seen)), "geojson:", dict(by_kind(want)))
    assert by_kind(seen) == by_kind(want)
    assert seen.keys() == want.keys()
    for k, p in want.items():  # tippecanoe writes arrays as JSON text; MVT has no array value
        got = {a: json.loads(v) if isinstance(p.get(a), list) else v for a, v in seen[k].items()}
        assert got == p, k


def test_build_without_tippecanoe_prints_the_notice_and_writes_no_tiles(tmp_path, monkeypatch, capsys):
    out = tmp_path / "catalog"
    build(out)
    (out / "outlines.pmtiles").write_bytes(b"stale")
    monkeypatch.setenv("PATH", str(tmp_path))  # no tippecanoe on it
    assert write_tiles(out, cache_dir=tmp_path / "tiles") is None
    assert "notice: tippecanoe not found" in capsys.readouterr().err
    assert not (out / "outlines.pmtiles").exists()
    assert (out / "outlines.geojson").exists()


# E09: snapshot identity. records.json `catalog` names the commits and a digest of the records array.

FIDELITY = os.path.join(os.path.dirname(__file__), "fixtures", "fidelity")
SRC, VER = "1" * 40, "2" * 40


def _fixture_build(tmp_path, name="catalog", now=None, vdir=None, records_dir=None):
    from datetime import UTC, datetime
    from pathlib import Path
    out = tmp_path / name
    build(out, Path(vdir or os.path.join(FIDELITY, "verification")),
          now=now or datetime(2026, 10, 23, 12, tzinfo=UTC), mirror_dir=tmp_path / "no-mirror",
          records_dir=Path(records_dir or os.path.join(FIDELITY, "records")), source_commit=SRC, verification_commit=VER)
    return json.loads((out / "records.json").read_text())


def test_records_json_carries_catalog_identity(tmp_path):
    import hashlib
    doc = _fixture_build(tmp_path)
    cat = doc["catalog"]
    assert set(cat) == {"source_commit", "verification_commit", "built_at", "records_digest"}
    assert (cat["source_commit"], cat["verification_commit"], cat["built_at"]) == (SRC, VER, "2026-10-23T12:00:00Z")
    canonical = json.dumps(doc["records"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert cat["records_digest"] == hashlib.sha256(canonical.encode()).hexdigest()


def test_records_digest_same_for_same_inputs(tmp_path):
    from datetime import UTC, datetime
    a = _fixture_build(tmp_path, "a", now=datetime(2026, 10, 23, 12, tzinfo=UTC))
    b = _fixture_build(tmp_path, "b", now=datetime(2026, 10, 23, 12, 5, tzinfo=UTC))
    assert a["catalog"]["built_at"] != b["catalog"]["built_at"]
    assert a["catalog"]["records_digest"] == b["catalog"]["records_digest"]


def test_records_digest_changes_with_a_record_or_the_verification(tmp_path):
    base = _fixture_build(tmp_path, "base")["catalog"]["records_digest"]
    recs = tmp_path / "records"
    shutil.copytree(os.path.join(FIDELITY, "records"), recs)
    p = recs / "acme" / "two-wells.yaml"
    p.write_text(p.read_text().replace("Two synthetic wells", "Two synthetic wells, renamed"))
    edited = _fixture_build(tmp_path, "edited", records_dir=recs)["catalog"]["records_digest"]
    vdir = tmp_path / "verification"
    shutil.copytree(os.path.join(FIDELITY, "verification"), vdir)
    v = vdir / "acme__two-wells.json"
    v.write_text(v.read_text().replace('"checked_at": "2026-10-23T09:00:00+00:00"', '"checked_at": "2026-10-23T10:00:00+00:00"'))
    reverified = _fixture_build(tmp_path, "reverified", vdir=vdir)["catalog"]["records_digest"]
    assert len({base, edited, reverified}) == 3
