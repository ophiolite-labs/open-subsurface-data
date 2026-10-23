# E29 mutations (23 Oct 2026, each applied alone to the committed code, suite: tests/test_outlines.py, tests/test_stac.py, tests/test_records.py; restored after)

| mutation | edit in `src/osd/outlines/extractors.py` | suite result | failing tests |
|---|---|---|---|
| count check removed | `if len(seen) != count:` -> `if False:` | RED: 1 failed, 133 passed in 27.26s | test_arcgis_count_mismatch_is_refused |
| duplicate check removed | `if a[oid] in seen:` -> `if False:` | RED: 1 failed, 133 passed in 23.67s | test_arcgis_duplicate_object_ids_are_refused |
| page error swallowed | `_arcgis_error(page, what)` -> `pass` | RED: 1 failed, 133 passed in 23.53s | test_arcgis_page_error_is_refused |
| cap ignored | `if n > ARCGIS_MAX_FEATURES:` -> `if False:` | RED: 1 failed, 133 passed in 23.85s | test_arcgis_layer_above_the_cap_is_refused |
| wkid check removed | `if rec_input.get("crs") not in served:` -> `if False:` | RED: 1 failed, 133 passed in 25.27s | test_arcgis_wkid_mismatch_is_refused |
| hole dropped | `min(owner, key=lambda poly: abs(_signed_area(poly[0]))).append(h[::-1])` -> `pass` | RED: 2 failed, 132 passed in 25.34s | test_esri_json_geometries_match_geojson_fixtures[polygon-two-exteriors], test_esri_json_geometries_match_geojson_fixtures[polygon-with-hole] |
| date field dropped | `*(rule.get("period_fields") or {}).values(),` -> `(removed)` | RED: 3 failed, 131 passed in 23.90s | test_arcgis_feature_dates_are_exact, test_arcgis_register_items_equal_the_object_ids, test_arcgis_requests_page_by_object_id |
| off-by-a-day conversion | `when = EPOCH + timedelta(milliseconds=int(raw))` -> `when = EPOCH + timedelta(milliseconds=int(raw), days=1)` | RED: 6 failed, 128 passed in 23.33s | test_arcgis_feature_dates_are_exact, test_arcgis_register_items_equal_the_object_ids, test_epoch_ms_period_values[-3281857200000-1866-01-01T13:00:00Z], test_epoch_ms_period_values[0-1970-01-01T00:00:00Z], test_epoch_ms_period_values[1733356800000-2024-12-05T00:00:00Z], test_epoch_ms_period_values[1733356800123-2024-12-05T00:00:00.123Z] |

Unmutated: 134 passed.
