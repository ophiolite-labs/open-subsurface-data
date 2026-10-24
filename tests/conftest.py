import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tmp_records(tmp_path: Path):
    """A records dir with one valid record; tests mutate it."""
    d = tmp_path / "records" / "acme"
    d.mkdir(parents=True)
    (d / "demo.yaml").write_text(
        "id: acme/demo\ntitle: Demo set\n"
        "publisher: {name: Acme, url: https://acme.example, country: NL}\n"
        "origin: {url: https://acme.example/demo, access: anonymous}\n"
        "licence: {name: CC BY 4.0, spdx: CC-BY-4.0, redistribution: allowed, attribution: required}\n"
        "kinds: [seismic-3d]\nregion: {country: NL}\nlisted_by: [community]\nadded: 2026-10-23\n"
    )
    return tmp_path / "records"


@pytest.fixture
def tmp_outlines(tmp_path: Path):
    d = tmp_path / "outlines"
    d.mkdir()
    (d / "acme__demo.geojson").write_text(json.dumps({
        "type": "FeatureCollection", "licence": "CC BY 4.0",
        "inputs": {"demo-3d": {"url": "https://acme.example/demo.geojson", "sha256": "0" * 64}}, "features": [{
        "type": "Feature",
        "properties": {"record_id": "acme/demo", "kind": "survey-3d", "name": "Demo 3D",
                       "approximate": False, "source": "publisher shapefile",
                       "feature_id": "acme/demo#demo-3d", "input": "demo-3d"},
        "geometry": {"type": "Polygon", "coordinates": [[[4, 54], [5, 54], [5, 55], [4, 55], [4, 54]]]},
    }]}))
    return d


# --- E32: one real-catalogue build per session ---------------------------------------------------
# The real build (every record under records/) is the expensive one; the readers share `full_build`.
# A test that needs its own verification, custody or mirror inputs builds `records_subset` instead.

REAL_BUILDS: list[Path] = []


def pytest_configure(config):
    """Count every build of the real records, whoever calls it (before test modules import build)."""
    import inspect

    from osd import build as build_mod
    from osd import paths

    real = build_mod.build
    signature = inspect.signature(real)

    def counting(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        if Path(bound.arguments["records_dir"]) == paths.RECORDS_DIR:
            REAL_BUILDS.append(Path(bound.arguments["out_dir"]))
        return real(*args, **kwargs)

    counting.__wrapped__ = real
    build_mod.build = counting


def pytest_collection_modifyitems(session, config, items):
    """The build-count test runs after every consumer of the session's build."""
    last = [i for i in items if i.name == "test_one_real_build_per_session"]
    items[:] = [i for i in items if i not in last] + last


FULL_BUILD_USED: list[Path] = []


@pytest.fixture(scope="session")
def full_build(tmp_path_factory) -> Path:
    """The real catalogue as `make build` stages it (site/data/), built once with no verification
    results (as on CI), so its outlines.geojson is byte-equal to `make build`'s and the tile cache
    serves both. Read-only: copy what you change."""
    from osd.build import build

    root = tmp_path_factory.mktemp("full")
    vdir = root / "verification"
    vdir.mkdir()
    out = root / "site" / "data"
    build(out, vdir)
    FULL_BUILD_USED.append(out)
    return out


@pytest.fixture
def records_subset(tmp_path: Path):
    """records_subset(ids): a records directory holding only the named repository records (their
    outlines are read from outlines/ as usual), for a small build with a test's own inputs."""
    from osd import paths

    def make(ids) -> Path:
        out = tmp_path / "records-subset"
        for rid in ids:
            publisher, dataset = rid.split("/")
            (out / publisher).mkdir(parents=True, exist_ok=True)
            (out / publisher / f"{dataset}.yaml").write_bytes(
                (paths.RECORDS_DIR / publisher / f"{dataset}.yaml").read_bytes())
        return out
    return make
