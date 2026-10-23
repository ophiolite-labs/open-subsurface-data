## E32 Registers with a hundred thousand wells — CHARTERED · Kernel · strategy at lane open · Codex round closed (REWORK, reworked 23 Oct)

Authority: owner direction 23 Oct 2026 (levels on the map are real; the map scales, E05/E15);
E29 (ArcGIS adapter; its gate-budget evidence `docs/program/evidence/e29/gate-budget.md`, read
after E29 merges); E18 (Items carry their own dates; the tippecanoe ruling,
`docs/program/evidence/e18/registers.md`); E15 (tiles: the tile keeps the GeoJSON's properties,
`feature_id` is the promoted identity, `site/app.js:166-177`); OSD-D18 (the gate validates a
sample of Items, `make check-full` the tree); `docs/ENGINEERING.md` "The gate" (offline, under two
minutes); `Makefile:4`; `AGENTS.md:3`.

**Outcome.** The five registers E29 prepared but could not commit (Virginia `va-energy/gas-oil-wells`,
BCER `bcer/well-surface-holes-permitted`, SGC `sgc/banco-informacion-petrolera-pozos`, Utah
`ut-dogm/oil-gas-wells`, North Dakota `nd-dmr/wells`) show their wells on the map and reach L3, their
STAC Items are reachable by an ordinary recursive client walk, `make check` stays under two minutes
on CI with all nine registers' outlines committed, and the published site stays well inside GitHub
Pages' limits. All of this without changing what the site reads from a tile or a record.

**Context (E29's branch measurements; the lane re-measures on its own branch and states commit,
command and run id for every number it reports).** Nine tests across six modules (`test_build`,
`test_stac`, `test_verify`, `test_manifest`, `test_mirror`, the site snippets) each build the real
catalogue. One build writes a STAC Item per outline feature that has a `feature_id`, for every
record with a period (`src/osd/stac.py:163`). `make check` on main: about 2 minutes locally, 86 s on
CI, 18,436 outline features. With E29's four committed registers: about 2m45 locally, about 115 s on
CI. With all nine registers E29 measured about 8m40 locally and about 6 minutes on CI; around
178,000 features; `stac.write_catalog` was most of a build (Collections written indented with tens
of thousands of item links, one file per Item); the tile test failed because tippecanoe 2.49 wrote
another feature's string as `feature_id` for two features (North Dakota #18505 and Utah #11965
carried BCER well names), which is the E18 known red reproduced on real data. Pages would publish
roughly 190 MB of STAC and a 150 MB pmtiles. Both workflows install tippecanoe 2.49.0 by package
hash (`.github/workflows/ci.yml:19`, `.github/workflows/pages.yml:30`). After E29 merges the five
records carry `inputs`, `period` and `rules.yaml` entries (E29's PR names any record whose period is
missing; such a record gets outlines and L3 but no Items, said in this PR).

**The design the lane must map to.**
1. One real-catalogue build per test session. A session-scoped fixture builds the full catalogue
   once into a temporary directory; the tests that only read a full build read that one. A test
   that needs a changed input (its own verification, custody or mirror inputs: `tests/test_build.py:15`,
   `tests/test_stac.py:91`, `tests/test_mirror.py:469`) keeps its own small isolated build with
   fixture records, not a copy of the full build. The `make check` step on the PR's CI run is under
   two minutes with all nine registers committed; the lane states the step's duration (not the
   workflow's) before and after.
