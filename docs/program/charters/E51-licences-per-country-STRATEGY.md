## E51 slice 1 strategy: Norway's licences read from Sodir, with the contract (25 Nov 2026)

Charter `E51-licences-per-country.md` (dispositions of the Codex round at its end), OSD-D29, D37, D38.
Kernel class: a test per acceptance line, a mutation shown to fail per guard. The surface part
(design 5, acceptance 6, J13) is a second pull request after E48 merges; the United States is slice 3.

**What was read on 25 Nov** (one real read, generic client name, no project name sent). Sodir
FactMaps `FactMapsWGS84` FeatureServer, WGS84 (wkid 4326), `maxRecordCount` 1000, pages:
616 "Production licence, all - current with geometry" has **1,813 rows, 536 `prlStatus` ACTIVE and
1,277 INACTIVE** (relinquished: the "current" filter is real, not decorative); one row per licence;
`prlName` holds spaces ("091 F"), `prlNpdidLicence` is the stable id. 616 has no block attribute;
615 "Production licence, current - by block and operator" has 1,113 rows naming exactly the 536
active licences, each with `blcNpdidBlock`; every one is a block of 802 (1,827) with the same name.

**The contract** (`areas/licence/<cc>.yaml`, read by `osd.areas.read_config`, refused when a key is
missing): `country`, `service` (an ArcGIS FeatureServer), `licences` {`layer`, `id` (the stable id
field, area_id = `<CC>:<id>`), `name`, `name_prefix`, `current` {`field`, `op` (`=` or `in`),
`value`}, `edition` (a date field: its latest value is `source.edition`)}, `blocks` {`layer` (rows
per licence and block), `licence` (join key, equal to the licence layer's `join` field), `join`,
`block` (key into the block layer)}, `block_layer` {`layer`, `id`, `name`}, `tolerance_m`,
`decimals`, `source` {`name`, `url`, `licence`, `credit`}. Every layer is read whole by the
verifier's `layers.export_layer` (E35: paging, id list, edit date, the 50,000 cap) through an
injected `get`; the filter is applied to the whole read (616 is 1,813 rows; BLM's server-side
filter before paging is slice 3's change, F19). Output: area/1 unchanged (`blocks` and `country`
already in E46's feature), one feature per current licence, `blocks` naturally sorted.

**Guards** (each: the committed file stays byte-identical, exit 1, the finding printed and in the
summary): no current licence; an HTTP or paging failure (`Incomplete`, `NotWhole`); more than a
fifth of the committed licences missing from the read (covers both a count that falls and the same
count with other ids); a missing or repeated id or name; the filter's field absent from the layer;
a licence without block rows, a block row of no current licence, a block id absent from the block
layer or named twice differently; a layer not in WGS84; a geometry that is not a valid polygon after
simplification (area/1 and `geometry_problems`). `osd validate` refuses a licence file whose
`source.url` or `source.credit` is not written in `areas/SOURCES.md` (binds geometry to the terms,
F15). An unchanged read rewrites nothing (inbox note 2).

**The count and the row.** E46's count is unchanged: `kind: licence` is counted when a file exists.
`osd build` adds `records[].blocks` (the union of the block names of the record's licences, natural
order) when the record sits in 1 to 25 licences; above 25 it has none and the row shows the length
of `areas.licence` (F9).

**The schedule.** `.github/workflows/areas.yml`: weekly cron (Monday 05:17 UTC), dispatch (input
`dry`, default true) and pull requests touching the workflow or `areas/licence/*.yaml` (always dry:
acceptance 7 on this pull request). Permissions `contents: write`, `pull-requests: write`,
`issues: write`; GitHub calls: `git push` of branch `areas-read` only, `gh pr create|edit` for
"Licences read <date>", `gh issue comment` on "Licences: <CC> read refused" (created once). Never
main. `make check` never runs it or `osd areas read` (test).

| Acceptance | Test (`tests/test_areas_read.py` unless named) |
|---|---|
| 2 golden file, pagination, one feature per licence, blocks sorted | `test_read_writes_the_golden_file_across_pages`, `test_relinquished_licence_is_not_read` |
| 3 empty, failed, shrunken reads | `test_empty_read_leaves_the_file`, `test_http_error_leaves_the_file`, `test_a_fifth_missing_is_read`, `test_more_than_a_fifth_missing_is_refused`, `test_same_count_other_ids_is_refused` |
| 3, F14 guards | `test_refused_reads_leave_the_file` (8 cases), `test_validate_refuses_a_licence_file_not_in_sources_md`, `test_unchanged_read_leaves_the_file` |
| 4 the count, blocks, 26 licences | `test_licence_holding_a_well_is_written_and_the_other_not`, `test_record_blocks_are_its_licences_blocks`, `test_26_licences_give_no_block_list` |
| 5 real numbers | `test_real_norway_licences_hold_datasets` (full build), numbers in the PR body |
| 7 the workflow | `test_workflow_never_pushes_main_and_states_its_permissions`, `test_pr_and_issue_texts`; a dry run on this pull request |
| 8 offline, size | `test_check_never_reads_regulators`, `test_real_licence_file_under_5_mb`; `make check` timed |

Mutations (shown in the PR): each guard removed in turn makes its test fail. Time added to
`make check`: the fixture tests (no network, about a second) and the licence kind in the real
build's count (measured, stated in the PR).
