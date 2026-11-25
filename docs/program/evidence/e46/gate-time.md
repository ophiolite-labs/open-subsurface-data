# E46 slice 2: the gate back under two minutes (OSD-D39, acceptance 8)

CI runner: GitHub-hosted `ubuntu-24.04`, 4 cores (`nproc` printed on run 45654169550, the measuring commit). The CI
`make check` step runs `lint`, then `test`, `validate` and `build` side by side.

## Before

| Run | `make check` step | pytest wall | `build` target ends | site test step |
|---|---|---|---|---|
| main, after #95 (supervisor's number, #101) | 133 s | | | 242 s |
| main, earlier the same day | 131 s, 75 s | | | |
| #95, two pushes | 145 s, 154 s | 152 s | | |
| #98 measuring commit 482ac4f, run 45654169550 attempt 1 (main's code, durations on) | 90 s | 89 s | 56 s | |
| the same run, attempt 2 | 154 s | 153 s | 106 s | |

The same code took 90 s and 154 s: the runner varies by a factor of about 1.6. Pytest was the long
pole in every run. Its slowest items (run 1 / run 2):

| Item | Run 1 | Run 2 |
|---|---|---|
| the session's one real build (`full_build`, charged to `test_how_snippets` setup, the first consumer) | 28.5 s | 44.6 s |
| `test_records::test_repository_records_and_outlines_are_valid` | 9.3 s | 14.8 s |
| `test_stac::test_reached_items_are_exactly_the_outline_feature_ids` (walks 169,291 Items) | 6.0 s | 12.9 s |
| `test_stac::test_staged_catalog_collections_and_item_sample_validate_offline` | 3.8 s | 5.5 s |
| `test_areas::test_national_record_without_outline_...` (loads the area set again) | 3.0 s | 5.1 s |
| `test_areas::test_real_area_files_validate_and_stay_under_25_mb` | 1.5 s | 2.7 s |

The 22-45 s "setup of test_how_snippets" is the real build itself, built once per session (E32) and
charged to whichever test asks first; moving `test_how_snippets` off it moves the cost to the next
consumer. A profile of the build (local, count cached): STAC Items 17 s of 34 s, well grids 8.5 s,
the area count 2 s cached / about 6 s cold.

## Cuts, and what each saved

| Cut | Where | Saved on CI |
|---|---|---|
| 1. The test files that read the real build (`full_build`, found by name) run in one pytest process, the rest in a second, side by side (`make -j4`). One real build in the first, none in the second (`test_one_real_build_per_session` stays in the first and still counts). | `Makefile` | pytest wall 89-153 s -> the longer half 62-64 s; the other half 53-54 s |
| 2. Two real-catalogue area tests under `full` where the gate already guards the rule: the area files' validation (the gate's `make validate` runs `osd validate`, which reads them) and the real record made national (fixture `test_national_dataset_lights_its_country_only`). The 25 MB budget and every national record in the catalogue stay in the gate. | `tests/test_areas.py` | 4.5-7.8 s in the longer half |
| 3. The CI site test runs `npm run site-test` on the `site/data/` that `make check` staged instead of `make site-test`, which built the catalogue a second time. | `.github/workflows/ci.yml` | site test step 162 s -> 135-139 s |
| Tile runs side by side | already in #95 (`build.py`) | (in the before numbers) |
| 4. CI keeps `build/tiles` and `build/areas-cache` (`actions/cache`). Both are content-addressed inside, so an older copy that does not match is ignored and rebuilt; the count cache's key also holds `src/osd/areas.py`, so a change to the count's code never reads an older count. | `.github/workflows/ci.yml` | outline tiling, about 110 CPU-seconds of the 4 cores (38 s wall alone, measured locally), and the cold count twice; see the runs below |

Cut 4 was needed: with cuts 1-3 alone, three runs of commit 78fecf6 (after E51 added `test_areas_read.py` and the licence kind) took 96 s, 122 s and 76 s (run 45660870660). No test left the gate except the two in cut 2, each guarded in the gate by the named station or test.
`node --test` already runs the site test files side by side (one process per file); the shop journeys
file is the long one (about 85 s), so splitting it further belongs to its owner.


## After (three consecutive runs of the final commit)

Commit 57f42d2, run 45664911769, four attempts in a row:

| Attempt | Caches | `make check` step | pytest, rest / real-build half | site test step |
|---|---|---|---|---|
| 1 | empty (first run of the key) | 123 s | 85 s / 117 s | 197 s |
| 2 | restored | 54 s | 39 s / 54 s | 130 s |
| 3 | restored | 45 s | 41 s / 45 s | 137 s |
| 4 | restored | 57 s | 39 s / 56 s | 140 s |

Attempts 2-4 are the three consecutive runs under 120 s. Attempt 1 is the cost when the caches are empty: the
first PR run after a change to outlines (tiles) or to `src/osd/areas.py` (count), or after GitHub evicts the
cache (7 days unused). It was 123 s on a slow runner and 96 s on a fast one (78fecf6 attempt 1). Pushes to main
save the caches, and a PR restores main's through the `restore-keys` prefix.

What is left on the table, outside this claim: `test_records::test_repository_records_and_outlines_are_valid`
(9-27 s) checks what `make validate` checks beside it; it belongs to its owner to mark `full`.
