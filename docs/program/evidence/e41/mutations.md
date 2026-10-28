# E41 mutations

Each row: one change to the code, the tests run (`pytest -x -k <design's tests>`), and the first
test that went red. Applied and restored by a throwaway script (apply, run, restore the file); none
is committed. "red" is the expected result.

## C2, design 1: deposit (acceptance 1, 2)

| File | Mutation | Result | First red test |
|---|---|---|---|
| `src/osd/mirror.py` | streamed digest no longer compared with the first pass | red | test_deposit_swapped_digests_refused |
| `src/osd/mirror.py` | the walker no longer refuses a symlink | red | test_deposit_symlink_refused_by_name |
| `src/osd/mirror.py` | cap `>=` → `>` (exactly CAP_BYTES admitted) | red | test_deposit_refuses_exactly_the_cap |
| `src/osd/mirror.py` | tombstone check removed from the pre-checks | red | test_deposit_refuses_a_tombstoned_digest |
| `src/osd/mirror.py` | redistribution check removed from `deposit()` | red | test_deposit_refuses_rights[restricted] |
| `src/osd/mirror.py` | empty walk no longer refused | red | test_deposit_refuses_empty_directory |

## C3, designs 2 and 3: the deposit check, the ladder, the reasons (acceptance 3)

| File | Mutation | Result | First red test |
|---|---|---|---|
| `src/osd/verify.py` | the deposit check is never written | red | test_deposit_check_lists_the_files_and_gives_L2 |
| `src/osd/verify.py` | a skipped files-checksummed is kept beside the deposit | red | test_deposit_check_lists_the_files_and_gives_L2 |
| `src/osd/verify.py` | the check carries the deposit's licence digest, not this run's | red | test_deposit_check_lists_the_files_and_gives_L2 |
| `src/osd/verify.py` | `verify_all` reads no custody | red | test_verify_all_reads_the_custody_beside_the_results |
| `src/osd/reasons.py` | no L1 deposit sentence | red | test_deposit_without_licence_text_stays_L1 |
| `src/osd/reasons.py` | blocked reason no longer names the deposit | red | test_deposit_with_origin_failing_names_the_deposit[blocked] |
| `src/osd/reasons.py` | L2 reason not taken from the deposit check | red | test_deposit_check_lists_the_files_and_gives_L2 |

## C4, design 4: deposit assets, eligibility over a deposit, put (acceptance 4, 5)

| File | Mutation | Result | First red test |
|---|---|---|---|
| `src/osd/stac.py` | no deposit assets | red | test_deposit_stac_assets_manifest_and_get |
| `src/osd/stac.py` | `osd:provenance` dropped from the asset | red | test_deposit_stac_assets_manifest_and_get |
| `src/osd/stac.py` | an asset for a deposited copy the mirror does not hold | red (survived once; test_deposit_asset_gone_after_takedown added: a takedown between runs) | test_deposit_asset_gone_after_takedown |
| `src/osd/mirror.py` | eligibility ignores the deposit check | red | test_deposit_eligible_and_put_present |
| `src/osd/mirror.py` | `put` tries to fetch a deposited file | red | test_deposit_eligible_and_put_present |
| `src/osd/get.py` | control (E06 code, not changed here): ATTRIBUTION.md without the share-alike line | red | test_deposit_stac_assets_manifest_and_get |

## C5, design 5: derived uploads; the verifier ignores them (acceptance 7)

| File | Mutation | Result | First red test |
|---|---|---|---|
| `src/osd/mirror.py` | derived copies counted as the record's files (`deposits_of`) | red | test_mixed_custody_versions_through_sync_index_and_build |
| `src/osd/mirror.py` | lineage: every input, even for a derived file | red | test_put_derived_custody_lineage_and_e129_key_fill |
| `src/osd/mirror.py` | a file that is no artefact of the pack is uploaded | red | test_put_derived_refusals |
| `src/osd/mirror.py` | an artefact unlike the pack's digest is uploaded | red | test_put_derived_refusals |
| `src/osd/mirror.py` | a missing artefact is not refused | red | test_put_derived_refusals |
| `src/osd/mirror.py` | a restricted pack licence is not refused by name | red | test_put_derived_refusals |
| `src/osd/mirror.py` | another pack's held digest taken as this pack's (`_holder` without the pack id) | red | test_put_derived_refuses_a_digest_another_pack_holds |

## C7, supervisor answers 2 and 5 (custody before verify; idempotent put-derived)

| File | Mutation | Result | First red test |
|---|---|---|---|
| `src/osd/mirror.py` | a held artefact of the same pack is uploaded again on a rerun | red | test_put_derived_rerun_same_pack_is_idempotent |
| `.github/workflows/verify.yml` | the custody step before verify no longer syncs | red | test_workflow_syncs_custody_before_verifying_on_main |
