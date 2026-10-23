# E18: the two registers after `osd verify --outlines sodir/factpages nlog/nlog` (23 Oct 2026)

Run from ophiolite-epic-01, 8 min 30 s; both records L3, `outline-derived` pass (Sodir 11,210
features from 4 inputs, 2,589 listed without a position; NLOG 7,220 from 2 inputs).

## Items per register (`stac.item_period` over the committed outlines)

| Register | Collection period (the record's) | feature | feature-start,collection-end | collection | min feature start | max feature end | outside the Collection |
|---|---|---|---|---|---|---|---|
| sodir/factpages | 1966-01-01T00:00:00Z to 2026-10-23T23:59:59Z | 10,545 | 111 | 554 | 1966-07-19T00:00:00Z | 2026-10-19T23:59:59Z | 0 |
| nlog/nlog | 1800-01-01T00:00:00Z to 2026-10-23T23:59:59Z | 6,735 | 3 | 482 | 1800-01-01T00:00:00Z | 2026-10-11T23:59:59Z | 0 |

By input: Sodir wellbores 9,151 / 107 / 547 (the 547 state neither date), seismic-finished
1,394 / 0 / 7 (4 without a start, 3 reversed, e.g. survey/7498 `8/24/2011` to `8/23/2011`),
seismic-ongoing 0 / 3 / 0, seismic-paused 0 / 1 / 0; NLOG boreholes 6,735 / 3 / 0, surveys-3d
0 / 0 / 482 (no acquisition date on the layer, stop rule). No raw value failed to normalise.
Containment: no Item of either register leaves its Collection, so both registers carry their
own dates in this lane; `make check-full` on the built tree: `18525 STAC objects valid`.

## Named Items, before (main 20750f4) and after

| Item (file under site/data/stac/) | Before | After | osd:period_source |
|---|---|---|---|
| `sodir/factpages#survey/10003` (`sodir--factpages/items/survey_10003-0fb87e59.json`) | 1966-01-01T00:00:00Z to 2026-10-23T23:59:59Z | 2021-05-01T14:19:33Z to 2021-06-03T07:07:27Z | feature |
| `sodir/factpages#wellbore/2` (`sodir--factpages/items/wellbore_2-f362f84c.json`) | 1966-01-01T00:00:00Z to 2026-10-23T23:59:59Z | 1983-02-15T00:00:00Z to 1983-05-08T23:59:59Z | feature |
| `sodir/factpages#survey/11193` (`sodir--factpages/items/survey_11193-84cb6ba2.json`, ongoing) | 1966-01-01T00:00:00Z to 2026-10-23T23:59:59Z | 2026-08-15T09:35:11Z to 2026-10-23T23:59:59Z | feature-start,collection-end |
| `nlog/nlog#K18-KOTTER-01` (`nlog--nlog/items/K18-KOTTER-01.json`) | 1800-01-01T00:00:00Z to 2026-10-23T23:59:59Z | 1984-07-02T00:00:00Z to 1984-09-19T23:59:59Z | feature |
| `nlog/nlog#20050718-1` (`nlog--nlog/items/20050718-1.json`, 3D survey) | 1800-01-01T00:00:00Z to 2026-10-23T23:59:59Z | unchanged | collection |

## Outline diff

Every feature line changed and no other member did: feature ids, geometry, every pre-E18
property and `unplaced` are equal to main for all 11,210 + 7,220 features; each feature gains
`osd:period_*` members, each input of a dated layer gains `period_fields`. Input sha256s changed
because the requests now ask for the date fields (Sodir: all four; NLOG boreholes); NLOG
surveys-3d changed with the same request (the publisher's bytes moved since E03). Sizes: Sodir
4.29 MB to 5.89 MB, NLOG 2.64 MB to 3.66 MB (OSD-D16 allows 8 MB).

## Tiles

With the date members in the map layer, tippecanoe 2.49 wrote three wrong values into z12 tiles
(`nlog/nlog#WAS-17` publisher_id `2012-12-24`; `sodir/factpages#wellbore/5250`
`osd:period_start_raw` `1955-05-20` for `3/2/2006`; seen with `tippecanoe-decode` too) and
`test_tiles_hold_every_feature_with_its_properties_at_max_zoom` went red. `build()` leaves the
`osd:period_*` members out of `outlines.geojson`/`outlines.pmtiles` (the map does not read
them); the tiles are then the same 60.9 MB as on main and the test is green.

## Post-publication check (after merge, verify on main)

`curl -s https://opensubsurfacedata.org/data/stac/<file>` for each file in the named table
shows the "After" bounds and source.

The two decoded features are kept under `tippecanoe/` for a later tiles lane.
