from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"
RECORDS_DIR = ROOT / "records"
OUTLINES_DIR = ROOT / "outlines"
BUILD_DIR = ROOT / "build"
CATALOG_DIR = BUILD_DIR / "catalog"
VERIFICATION_DIR = BUILD_DIR / "verification"


def outline_path(record_id: str) -> Path:
    """outlines/<publisher>__<dataset>.geojson for records/<publisher>/<dataset>.yaml."""
    return OUTLINES_DIR / (record_id.replace("/", "__") + ".geojson")
