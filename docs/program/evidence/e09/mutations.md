# E09 mutations

Each applied alone to the committed code, the unchanged suite run, the file restored.

| Mutation | File | Suite | Failing tests |
|---|---|---|---|
| hash compare dropped | `src/osd/verify.py` | red | test_rejects_mismatched_input_hash |
| level copied (L4 on acceptance) | `src/osd/verify.py` | red | test_no_l4_when_own_l3_absent |
| lower checks copied (own L1-L3 set to pass) | `src/osd/verify.py` | red | test_no_l4_when_own_l3_absent |
| snapshot made a criterion again (older built_at refused) | `src/osd/verify.py` | red | test_snapshot_is_identity_not_a_criterion |
| carry-forward drops the file comparison | `src/osd/verify.py` | red | test_verification_run_with_unchanged_files_keeps_the_conversion |
| carry-forward dropped (network run always skips) | `src/osd/verify.py` | red | test_verification_run_with_unchanged_files_keeps_the_conversion |
| null attribution wording dropped | `src/osd/get.py` | red | test_licence_round_trip_attribution_null |
| record-id compare dropped | `src/osd/verify.py` | red | test_cli_fidelity_from_prints_reasons, test_rejects_mismatched_record_id |
| reason guard dropped | `src/osd/verify.py` | red | test_rejects_failed_input_without_reason, test_rejects_partial_input_without_reason |
| empty-inputs guard dropped | `src/osd/verify.py` | red | test_rejects_empty_inputs |
| coverage guard dropped | `src/osd/verify.py` | red | test_rejects_inventory_file_without_result |
| one-converted guard dropped | `src/osd/verify.py` | red | test_rejects_no_input_converted |
| status coverage dropped | `src/osd/verify.py` | red | test_fixture_fidelity_awards_l4_two_of_two, test_partial_coverage_one_of_two_awards_l4, test_status_shows_coverage_beside_l4 |
| mapper drops a stated statement | `src/osd/manifest.py` | red | test_attribution_statements_verbatim, test_licence_copied_whole, test_licence_round_trip_attribution_null, test_licence_round_trip_every_field_exact | absent case on its own test: green |
| catalog allowed on /1 and /2 | `schema/manifest.schema.json` | red | test_catalog_on_v2_refused |
| /3 without catalog allowed | `schema/manifest.schema.json` | red | test_schema_rejects[format_3], test_v3_without_catalog_refused |
| attribution null allowed on /2 | `schema/manifest.schema.json` | red | test_catalog_on_v2_refused |
| fidelity output without kind allowed | `schema/fidelity.schema.json` | red | test_fidelity_schema_rejects[output_without_kind] |
| digest over ids only | `src/osd/build.py` | red | test_records_digest_changes_with_a_record_or_the_verification, test_records_json_carries_catalog_identity, test_fixture_is_valid_and_names_the_fixture_snapshot |
| built_at inside the digest | `src/osd/build.py` | red | test_records_digest_same_for_same_inputs, test_records_json_carries_catalog_identity, test_fixture_is_valid_and_names_the_fixture_snapshot |
