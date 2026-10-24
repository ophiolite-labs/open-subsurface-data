# E32: the gate on CI, before and after (stop rule)

| | main, run 40012942891 (merge base era, 25,406 outline features, tippecanoe 2.49) | PR #49, run 40024902546 (177,895 features, tippecanoe 2.79.0) |
|---|---:|---:|
| `make check` step | **123 s** (19:39:41 to 19:41:44Z) | **226 s** (21:11:28 to 21:15:14Z) |
| `pytest -q` | 115 s, 485 passed | 183 s, 494 passed |
| `osd validate` | 4 s | 14 s |
| `osd build` (tiles from the cache pytest filled) | 3 s | 20 s |
| real-catalogue builds in the session | 9 | 1 |

Main's run before it, 40009630760, took 163 s, so the 120 s bound was not met on main either.

**Stop rule.** Designs 1 and 2 did not bring the gate under 120 s on CI with nine registers
committed. The lane stops here with these measurements and makes no infrastructure proposal.

Slowest tests on the branch, measured locally with a cold tile cache as on CI
(`pytest -q --durations=20`, 16 cores, load average 8; 494 passed in 190 s):

| s | test | rebuilds? |
|---:|---|---|
| 86.1 | `test_build.py::test_tiles_hold_every_feature_with_its_properties_at_max_zoom` | no build; it tiles the full build's `outlines.geojson` with tippecanoe (two runs and tile-join, nine registers) and decodes z12. On CI the cache is always cold, and this filled cache is what makes `make build`'s tiling a copy |
| 24.0 | setup of `site/test_how_snippets.py` (the session `full_build`) | **the one real-catalogue build** |
| 17.7 | `test_records.py::test_repository_records_and_outlines_are_valid` | no; validates every record and outline again after `osd validate` (outside the claim) |
| 17.7 | `test_stac.py::test_reached_items_are_exactly_the_outline_feature_ids` | no; walks 178k Item links (the charter's reachability line) |
| 7.7 | `test_stac.py::test_staged_catalog_collections_and_item_sample_validate_offline` | no |
| under 2.1 each | the rest, including the six `records_subset` builds (one to four records each) | small isolated builds |

So no test rebuilds the real catalogue beyond the one session build. The time that remains grows
with features: tiling and decoding at 86 s, the build at 24 s, revalidation at 18 s and the full
reach walk at 18 s.

**Site test.** The site test (a separate CI step, not `make check`) is red on the PR run:
`tiles: the page loads tiles for the viewport, under 1 MB from the site` fails with
`site bytes 1780594 before any pan` (pmtiles 7 ranges, 1,239,898 bytes). Main's run had 993,331
bytes (pmtiles 452,635). The tiles keep every well at every zoom (`-r1 --no-feature-limit
--no-tile-size-limit`, E15), so the world view's low-zoom tiles grow with the five registers.
Measured on the nine-register tile, the low-zoom tile sizes are equal on 2.49.0 and 2.79.0 (z0
4,188,336 vs 4,187,720 bytes), so the cause is the data, not the release. The tile flags
(`build.py` `TILE_*`) and the site test are outside the claim (inbox e32 note 8).
