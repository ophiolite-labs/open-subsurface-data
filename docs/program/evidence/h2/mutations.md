# H2 mutations

Each mutation applied alone to the branch at d9e3612, the named test run, the file restored
(script `docs/program/evidence/h2/mutate.py`: each exact replacement applied, then
`uv run pytest -q -x <test>`). Every one turned the test red.

| mutation | file | test | result |
|---|---|---|---|
| shard by list position | `src/osd/shards.py` | `test_a_record_that_sorts_first_moves_no_other_record` | RED: 1 failed in 0.82s |
| CLI ignores --shard | `src/osd/cli.py` | `test_shard_calls_the_verifier_with_exactly_its_ids` | RED: 1 failed in 2.63s |
| empty shard calls the verifier (verifies everything) | `src/osd/cli.py` | `test_an_empty_shard_calls_nothing` | RED: 1 failed in 0.83s |
| --shard '' read as no shard | `src/osd/cli.py` | `test_malformed_shards_and_ids_with_a_shard_are_refused` | RED: 1 failed, 8 passed in 0.86s |
| destination deleted before overlay | `src/osd/shards.py` | `test_a_failed_shards_records_keep_their_earlier_files` | RED: 1 failed in 1.57s |
| overwrite suppressed | `src/osd/shards.py` | `test_a_fresh_file_replaces_the_earlier_one` | RED: 1 failed in 0.70s |
| foreign id accepted | `src/osd/shards.py` | `test_a_shard_artifact_outside_its_shard_is_discarded` | RED: 1 failed in 0.80s |
| --verified all restored in the finishing step | `.github/workflows/verify.yml` | `test_the_finishing_report_passes_only_fresh_ids` | RED: 1 failed in 1.20s |
| zero fresh ids guard removed | `.github/workflows/verify.yml` | `test_no_fresh_ids_opens_and_closes_no_issue` | RED: 1 failed in 1.16s |

The replacements, exactly:

- shard by list position: `select` returns `[rid for k, rid in enumerate(recs) if k % n + 1 == i]`
- CLI ignores `--shard`: the line `ids = shards_mod.select(load_records(), i, n)` removed (ids stay None: every record)
- empty shard calls the verifier: ` if ids != [] else []` removed from `cmd_verify`
- `--shard ''` read as no shard: `if a.shard is not None:` replaced by `if a.shard:`
- destination deleted before overlay: `shutil.rmtree(out); out.mkdir()` after the snapshot copy
- overwrite suppressed: a shard file is copied only when the destination is absent
- foreign id accepted: the shard-membership check in `check_artifact` disabled
- `--verified all` restored: the finishing step's `--verified "$fresh"` replaced by `--verified all`
- zero fresh ids guard removed: the finishing step's empty-fresh branch never taken (`--verified ""` means all)
