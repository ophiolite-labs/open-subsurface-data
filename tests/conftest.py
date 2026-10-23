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
    (d / "acme__demo.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [{
        "type": "Feature",
        "properties": {"record_id": "acme/demo", "kind": "survey-3d", "name": "Demo 3D",
                       "approximate": False, "source": "publisher shapefile"},
        "geometry": {"type": "Polygon", "coordinates": [[[4, 54], [5, 54], [5, 55], [4, 55], [4, 54]]]},
    }]}))
    return d
