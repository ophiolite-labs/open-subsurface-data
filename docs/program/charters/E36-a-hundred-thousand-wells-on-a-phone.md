## E36 A hundred thousand wells on a phone — QUEUED · Surface (with build) · no strategy, no Codex round (surface class)

Authority: owner direction 23 Oct 2026 (the map scales; a phone connection loads the viewport, E05,
E15); E32 (PR #49: the split ruling of 24 Oct, its gate, tiles and pages evidence under
`docs/program/evidence/e32/`); E15 (tiles: same properties, `feature_id` promoted); E05 (clustering
stays on the page); OSD-D16 as amended 24 Oct.

**Outcome.** Virginia, British Columbia, Colombia, Utah and North Dakota (159,459 wells with E29's
four) are on the map, the world view on a phone still loads under 1 MB, cluster counts are exact,
and `make check` stays inside its budget.

**Context (main 394e4fd, 24 Oct; E32's measurements).** With all nine registers committed the
site's first load is 1,780,594 bytes (pmtiles 1,239,898; main 993,331) because the tiles keep
every well at every zoom (`-r1 --no-feature-limit --no-tile-size-limit`, `src/osd/build.py`
`TILE_*`), and the page clusters the wells of the tiles loaded so far below
`CLUSTER_BELOW_ZOOM` (`site/app.js:28-29`, `:180-205`). The real-catalogue tile test took 86 s
of a 226 s `make check` on CI. The five outlines are derived and reviewed in E32's evidence
(17.5, 13.6, 13.3, 9.0 MB and Virginia).

**The design the lane must map to.**
1. Wells below `CLUSTER_BELOW_ZOOM` come from a small static file the build writes (per-record
   well counts on a grid per zoom, or an equivalent the PR names with its size), not from tiles; the
   z0 to `CLUSTER_BELOW_ZOOM`-1 tile run carries no wellbore points. From `CLUSTER_BELOW_ZOOM` up,
   single wells come from the tiles as today (exact positions, `feature_id` promoted).
2. The record filter, the period filter and the approximate toggle change the cluster counts the
   same way they change the wells today.
3. The five outlines committed under `outlines/`; their records' `known_issues` "outline
   deferred" line removed.
4. The real-catalogue tile build and full comparison run in `make check-full` (pytest marker); the
   gate keeps E32's crossing fixture test and a small fixture tile test.

**Acceptance.**
- Site test: first load at the world view under 1 MB with all nine registers (the existing test,
  budget unchanged); a new journey test: at the world view the cluster total equals the sum of the
  nine registers' committed feature counts; filtered to one register it equals that register's
  count; at `CLUSTER_BELOW_ZOOM` a clicked well opens its dataset panel as today.
- `make check` step on the PR's CI run inside main's spread (stated with run ids); `make
  check-full` green on the branch with the full tile comparison.
- Phone-width screenshots: the world view, North Dakota at a town zoom, the dataset panel after
  clicking a well (with a record selected; E32 note 7).
- Staged site size table; under 500 MB.

**Out of scope.** Layers above 50,000 features (SK MER, PGI, CGS); new filters; tippecanoe polygon
clipping (E32 note 3).

**Ownership and dependencies.** Surface lane, after E32 merges. Paths: `site/**`, `tests/site/**`,
`src/osd/build.py` (tile runs and the cluster file), `tests/test_build.py` (the tile tests and
their marker), `Makefile` and `pyproject.toml` (the marker), `outlines/` for the five records,
those five records' `known_issues` line, `docs/program/evidence/e36/**`.
