## E46 Areas that hold data: the build says which country, province and basin each dataset sits in — CHARTERED 25 Nov 2026 (Kernel; strategy at lane open; one Codex round)

Authority: family `MAP-AS-A-SHOP-family.md` (R-S3, R-S4, R-S5, R-S8); OSD-D27, OSD-D28; E03 and E29
(committed outlines), E32 (build shape, tiles), E36 (first-load budget). Evidence:
`global-layers.md` and `build_areas.py` beside the prototype (the prototype counts one point per
dataset and leaves national registers out; this charter replaces that rule with the decided one).

**Outcome.** After `osd build`, every record in `records.json` says which areas it sits in, per
kind, and the catalogue holds, per kind, exactly the areas that hold at least one dataset, with a
name, a label point and the dataset ids. The shop (E48) draws and filters from these files and
computes nothing itself.

**Context today (verified on `origin/main` `fd69de4`, 25 Nov).**

- `src/osd/build.py` `build()` joins records with verification, collects outline features
  (169,295 features: 166,412 well points, the rest survey polygons and lines) and writes
  `records.json`, `outlines.geojson`, well grids and `outlines.pmtiles` (tippecanoe).
- `schema/record.schema.json` is record/5: `region.country` (ISO alpha-2), `region.basin` (free
  text), `region.bbox`. 192 of 236 records carry a bbox. Nothing says a dataset is country-wide; the
  prototype guesses it from the ratio of the box to the country's box.
- `src/osd/outlines/geometry.py` has simplification and ring helpers; there is no point-in-polygon
  and no area data in the repository.
- Network is allowed only in the commands AGENTS.md names; the build is offline.

**The design the charter fixes.**

