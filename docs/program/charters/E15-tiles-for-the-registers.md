## E15 Tiles for the registers — QUEUED · Surface · no strategy, no Codex round

Authority: OSD-D16 (register outlines up to 8 MB until a tiling lane); E05 as merged (the page
prefers `data/outlines.pmtiles` when `files.txt` lists it); `docs/ARCHITECTURE.md` (PMTiles).

**Outcome.** Opening the map on a phone connection no longer downloads the register outlines whole:
the page loads tiles for the viewport, and every feature still carries the same properties and
`feature_id` as `outlines.geojson`.

**Context today (verified 23 Oct, main after PR #7).** `outlines/sodir__factpages.geojson` is
4.3 MB and `outlines/nlog__nlog.geojson` 2.6 MB; `make build` concatenates all outlines into
`build/catalog/outlines.geojson`, which the page fetches whole. E05 added the `pmtiles` protocol
and the `files.txt` probe but nothing writes a PMTiles file. `tippecanoe` is not installed in CI.

**The design the lane must map to.**
1. `make build` writes `build/catalog/outlines.pmtiles` from `outlines.geojson` with `tippecanoe`
   (pinned version, installed in the `check` workflow from the official release or a pinned apt
   package; the build skips tiling with a visible notice when the binary is absent, so `make check`
   stays offline-capable locally). Zoom range 0 to 12, point features kept at every zoom with
   clustering left to the page, polygons simplified by tippecanoe only below zoom 8.
2. The page uses the tiles for the extents, surveys and wells layers when present and falls back to
   the GeoJSON otherwise; the list, search and detail panel keep reading `records.json` and
   `outlines.geojson` metadata (ids and names), not the tiles.
3. `feature_id` is the tile feature id; a Playwright test opens `#q=sodir`, clicks a wellbore and
   gets the same detail title as the GeoJSON path.

**Acceptance.**
- With tiles present, the page's network log on load shows no request for `outlines.geojson`
  larger than the metadata fetch (Playwright, offline, asserts the transferred bytes under 1 MB
  before any pan).
- The 10,000-wellbore performance test from E05 passes unchanged on the tile path.
- Tile feature count per layer equals the GeoJSON feature count at the maximum zoom (test using
  the `pmtiles` CLI or a Python reader).
- `make check` without `tippecanoe` prints the notice and passes.

**Out of scope.** Changes to outline files or schemas; STAC (E04).

**Ownership and dependencies.** Coding lane; paths `Makefile` (build target), `src/osd/build.py`
(tiling call only), `.github/workflows/ci.yml` and `pages.yml` (tippecanoe install step, announced),
`site/app.js`, `tests/site/**`, `tests/test_build.py` (tile count test). Depends on E03 (merged).
Runs in parallel with E04 (disjoint paths except `src/osd/build.py`: E15 adds one call at the end of
`build()`; E04 adds `stac.py` and one call; the second to merge rebases).

**Evidence to inspect.** The network-log assertion; the count test; a phone screenshot.
