# E35 mutations (24 Oct 2026, branch e35-whole-layers at 953b6ad)

Each mutation is one literal edit applied by `mutate.py` (this directory): the file is copied aside,
the edit applied and re-read from disk, the named test run (RED expected), the original bytes
written back and their SHA-256 compared, the test run again (pass). Rerun with
`uv run python docs/program/evidence/e35/mutate.py /tmp/table.md` from the repository root.

The charter's nine are rows 1-10 (the page-error check is mutated at both sources: the error JSON
in the shared assembly and the HTTP error in the verifier's get); row 11 is the id-set guard.
Rows 5 and 6: with the error check removed, the page reaches the frame check (an error body states
no geometryType), so the tests assert the error reason itself and go red on the other reason.
Row 4: without the duplicate check the count guard still refuses; the test asserts "served twice".

| # | mutation | file | test | mutated | restored |
|---|---|---|---|---|---|
| 1 | sort removed | `src/osd/verifier/layers.py` | `test_shuffled_pages_and_features_give_identical_bytes` | RED: E       assert b'{"features"..."wkid":2193}}' == b'{"features"..."wkid":2193}}' | pass |
| 2 | count guard removed | `src/osd/outlines/extractors.py` | `test_count_guard_alone_catches_an_oversized_final_page` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (6 features, esri-jso | pass |
| 3 | feature cap removed | `src/osd/verifier/layers.py` | `test_a_layer_above_the_feature_cap_stays_a_partial_export` | RED: E       AssertionError: assert ('fail', 'L1') == ('skip', 'L1') | pass |
| 4 | duplicate check removed | `src/osd/outlines/extractors.py` | `test_duplicate_id_fails` | RED: E       AssertionError: whole layer https://fixture.test/arcgis/rest/services/W/MapServer/0: the layer: the layer counts 5 features, the pag | pass |
| 5 | page-error check removed (error JSON) | `src/osd/outlines/extractors.py` | `test_error_json_page_fails` | RED: E       AssertionError: whole layer https://fixture.test/arcgis/rest/services/W/MapServer/0: the layer: page at offset 2 states geometryType | pass |
| 6 | page-error check removed (HTTP) | `src/osd/verify.py` | `test_http_page_error_fails` | RED: E       AssertionError: whole layer https://fixture.test/arcgis/rest/services/W/MapServer/0: the layer: page at offset 2 states geometryType | pass |
| 7 | robots check bypassed | `src/osd/verify.py` | `test_robots_disallow_skips_the_layer` | RED: E       AssertionError: assert ('pass', 'L2') == ('skip', 'L1') | pass |
| 8 | pacing removed (injected clock) | `src/osd/verify.py` | `test_every_layer_request_is_paced_per_host` | RED: E       AssertionError: assert (0 == (10 - 1)) | pass |
| 9 | budget bound removed | `src/osd/verify.py` | `test_a_page_over_the_budget_share_is_abandoned_and_counted` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, esri-jso | pass |
| 10 | a layer export written into files | `src/osd/verify.py` | `test_a_layer_export_never_becomes_an_asset` | RED: E       AssertionError: assert ([{'layer': 'https://fixture.test/arcgis/rest/services/W/MapServer/0', 'format': 'esri-json', 'features': 5,  | pass |
| 11 | id-set equality removed | `src/osd/verifier/layers.py` | `test_ids_differing_from_return_ids_only_fail` | RED: E       AssertionError: {'name': 'files-checksummed', 'level': 'L2', 'outcome': 'pass', 'detail': 'whole layer checked (5 features, esri-jso | pass |
