# E38 mutations (24 Oct 2026, branch e38-wfs-and-ogc-api-layers at 15632bd)

Each mutation is one literal edit applied by `mutate.py` (this directory): the file is copied aside,
the edit applied and re-read from disk, the named test of `tests/test_ogc_layers.py` run (RED
expected), the original bytes written back and their SHA-256 compared, the test run again (pass).
Rerun with `uv run python docs/program/evidence/e38/mutate.py /tmp/table.md` from the repository root.

The charter's list maps to rows: `numberMatched` and hits mismatch 2-3; duplicate id 4; paging loop 5;
missing count gives unconfirmed and no L2 9; cap fallback 10-12 (partial evidence, no `files` entry,
no L2, no STAC asset); unsortable WFS 13-14; robots refusal on a later page 15; budget exhaustion 16;
exception responses 17-18; dispatch precedence over `file: true` and attachment headers 19; end to end
through `check_files` with an injected opener 20 (and every row from 2 on runs `verify_record`).
Rows 6-8 and 21 are the lane's further guards (empty page with a next link, short WFS page, crs, pacing).

Notes. Row 5: without the loop check page 2 is fetched again and the duplicate check refuses it; the
test asserts "paging loop", so it goes red on the other reason. Rows 17-18: without the named
exception the page fails as "is XML, not GeoJSON" or "not a GeoJSON FeatureCollection"; the tests
assert the publisher's message. Row 12: the evidence carries `partial: true`, so verification/6
refuses it in `files` (the test validates every result) besides the test's own assertion.

| # | mutation | file | test | mutated | restored |
|---|---|---|---|---|---|
| 1 | sort removed from the canonical bytes | `src/osd/verifier/layers.py` | `test_shuffled_pages_and_features_within_pages_give_identical_bytes` | RED: E       assert (b'{"crs":{"p...Collection"}') == (b'{"crs":{"p...Collection"}') | pass |
| 2 | count guard removed (WFS hits) | `src/osd/verifier/layers.py` | `test_hits_mismatch_fails_with_unique_ids_and_valid_pages` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, wfs-geoj | pass |
| 3 | count guard removed (OGC numberMatched) | `src/osd/verifier/layers.py` | `test_number_matched_mismatch_fails_with_unique_ids_and_valid_pages` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, ogcapi-g | pass |
| 4 | duplicate id check removed | `src/osd/verifier/layers.py` | `test_a_duplicate_id_fails` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, wfs-geoj | pass |
| 5 | paging loop check removed | `src/osd/verifier/layers.py` | `test_a_paging_loop_fails` | RED: E       AssertionError: whole layer https://fixture.test/ogc/collections/wells: the collection https://fixture.test/ogc/collections/wells: f | pass |
| 6 | empty page with a next link allowed | `src/osd/verifier/layers.py` | `test_an_empty_page_that_links_a_next_page_fails` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, ogcapi-g | pass |
| 7 | short WFS page allowed | `src/osd/verifier/layers.py` | `test_a_short_wfs_page_before_the_end_fails` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, wfs-geoj | pass |
| 8 | crs check removed | `src/osd/verifier/layers.py` | `test_a_crs_differing_between_pages_fails` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, wfs-geoj | pass |
| 9 | missing count read as complete | `src/osd/verifier/layers.py` | `test_a_missing_count_is_unconfirmed_and_earns_no_l2` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, ogcapi-g | pass |
| 10 | WFS feature cap removed | `src/osd/verifier/layers.py` | `test_above_the_cap_a_wfs_layer_is_partial_with_the_manifests_export_as_evidence` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'fail', 'detail': 'whole layer https://fixture.test/geoserve | pass |
| 11 | OGC feature cap removed | `src/osd/verifier/layers.py` | `test_above_the_cap_an_ogc_collection_keeps_its_first_page_as_evidence` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'fail', 'detail': 'whole layer https://fixture.test/ogc/coll | pass |
| 12 | partial evidence written into files | `src/osd/verify.py` | `test_above_the_cap_a_wfs_layer_is_partial_with_the_manifests_export_as_evidence` | RED: E           jsonschema.exceptions.ValidationError: {'path': 'GetFeature export (at most 1000 of 50001 features)', 'url': 'https://fixture.te | pass |
| 13 | ImplementsSorting not read | `src/osd/verifier/layers.py` | `test_a_wfs_that_cannot_be_read_whole_is_partial_and_not_hashed and sorting-false` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, wfs-geoj | pass |
| 14 | sort property not required | `src/osd/verifier/layers.py` | `test_a_wfs_that_cannot_be_read_whole_is_partial_and_not_hashed and no-sort-property` | RED: E       AssertionError: https://fixture.test/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=ns%3Awells&count=2&startIn | pass |
| 15 | robots check bypassed (a later page) | `src/osd/verify.py` | `test_robots_refusal_on_a_later_page_declines_the_layer` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, ogcapi-g | pass |
| 16 | budget bound removed | `src/osd/verify.py` | `test_a_page_over_the_budget_share_is_abandoned_and_counted` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, wfs-geoj | pass |
| 17 | OWS exception report not named | `src/osd/verifier/layers.py` | `test_exception_responses_fail_with_the_publishers_message` | RED: E       AssertionError: whole layer https://fixture.test/geoserver/wfs ns:wells: page at startIndex 2 is XML, not GeoJSON: b'<?xml version=" | pass |
| 18 | OGC API exception not named | `src/osd/verifier/layers.py` | `test_exception_responses_fail_with_the_publishers_message` | RED: E       AssertionError: whole layer https://fixture.test/ogc/collections/wells: page 2 (https://fixture.test/ogc/collections/wells/items?f=j | pass |
| 19 | dispatch precedence removed (file: true, attachment) | `src/osd/verify.py` | `test_the_wfs_reader_takes_the_manifest_over_file_true_and_an_attachment_header` | RED: E       AssertionError: assert 'whole layer checked (5 features, wfs-geojson)' in 'sample, not the whole dataset: 1 of 1 selected files hash | pass |
| 20 | a complete export written into files (end to end) | `src/osd/verify.py` | `test_a_complete_layer_passes_l2_as_evidence_never_a_file_or_asset` | RED: E       AssertionError: assert ('files' not in {'record_id': 'terranubis/f3-demo-2020', 'checked_at': '2026-10-24T03:39:59+00:00', 'tool_ver | pass |
| 21 | pacing removed (injected clock) | `src/osd/verify.py` | `test_every_layer_request_is_paced_per_host` | RED: E       AssertionError: assert (0 == (6 - 1)) | pass |
