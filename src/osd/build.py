"""Build the published catalogue from records, outlines and verification records.

Outputs (build/catalog/):
  records.json    every record, joined with its latest verification level, the date it was
                   established, `stale` when that date is over 30 days old (or absent) and
                   `blocked_since` while the origin refuses this runner (OSD-D9); `reasons`, by record
                   id, why the record is at its level in the verifier's words ("never verified" when
                   it never was), the very string `osd status` prints (osd.reasons, E27), kept beside
                   the records array so records_digest and the manifests that pin it are unchanged;
                   and `catalog`,
                   the snapshot identity (E09): source_commit, verification_commit, built_at and
                   records_digest, the sha256 of the records array as canonical JSON (keys sorted,
                   separators "," ":", UTF-8), which manifest/3 and fidelity/1 carry back
  outlines.geojson one FeatureCollection, every feature joined with record title, kinds,
                   licence and level so the map needs no second lookup
  stac/            the static STAC catalogue (src/osd/stac.py)
  collections.json {"collections": [...]}, the same STAC Collections in one file
  outlines.pmtiles the same features as vector tiles, z0-12, when tippecanoe is installed (E15)
  mirror.json     {"copies": [...]}, the public index of what the mirror holds, regenerated from the
                   custody documents in <mirror_dir>/custody/ (E07); STAC assets gain the alternates
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from . import __version__, mirror, paths, stac
from .reasons import reason
from .records import load_outline, load_records
from .verify import is_stale


def latest_verification(rid: str, vdir: Path = paths.VERIFICATION_DIR) -> dict | None:
    p = vdir / (rid.replace("/", "__") + ".json")
    return json.loads(p.read_text()) if p.exists() else None


COMMIT = re.compile(r"^[0-9a-f]{40}$")
FROM_ENVIRONMENT = "from-environment"


def records_digest(records: list[dict]) -> str:
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def git_head(root: Path = paths.ROOT) -> str | None:
    """HEAD of the checkout the records come from; None outside git."""
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 and COMMIT.match(r.stdout.strip()) else None


def verification_commit_from_env() -> str | None:
    """The verification-results commit the workflow extracted into build/verification, as it says in
    OSD_VERIFICATION_COMMIT; None when it says nothing (a local build)."""
    v = os.environ.get("OSD_VERIFICATION_COMMIT", "").strip()
    if v and not COMMIT.match(v):
        raise ValueError(f"OSD_VERIFICATION_COMMIT={v!r} is not a 40-character commit id")
    return v or None


def build(out_dir: Path = paths.CATALOG_DIR, vdir: Path = paths.VERIFICATION_DIR,
          now: datetime | None = None, mirror_dir: Path = mirror.MIRROR_DIR,
          records_dir: Path = paths.RECORDS_DIR, source_commit: str | None = FROM_ENVIRONMENT,
          verification_commit: str | None = FROM_ENVIRONMENT) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = load_records(records_dir)
    records_out = []
    reasons = {}
    features = []
    for rid, rec in recs.items():
        v = latest_verification(rid, vdir)
        level = v["level"] if v else "L0"
        checked = v["checked_at"] if v else None
        blocked = (v or {}).get("origin", {}).get("blocked_since")
        joined = dict(rec, level=level, checked_at=checked, stale=is_stale(checked, now), blocked_since=blocked)
        reasons[rid] = reason(v, rec)
        records_out.append(joined)
        op = paths.outline_path(rid)
        if op.exists():
            for f in load_outline(op)["features"]:
                # E18: a feature's dates are its STAC Item's, not map attributes (tippecanoe 2.49
                # wrote other features' values into three tiles with them: evidence/e18/registers.md)
                props = {k: v for k, v in f["properties"].items() if not k.startswith("osd:period_")}
                props.update({
                    "title": rec["title"], "publisher": rec["publisher"]["name"],
                    "kinds": rec["kinds"], "licence": rec["licence"]["name"],
                    "redistribution": rec["licence"]["redistribution"], "level": level,
                })
                fid = {"id": props["feature_id"]} if "feature_id" in props else {}
                features.append({"type": "Feature", **fid, "properties": props, "geometry": f["geometry"]})
    catalog = {
        "source_commit": git_head() if source_commit == FROM_ENVIRONMENT else source_commit,
        "verification_commit": (verification_commit_from_env() if verification_commit == FROM_ENVIRONMENT
                                else verification_commit),
        "built_at": (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records_digest": records_digest(records_out),
    }
    (out_dir / "records.json").write_text(json.dumps(
        {"tool_version": __version__, "count": len(records_out), "catalog": catalog, "records": records_out,
         "reasons": reasons},
        indent=2) + "\n")
    (out_dir / "outlines.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": features}) + "\n")
    index = mirror.public_index(mirror_dir / "custody")
    (out_dir / "mirror.json").write_text(json.dumps({"copies": index}, indent=2) + "\n")
    collections = stac.write_catalog(out_dir, records_out, vdir, mirror_index=index)
    (out_dir / "collections.json").write_text(json.dumps({"collections": collections}, indent=2) + "\n")
    write_tiles(out_dir) if out_dir == paths.CATALOG_DIR else None  # test builds into tmp dirs skip tiling
    return {"records": len(records_out), "features": len(features), "collections": len(collections)}


# Tiling (E15). One source layer, "outlines", every GeoJSON property kept. Points are kept at every
# zoom (-r1) and clustered by the page; polygons are simplified by tippecanoe below zoom 8 only, so
# z0-7 and z8-12 are two runs joined. Pinned in CI: Ubuntu 24.04 tippecanoe 2.49.0-1build1.
TIPPECANOE_PIN = "2.49.0"
TILE_RUNS = (
    ["-Z0", "-z7"],
    ["-Z8", "-z12", "--no-line-simplification"],
)
TILE_COMMON = ["-q", "-f", "-l", "outlines", "-r1", "--no-feature-limit", "--no-tile-size-limit",
               "--no-tiny-polygon-reduction"]


def write_tiles(out_dir: Path, cache_dir: Path = paths.BUILD_DIR / "tiles") -> Path | None:
    """out_dir/outlines.pmtiles from out_dir/outlines.geojson, or None with a notice when
    tippecanoe is absent (the page then reads the GeoJSON whole). Cached by input and tool version,
    so a second build of the same outlines (the site test's) costs a copy."""
    import hashlib
    import shutil
    import subprocess
    import sys
    import tempfile

    src, dst = out_dir / "outlines.geojson", out_dir / "outlines.pmtiles"
    dst.unlink(missing_ok=True)
    if not (shutil.which("tippecanoe") and shutil.which("tile-join")):
        print("notice: tippecanoe not found, outlines.pmtiles not written; the map reads outlines.geojson "
              f"whole (install tippecanoe {TIPPECANOE_PIN}, see .github/workflows/ci.yml)", file=sys.stderr)
        return None
    version = subprocess.run(["tippecanoe", "--version"], capture_output=True, text=True, check=False).stderr.strip()
    key = hashlib.sha256(src.read_bytes())
    key.update(json.dumps([version, TILE_RUNS, TILE_COMMON]).encode())
    cached = cache_dir / f"outlines-{key.hexdigest()[:16]}.pmtiles"
    if not cached.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            parts = [Path(tmp) / f"z{i}.pmtiles" for i in range(len(TILE_RUNS))]
            runs = [subprocess.Popen(["tippecanoe", *TILE_COMMON, *zooms, "-o", str(part), str(src)],
                                     stderr=subprocess.PIPE, text=True) for zooms, part in zip(TILE_RUNS, parts)]
            for r in runs:
                err = r.communicate()[1]
                if r.returncode:
                    raise RuntimeError(f"tippecanoe failed: {err}")
            joined = Path(tmp) / "outlines.pmtiles"
            j = subprocess.run(["tile-join", "-q", "-f", "--no-tile-size-limit", "-o", str(joined), *map(str, parts)],
                               capture_output=True, text=True, check=False)
            if j.returncode:
                raise RuntimeError(f"tile-join failed: {j.stderr}")
            for old in cache_dir.glob("outlines-*.pmtiles"):
                old.unlink()
            shutil.move(joined, cached)
    shutil.copyfile(cached, dst)
    note = "" if TIPPECANOE_PIN in version else f" (CI pins {TIPPECANOE_PIN})"
    print(f"tiles: {dst.name} {dst.stat().st_size / 1e6:.1f} MB, z0-12, {version}{note}", file=sys.stderr)
    return dst
