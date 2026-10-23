# E18 mutations (each against the unchanged suite: tests/test_outlines.py, tests/test_stac.py, tests/test_schema.py; then restored). Rerun after the rebase over E19 (stac-osd ?v=3)

| Mutation | File | Result | pytest | Red tests |
|---|---|---|---|---|
| placeholder rule dropped | `src/osd/outlines/extractors.py` | RED | 4 failed, 128 passed in 19.07s | test_fixture_register_outline_period_members, test_placeholder_is_kept_raw_not_normalised, test_fixture_items_lie_inside_their_collection_and_validate, test_fixture_register_item_periods |
| fallback dropped | `src/osd/stac.py` | RED | 10 failed, 122 passed in 18.69s | test_fixture_items_lie_inside_their_collection_and_validate, test_fixture_register_item_periods, test_item_ids_equal_feature_ids_with_period, test_item_outside_its_collection_fails_validation, test_item_time_and_provenance, test_staged_catalog_collections_and_item_sample_validate_offline |
| reversed accepted | `src/osd/stac.py` | RED | 1 failed, 131 passed in 20.01s | test_fixture_register_item_periods |
| dates read from the record | `src/osd/stac.py` | RED | 10 failed, 122 passed in 20.06s | test_fixture_register_item_periods, test_item_outside_its_collection_fails_validation |
| raw not kept | `src/osd/outlines/extractors.py` | RED | 2 failed, 130 passed in 20.90s | test_fixture_register_outline_period_members, test_placeholder_is_kept_raw_not_normalised |
| mixed provenance labelled feature | `src/osd/stac.py` | RED | 1 failed, 131 passed in 20.89s | test_fixture_register_item_periods |
| containment guard dropped | `src/osd/stac.py` | RED | 1 failed, 131 passed in 19.97s | test_item_outside_its_collection_fails_validation |
| date fields removed from propertyName | `src/osd/outlines/rules.yaml` | RED | 1 failed, 131 passed in 23.35s | test_wfs_requests_carry_the_period_fields |
| zone ignored, not converted | `src/osd/outlines/extractors.py` | RED | 3 failed, 129 passed in 22.48s | test_fixture_register_outline_period_members, test_normalise_period_values, test_fixture_register_item_periods |
| date end read as its first second | `src/osd/outlines/extractors.py` | RED | 4 failed, 128 passed in 23.36s | test_fixture_register_outline_period_members, test_normalise_period_values, test_fixture_register_item_periods |
| start after the collection end accepted | `src/osd/stac.py` | RED | 1 failed, 131 passed in 20.94s | test_fixture_register_item_periods |
| PM hour not added | `src/osd/outlines/extractors.py` | RED | 1 failed, 131 passed in 22.97s | test_normalise_period_values |
| v2 identifier no longer accepted by v3 | `schema/stac-osd.json` | RED | 1 failed, 131 passed in 21.49s | test_stac_osd_1_and_2_documents_validate_under_their_frozen_schemas |
| period_source enum opened | `schema/stac-osd.json` | RED | 1 failed, 131 passed in 21.28s | test_stac_osd_1_and_2_documents_validate_under_their_frozen_schemas |
| period_fields not named in the outline inputs | `src/osd/outlines/__init__.py` | RED | 3 failed, 129 passed in 21.94s | test_derived_features_carry_identity_and_licence, test_fixture_register_outline_period_members, test_outline_2_files_validate_under_outline_2_and_3 |
