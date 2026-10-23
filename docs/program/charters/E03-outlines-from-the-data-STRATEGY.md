# E03 strategy: outlines from the data

Charter: `E03-outlines-from-the-data.md` (Kernel). Base: main 37c010c (E02 merged). Written at
lane open, 23 Oct; measured against the live publishers the same day.

## Shape

```
records/<id>.yaml  inputs: [{name, url, crs, format, units?}]   publisher facts (record/2)
src/osd/outlines/rules.yaml   per id: min_features, per input: extractor, fields, paging   (OSD-D11)
        |
osd verify --outlines  --opener-->  build/inputs/<id>/<input>/<parts> + SHA256SUMS
        |                            (the verifier's injected Opener, paced, robots.txt obeyed)
derive(): pure over local bytes --> outlines/<id>.geojson (committed, OSD-D12)
        |                            register-wfs | register-csv | segy-hull | publisher-file
outline-derived check: every feature derived, the collection's inputs {url, sha256} == stored inputs,
        count >= rules min_features --> pass; L3 = L2 + outline checks (ladder unchanged)
```

- An input's `sha256` is the sha256 of the input's `SHA256SUMS` (one `sha256sum` line per fetched part,
  in fetch order): one rule for single files, WFS pages and MDIO chunks alike.
- An input is refused, with the reason, when its CRS is not declared (record `crs` absent, or a
  response that declares another), its units are not declared (SEG-Y measurement system 0 and no
  record `units`, or units that disagree with the CRS axis), the response is empty, a WFS hit count
  disagrees with the features read, a ring is open or empty, or two features share a `feature_id`.
  A refused input writes no outline; the old file stays and is reported.
- Transform: `pyproj`, `always_xy=True`; coordinates are read as (east, north) as served and
  rounded to 6 decimals (0.11 m). Hull: Andrew's monotone chain over every live trace.
- MDIO (Poseidon) is read without a new dependency: a 60-line blosc/LZ4 decoder for the
  `trace_mask` chunks and the trace-header chunks holding the hull vertices (cdp-x, cdp-y,
  `scalar_apply_coords`), so `segy-hull` serves SEG-Y files and MDIO stores alike. `segyio` is not
  added: the trace-header reader is `struct` over bytes 71, 181, 185 (rule-bound, so the x/y swap
  mutation is one edit).

## Targets as measured on 23 Oct

| id | input | expected |
|---|---|---|
| sodir/factpages | FactMaps WFS 2.0 (GeoJSON, EPSG:4326): `Wellbores__all` (9869), seismic finished/ongoing/paused | solid; L3 (L2 passes today) |
| nlog/nlog | GDN WFS: `gdw_ng_wll_all_utm` (6738, EPSG:23031), `gdw_ng_smc_grid_utm` (482, EPSG:4230) | solid; L3 after `manifest_url` (the borehole listing) and a samples entry (supervisor answer 3) |
| nopims/poseidon | TGS MDIO on S3, CRS from the registry page (GDA94 / MGA 51 = EPSG:28351), units m in `.zattrs` | solid; L3 |
| nzpam/parihaka, nzpam/kerry-3d | the survey page's "Survey Extents in GeoJSON" (RFC 7946, WGS84) | solid; L1 only: no machine listing (resources behind a human check and RealMe), reported |
| terranubis/f3-demo-2020 | download behind TerraNubis registration | dashed, reported (login) |
| rmotc/teapot-dome | EDX login | dashed, reported (login) |

Sodir's WFS capabilities carry empty `Fees`/`AccessConstraints`. Sodir's own catalogue entries in
Geonorge (FactMapsData, FactMaps service) state NLOD; that is taken as the publisher's licence
statement for the outlines (accepted, OSD-D15; the record's known_issues names the NLOD 1.0 / 2.0
difference between the catalogue and the terms page).

## Ruled during the lane

- OSD-D16 (amended by answers E03-2, E03-3): survey polygons simplified by Douglas-Peucker in
  the extractor (`simplify_m`, default 50 m, recorded as `simplified_m`); rings below
  `simplify_m`² dropped; 2D surveys written as exteriors only (`exteriors_only`); polygon positions
  rounded to 5 decimals (`polygon_decimals`); dropped rings counted in `rings_dropped`; the rules
  applied are named in `source`. Points exact. Input identity and licence are carried once per file
  (`inputs: {name: {url, sha256}}`, `licence`); features name their `input`. Size: under 2 MB per
  file, register outlines up to 8 MB until a tiling lane (E05).
