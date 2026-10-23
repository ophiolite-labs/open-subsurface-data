# E29 strategy: outlines from the registers' map services

Authority: `E29-outlines-from-the-map-services.md` (Kernel, Codex round done). Base: main 1621487.
Lane-open facts measured 23 Oct from the VPS: `docs/program/evidence/e29/sources.md`.

## What the lane-open check changed (dispositions of the charter wording, supervisor answer 23 Oct)

- **Esri JSON only (`f=json`), never `f=geojson`.** ArcGIS Server's GeoJSON is reprojected to WGS84
  and carries no `spatialReference` (Virginia 102747/2284, North Dakota 102100/3857, SGUDDS
  102067/5514, checked live). The charter's wkid check and "transform from the declared crs as the
  WFS path does" exist only on Esri JSON; GeoJSON would be transformed twice.
- **Object id field**: the description's `objectIdField`, else its one `esriFieldTypeOID` field
  (MapServer descriptions here carry no `objectIdField`). Neither: refused.
- **`outFields` = the fields the rule names** (object id, uwi, name, kind field, period fields), not
  `*`: the parts' sha256 is the L3 identity; `*` changes it with every attribute edit of a nightly
  register and doubles the page size. Same role as WFS `propertyName`.
- **Polylines with several paths are MultiLineString** (959 of 990 NZP&M 2D lines): `records.py`
  `geometry_problems` gains MultiLineString and MultiPoint branches (granted, note 4).
- **L3 sits on L2.** BCER, SGC, UT DOGM, Virginia and North Dakota stay L1 (the verifier's ArcGIS
  listing export is partial above `maxRecordCount`; listing reader out of scope), SGUDDS's page
  answers 403 to the runner. The live line reads "L3, or the first failing check named per record";
  the listing-reader paging is a follow-up slice after merge (supervisor, answer 1).
- **Gate budget: four outlines committed, five held** (supervisor, answer 5; measurement in
  `docs/program/evidence/e29/gate-budget.md`). SGUDDS, NZP&M x2 and WA DEMIRS carry outlines;
  Virginia, BCER, SGC, UT DOGM and North Dakota carry inputs, period and rules only (all nine
  outlines would take `make check` to ~6 min on CI). E32 lands the other five.
- **The stored layer part is the description's facts, not its bytes**: object id field, OID fields,
  pagination, maxRecordCount, geometry type, spatial reference, canonical JSON. WA SLIP's
  load-balanced nodes serve different `drawingInfo` (seen 23 Oct: the dispatch failed WA's
  `outline-derived` with identical features); test `test_arcgis_input_identity_ignores_the_description_beyond_its_facts`.
- **Lines across the antimeridian are cut at ±180** (RFC 7946 §3.1.9; ten NZP&M 2D lines step from
  179.9 to -179.9): `geometry.split_antimeridian`, test `test_lines_across_the_antimeridian_are_cut_there`.

## Design

```
record input {name, url: layer URL, format: arcgis, crs: EPSG:n, stated}       record/5
rules.yaml   {extractor: register-arcgis, kind, uwi?, name, period_fields, period_format: epoch-ms}
fetch_parts  layer   <- url?f=json             _arcgis_layer: pagination, oid field, maxRecordCount
             count   <- url/query?returnCountOnly=true   _arcgis_count: >0, <= 50,000 (the cap)
             page-N  <- url/query?outFields=..&orderByFields=<oid> ASC&resultOffset=N
                        &resultRecordCount=maxRecordCount&f=json   for N in 0, max, .. < count
register_arcgis (pure, over stored parts): every page present, none short but the last, no
  `error`, spatialReference wkid or latestWkid == crs, object ids unique, their number == count;
  esri_geometry() -> GeoJSON in native coordinates -> to_wgs84(crs) (the WFS path's transform);
  null geometry -> unplaced; feature key = object id (Item id = <record>#<oid>).
```

- Esri rings: clockwise exteriors, counter-clockwise holes (shoelace sign in native x/y); each hole
  goes to the exterior containing its first vertex, none: refused; output rings in RFC 7946 order.
  One exterior: Polygon, several: MultiPolygon. Paths: one LineString, several MultiLineString.
