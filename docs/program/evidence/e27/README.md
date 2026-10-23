# E27 evidence: the map says why

Fixture catalogue: `tests/fixtures/site/verification/` (one verification per reason class), built by
`osd.build` and served in place of `data/records.json` by `tests/site/site.test.mjs`. Captured by the
journey tests on 23 Oct 2026 (Playwright, Chromium with swiftshader); phone captures are clipped to the
sheet (HANDOFF known red: black map canvases at phone width).

| File | What it shows |
|---|---|
| `phone-detail-blocked.png` | 390 px: NM OCD, `blocked since 2026-10-21` in place of a level badge, "Why this level": the OSD-D20 sentence, "checked 23 Oct 2026" |
| `phone-detail-l2.png` | 390 px: Sodir FactPages at L2, "Why this level": the files the verifier hashed, "checked 23 Oct 2026" |
| `status-desktop.png` | 1400 px: the Why column, checked rows first (sorted by Last checked, descending) |
| `status-phone.png` | 390 px: level, dataset and date only; the Why column hidden like Access, Redistribution, Holds |

Mutation (charter acceptance): `build.py` formats its own sentence (E23's `l2_reason` copied into
build.py in place of `from .reasons import reason`) -> `tests/test_build.py::test_records_json_reason_is_the_status_reason`
red (1 failed): L2 and above read "" in records.json while `osd status` prints the evidence. Restored -> green.

Gate: `make check` green (451 passed, 88 s locally). Site tests: `npm run site-test` 30 of 30.
