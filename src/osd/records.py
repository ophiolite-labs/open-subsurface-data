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
    # period: unquoted 1993-06-30 is a date and 1993 an int; the schema wants the strings
    period = data.get("period")
    if isinstance(period, dict):
        for k in ("start", "end"):
            x = period.get(k)
            if hasattr(x, "isoformat"):
                period[k] = x.isoformat()
            elif isinstance(x, int) and not isinstance(x, bool):
                period[k] = str(x)
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
    and name an existing record; the file name must match that record. Geometry is WGS84 with
    closed, non-empty rings; a feature_id is '<record-id>#...' and unique in its file; a derived
    feature names an input the collection carries and has a licence (its own or the file's)."""
    problems: list[Problem] = []
    v = _validator("outline")
    vc = Draft202012Validator(_schema("outline")["$defs"]["collection"], format_checker=FormatChecker())
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
        ids: dict[str, int] = {}
        for err in vc.iter_errors({k: x for k, x in fc.items() if k not in ("type", "features")}):
            problems.append(Problem(rel, f"collection: {err.message}"))
        named = fc.get("inputs") if isinstance(fc.get("inputs"), dict) else {}
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
            for msg in geometry_problems(f.get("geometry") or {}):
                problems.append(Problem(rel, f"feature {i}: {msg}"))
            if props.get("approximate") is False:
                if "input" in props and props["input"] not in named:
                    problems.append(Problem(rel, f"feature {i}: input '{props['input']}' is not in the collection's inputs"))
                if not (props.get("licence") or fc.get("licence")):
                    problems.append(Problem(rel, f"feature {i}: no licence (the feature's or the collection's)"))
            fid = props.get("feature_id")
            if fid is not None:
                if not str(fid).startswith(expected_id + "#"):
                    problems.append(Problem(rel, f"feature {i}: feature_id '{fid}' is not '{expected_id}#...'"))
                if fid in ids:
                    problems.append(Problem(rel, f"feature {i}: duplicate feature_id '{fid}' (also feature {ids[fid]})"))
                ids.setdefault(fid, i)
    return problems


def _position_problem(p) -> str | None:
    if not (isinstance(p, list) and len(p) in (2, 3)
            and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in p)):
        return f"position {p!r} is not [lon, lat]"
    if not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90):
        return f"position {p!r} outside WGS84 lon/lat"
    return None


def _ring_problems(ring) -> list[str]:
    if not isinstance(ring, list) or len(ring) < 4:
        return ["ring has fewer than 4 positions"]
    out = [m for m in map(_position_problem, ring) if m][:1]
    if not out and ring[0] != ring[-1]:
        out.append("ring is not closed")
    return out


def geometry_problems(g: dict) -> list[str]:
    """WGS84 positions, closed non-empty rings, lines of at least two positions."""
    t, c = g.get("type"), g.get("coordinates")
    if t == "Point":
        m = _position_problem(c)
        return [m] if m else []
    if t == "LineString":
        if not isinstance(c, list) or len(c) < 2:
            return ["line has fewer than 2 positions"]
        return [m for m in map(_position_problem, c) if m][:1]
    if t == "Polygon":
        if not isinstance(c, list) or not c:
            return ["polygon has no rings"]
        return [m for r in c for m in _ring_problems(r)][:1]
    if t == "MultiPolygon":
        if not isinstance(c, list) or not c or not all(isinstance(p, list) and p for p in c):
            return ["multipolygon has an empty part"]
        return [m for p in c for r in p for m in _ring_problems(r)][:1]
    return [f"geometry type {t!r} not allowed"]