2. STAC writing proportional to the data, in standard objects only. A Collection with more than a
   stated threshold of Items (the strategy fixes it; of the order of 2,000) links to child Catalog
   shards (`rel: child`, `type: Catalog`) that carry the `rel: item` links; every Item keeps
   `collection` = the Collection id and `rel: collection`/`rel: parent` links to it. No `next`
   links, no bespoke page objects, `schema/stac/**` untouched. Collections and shards are written
   compact (no indentation of link arrays); Items stay one file each. Everything that walks the tree
   follows `child` as well as `item`: `reachable` (`src/osd/stac.py:281`), `containment_problems`
   (`src/osd/stac.py:241`; today it scans only `*/collection.json` and sibling `items/*.json`),
   `link_problems`, the OSD-D18 sample, and manifest selection (`src/osd/manifest.py:240` reads only
   the Collection's direct item links today). `osd build` prints Items and bytes per Collection.
3. Tiles. The tippecanoe attribute corruption is reproduced in a fixture test (two registers whose
   strings cross, as on the real data), then fixed with a tippecanoe release that is correct, pinned
   by hash in both `ci.yml` and `pages.yml` and in `TIPPECANOE_PIN` (`src/osd/build.py:93`). The
   tile keeps every GeoJSON property and the string `feature_id` (E15's contract); the site is not
   touched. If no release is correct, the stop rule applies.
4. Outlines for the five records committed under `outlines/` with `osd verify --outlines`, reviewed
   (feature counts equal the day's `returnCountOnly` per layer, stated), then checked with
   `--outline-inputs` on one all-record `verify.yml` dispatch on the branch, under 60 minutes,
   duration stated.
5. Pages. The lane states the staged site's size (STAC bytes, pmtiles bytes, `records.json`,
   `collections.json`, which repeats every Collection's links, `src/osd/build.py:117`) and shows the
   complete staged site under 500 MB, half of GitHub Pages' 1 GB site limit. Screenshots at phone
   width: North Dakota's wells at a town zoom; the dataset panel as it is today after clicking one
   well.

**Acceptance.**
- Build count: a test spies on the real build and asserts the aggregate count over the whole
  session is one across all consumers; mutation: fixture scope set to function → red (the count
  rises above one).
- `make check` step under 120 s on the PR's CI run, nine registers committed; the duration is in
  the PR body with the run id.
- STAC reachability: a test walks from `catalog.json` by `child` and `item` and compares the set of
  reached Item ids with the exact set of outline feature ids of every record with a period, no
  duplicates, no misses; mutation: a shard's `child` link removed from its Collection → red.
- STAC validity: `make check-full` green on the tree; a Collection file under 2 MB; the OSD-D18
  sample draws from shards too (mutation: an Item with a date outside its Collection's interval
  placed in a later shard → `check-full` red).
- Manifest: selecting a well whose Item lives on a later shard yields an entry with `item_id` set
  (test with the fixture layout; mutation: manifest reads only direct item links → red).
- Client walk: pystac (stated version) walks the North Dakota Collection and the Item count equals
  the record's committed outline feature count; output in evidence.
- Tiles: the fixture test is red on 2.49 and green on the pinned release; on the real tile of all
  nine registers every feature's id, kind, title and geometry (point coordinates to 1e-6) equal
  its outline feature's, compared in full (every feature, both directions), the comparison script
  and its output in evidence. The E18 known red is closed in HANDOFF.
- Levels: the five records at L3 on the all-record branch dispatch. A register that fails a check
  with outage evidence (status, time, retry) keeps its record edits and outline but the outcome is
  reported partial for that register; outage evidence does not make the lane complete.
- Diffs: `outlines/` shows exactly five new files; `records/**` unchanged (or only a `known_issues`
  line removed where a record said its outline was deferred); `site/**` unchanged.
- Size table for the complete staged site in the PR, with the 500 MB bound shown met.

**Out of scope.** Layers above 50,000 features (SK MER, PGI, CGS); new formats; any records beyond
the five; site features; the verifier's listing reader for ArcGIS layers (a later slice).

**Stop rules.** If no tippecanoe release is correct, stop after designs 1, 2, 4 and 5, keep 2.49
pinned, leave the five outlines uncommitted, record the reproduction and the releases tried, and
name the encoder question for a decision. If designs 1 and 2 cannot bring the gate under 120 s on
CI, stop with the measurements and name which tests still rebuild, no infrastructure proposal.

**Ownership and dependencies.** Coding lane. Paths: `tests/conftest.py`; the six test modules named
above (fixture use only, plus the new tests named here); `src/osd/stac.py`; `src/osd/build.py`
(size print, `TIPPECANOE_PIN`); `src/osd/manifest.py` (shard-aware item lookup only);
`tests/fixtures/stac/**` and `tests/fixtures/tiles/**` (new); the tippecanoe install step in
`.github/workflows/ci.yml` and `.github/workflows/pages.yml` (granted, both named in the PR title);
`outlines/` for the five records; `docs/program/evidence/e32/**`. Not touched: `schema/**`,
`site/**`, `records/**` beyond the one allowed line, `src/osd/verify.py`, `src/osd/outlines/**`.
Depends on E29 merged first; the lane reads E29's PR body and gate-budget evidence before writing
its strategy.

**Evidence to inspect.** CI step durations before and after with run ids; the build-count test;
the reachability test; the pystac walk output; the tile comparison script and output; the size
table; the two screenshots.

### Dispositions (Codex round 23 Oct, REWORK; one round, OSD-D8)

| # | Finding | Disposition |
|---|---|---|
| 1 | Items need `feature_id`, not only a period; the 178,056 figure is not an Item count | Accepted. Context rewritten; all numbers marked as E29 branch measurements, lane re-measures and cites commit, command, run id |
| 2 | Branch measurements are not HEAD facts | Accepted. Authority names E29's gate-budget evidence; lane cites it after merge |
| 3 | Dependency assumption: E29 may leave periods missing | Accepted. Context says E29's PR names missing periods; such a record gets L3 but no Items, said in this PR |
| 4 | `check.yml` does not exist; two workflows install tippecanoe | Accepted. `ci.yml` and `pages.yml` both named, same pinned release in both and in `TIPPECANOE_PIN` |
| 5 | Three-minute budget contradicts the two-minute gate policy | Accepted. 120 s, measured as the `make check` step |
| 6 | A copied build cannot test a changed input's join | Accepted. One shared full build for readers; isolated small builds for tests with their own inputs |
| 7 | `next` pages are not interoperable static traversal | Accepted. Child Catalog shards with item links; Items keep their Collection; every walker follows `child` |
| 8 | Manifest selection reads only direct item links | Accepted. `manifest.py` claimed; acceptance test for an Item on a later shard |
| 9 | Numeric ids and string removal break the site contract | Accepted. Dropped. Corrected encoder preserving properties; site untouched; stop rule if none is correct |
| 10 | Pages would still publish with 2.49 | Accepted. Both workflows pinned |
| 11 | `schema/stac/**` is not permission for bespoke pages | Accepted. Standard objects only; `schema/**` not touched |
| 12 | Build-count spy on one consumer is loose | Accepted. Aggregate session count across all consumers |
| 13 | Counting Items permits duplicates | Accepted. Exact id set, no duplicates |
| 14 | "paging removed → size red" is incoherent | Accepted. Replaced by reachability and completeness; size bound kept as its own check |
| 15 | Id-only tile check misses corrupted names and geometry | Accepted. Full comparison of id, kind, title, geometry, both directions |
| 16 | Outage exceptions could excuse all five | Accepted. Outage evidence makes a register partial, not complete |
| 17 | Size table without a bound | Accepted. Complete staged site under 500 MB, `collections.json` included |
| 18 | Containment check scans only the old layout | Accepted. Walkers follow shards; mutation named |
| 19 | E29 owns the nine records and outlines | Accepted. Lane opens after E29 merges and reads its PR body; five outline files are the only overlap |
| 20 | Tile change reopened E15's contract | Accepted with 9. Properties preserved, site untouched |
| 21 | "Detail panel of one well" adds surface behaviour | Accepted. The dataset panel as it is today after clicking a well |
