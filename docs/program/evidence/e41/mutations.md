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
