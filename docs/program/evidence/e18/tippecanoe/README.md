# Two tippecanoe 2.49 misplaced values (for a later tiles lane)

Input: `outlines.geojson` as `osd build` wrote it at this branch's regenerated outlines, with each
feature's `osd:period_*` members put back (what build wrote before the one-line exclusion);
tiled by `osd.build.write_tiles` (the project's two tippecanoe runs plus tile-join, 83.9 MB).
Each file is the one feature as `tippecanoe-decode outlines.pmtiles 12 <x> <y>` printed it.

| File | Feature | Member | In the GeoJSON | In the tile |
|---|---|---|---|---|
| `nlog--WAS-17.json` (z12/2097/1351) | `nlog/nlog#WAS-17` | `publisher_id` | `WAS-17` | `2012-12-24` |
| `sodir--wellbore-5250.json` | `sodir/factpages#wellbore/5250` | `osd:period_start_raw` | `3/2/2006` | `1955-05-20` |

A third feature was wrong the same way (three `publisher_id`, one `osd:period_start_raw` over
the whole z12 set). With the `osd:period_*` members absent the same run is exact (main's
`test_tiles_hold_every_feature_with_its_properties_at_max_zoom`); renaming the keys without the
colon does not help, so the key spelling is not the cause.
