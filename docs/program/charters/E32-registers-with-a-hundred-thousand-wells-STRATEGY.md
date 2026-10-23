# E32 strategy: registers with a hundred thousand wells

Charter: `E32-registers-with-a-hundred-thousand-wells.md` (Kernel, Codex round closed, 21
dispositions). Base: main dd06ac9 (E29 merged as d0e3241). Read first: E29's PR #43 body and
`docs/program/evidence/e29/gate-budget.md`. Mutations: `docs/program/evidence/e32/mutations.md`.

## Lane-open facts (this branch, 23 Oct)

- `uv run pytest -q` on dd06ac9 here: 485 passed, 2m36 wall (with an empty tile cache, a
  concurrent `osd verify --outlines` running). Slowest: the tile test 61 s (tippecanoe on the real
  outlines), then nine real-catalogue builds of 5 to 8.5 s each: `test_build.py` x4 (lines 20, 157,
  181, 296), `test_stac.py::staged`, `site/test_how_snippets.py::site`, `test_mirror.py:469`,
  `test_manifest.py:548`, `test_verify.py:369`.
- The five outlines are re-derived on the branch with `osd verify --outlines <five ids>`; E29's
  derived copies did not survive its worktree.
- The tippecanoe corruption is tippecanoe's string pool: before 2.55.0, `swizzlecmp` returned
  `(int)(ahash - bhash)`, so two different strings whose 64-bit FNV-1a hashes share their low 32
  bits compare equal and the second one is stored as the first (felt/tippecanoe#239, "Fix hash
  collisions in the string pool", 2.55.0). Reproduced here on a four-feature fixture with a
  colliding pair found by brute force: 2.49.0 and 2.53.0 write register A's well name as register
  B's `feature_id`; 2.79.0 writes every string as given.

## Design 1: one real-catalogue build per session

```
tests/conftest.py
  pytest_configure        wrap osd.build.build before any test module imports it; every call whose
                          records_dir is paths.RECORDS_DIR is appended to REAL_BUILDS
  full_build (session)    build(<tmp>/site/data, <empty tmp vdir>) once; read-only for consumers
  pytest_collection_modifyitems   test_build.py::test_one_real_build_per_session runs last
  records_subset(tmp, ids) a records dir of the named real records (the small isolated builds)
```

- Readers of the full build: the tile test (copies `outlines.geojson` into its own tmp dir and tiles
  there), the no-tippecanoe test (same copy), the whole-tree STAC tests in `test_stac.py`
  (sample validation, links, reachability, licences, `feature_id` on the GeoJSON, the schema-map
  test), the site snippets (served from the build's parent directory), the new reachability test.
- Changed-input tests keep their own small build with `records_subset`: `test_build.py:15` (volve
  L1, nlog, one CC-BY-SA record), `test_build.py:296` (the site verifications and L4 Norne, the
  records they name; `status_lines(records_dir=...)`), `test_stac.py` staged (volve L2 with files,
  nlog L1, one L0: the assets and levels tests), `test_mirror.py:469` and `test_manifest.py:548`
  (Norne), `test_verify.py:369` (the four records it names).
- The full build's vdir is empty, as `make build` on CI has no `build/verification`: the
  `outlines.geojson` bytes are then equal to `make build`'s and the tile cache (`build/tiles/`,
  keyed by those bytes and the tippecanoe version) turns the gate's second tiling into a copy.
- Build-count test: asserts `len(REAL_BUILDS) == 1` when `full_build` was set up this session
  (0 otherwise). Mutation: `full_build` scope `function` -> count > 1, red.
- Duration: the `make check` step on CI before (main's last check run) and after, with run ids.

## Design 2: STAC in standard objects, proportional to the data

- **Threshold 2,000 Items per Collection** (`stac.SHARD_SIZE`). A Collection with at most 2,000
  Items links them directly as today. Above it, the Collection carries one `rel: child`,
  `type: application/json` link per shard, `./shards/<k>/catalog.json`, k = 1..n in Item order of
  the outline; each shard is a standard STAC Catalog (`id` `<cid>-<k>`, root, parent = the
  Collection, `rel: item` links `../../items/<name>.json`). North Dakota (44,018) gets 23 shards.
- Items stay `<cid>/items/<name>.json`, one file each, unchanged: `collection` = the Collection id,
  `parent` and `collection` links to `../collection.json`.
- Collections and shards are written compact (`separators=(",", ":")`, no indent); the root catalog
  stays indented (one link per record). No `next` links, nothing under `schema/stac/**` changes.
- Walkers follow `child` and `item`:
  - `reachable` already follows both (shards are Catalogs, neither counted as Collection nor Item).
  - `collection_items(col_path)` (new) yields the Item paths of one Collection by its `item` links and
    its child shards' `item` links; `containment_problems` uses it instead of globbing `items/`.
  - `link_problems` already checks every JSON file's relative links (shards included).
  - The OSD-D18 sample (`test_stac.py::item_sample`) draws from `collection_items`, so shards are
    sampled; mutation in the charter: an out-of-interval Item on a later shard -> `check-full` red.
  - `manifest.py`: the item lookup reads the Collection's `item` links and those of its child
    Catalogs (`stac.collection_items`). Mutation: direct links only -> red.
- `osd build` prints Items and bytes per Collection that has Items, and one total line for the
  STAC tree, `collections.json` and `records.json` (stderr, like the tiles line).

## Design 3: tiles

- Fixture `tests/fixtures/tiles/crossing.geojson`: register A (`crossing/register-a`) has well names
  `A-001377 WELL`, `A-002095 WELL`; register B's `feature_id`s `crossing/register-b#900540` and
  `#904407` share those names' low 32 hash bits (the README there gives the hash and the search).
  The test tiles it through `write_tiles` (the project's two runs and tile-join) and requires every
  feature's properties at z12 to equal the GeoJSON's.
- **Releases tried**: 2.49.0 (Ubuntu 24.04 `2.49.0-1build1`, red), 2.53.0 (Ubuntu
  `2.53.0-1build1`, red: before the fix), **2.79.0 (Ubuntu `2.79.0-1`, the newest packaged
  release; depends on libc6 >= 2.38 and libstdc++6 >= 13.1, both on 24.04; green)**. The pin is
  the `.deb` by sha256 `78261946e0ee8f6cb10c00c4aaf5e66858f0bfb9d870c530d6704fbcc67fb727` in
  `ci.yml` and `pages.yml`, `TIPPECANOE_PIN = "2.79.0"`.
- Real tile, all nine registers: `docs/program/evidence/e32/compare_tiles.py` decodes z12 of the
  built `outlines.pmtiles` and compares every feature both ways with `outlines.geojson`: id, kind,
  title, every property, geometry type; a point's decoded position equals the outline's position
  on the z12 tile grid (MVT stores integers: at z12 with extent 4096 one unit is 2.1e-5 degrees of
  longitude, so 1e-6 degrees is below the grid; the script reports the largest difference in
  degrees and the grid check is exact); line and polygon extents within one grid unit.

## Design 4: outlines for the five

`osd verify --outlines` for va-energy, bcer, sgc, ut-dogm, nd-dmr; reviewed (feature count per layer
= the day's `returnCountOnly`, stated in evidence), then one all-record `verify.yml` dispatch on the
branch with `--outline-inputs`, duration stated (< 60 min). No record changes unless a record carries
a `known_issues` line saying its outline is deferred.

## Design 5: Pages

Size table of the staged `site/` after `make build` (STAC bytes and file count, pmtiles,
`records.json`, `collections.json`, the rest) with the 500 MB bound; screenshots at phone width
(`tools/shot.mjs` or Playwright): North Dakota wells at a town zoom, the dataset panel after one
well is clicked.

## Stop rules as they apply

2.79.0 is correct on the fixture, so the tippecanoe stop rule does not apply unless the real tile
comparison fails. If designs 1 and 2 leave the `make check` step over 120 s on CI, the lane stops
with the measurements and names the tests that still rebuild.
