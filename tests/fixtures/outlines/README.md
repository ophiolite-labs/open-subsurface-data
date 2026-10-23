# Frozen responses for tests/test_outlines.py

Fetched 23 Oct 2026 from the publishers' own services. Each directory is laid out as
`osd verify --outlines` stores an input: `<record id with __>/<input name>/<parts>`.

| Fixture | Request | Truncation |
|---|---|---|
| `sodir__factpages/wellbores` | FactMaps WFS 2.0 `Wellbores__all`, GeoJSON, `propertyName=Wellbore_name,NPDID_wellbore,SHAPE`, `count=3`, `startIndex` 0, 3, 6; `resultType=hits` | `page-000006` cut from 3 to 2 features (a short last page ends paging); `hits` numberMatched edited 9869 -> 8 |
| `sodir__factpages/seismic-finished` | `Seismic_surveys__finished`, `propertyName=Survey_name,NPDID_for_survey,Sub_type,Net_or_gross,SHAPE`, `count=2`, `startIndex` 0, 2, 4 | `page-000004` cut to its net feature; `hits` 4560 -> 5 |
| `sodir__factpages/wellbores-unplaced` | `Wellbores__all` page at `startIndex=136` (count 3) | cut to 3 features; NPDID 139 is served as `[nan,nan]` (FactMaps' wellbore without a position) |
| `sodir__factpages/seismic-unplaced` | `Seismic_surveys__finished` page at `startIndex=547` (count 2) | cut to 2 features; NPDID 2000 is served as `{"type":"MultiPolygon",}` (a survey without an area) |
| `nlog__nlog/boreholes` | GDN WFS `nlog:gdw_ng_wll_all_utm`, `application/json`, `count=3`, `startIndex` 0, 3, 6 | `page-000006` cut to 2 features; `hits` 6738 -> 8 |
| `nlog__nlog/surveys-3d` | `nlog:gdw_ng_smc_grid_utm`, `count=2`, `startIndex` 0, 2 | `page-000002` cut to 1 feature; `hits` 482 -> 3 |
| `nopims__poseidon/full-stack-agc` | `s3://tgs-opendata-poseidon/full_stack_agc.mdio/`: `.zmetadata`, all four `trace_mask` chunks, the four corner `headers` chunks | none (the store holds 1080 header chunks; only those the hull needs are fetched) |
| `nzpam__parihaka/survey-extent`, `nzpam__kerry-3d/survey-extent` | `https://geodata.nzpam.govt.nz/survey/<id>` | page cut to its `<title>` and the "Survey Extents in GeoJSON" table row |
| `segy/irregular.sgy` | synthetic, written by `segy/make_segy.py` | none: an irregular survey with a known exact hull and one dead trace |
| `schema/*-1.schema.json` | `schema/record.schema.json` and `schema/outline.schema.json` at 37c010c | frozen version 1, for the still-validates tests |

Edited counts keep the hit-count guard meaningful on truncated pages;
`test_wfs_hit_count_mismatch_is_refused` restores the real 9869 and expects a refusal.
