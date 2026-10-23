"""Load and validate dataset records (records/<publisher>/<dataset>.yaml) and outlines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from . import paths


@dataclass(frozen=True)
class Problem:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def _schema(name: str) -> dict:
    return json.loads((paths.SCHEMA_DIR / f"{name}.schema.json").read_text())


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(_schema(name), format_checker=FormatChecker())


def record_files(records_dir: Path = paths.RECORDS_DIR) -> list[Path]:
    return sorted(records_dir.glob("*/*.yaml"))


def load_record(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"{path}: not a mapping")
    # dates: yaml parses 2026-10-23 into a date; the schema wants the ISO string
    if "added" in data and not isinstance(data["added"], str):
        data["added"] = data["added"].isoformat()
    return data


def load_records(records_dir: Path = paths.RECORDS_DIR) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in record_files(records_dir):
        rec = load_record(p)
        out[rec.get("id", str(p))] = rec
    return out


def validate_records(records_dir: Path = paths.RECORDS_DIR) -> list[Problem]:
    """Schema validity plus the two consistency rules a schema cannot express."""
    problems: list[Problem] = []
    v = _validator("record")
    seen: dict[str, Path] = {}
    for p in record_files(records_dir):
        rel = str(p.relative_to(records_dir))
        try:
            rec = load_record(p)
        except (OSError, TypeError, yaml.YAMLError) as e:
            problems.append(Problem(rel, f"unreadable: {e}"))
            continue
        for err in sorted(v.iter_errors(rec), key=lambda e: list(e.path)):
            where = "/".join(str(x) for x in err.path) or "<root>"
            problems.append(Problem(rel, f"{where}: {err.message}"))
        rid = rec.get("id")
        if isinstance(rid, str):
            if rid + ".yaml" != rel:
                problems.append(Problem(rel, f"id '{rid}' does not match the file path"))
            if rid in seen:
                problems.append(Problem(rel, f"duplicate id '{rid}' (also {seen[rid].name})"))
            seen[rid] = p
        lic = rec.get("licence", {})
        if lic.get("share_alike") and lic.get("redistribution") == "forbidden":
            problems.append(Problem(rel, "share_alike with redistribution forbidden is contradictory"))
    return problems


def load_outline(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_outlines(
    outlines_dir: Path = paths.OUTLINES_DIR, records_dir: Path = paths.RECORDS_DIR
) -> list[Problem]:
    """Each outline file is a FeatureCollection whose features carry the outline properties
    and name an existing record; the file name must match that record."""
    problems: list[Problem] = []
    v = _validator("outline")
    known = set(load_records(records_dir))
    for p in sorted(outlines_dir.glob("*.geojson")):
        rel = p.name
        try:
            fc = load_outline(p)
        except (OSError, ValueError) as e:
            problems.append(Problem(rel, f"unreadable: {e}"))
            continue
        if fc.get("type") != "FeatureCollection":
            problems.append(Problem(rel, "not a FeatureCollection"))
            continue
        expected_id = p.stem.replace("__", "/")
        if expected_id not in known:
            problems.append(Problem(rel, f"no record '{expected_id}' for this outline file"))
        for i, f in enumerate(fc.get("features", [])):
            props = f.get("properties", {})
            for err in v.iter_errors(props):
                problems.append(Problem(rel, f"feature {i}: {err.message}"))
            if props.get("record_id") != expected_id:
                problems.append(
                    Problem(rel, f"feature {i}: record_id '{props.get('record_id')}' != '{expected_id}'")
                )
            g = f.get("geometry") or {}
            if g.get("type") not in {"Point", "Polygon", "LineString", "MultiPolygon"}:
                problems.append(Problem(rel, f"feature {i}: geometry type {g.get('type')!r} not allowed"))
    return problems
