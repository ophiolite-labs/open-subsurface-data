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

## Slice 2 (E07s2, 28 Oct): the S3 transport, the dry run, the custody refresh, the workflow

Each mutation applied alone to the slice 2 head, `uv run pytest tests/test_mirror.py` run unchanged, then restored.

| Mutation | File | Unchanged suite under the mutation |
|---|---|---|
| signature: query not sorted | `src/osd/mirror.py` | RED: test_sigv4_matches_aws_example |
| signature: range header not signed | `src/osd/mirror.py` | RED: test_sigv4_matches_aws_example |
| payload hash unsigned (UNSIGNED-PAYLOAD) | `src/osd/mirror.py` | RED: test_cli_dry_run_and_custody_on_s3, test_custody_sync_feeds_the_build, test_custody_sync_keeps_the_old_set_when_a_document_is_bad, test_put_dry_run_writes_nothing, test_s3_acl_on_public_keys_only, test_s3_copy_error_in_200, test_s3_corrupted_stream_leaves_no_public_key, test_s3_keys_paginate, test_s3_large_copy_in_ranges, test_s3_mirror_three_files, test_s3_multipart_upload, test_s3_origin_failure_aborts_multipart, test_s3_rerun_after_interruption_and_crash_before_move, test_s3_takedown, test_s3_wrong_key_is_refused_without_showing_it |
| multipart: last part dropped | `src/osd/mirror.py` | RED: test_s3_multipart_upload |
| no abort on a failed upload | `src/osd/mirror.py` | RED: test_s3_origin_failure_aborts_multipart |
| copy error inside a 200 ignored | `src/osd/mirror.py` | RED: test_s3_copy_error_in_200 |
| ACL public-read on every key (staging too) | `src/osd/mirror.py` | RED: test_s3_acl_on_public_keys_only |
| dry run ignored (writes) | `src/osd/mirror.py` | RED: test_cli_dry_run_and_custody_on_s3, test_put_dry_run_writes_nothing |
| custody refresh keeps stale documents | `src/osd/mirror.py` | RED: test_custody_sync_feeds_the_build |
| custody refresh unchecked | `src/osd/mirror.py` | RED: test_custody_sync_keeps_the_old_set_when_a_document_is_bad |
| workflow: put on branch dispatches | `.github/workflows/verify.yml` | RED: test_workflow_keys_only_on_dispatch |
| workflow: keys on pull-request runs | `.github/workflows/verify.yml` | RED: test_workflow_keys_only_on_dispatch |
