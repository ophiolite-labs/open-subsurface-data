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
