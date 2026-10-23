"""Write and check the static STAC 1.0 catalogue (E04).

Output (build/catalog/stac/), all links relative so the tree serves from any address:
  catalog.json                    the root Catalog, one `child` link per record
  <cid>/collection.json           one Collection per record: licence, level, access, the files E02
                                   checksummed as assets, temporal extent from the record's `period`
  <cid>/items/<name>.json         one Item per outline feature with a feature_id, only when the record
                                   declares a `period` (OSD-D14); id = the outline's feature_id

`<cid>` is the record id with '/' replaced by '--'. Collection fields carry record-level assurance
from the verification record; Item fields carry the outline's provenance. Both are the `osd`
extension (schema/stac-osd.json). Validation runs offline against the schemas bundled in
schema/stac/ (schema/stac/schema-map.json).
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import shutil
from pathlib import Path

from . import paths
from .records import load_outline

STAC_VERSION = "1.0.0"
OSD_EXTENSION = ("https://raw.githubusercontent.com/ophiolite-labs/open-subsurface-data/main/"
                 "schema/stac-osd.json?v=2")   # v2 (E19): osd:access admits purchase; the v1 URL still validates
FILE_EXTENSION = "https://stac-extensions.github.io/file/v2.1.0/schema.json"
ALTERNATE_EXTENSION = "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"
MIRROR_TITLE = "Open Subsurface Data mirror"
SCHEMA_MAP = paths.SCHEMA_DIR / "stac" / "schema-map.json"
WORLD = [-180.0, -90.0, 180.0, 90.0]


def collection_id(record_id: str) -> str:
    return record_id.replace("/", "--")


def item_file_name(feature_id: str) -> str:
    """The part after '#', path-safe; a lossy name gets a short hash so two ids never collide."""
    local = feature_id.split("#", 1)[1]
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", local).lstrip(".") or "_"
    if safe != local:
        safe += "-" + hashlib.sha256(feature_id.encode()).hexdigest()[:8]
    return safe + ".json"


def _instant(date: str, end: bool) -> str:
    """'1993' / '1993-06' / '1993-06-30' to the first (or last) second of it, UTC."""
    parts = [int(x) for x in date.split("-")]
    y, m, d = (parts + [None, None])[:3]
    if end:
        m = m or 12
        d = d or calendar.monthrange(y, m)[1]
        return f"{y:04d}-{m:02d}-{d:02d}T23:59:59Z"
    return f"{y:04d}-{m or 1:02d}-{d or 1:02d}T00:00:00Z"


def interval(rec: dict) -> list:
    p = rec.get("period")
    if not p:
        return [None, None]
    start, end = _instant(p["start"], False), _instant(p["end"], True)
    if end < start:
        raise ValueError(f"{rec['id']}: period ends before it starts ({p['start']} > {p['end']})")
    return [start, end]


def _positions(c):
    if c and isinstance(c[0], (int, float)):
        yield c
    else:
        for x in c:
            yield from _positions(x)


def bbox(geometry: dict) -> list[float]:
    xs, ys = zip(*((p[0], p[1]) for p in _positions(geometry["coordinates"])))
    return [min(xs), min(ys), max(xs), max(ys)]


def _union(boxes: list[list[float]]) -> list[float] | None:
    if not boxes:
        return None
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)]


def _assets(verification: dict | None, mirrored: dict[str, str] | None = None) -> dict:
    """E02's checksummed files that carry a fetch address; collection-level, since which Item a
    file belongs to is not established. A file the mirror holds (E07, by sha256) keeps one logical
    asset and one checksum and gains the mirror as an alternate location."""
    out = {}
    for f in (verification or {}).get("files", []):
        if f.get("url"):
            out[f["path"]] = {"href": f["url"], "title": f["path"], "roles": ["data"],
                              "file:size": f["bytes"], "file:checksum": "1220" + f["sha256"]}
            if f["sha256"] in (mirrored or {}):
                out[f["path"]]["alternate"] = {"mirror": {"href": mirrored[f["sha256"]], "title": MIRROR_TITLE}}
    return out


def _item(rec: dict, cid: str, feature: dict, inputs: dict, when: list) -> dict:
    p = feature["properties"]
    props = {"title": p["name"], "datetime": None, "start_datetime": when[0], "end_datetime": when[1],
             "osd:approximate": p["approximate"], "osd:derivation": p["source"]}
    sha = inputs.get(p.get("input"), {}).get("sha256")
    if sha:
        props["osd:input_sha256"] = sha
    return {
        "type": "Feature", "stac_version": STAC_VERSION, "stac_extensions": [OSD_EXTENSION],
        "id": p["feature_id"], "collection": cid, "geometry": feature["geometry"],
        "bbox": bbox(feature["geometry"]), "properties": props,
        "links": [{"rel": "root", "href": "../../catalog.json", "type": "application/json"},
                  {"rel": "parent", "href": "../collection.json", "type": "application/json"},
                  {"rel": "collection", "href": "../collection.json", "type": "application/json"}],
        "assets": {},
    }


def write_catalog(out_dir: Path, records: list[dict], vdir: Path = paths.VERIFICATION_DIR,
                  outlines_dir: Path = paths.OUTLINES_DIR, mirror_index: list[dict] | None = None) -> list[dict]:
    """Write out_dir/stac/ from the joined records (record fields plus level, checked_at,
    blocked_since as build() joins them) and return the Collections. `mirror_index` is the public
    index of copies the mirror holds (osd.mirror.public_index). A duplicate feature_id
    anywhere in the outlines fails the build: it is the key Items and the map share."""
    root = out_dir / "stac"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    collections, children = [], []
    for rec in records:
        rid, cid = rec["id"], collection_id(rec["id"])
        op = outlines_dir / (rid.replace("/", "__") + ".geojson")
        fc = load_outline(op) if op.exists() else {"features": []}
        for f in fc["features"]:
            fid = f["properties"].get("feature_id")
            if fid in seen:
                raise ValueError(f"duplicate feature_id '{fid}'")
            if fid:
                seen.add(fid)
        when = interval(rec)
        items = []
        if rec.get("period"):
            items = [_item(rec, cid, f, fc.get("inputs", {}), when)
                     for f in fc["features"] if f["properties"].get("feature_id")]
        names: dict[str, str] = {}
        for it in items:
            n = item_file_name(it["id"])
            if n in names:
                raise ValueError(f"{rid}: item file {n} for both '{names[n]}' and '{it['id']}'")
            names[n] = it["id"]
        vp = vdir / (rid.replace("/", "__") + ".json")
        mirrored = {c["sha256"]: c["href"] for c in mirror_index or [] if c["record_id"] == rid}
        assets = _assets(json.loads(vp.read_text()) if vp.exists() else None, mirrored)
        alternate = any("alternate" in a for a in assets.values())
        lic = rec["licence"]
        spatial = (rec.get("region", {}).get("bbox")
                   or _union([bbox(f["geometry"]) for f in fc["features"] if f.get("geometry")])
                   or WORLD)
        col = {
            "type": "Collection", "stac_version": STAC_VERSION,
            "stac_extensions": [OSD_EXTENSION] + ([FILE_EXTENSION] if assets else [])
                               + ([ALTERNATE_EXTENSION] if alternate else []),
            "id": cid, "title": rec["title"], "description": rec.get("summary") or rec["title"],
            "license": lic.get("spdx") or "other",
            "keywords": rec["kinds"],
            "providers": [{"name": rec["publisher"]["name"], "roles": ["producer", "licensor"],
                           "url": rec["publisher"]["url"]}],
            "extent": {"spatial": {"bbox": [spatial]}, "temporal": {"interval": [when]}},
            "links": [{"rel": "root", "href": "../catalog.json", "type": "application/json"},
                      {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
                      {"rel": "about", "href": rec["origin"]["url"], "title": "Publisher's page"},
                      {"rel": "license", "href": lic.get("url", rec["origin"]["url"]),
                       "title": lic["name"]}]
                     + [{"rel": "item", "href": f"./items/{n}", "type": "application/geo+json"}
                        for n in names],
            "osd:level": rec["level"], "osd:checked_at": rec["checked_at"],
            "osd:access": rec["origin"]["access"], "osd:redistribution": lic["redistribution"],
        }
        if rec.get("blocked_since"):
            col["osd:blocked_since"] = rec["blocked_since"]
        if assets:
            col["assets"] = assets
        d = root / cid
        (d / "items" if items else d).mkdir(parents=True, exist_ok=True)
        (d / "collection.json").write_text(json.dumps(col, indent=2) + "\n")
        for n, it in zip(names, items):
            (d / "items" / n).write_text(json.dumps(it) + "\n")
        collections.append(col)
        children.append({"rel": "child", "href": f"./{cid}/collection.json",
                         "type": "application/json", "title": rec["title"]})
    catalog = {
        "type": "Catalog", "stac_version": STAC_VERSION, "id": "open-subsurface-data",
        "title": "Open Subsurface Data",
        "description": "Open subsurface datasets as their publishers state them, one Collection per "
                       "record, with the level our tools verified.",
        "links": [{"rel": "root", "href": "./catalog.json", "type": "application/json"}] + children,
    }
    (root / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    return collections


def validate(path: Path, recursive: bool = True, schema_config: Path = SCHEMA_MAP) -> tuple[bool, list]:
    """stac-validator over a local file or tree, against the bundled schemas only."""
    from stac_validator.utilities import fetch_and_parse_schema
    from stac_validator.validate import StacValidate

    fetch_and_parse_schema.cache_clear()   # a schema map change must not reuse a cached schema
    v = StacValidate(str(path), recursive=recursive, schema_config=str(schema_config))
    ok = v.run()
    return ok and all(m.get("valid_stac") for m in v.message), v.message


def _links(path: Path) -> list[dict]:
    return json.loads(path.read_text()).get("links", [])


def link_problems(root: Path) -> list[str]:
    """Every relative link in the tree points at a file that exists."""
    out = []
    for p in sorted(root.rglob("*.json")):
        for link in _links(p):
            href = link["href"]
            if "://" not in href and not (p.parent / href).resolve().is_file():
                out.append(f"{p.relative_to(root)}: {link['rel']} -> {href} does not exist")
    return out


def reachable(catalog: Path) -> dict[str, set[str]]:
    """Collection and Item ids a client reaches from the root by child and item links."""
    out: dict[str, set[str]] = {"collections": set(), "items": set()}
    todo, seen = [catalog.resolve()], set()
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        doc = json.loads(p.read_text())
        if doc["type"] == "Collection":
            out["collections"].add(doc["id"])
        elif doc["type"] == "Feature":
            out["items"].add(doc["id"])
        todo += [(p.parent / x["href"]).resolve() for x in doc.get("links", [])
                 if x["rel"] in ("child", "item")]
    return out
