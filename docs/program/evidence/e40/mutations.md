# E40 mutations

Each line: what was broken, the test that went red, restored byte for byte (copy aside, written back),
the same tests green again. Run with a helper that refuses a target occurring other than once and
re-reads the mutated file before running (`mut.py`, lane scratchpad).

## C2: custody/2 and verification/7 (design 2, 3; acceptance 8 in part)

| Mutation | Red test |
|---|---|
| custody/2: the deposit branch loses its `not verifier_run/derived` | `test_custody_2_exactly_one_provenance[deposit-and-derived]` |
| custody/2: the `if format /1 then verified` rule removed | `test_custody_2_exactly_one_provenance[v1-deposit]` |
| custody/2: `deposit.by` loses its role pattern | `test_custody_2_exactly_one_provenance[by-a-name]` |
| verification/7: the reason-sentence pattern on a passing deposit removed | `test_deposit_check_refuses[reason-sentence]` |
| verification/7: a deposit file without `key` admitted | `test_deposit_check_refuses[file-without-key]` |
| verification/7: a check named `deposit` no longer selects the deposit shape | `test_deposit_check_shape` |

## C3: starter/1 and the fixtures (design 1, 7; acceptance 8)

| Mutation | Red test |
|---|---|
| starter/1: `topic` any string (unknown topic admitted) | `test_starter_schema_is_not_permissive[unknown-topic]` |
| starter/1: `subject` not required | `test_starter_schema_is_not_permissive[missing-subject]` |
| starter/1: an artefact without `key` admitted | `test_starter_schema_is_not_permissive[artefact-without-key]` |

## C4: custody/2 readers (design 2)

| Mutation | Red test |
|---|---|
| live custody schema admits only /1 (readers refuse /2) | `test_mixed_custody_set_through_index_sync_and_build` |
| `mirror.public_index` stops excluding tombstoned digests | `test_mixed_custody_set_through_index_sync_and_build` |
| `custody.provenance` never says `derived` | `test_mixed_custody_set_through_index_sync_and_build` |

## C3b: keys come last while unpublished (supervisor answer 6, Ophiolite E129)

| Mutation | Red test |
|---|---|
| starter/1: the `else` requiring `key` on a published pack removed | `test_starter_schema_is_not_permissive[artefact-without-key]` |
| starter/1: the `if` loses `required: [unpublished]` (an absent flag counts as unpublished) | `test_starter_schema_is_not_permissive[artefact-without-key]` |

## C5: the nine validity tests (design 4; acceptance 1 to 5)

| Rule | Mutation in `src/osd/starters.py` (unless named) | Red test |
|---|---|---|
| (a) | the file-name rule skipped | `test_file_name_and_record` |
| (a) | schema: sources' `redistribution` any string | `test_licence_value_outside_the_enum` |
| (b) wrong record, deposited | the custody `record_id` comparison skipped | `test_input_of_another_record` |
| (b) wrong record, verified | the other-record lookup skipped | `test_input_of_another_record_verified` |
| (b) wrong `verifier_run` | the run comparison skipped | `test_input_wrong_verifier_run` |
| (b) wrong size | the bytes comparison skipped | `test_input_wrong_size` |
| (b) wrong name | the name comparison skipped | `test_input_wrong_name` |
| (b) tombstoned key | the removed-key refusal skipped | `test_input_tombstoned_custody_key` |
| (b) not a deposit | the provenance comparison skipped | `test_input_deposit_must_be_a_deposit` |
| (b) evidence absent | the "unchecked here" branch removed | `test_without_evidence_nothing_is_passed_that_needs_it` |
| (c) | the `from` membership skipped | `test_derived_from_an_input` |
| (d) restricted, unknown | the `allowed` test skipped | `test_licence_not_allowed[restricted]` |
| (d) mixed spdx | the agreement test skipped | `test_licence_mixed_spdx` |
| (d) dropped required attribution | `required` computed only when all require it | `test_licence_dropped_required_attribution` |
| (d) share-alike over a true input | share-alike computed false | `test_licence_share_alike_over_a_share_alike_input` |
| (d) sources entry edited | the evidence comparison skipped | `test_licence_sources_entry_edited` |
| (d) stated vs computed | the field comparison skipped | `test_licence_dropped_required_attribution` |
| (e) one well's depth-reference | `depth-reference` dropped from the well topics | `test_decision_missing_for_one_well` |
| (e) per object | a `pack` line satisfies every object | `test_a_pack_line_satisfies_no_object` |
| (e) contradicting duplicate | the two-values refusal skipped | `test_decision_contradicting_duplicate` |
| (e) depth cube without velocity | velocity never required | `test_decision_depth_cube_needs_velocity` |
| (e) subject | the subject membership skipped | `test_decision_subject_and_count` |
| (f) missing custody object | the not-held refusal skipped | `test_artefact_missing_custody_object` |
| (f) tombstone | removed-first order and the sibling-tombstone exclusion are two guards: each alone stays green (equivalent), both together red | `test_artefact_tombstone` |
| (f) size mismatch | the bytes/digest comparison skipped | `test_artefact_size_mismatch` |
| (f) another pack's artefact | the `pack_id` comparison skipped | `test_artefact_of_another_pack` |
| (g) `import` names no artefact | the membership skipped | `test_import_names_no_artefact` |
| (g) one path, one digest | the clash refusal skipped | `test_one_path_one_digest` |
| (h) one input missing | the coverage refusal skipped | `test_fidelity_refusals[input-missing]` |
| (h) one extra | the extra refusal skipped | `test_fidelity_refusals[input-extra]` |
| (h) a `failed` result | `failed` admitted | `test_fidelity_refusals[failed]` |
| (h) wrong `record` | the record comparison skipped | `test_fidelity_refusals[wrong-record]` |
| (h) output kind | the contents-kind test skipped | `test_fidelity_refusals[kind]` |
| (h) confined to starters/ | `exists()` instead of resolve-inside (a symlink out) | `test_fidelity_path_stays_in_starters` |
| (i) | the `values == 0` refusal skipped; the `unpublished` exemption removed | `test_oracle` (twice) |
| discovery | `osd validate` no longer counts starter problems | `test_osd_validate_names_the_invalid_pack` |
