# E18 mutations (each against the unchanged suite: tests/test_outlines.py + tests/test_stac.py, then restored)

| Mutation | File | Result | pytest | Red tests |
|---|---|---|---|---|
| placeholder rule dropped | `src/osd/outlines/extractors.py` | RED | 4 failed, 94 passed in 22.44s | test_fixture_register_outline_period_members, test_placeholder_is_kept_raw_not_normalised, test_fixture_items_lie_inside_their_collection_and_validate, test_fixture_register_item_periods |
| fallback dropped | `src/osd/stac.py` | RED | 10 failed, 88 passed in 18.58s | test_fixture_items_lie_inside_their_collection_and_validate, test_fixture_register_item_periods, test_item_ids_equal_feature_ids_with_period, test_item_outside_its_collection_fails_validation, test_item_time_and_provenance, test_staged_catalog_collections_and_item_sample_validate_offline |
| reversed accepted | `src/osd/stac.py` | RED | 1 failed, 97 passed in 25.38s | test_fixture_register_item_periods |
| dates read from the record | `src/osd/stac.py` | RED | 10 failed, 88 passed in 20.88s | test_fixture_register_item_periods, test_item_outside_its_collection_fails_validation |
| raw not kept | `src/osd/outlines/extractors.py` | RED | 2 failed, 96 passed in 19.06s | test_fixture_register_outline_period_members, test_placeholder_is_kept_raw_not_normalised |
| mixed provenance labelled feature | `src/osd/stac.py` | RED | 1 failed, 97 passed in 18.73s | test_fixture_register_item_periods |
| containment guard dropped | `src/osd/stac.py` | RED | 1 failed, 97 passed in 17.88s | test_item_outside_its_collection_fails_validation |
| date fields removed from propertyName | `src/osd/outlines/rules.yaml` | RED | 1 failed, 97 passed in 19.29s | test_wfs_requests_carry_the_period_fields |
| zone ignored, not converted | `src/osd/outlines/extractors.py` | RED | 3 failed, 95 passed in 19.19s | test_fixture_register_outline_period_members, test_normalise_period_values, test_fixture_register_item_periods |
| date end read as its first second | `src/osd/outlines/extractors.py` | RED | 4 failed, 94 passed in 19.21s | test_fixture_register_outline_period_members, test_normalise_period_values, test_fixture_register_item_periods |
| start after the collection end accepted | `src/osd/stac.py` | RED | 1 failed, 97 passed in 18.13s | test_fixture_register_item_periods |
| PM hour not added | `src/osd/outlines/extractors.py` | RED | 1 failed, 97 passed in 19.15s | test_normalise_period_values |
| v1 URL validated by the current schema | `schema/stac/schema-map.json` | RED | 1 failed, 97 passed in 19.11s | test_stac_osd_1_documents_validate_under_their_frozen_schema |
| period_fields not named in the outline inputs | `src/osd/outlines/__init__.py` | RED | 3 failed, 95 passed in 18.50s | test_derived_features_carry_identity_and_licence, test_fixture_register_outline_period_members, test_outline_2_files_validate_under_outline_2_and_3 |
