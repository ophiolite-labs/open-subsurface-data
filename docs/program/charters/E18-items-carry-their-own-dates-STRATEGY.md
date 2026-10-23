# E18 strategy: Items carry their own dates

Authority: `E18-items-carry-their-own-dates.md`. Lane-open facts: `docs/program/evidence/e18/fields.md`
(live Sodir and NLOG services, 23 Oct). Versioning follows OSD-D19 (stac-osd `?v=<n>`, frozen copies
under `tests/fixtures/schema/`) and the outline precedent (path `$id`, frozen copy under
`tests/fixtures/outlines/schema/`).

## What the lane-open check changed

- Sodir's GeoJSON writes `xsd:dateTime` values as `M/D/YYYY` or `M/D/YYYY h:mm:ss AM|PM`
  (`Entered_date` `2/15/1983` beside `Entry_day` 15, `Entry_month` 2). The rule therefore names
  the service's string form: `period_format: m/d/y` (default `iso`). Anything not in the named
  form is invalid: raw kept, normalised member omitted.
- NLOG 3D surveys carry only `DATE_RELEASE` (a release, not when the survey was shot): stop rule,
  no `period_fields`, those Items keep the collection period.
- NLOG `1800-01-01` (five boreholes, each ending `1801-01-01`, the same shape as the two
  `1828-01-01` to `1829-01-01` boreholes) reads as year precision, not a placeholder the service
  marks: NLOG `period_placeholders` stays empty. The mechanism is tested on the fixture register.

## Design (one paragraph per charter point)

1. `rules.yaml`, per register input: `period_fields: {start, end}`, `period_format`,
   `period_placeholders`; the same names are appended to `params.propertyName`.
2. `extractors._period(rule, props)` writes `osd:period_start_raw`/`osd:period_end_raw`
   (verbatim string) and `osd:period_start`/`osd:period_end` (RFC 3339 UTC; date start
   `T00:00:00Z`, date end `T23:59:59Z`, zone-less timestamp read as UTC, zoned converted to UTC;
   placeholder or unreadable: normalised omitted). `derive` names the fields in the collection's
   `inputs[<name>].period_fields`. outline/3 admits the four members and `period_fields`.
3. `stac.item_period(props, collection_interval) -> (interval, source)`: feature when both
   normalised and start ≤ end; `feature-start,collection-end` when no normalised end and start ≤
   collection end; otherwise `collection`. The Item gets `osd:period_source`; stac-osd v2 requires
   it on Items (closed enum) and still accepts documents naming the v1 URL.
4. `stac.containment_problems(root)` lists Items outside their Collection's interval;
   `stac.validate` on a tree fails on any, so `make check-full` carries the guard unchanged.
5. Collection extents stay `interval(rec)`. Per-register counts and named examples go to
   `docs/program/evidence/e18/registers.md`.

## Acceptance to tests

| Acceptance line | Test |
|---|---|
| Request carries the date fields; removing them fails | `test_outlines.py::test_wfs_requests_carry_the_period_fields` |
| Dated → own bounds, exact strings per id | `test_stac.py::test_fixture_register_item_periods[dated]`, `[timestamp-utc]` |
| Undated → collection, `collection` | `…[undated]` |
| Placeholder → undated | `…[placeholder]`; `test_outlines.py::test_placeholder_is_kept_raw_not_normalised` |
| Reversed → collection | `…[reversed]` |
| Open end → feature start + collection end, mixed | `…[open-end]` |
| Start after collection end, no end → collection | `…[late-start]` |
| Malformed → raw kept, normalised omitted, collection | `…[malformed]`; `test_outlines.py::test_fixture_register_outline_period_members` |
| Timestamp without zone → UTC | `…[timestamp-utc]`; `test_outlines.py::test_normalise_period_values` |
| Containment green on the fixture | `test_stac.py::test_fixture_items_lie_inside_their_collection` |
| Containment guard fires | `test_stac.py::test_item_outside_its_collection_fails_validation` |
| `make check-full` containment on the tree | `test_stac.py::test_makefile_check_full_validates_whole_tree_and_verify_runs_it_on_main_only` (existing: check-full runs `stac.validate`) + the run in the PR |
| outline/2 files validate under their own schema | `test_outlines.py::test_outline_2_files_validate_under_outline_2_and_3` |
| STAC files without `osd:period_source` validate under their own schema; map carries both | `test_stac.py::test_stac_osd_1_documents_validate_under_their_frozen_schema` |
| Dates read from the feature, not the record | `…[dated]` (fixture period 1990–2000, feature 1993) |

## Mutations (each shown red against the unchanged suite, then restored)

placeholder rule dropped; fallback dropped (`collection` branch returns feature values);
reversed accepted (`start <= end` removed); dates read from the record; raw not kept; mixed
provenance labelled `feature`; containment guard dropped; date fields removed from
`propertyName`; zone-less timestamp read as local time.

## Commits

1. Strategy and lane-open evidence. 2. Tests (red). 3. outline/3, extractor and rules. 4. stac-osd
v2, Item periods, containment. 5. Regenerated Sodir and NLOG outlines with the register report.
