| Mutation | File | Unchanged suite under the mutation |
|---|---|---|
| cap 20 -> 30 GB | `src/osd/mirror.py` | RED: test_not_eligible_over_cap[declared], test_not_eligible_over_cap[inventory] |
| checksum requirement dropped | `src/osd/mirror.py` | RED: test_not_eligible_missing_checksum |
| redistribution check dropped | `src/osd/mirror.py` | RED: test_cli_put_eligible_remove, test_mirror_refuses_ineligible, test_not_eligible_rights[forbidden], test_not_eligible_rights[restricted], test_not_eligible_rights[unknown], test_not_eligible_volve_unknown |
| level check dropped | `src/osd/mirror.py` | RED: test_not_eligible_below_l2, test_not_eligible_without_inventory_or_rule |
| blocked/dead check dropped | `src/osd/mirror.py` | RED: test_not_eligible_blocked_origin |
| completeness (unhashed) check dropped | `src/osd/mirror.py` | RED: test_inventory_counts_against_the_run_budget, test_not_eligible_one_unhashed_entry |
| hash compare before move dropped | `src/osd/mirror.py` | RED: test_corrupted_stream_leaves_no_public_key |
| published state not recognised | `src/osd/mirror.py` | RED: test_rerun_after_interruption, test_takedown |
| staging not reused | `src/osd/mirror.py` | RED: test_rerun_after_crash_before_move |
| tombstone check dropped | `src/osd/mirror.py` | RED: test_cli_put_eligible_remove, test_interrupted_takedown_already_drops_the_copy_and_reruns, test_takedown |
| custody validation before publish dropped | `src/osd/mirror.py` | RED: test_no_public_copy_without_a_valid_custody_document |
| index includes removed copies | `src/osd/mirror.py` | RED: test_interrupted_takedown_already_drops_the_copy_and_reruns |
| get: mirror bytes accepted unverified | `src/osd/get.py` | RED: test_cli_get_summary_names_share_alike, test_get_corrupt_byte_is_mismatch, test_get_mirror_mismatch_then_origin, test_mismatch_leaves_existing_file_untouched |
| get: no fallback to origin | `src/osd/get.py` | RED: test_get_falls_back_when_mirror_unreachable, test_get_mirror_mismatch_then_origin |
| custody: takedown not required | `schema/custody.schema.json` | RED: test_custody_rejects[missing-contact] |
| custody: object size not compared | `src/osd/custody.py` | RED: test_custody_rejects[inconsistent-size], test_custody_rejects_size_unlike_the_object |
| manifest/1 alternates allowed | `schema/manifest.schema.json` | RED: test_manifest_v1_refuses_alternates |
| inventory: partial reported complete | `src/osd/mirror.py` | RED: test_inventory_counts_against_the_run_budget |