- `period_instant(raw, bound, "epoch-ms")`: integer milliseconds -> RFC 3339 UTC, raw kept in
  `osd:period_*_raw` (E18's members, provenance rules and containment unchanged).
- Every refusal is `Refused` (JSON that does not parse included), so `derive_outline` reports it and
  `outline-derived` fails; levels come from today's checks only (a record that was L3 drops).
- record/5: `inputs[].format` gains `arcgis`; record/4 frozen as `tests/fixtures/schema/record-4.schema.json`.
- Periods for the six without one (E16 design 2): earliest date the register's own layer states
  (outStatistics, UTC day) to today where the publisher says it updates (BCER nightly, SGUDDS
  continuously), else to the latest such date; `stated` names the field and query time.
- Budget: one record at a time in size order; the all-record dispatch on the branch measures it.

## Acceptance to tests

| Acceptance line | Test |
|---|---|
| pages reassemble the layer with the exact object-id set | `test_outlines.py::test_arcgis_pages_reassemble_the_object_id_set` |
| duplicates refuse | `test_arcgis_duplicate_object_ids_are_refused` |
| a missing page refuses | `test_arcgis_missing_page_is_refused` |
| a page error refuses (HTTP and `error` JSON) | `test_arcgis_page_error_is_refused` |
| a count mismatch refuses | `test_arcgis_count_mismatch_is_refused` |
| no pagination support / no object id field refuses | `test_arcgis_without_pagination_or_object_ids_is_refused` |
| wkid mismatch refuses | `test_arcgis_wkid_mismatch_is_refused` |
| the 50,000 cap | `test_arcgis_layer_above_the_cap_is_refused` |
| point, two-path polyline, polygon with a hole, two-exterior polygon == GeoJSON fixtures | `test_esri_json_geometries_match_geojson_fixtures[...]` |
| native CRS transformed like the WFS path | `test_arcgis_native_coordinates_transform_like_wfs` |
| epoch-ms dates == given RFC 3339 strings, feature dates distinct from the collection's | `test_arcgis_feature_dates_are_exact`; `test_epoch_ms_period_values` |
| request names oid order, offset, maxRecordCount, rule fields; no outSR, f=json | `test_arcgis_requests_page_by_object_id` |
| refused input fails outline-derived; an L3 record is demoted | `test_refused_arcgis_input_demotes_an_l3_record` |
| STAC Item id set == object-id set; exact dates, `feature`; suppressing Items fails | `test_outlines.py::test_arcgis_register_items_equal_the_object_ids` |
| record/5, record/4 frozen, one fixture set under both, every record under record/5 | `test_schema.py::test_record_4_fixtures_validate_under_record_4_and_record_5`, `test_record_ids_are_versioned`, `test_record_5_admits_arcgis_and_record_4_refuses_it` |
| MultiLineString, MultiPoint geometry rules | `test_outlines.py::test_multilinestring_parts_follow_linestring_rules`, `test_multipoint_parts_follow_point_rules` |
| rules for the nine | `test_rules_name_records_with_inputs` (existing) |

Mutations (each red against the unchanged suite, then restored; results in
`docs/program/evidence/e29/mutations.md`): count check removed; duplicate check removed; page error
swallowed; cap ignored; wkid check removed; hole dropped; date field dropped from `outFields`;
off-by-a-day conversion.

Live: `osd verify --outlines <id>` per register in size order (SGUDDS, NZP&M x2, WA, Virginia,
BCER, SGC, UT, North Dakota), outlines reviewed and committed one register per commit, then one
all-record dispatch of `verify.yml` on the branch (`ids` empty); `make check-full` on its
downloaded results; PR table: record, layer, count on the day, level, Items.

## Commits

1. Strategy and lane-open evidence. 2. record/5 with frozen record/4. 3. ArcGIS adapter, geometry
branches and fixtures. 4. Dates and STAC. 5..n. Records, rules and outlines, one register each.
