## E32 Registers with a hundred thousand wells — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: owner direction 23 Oct 2026 (levels on the map are real; the map scales, E05/E15);
E29 (ArcGIS adapter, its inbox note 5 with the measurements below, PR pending); E18 (Items carry
their own dates; the tippecanoe ruling); E15 (tiles); OSD-D18 (the gate validates a sample of
Items, `make check-full` the tree); `docs/ENGINEERING.md`.

**Outcome.** The five registers E29 could only prepare (Virginia 8,605 wells, BCER 34,431, SGC
25,013, Utah DOGM 40,422, North Dakota 44,018) show their wells on the map, reach L3, and have
STAC Items a client can page through, while `make check` stays a gate a contributor waits for
(under three minutes on CI) and the site's pages build stays within GitHub Pages' limits.

**Context today (E29 measurements, VPS, 23 Oct 17:40 UTC; CI is about 0.7 of these times).**
Nine tests build the real catalogue (`test_build`, `test_stac`, `test_verify`, `test_manifest`,
`test_mirror`, site snippets); one build writes one STAC Item file per feature of a record with a
period. `make check` today: 2m02 here, 86 s on CI, 18,436 features. With E29's four committed
registers: 2m48 / ~118 s, 25,406 features. With all nine: 8m37 / ~6 min, 177,895 features, 178,056
Item files (193 MB; 35 of 46 s per build in `stac.write_catalog`, Collections indented with tens of
thousands of item links), and the tile test fails: tippecanoe 2.49 writes another feature's string
as `feature_id` for two features (ND #18505, UT #11965 carry BCER well names), the known red of
E18's ruling now reproduced on real data. Pages would publish about 190 MB of STAC and a 150 MB
pmtiles. After E29 merges, the five records carry `inputs`, `period` and `rules.yaml` entries, and
their outlines are one `osd verify --outlines` away.

**The design the lane must map to.**
1. One real build per test session: a session-scoped fixture builds the catalogue once into a
   temporary directory and the nine tests read it; a test that mutates the build gets its own
   copy. `make check` with all nine registers under three minutes on CI (the PR's check run is the
   proof, its duration stated).
2. STAC writing proportional to the data: Collections written compact (no indentation of item
   link arrays) or Items grouped per Collection in paged link files as the STAC spec allows
   (`rel: next` pages of item links), chosen in the strategy with the client test (OSD-D18 sample
   validation and `make check-full` on the tree); a STAC client (pystac or the QGIS browser,
   stated) lists the Items of North Dakota. Item count and byte size per Collection are printed
   by `osd build` and go in the PR.
3. Tiles: the tippecanoe attribute corruption is reproduced in a fixture test (two features whose
   strings cross), then fixed by a tippecanoe version that is correct (stated and pinned in the
   CI setup) or by writing `feature_id` as a numeric property and keeping strings out of the
   tile attributes (the detail panel reads strings from `records.json` and the outline files,
   not from the tile); the fix is proven by the fixture test and by the real tile of all nine
   registers. The E18 known red is closed in HANDOFF.
4. Outlines for the five records committed under `outlines/` (`osd verify --outlines`, reviewed:
   counts equal the day's `returnCountOnly`), verified with `--outline-inputs` on the branch
   dispatch; the all-record dispatch under 60 minutes, duration stated.
5. Pages: the published site size stated (STAC bytes, pmtiles bytes, records.json bytes) and
   under GitHub Pages' 1 GB site limit with headroom; a phone-width screenshot of North Dakota's
   wells at a town zoom and the detail panel of one well.

**Acceptance.**
- `make check` on CI under three minutes with all nine registers' outlines committed; the
  session fixture test proves one build (a counter or a spy; mutation: fixture scope dropped →
  the build count test red).
- STAC: `make check-full` green; pystac (or the stated client) walks the North Dakota Collection
  and counts 44,018 Items (or the day's count); a Collection file under 2 MB; mutation: paging
  removed → the size test red.
- Tiles: the fixture test with crossing strings red before the fix, green after; the real tile
  of all nine registers has every feature's `feature_id` equal to its outline id (a full
  comparison, not a sample).
- The five records at L3 on the branch dispatch (or the first failing check named with outage
  evidence); outlines diff shows only the five files; record diffs empty.
- Published size table in the PR.

**Out of scope.** Layers above 50,000 features (SK MER, PGI, CGS); new formats; any records
beyond the five; site features.

**Stop rules.** If no STAC layout keeps a client listing Items and the tree under `check-full`,
stop after design 1 and 3, record the measurements, and name the layout question for a decision.

**Ownership and dependencies.** Coding lane; paths `tests/conftest.py`, the nine test modules
(fixture use only), `src/osd/stac.py`, `src/osd/build.py` (tile attributes, size print),
`schema/stac/**` if the layout needs it (named in the PR title), `tests/test_stac.py`,
`tests/test_build.py`, `tests/fixtures/stac/**` and `tests/fixtures/tiles/**` (new), the
tippecanoe install step in `.github/workflows/check.yml` (granted, named in the PR),
`outlines/` for the five records, `docs/program/evidence/e32/**`. Depends on E29 (merged first).

**Evidence to inspect.** CI durations before and after; the build-count test; the client walk;
the tile comparison; the size table; the screenshot.
