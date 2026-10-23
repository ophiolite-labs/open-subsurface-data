# E26 strategy: the kinds the records lanes asked for (Kernel, small)

Charter: `E26-vocabulary-kinds-the-records-lanes-asked-for.md` (Codex round dispositioned at its end). Base:
main 9d144d0 (`make check` green, 140 records, 0 problems). Claim row E26 in `CLAIMS.md`. Open questions:
`~/.local/share/osd-program/inbox/e26.md`.

## Shape

```
schema/record.schema.json  record/3 -> record/4: kinds += velocity-model, geological-model,
   |                       airborne-em, radiometrics, stress (one clause each in the description)
   |                       frozen record/3 -> tests/fixtures/schema/record-3.schema.json
   +-> records/*.yaml (the ten of design 5) --osd build--> records.json kinds (copied, build.py:89)
   |                                                   +-> STAC Collection keywords (stac.py:186)
   |                                                   +-> site chips (data-derived; no change)
   +-> osd new: kinds comment = " | ".join(schema kinds enum), like access/redistribution (new.py)
```

No code path changes for propagation: `build.py` and `stac.py` copy the list. The only source edit is
`new.choices()` gaining `kinds` and `scaffold()` writing it. `schema/manifest.schema.json`,
`schema/stac-osd.json`, `site/**`, `tests/site/**` stay out of the diff.

## Slices (one commit each)

1. **Schema and compatibility.** Freeze main's `schema/record.schema.json` byte-for-byte as
   `tests/fixtures/schema/record-3.schema.json`; record/4 `$id`, title, description sentence; the five
   kinds appended to the enum; the kinds description defines each in one clause. Tests in
   `tests/test_schema.py`: the `$id` test names /4 and /3; `RECORD_3` renamed `RECORD` (the live schema).
   The existing record/2 file test skips record/4 kinds as well as record/3 values.
2. **Scaffold.** `new.choices()["kinds"]`; scaffold line `kinds: []  # fill: <kinds enum>`.
3. **Propagation.** One parameterised function at the end of `tests/test_build.py` (E27 shares the
   file; this keeps E26 to one hunk).
4. **The ten records.** Exact edits of design 5; the diff saved to `docs/program/evidence/e26/records.diff`.

## Acceptance → tests

| Acceptance line | Test |
|---|---|
| record/4: each new kind validates | `test_schema.py::test_record_4_admits_each_new_kind[<kind>]` (5) |
| an unknown kind is refused | `test_schema.py::test_unknown_values_refused[kind]`, `::test_record_4_refuses_an_unknown_kind` |
| one fixed record/3 fixture set (every record/3 kind, one each) validates under frozen record/3 and record/4 | `test_schema.py::test_record_3_fixtures_validate_under_record_3_and_record_4` |
| frozen record/3 is the old contract (refuses each new kind) | same test, second half |
| `osd validate`: main's count, 0 problems | `make check` (`140 records, 0 problems`); existing `test_the_six_records_state_the_new_values` (`validate_records() == []`) |
| propagation over the five kinds: records.json kinds unchanged, STAC keywords contain it | `test_build.py::test_new_kinds_travel_to_records_json_and_stac_keywords[<kind>]` (5) |
| manifest, stac-osd, site absent from the diff | `git diff --stat main` in the PR body |
| scaffold kinds comment equals the schema enum and names the five literally | `test_schema.py::test_new_scaffold_kinds_comment_lists_the_schema_kinds` |
| ten record diffs beside the table | PR body + `docs/program/evidence/e26/records.diff`; no permanent test pins record content (E20) |

## Mutations (each shown red, then restored; `docs/program/evidence/e26/mutations.txt`)

1. record/4 without an old kind (`time-depth` removed from the live enum) →
   `test_record_3_fixtures_validate_under_record_3_and_record_4` red.
2. `new.scaffold` kinds comment omits one entry (`[:-1]`) → `test_new_scaffold_kinds_comment_lists_the_schema_kinds` red.
3. `stac.py` keywords drop a new kind (filter `velocity-model`) →
   `test_new_kinds_travel_to_records_json_and_stac_keywords[velocity-model]` red (proves the propagation
   test is not vacuous; charter names two mutations, this is the third the brief asks for).

## Outside the claim, named

Raising `$id` to record/4 turns `tests/test_outlines.py:518` red (asserts `/record/3`), and the record/1
check beside it (`:521`) must skip records carrying record/4 kinds (velocity-model on Utah FORGE seismic
is not a record/1 kind). Same two-token pattern as E19's; edited in this PR, named in the inbox note and
the PR body. `tests/test_stac.py:318` (also asserts `/record/3`) is inside the claim as an edit to the
existing assert.

## Record edits (design 5; the record's own text, nothing re-fetched)

Notes are edited by removing the named sentence and nothing else. Two readings fixed here: Bedretto's
sentence "Stress inversion results have no kind (nearest: wellbore-logs, from which they are derived)."
goes whole (its parenthesis has no meaning once the kind exists); IGME's want loses only
"airborne radiometrics and " ("Want: kinds for electrical/electromagnetic soundings; potential-fields
covers the gravimetry and aeromagnetics only."). Utah FORGE gravity keeps "nearest kind potential-fields"
verbatim (the charter keeps the rest of each note verbatim); the PR names it.
