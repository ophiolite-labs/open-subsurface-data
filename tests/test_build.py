import collections
import json
import os
import shutil
from pathlib import Path

import pytest

from osd.build import build, write_tiles
from osd.records import load_records


def test_build_joins_records_outlines_and_levels(tmp_path, records_subset):
    recs_dir = records_subset(["equinor/volve", "nlog/nlog", "terranubis/force-ml-2020-synthetic"])
    vdir = tmp_path / "verification"
    vdir.mkdir()
    (vdir / "equinor__volve.json").write_text(json.dumps(
        {"record_id": "equinor/volve", "checked_at": "2026-10-23T12:00:00+00:00",
         "tool_version": "t", "level": "L1", "checks": []}))
    out = tmp_path / "catalog"
    n = build(out, vdir, records_dir=recs_dir)
    assert n["records"] == len(load_records(recs_dir)) == 3
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


def _outlines_only(tmp_path, full_build):
    """A catalogue directory holding the session build's outlines.geojson, for tiling (E32)."""
    out = tmp_path / "catalog"
    out.mkdir()
    shutil.copyfile(full_build / "outlines.geojson", out / "outlines.geojson")
    return out


_needs_tippecanoe = pytest.mark.skipif(not (shutil.which("tippecanoe") or os.environ.get("CI")),
                                       reason="tippecanoe not installed (CI installs it)")


@_needs_tippecanoe
def test_tiles_hold_every_feature_with_its_properties_at_max_zoom(tmp_path, full_build):
    out = _outlines_only(tmp_path, full_build)  # the real catalogue's; tiling is cached by content
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


@_needs_tippecanoe
def test_crossing_strings_keep_their_own_features(tmp_path):
    """E32: two registers whose strings collide in tippecanoe's string pool before 2.55.0 (the
    fixture's README); the tile keeps every property of every feature. Red on 2.49.0 and 2.53.0."""
    out = tmp_path / "catalog"
    out.mkdir()
    shutil.copyfile(Path(__file__).parent / "fixtures" / "tiles" / "crossing.geojson", out / "outlines.geojson")
    tiles = write_tiles(out, cache_dir=tmp_path / "tiles")
    want = {(f["properties"]["record_id"], f["properties"]["name"]): f["properties"]
            for f in json.loads((out / "outlines.geojson").read_text())["features"]}
    seen = {}
    for tile in _tiles_at(tiles, 12):
        for _, props in _features(tile):
            seen.setdefault((props["record_id"], props["name"]), props)
    assert seen.keys() == want.keys()
    for k, p in want.items():
        got = {a: json.loads(v) if isinstance(p.get(a), list) else v for a, v in seen[k].items()}
        assert got == p, k


def test_both_workflows_install_the_pinned_tippecanoe():
    """E32: the check and the published site tile with the same release, the one TIPPECANOE_PIN names."""
    import re

    from osd.build import TIPPECANOE_PIN
    pins = set()
    for wf in ("ci.yml", "pages.yml"):
        text = (Path(__file__).parents[1] / ".github" / "workflows" / wf).read_text()
        deb = re.findall(r"tippecanoe_([0-9.]+)-[^/\s]*_amd64\.deb", text)
        sha = re.findall(r'echo "([0-9a-f]{64})  /tmp/tippecanoe\.deb" \| sha256sum -c', text)
        assert len(deb) == len(sha) == 1, wf
        pins.add((deb[0], sha[0]))
    assert len(pins) == 1 and next(iter(pins))[0] == TIPPECANOE_PIN


def test_build_without_tippecanoe_prints_the_notice_and_writes_no_tiles(tmp_path, monkeypatch, capsys, full_build):
    out = _outlines_only(tmp_path, full_build)
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


# E26: the record/4 kinds travel from a record to records.json and the STAC Collection keywords unchanged.

@pytest.mark.parametrize("kind", ["velocity-model", "geological-model", "airborne-em", "radiometrics", "stress"])
def test_new_kinds_travel_to_records_json_and_stac_keywords(tmp_path, kind):
    recs = tmp_path / "records"
    shutil.copytree(os.path.join(FIDELITY, "records"), recs)
    p = recs / "acme" / "two-wells.yaml"
    p.write_text(p.read_text().replace("kinds: [wellbore-logs]", f"kinds: [wellbore-logs, {kind}]"))
    doc = _fixture_build(tmp_path, records_dir=recs)
    (rec,) = [r for r in doc["records"] if r["id"] == "acme/two-wells"]
    assert rec["kinds"] == ["wellbore-logs", kind]
    cols = [json.loads(c.read_text()) for c in (tmp_path / "catalog" / "stac").rglob("collection.json")]
    (col,) = [c for c in cols if kind in c.get("keywords", [])]
    assert col["keywords"] == ["wellbore-logs", kind] and col["title"] == rec["title"]


