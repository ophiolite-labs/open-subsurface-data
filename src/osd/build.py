"""Build the published catalogue from records, outlines and verification records.

Outputs (build/catalog/):
  records.json    every record, joined with its latest verification level, the date it was
                   established, `stale` when that date is over 30 days old (or absent) and
                   `blocked_since` while the origin refuses this runner (OSD-D9)
  outlines.geojson one FeatureCollection, every feature joined with record title, kinds,
                   licence and level so the map needs no second lookup
  stac/            the static STAC catalogue (src/osd/stac.py)
  collections.json {"collections": [...]}, the same STAC Collections in one file
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import __version__, paths, stac
from .records import load_outline, load_records
from .verify import is_stale


def latest_verification(rid: str, vdir: Path = paths.VERIFICATION_DIR) -> dict | None:
    p = vdir / (rid.replace("/", "__") + ".json")
    return json.loads(p.read_text()) if p.exists() else None


def build(out_dir: Path = paths.CATALOG_DIR, vdir: Path = paths.VERIFICATION_DIR,
          now: datetime | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = load_records()
    records_out = []
    features = []
    for rid, rec in recs.items():
        v = latest_verification(rid, vdir)
        level = v["level"] if v else "L0"
        checked = v["checked_at"] if v else None
        blocked = (v or {}).get("origin", {}).get("blocked_since")
        joined = dict(rec, level=level, checked_at=checked, stale=is_stale(checked, now), blocked_since=blocked)
        records_out.append(joined)
        op = paths.outline_path(rid)
        if op.exists():
            for f in load_outline(op)["features"]:
                props = dict(f["properties"])
                props.update({
                    "title": rec["title"], "publisher": rec["publisher"]["name"],
                    "kinds": rec["kinds"], "licence": rec["licence"]["name"],
                    "redistribution": rec["licence"]["redistribution"], "level": level,
                })
                fid = {"id": props["feature_id"]} if "feature_id" in props else {}
                features.append({"type": "Feature", **fid, "properties": props, "geometry": f["geometry"]})
    (out_dir / "records.json").write_text(json.dumps(
        {"tool_version": __version__, "count": len(records_out), "records": records_out}, indent=2) + "\n")
    (out_dir / "outlines.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": features}) + "\n")
    collections = stac.write_catalog(out_dir, records_out, vdir)
    (out_dir / "collections.json").write_text(json.dumps({"collections": collections}, indent=2) + "\n")
    return {"records": len(records_out), "features": len(features), "collections": len(collections)}