1. *Area files are committed inputs, like outlines.* `areas/<kind>.geojson` for `country`,
   `province`, `basin`, each validated by a new `schema/area.schema.json` (area/1): a
   FeatureCollection whose top level carries `kind`, `source` (`name`, `url`, `licence`, `credit`,
   `edition`, `retrieved`, `sha256` of the publisher's file) and whose features carry `area_id`
   (stable, from the source's own code: ISO alpha-2, `iso_3166_2` or `adm1_code`, the USGS province
   code), `name`, and for provinces `country`. Geometry is simplified once, at preparation, to what
   zoom 8 can show; the three files together stay under 25 MB in git. Licence areas (E51) use the
   same schema with `kind: licence`, so E51 adds files, not a contract.
2. *Preparation is a maintainer command, not the build.* `osd areas prepare <kind> <file>` reads a
   publisher file already on the machine (Natural Earth 50m countries, Natural Earth 10m admin-1,
   USGS WEP_PRVG; shapefile or GeoJSON, read as data, never executed), simplifies, and writes the
   committed area file with the source block. It reaches no network; AGENTS.md's network line is
   unchanged. The publisher files themselves are not committed; `areas/SOURCES.md` records where
   each was taken from, its digest and its terms sentence, quoted.
3. *record/6: a dataset can say it is country-wide.* Optional `region.national: true`: the
   publisher presents the dataset as covering the country named in `region.country` (a national
   register, a national survey). A publisher fact; E52 fills it. record/5 files still validate.
4. *The count (R-S3), in `osd build`, module `src/osd/areas.py`.* For each record, its positions
   are: every committed outline feature of the record (a well point as itself; a polygon or line by
   its vertices and one interior point); when it has none, the middle of `region.bbox`; when it
   has neither, no position. A record sits in an area when at least one position lies inside it.
   A record with `region.national` sits in its country and, by this rule alone, in no province or
   basin unless it has outline positions (a national register with committed wells does light the
   basins its wells are in: that is the point of the ruling). A record without `national` and
   without positions but with `region.country` counts for the country.
   Containment is exact on the committed (simplified) geometry, with a bounding-box index so the
   166,412 points cost seconds, and the per-register result is cached under `build/` keyed by the
   digests of the outline and area files so `make check` stays inside its two minutes.
5. *What the build writes.* `records.json`: each record gains `areas: {country: [...], province:
   [...], basin: [...]}` (area ids, sorted; a kind absent when empty). `build/catalog/areas.json`
   (areas/1 index): per kind the `source` block and the list of areas that hold a dataset:
   `area_id`, `name`, `label` ([lon, lat] inside the largest part), `bbox`, `n`, `ids`.
   Geometry of those areas only goes to tiles: one layer per kind (`areas_country`,
   `areas_province`, `areas_basin`) in a separate `areas.pmtiles`, feature id = a stable integer,
   properties `area_id`, `name`, `n` only; and `areas-<kind>.geojson` beside it as the fallback for
   a server without byte ranges and for the offline tests. An area that holds nothing is in neither.
6. *Slices.* Slice 0 is the contract and lands first, alone: area/1 and record/6 schemas with their
   old-file tests, `osd validate` reading `areas/`, a fixture set under `tests/fixtures/areas/`
   (three small countries, four provinces, three basins, six records: a register with wells across
   two basins, a survey polygon across a border, a bbox-only dataset, a `national` one, one with
   nothing, one whose bbox middle falls in the sea), the expected `areas.json` for it committed as
   the golden file, and `build()` writing `areas.json` and `records[].areas` from whatever is in
   `areas/` (nothing yet: empty lists, valid files). Slice 1 commits the three real area files and
   `SOURCES.md`, the tiles, the cache, and the numbers.

**Acceptance.**

1. Slice 0: `schema/area.schema.json` exists with `$id` …/area/1; record schema `$id` is
   …/record/6; every record/5 file on main validates against record/6 (test kept); a test shows a
   record/5 fixture file still valid and `region.national: "yes"` invalid.
2. Slice 0: the fixture build's `areas.json` equals the golden file byte for byte; each of the six
   fixture records has the `areas` the charter's rule gives, asserted one by one with the reason
   in the test name.
3. Slice 0: with an empty `areas/`, `osd build` writes a valid `areas.json` with empty lists and
   no `areas` key on records, and the live site's tests pass unchanged.
4. Slice 1: `areas/country.geojson`, `province.geojson`, `basin.geojson` validate, total under
   25 MB; `areas/SOURCES.md` quotes each terms sentence and digest; the PR states how many areas of
   each kind hold a dataset and how many datasets are placed per kind, beside the prototype's
   (933 named basins, 4,590 provinces, 121 datasets with a place).
5. Slice 1: no area with `n = 0` in `areas.json`, the tiles or the fallback files (test over the
   real build); every `ids` entry is a record id; every record's `areas` agrees with the index in
   both directions.
6. Slice 1: the Sodir register lights more than one basin and exactly one country; a record with
   `national` and no outline lights its country and no basin (tests on the real catalogue, written
   so that E52's edits do not break them).
7. Guards, one mutation each shown to fail: a point on the far side of a hole is outside; a
   polygon crossing the antimeridian is handled as the committed outlines handle it; the bbox middle
   is used only when no outline exists; an area file whose `source.licence` is empty is refused by
   `osd validate`.
8. `make check` on CI stays under 120 s (number in the PR); first load of the live page is
   unchanged (it requests none of the new files).

**Out of scope.** Drawing anything (E48); licence areas (E51); filling `national` (E52); renaming
or removing `region.basin`; STAC exposure of areas.

**Stop rules.** If exact containment for the five large registers cannot be cached to keep
`make check` under 120 s, stop and write the measured times to the inbox with the default
"count the large registers from their well-grid cells at z6 and say so in `areas.json`".
If the three area files cannot be brought under 25 MB at a tolerance that still reads at zoom 8,
stop with the sizes; do not raise the budget alone.

**Ownership and dependencies.** Coding lane (kernel). Paths: `schema/area.schema.json` (new),
`schema/record.schema.json` (record/6), `tests/fixtures/schema/record-5.schema.json`,
`src/osd/areas.py` (new), `src/osd/build.py`, `src/osd/cli.py` (`areas prepare`, validate),
`src/osd/records.py` and `src/osd/paths.py` (as needed for `areas/`), `areas/**` (new),
`tests/test_areas.py` (new), `tests/fixtures/areas/**` (new), `tests/test_schema.py` and
`tests/test_build.py` (additions), `Makefile` (copying the new files to `site/data/` only),
`docs/program/charters/E46-*`, `docs/program/evidence/e46/**`. No dependency. `pyproject.toml` is
E49's while both are open: this lane adds no dependency.

**Evidence to inspect.** The golden `areas.json`; the counts table in the PR; the `make check`
time; the mutation list.