- Publisher positions that are absent (`[nan,nan]`, `{"type":"MultiPolygon",}` in FactMaps) are
  listed in the collection's `unplaced` member when the rule says `unplaced: report`, never drawn
  and never guessed.
- Sodir numbers wellbores and surveys from one NPDID sequence: the rule's `id_scope` makes the
  feature_id `<record-id>#wellbore/<npdid>` and `#survey/<npdid>`.

## Acceptance to test (`tests/test_outlines.py`)

| Acceptance line | Test |
|---|---|
| Sodir wellbore ids equal the frozen paginated fixture's id set, unique | `test_sodir_wellbore_ids_equal_the_fixture_id_set` |
| NLOG boreholes, same shape | `test_nlog_borehole_ids_equal_the_fixture_id_set` |
| NLOG 3D surveys, same shape | `test_nlog_3d_survey_ids_equal_the_fixture_id_set` |
| F3 hull from an irregular trace-header fixture matches the listed exact hull to 1 m | `test_segy_hull_matches_the_known_exact_hull` |
| hull replaced by a bounding box fails it | mutation on `convex_hull` (PR body) |
| x/y header bytes swapped fail the known-coordinate test | `test_segy_known_coordinate_and_axis_order`, mutation on the rule bytes |
| known coordinates and axis order through pyproj | `test_transform_known_coordinates_and_axis_order` |
| missing `inputs` never reaches pass | `test_missing_inputs_never_passes` |
| empty response | `test_empty_response_never_passes` |
| undeclared CRS | `test_undeclared_crs_never_passes` |
| undeclared units | `test_undeclared_units_never_passes` |
| a feature with `approximate: true` | `test_approximate_feature_never_passes` |
| a duplicate `feature_id` | `test_duplicate_feature_id_never_passes` |
| L3 for a reached target; L3 still requires L2 | `test_derived_outline_with_stored_inputs_is_L3`, `test_derived_outline_without_L2_is_not_L3` |
| check compares with the stored inputs and the rules count | `test_changed_input_bytes_fail_outline_derived`, `test_feature_count_below_rules_fails` |
| every version-1 record still validates under record/2 | `test_every_version_1_record_validates_under_record_2` |
| derived features carry the contract (design 4, OSD-D13) | `test_derived_features_carry_identity_and_licence`, `test_derived_feature_without_identity_is_a_problem` (a feature naming an input the collection lacks), `test_open_ring_is_a_problem` |
| unplaced and namespaced ids | `test_wellbores_without_a_position_are_listed_not_drawn`, `test_surveys_without_an_area_are_listed_not_drawn`, `test_overlapping_publisher_ids_are_scoped_not_collided` |
| OSD-D16 | `test_survey_polygons_are_simplified_within_tolerance_points_exact`, `test_rings_below_tolerance_squared_are_dropped_and_counted`, `test_polygon_rules_are_named_in_the_derivation` |
| CI checks the committed file, never rewrites it | `test_outline_inputs_check_the_committed_file_and_outlines_rewrite_it` |
| supporting guards | `test_blosc_lz4_decodes_a_real_chunk`, `test_mdio_hull_from_frozen_poseidon_chunks`, `test_wfs_hit_count_mismatch_is_refused`, `test_fetch_stores_parts_and_sums`, `test_publisher_page_extent`, `test_register_csv_ids_equal_the_fixture_id_set`, `test_rules_name_records_with_inputs` |

After the run: `uv run osd status` in the PR body, the Sodir table-page count recorded by hand in
`docs/program/evidence/e03/`, a screenshot of Norway with solid outlines.

## Outside the claim, declared

`src/osd/cli.py` (the `--outlines` flag), `tests/conftest.py` (the shared outline fixture gains
the four derived-feature properties outline/2 requires), `uv.lock` (pyproj): added to the claim
by the supervisor (answer 2). `.github/workflows/verify.yml` for the outlines flag only, and
`origin.manifest_url` plus `src/osd/verifier/samples.yaml` entries for the seven targets (answer 3). `outline.schema.json` moves to outline/2 with a test that the placeholder files still validate.

## Not done here

PMTiles and rendering (E05). The verify workflow runs `osd verify --outline-inputs`: it fetches the
inputs and checks the committed outline against them, and never rewrites it; `--outlines` (fetch,
derive, rewrite) is a reviewed local run whose diff is committed.
