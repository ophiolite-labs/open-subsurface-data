# E46 strategy: areas that hold data

Charter: `E46-areas-that-hold-data.md` (Kernel), with the Codex dispositions at its end. Base: main
c3baa16. Gate: `make check`, offline. Two pull requests: slice 0 (contract) then slice 1 (data,
tiles, cache, numbers) stacked on `e46-areas-slice-1`.

## Shape

```
areas/<kind>.geojson, areas/<kind>/<name>.geojson   (area/1, committed; empty in slice 0)
      │  osd validate: schema, ids unique per kind, rings closed, no edge > 180 deg, province country known
      ▼
osd build ── records + outlines/ ──► src/osd/areas.py
      │        positions: outline features (point; line and ring edges, split at +-180),
      │        else bbox middle (never for `national`); intersection with each area part
      │        (vertex in part | edge crosses edge | part vertex in feature polygon), even-odd, half-open
      ▼
build/catalog/areas.json        index (area/1 #/$defs/index): version, kinds{kind: sources[], areas[]}
build/catalog/areas-<kind>.geojson  drawn areas only (#/$defs/drawn): id = stable int, area_id, name, n
build/catalog/records.json      records[].areas {kind: [ids]} for every indexed kind, when any area file exists
build/catalog/areas.pmtiles     slice 1, layers areas_<kind>
```

## Decisions inside the charter's design

- **Ids.** `(kind, area_id)` is the global key. Patterns in area/1: country `^[A-Z]{2}$` (ISO 3166-1
  alpha-2, equal to `region.country`); province `^[A-Z]{2}-[A-Z0-9]{1,3}$` (ISO 3166-2) or
  `^[A-Z]{3}-[0-9]+$` (Natural Earth `adm1_code` when the ISO code is absent or repeated), with a
  mandatory `country`; basin `^usgs-[0-9]+$` (WEP_PRVG province code); licence `^[A-Z]{2}:\S+$`
  (E51). `osd validate` refuses a repeated id within a kind across all its files.
- **Sources.** Each file carries one `source`; the index lists `sources` per kind (one per file,
  `file` = path under `areas/`), each area entry names its `source` file. E51 adds files per country.
  Licence features may carry `blocks` (sorted strings); no other extra property.
- **The count.** Exact on the committed geometry, closed-set intersection by float orientation tests,
  deterministic. A record with outline features uses only them; otherwise its bbox middle (lon wrapped
  when west > east); `national` never uses the bbox and always adds `region.country`. Country fallback
  (not in the first charter text, recorded in the dispositions and inbox note 1): a non-national
  record none of whose positions lies in any country counts for `region.country` when that country
  is an area; offshore registers (Sodir) would otherwise light no country.
- **Stable representation.** The index always has `country`, `province`, `basin`, plus any other kind
  with a file. When at least one area file exists every record has `areas` with exactly the index's
  kinds (empty lists allowed); with none, no record has the key (acceptance 3).
- **Labels.** Largest part by planar area; its ring centroid when inside, else the middle of the widest
  inside span of the horizontal line through the centroid. Six decimals, like outlines.
- **Drawn feature id.** First 6 bytes of sha256(`kind:area_id`) as an integer: stable across builds,
  JS-safe.
- **Speed (slice 1).** Per-part latitude bands of edges and a 1-degree cell index of part boxes; a
  record skips areas it already sits in. Cache: one file per area-set digest under `build/areas-cache/`,
  keyed per record by outline bytes and region, written by the live build only, atomically; never
  published.
- **Preparation (slice 1).** `osd areas prepare <kind> <file>` reads GeoJSON or a polygon Shapefile
  (zip, .shp/.dbf read by a small reader in the package, no dependency, no external tool); the source
  fields other than `sha256` come from `areas/prepare.yaml`; simplifies to zoom 8; splits at +-180.

## Acceptance -> test (tests/test_areas.py unless named)

| Line | Test |
|---|---|
| 1 area/1 exists | `test_area_schema_id_is_area_1` |
| 1 record/6, old files valid | `tests/test_schema.py::test_record_5_fixtures_validate_under_record_5_and_record_6` |
| 1 `national: "yes"` invalid, record/5 refuses `national` | `test_schema.py::test_record_6_national_is_a_boolean_and_needs_a_country` |
| 2 golden byte for byte | `test_fixture_areas_json_equals_the_golden_file` |
| 2 six records one by one | `test_register_with_wells_lights_two_basins_and_not_its_box`, `test_survey_across_a_border_lights_both_countries_and_a_basin_its_line_crosses`, `test_bbox_only_dataset_counts_by_its_box_middle`, `test_national_dataset_lights_its_country_only`, `test_dataset_with_nothing_lights_nothing`, `test_box_middle_in_the_sea_falls_back_to_its_country` |
| 3 empty `areas/` | `test_empty_areas_dir_writes_empty_index_and_no_record_key` |
| F12 outputs valid | `test_fixture_outputs_validate_and_agree_both_ways` |
| 7 hole | `test_point_beyond_a_hole_is_outside` |
| 7 antimeridian | `test_area_edge_over_180_degrees_refused`, `test_feature_crossing_the_antimeridian_is_split` |
| 7 bbox only without outline | covered by the register test (its box middle is in XB-E) |
| 7 empty licence refused | `test_validate_refuses_empty_source_licence` |
| F15 duplicates, sea, crossing | `test_validate_refuses_a_repeated_area_id`, the survey test (line crossing with no vertex inside) |
| 4–6, 8, F13, F19 | slice 1: `test_real_areas_*`, `test_cache_*`, `test_prepare_reaches_no_network` |

Mutations (each shown red, listed in the PR): hole ignored; edge crossing skipped; bbox middle used
with outlines; `national` using its bbox; country fallback removed; `minLength` on licence dropped;
duplicate-id check removed; 180-degree edge check removed; antimeridian split skipped.
