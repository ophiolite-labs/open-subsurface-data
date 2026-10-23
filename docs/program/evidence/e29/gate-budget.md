# E29 gate budget: measurement and ruling (23 Oct)

Measured on the VPS, 23 Oct ~17:40 UTC, `make check` with an empty tile cache (CI has none);
CI's last green `make check` on main took 86 s against 122 s here (ratio about 0.70):

| outlines committed | features in outlines.geojson | STAC Items | `make check` here | CI estimate | tile test |
|---|---|---|---|---|---|
| main today | 18,436 | ~18,400 | 2m02 | 86 s (measured) | pass |
| + SGUDDS, NZP&M x2, WA (6,970) | 25,406 | ~25,400 | 2m48 | ~118 s | pass |
| + Virginia (8,605) | 34,011 | ~34,000 | 3m16 | ~137 s | pass |
| all nine (159,459) | 177,895 | ~178,000 | 8m37 | ~6 min | FAIL |

Why: nine tests build the real catalogue (`test_build`, `test_stac`, `test_verify`, `test_manifest`,
`test_mirror`, site snippets), and one build writes one STAC Item file per feature of a record with
a period: 46 s per build with all nine, 35 s of it in `stac.write_catalog` (178,056 files, 193 MB;
Collections indented with tens of thousands of item links). With all nine the tile test also fails:
tippecanoe 2.49 writes another feature's string as `feature_id` for two features (ND #18505, UT
#11965 carry BCER well names) — the known red of E18's ruling, now reproduced on real data.
Pages would publish ~190 MB of STAC and a 150 MB pmtiles.

Default taken (the charter's stop rule): commit outlines for SGUDDS, NZP&M petroleum wells,
NZP&M 2D lines and WA DEMIRS (gate estimate at the budget edge; the PR's check run is the proof);
Virginia, BCER, SGC, UT DOGM and North Dakota get record `inputs`, `period` and rules but no
committed outline (outline-present fails, as today); their outlines were derived and reviewed here
(counts 8,605 / 34,431 / 25,013 / 40,422 / 44,018, all `outline-derived: pass`) and are one
`osd verify --outlines` away. The all-record dispatch still fetches their inputs, so the duration
proof covers all nine.

What would let the other five land (each outside E29's claim): (a) one session-scoped real build
shared by those tests (conftest fixture), (b) faster `stac.write_catalog` (no indent on
Collections, or Item files batched), (c) the tippecanoe attribute bug (E15/E27 owner) before any
lane adds ~150k map features. Supervisor: choose, or confirm the default.

## Supervisor ruling (23 Oct)
Default confirmed: commit outlines for SGUDDS, NZP&M x2 and WA DEMIRS; Virginia, BCER, SGC, UT DOGM and North Dakota get inputs, period and rules without committed outlines; the all-record dispatch covers all nine for the duration proof. Put the measurement table in the PR body and in `docs/program/evidence/e29/`; keep the five derived outlines out of the PR. A follow-up kernel charter (E32, registers with a hundred thousand wells: shared build fixture, faster STAC writing, the tippecanoe attribute bug) is being written now for the free coding slot and depends on your merge.