# E27: why a record is at its level. One source (osd.reasons): records.json carries the string
# `osd status` prints, for every level, for blocked and for a record never verified.

SITE_VDIR = Path(__file__).parent / "fixtures" / "site" / "verification"
L4 = {"record_id": "opm/norne", "checked_at": "2026-10-23T14:10:00+00:00", "tool_version": "0.1.0", "level": "L4",
      "origin": {"http_status": 200, "final_url": "https://opm-project.org/", "reachability": "ok"},
      "checks": [{"name": "origin-reachable", "level": "L1", "outcome": "pass", "detail": "HTTP 200"},
                 {"name": "files-checksummed", "level": "L2", "outcome": "pass", "detail": "sample: 2 of 2 hashed"},
                 {"name": "canonical-conversion", "level": "L4", "outcome": "pass",
                  "detail": "2 of 2 inputs converted to kinds well-log, grid"}]}
WHY = {
    "bgs/single-onshore-borehole-index": "files-checksummed: no file address is published to us "
                                         "(no origin.manifest_url; access anonymous)",
    "nzpam/kerry-3d": "files-checksummed: no file address is published to us (no origin.manifest_url; access registration)",
    "gsq/qped": "files-checksummed: the listing (ckan) names no files",
    "ak-dggs/tax-credit-well-data": "files-checksummed: robots.txt disallows the listing https://dggs.alaska.gov/pubs/id/30000",
    "nm-ocd/oil-and-gas-wells": "origin-reachable: answers a browser, not the verifier (HTTP 404 to osd-verifier, "
                                "HTTP 200 to a browser agent); blocked since 2026-10-21",
    "seg/open-data-wiki": "origin-reachable: blocked from this runner (challenge page, HTTP 403 from "
                          "https://wiki.seg.org/wiki/Open_data); blocked since 2026-10-20",
    "geus/deep-subsurface-data": "origin-reachable: HTTP 502 from "
                                 "https://eng.geus.dk/products-services-facilities/data-and-maps/subsurface-data-denmark",
    "sodir/factpages": "sample, not the whole dataset: 3 of 3 selected files hashed (1732088 bytes); 48 entries listed",
    "nopims/poseidon": "1 features derived from 1 inputs, every input sha256 equal to the stored bytes (min_features 1)",
    "opm/norne": "2 of 2 inputs converted to kinds well-log, grid",
    "equinor/volve": "never verified",
}


def test_site_fixture_verifications_validate():
    from osd.verify import _validator
    for p in sorted(SITE_VDIR.glob("*.json")):
        _validator().validate(json.loads(p.read_text()))


def test_records_json_reason_is_the_status_reason(tmp_path, records_subset):
    # mutation: build.py formats its own sentence (the E23 l2_reason copied in) -> L2 and up differ, red
    from osd.cli import status_lines
    vdir = tmp_path / "verification"
    shutil.copytree(SITE_VDIR, vdir)
    (vdir / "opm__norne.json").write_text(json.dumps(L4))
    recs_dir = records_subset(WHY)
    build(tmp_path / "catalog", vdir, records_dir=recs_dir)
    built = json.loads((tmp_path / "catalog" / "records.json").read_text())
    recs, why = {r["id"]: r for r in built["records"]}, built["reasons"]
    status = dict(zip(recs, status_lines(vdir, records_dir=recs_dir)[1:]))   # one line per record, in the same order
    assert why.keys() == recs.keys()
    for rid in recs:
        assert f" {rid} " in status[rid] and why[rid] and status[rid].endswith(" " + why[rid]), rid
    assert {rid: why[rid] for rid in WHY} == WHY
    assert {recs[rid]["level"] for rid in WHY} == {"L0", "L1", "L2", "L3", "L4"}
    assert recs["nm-ocd/oil-and-gas-wells"]["blocked_since"] and recs["equinor/volve"]["checked_at"] is None


# E32: the real catalogue is built once per session (tests/conftest.py `full_build`); every other
# build reads a records subset. This test runs last (conftest orders it).

def test_one_real_build_per_session():
    # mutation: `full_build` scope "function" -> one real build per consumer, red
    from conftest import FULL_BUILD_USED, REAL_BUILDS
    assert len(REAL_BUILDS) == (1 if FULL_BUILD_USED else 0), REAL_BUILDS
