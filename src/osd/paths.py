from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"
RECORDS_DIR = ROOT / "records"
OUTLINES_DIR = ROOT / "outlines"
AREAS_DIR = ROOT / "areas"   # committed area files, area/1 (E46)
BUILD_DIR = ROOT / "build"
CATALOG_DIR = BUILD_DIR / "catalog"
VERIFICATION_DIR = BUILD_DIR / "verification"


def outline_path(record_id: str, outlines_dir: Path = OUTLINES_DIR) -> Path:
    """outlines/<publisher>__<dataset>.geojson for records/<publisher>/<dataset>.yaml."""
    return outlines_dir / (record_id.replace("/", "__") + ".geojson")
