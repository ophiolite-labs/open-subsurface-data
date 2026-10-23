| missing bundled schema (map entry for collection.json removed) | `schema/stac/schema-map.json` | `test_staged_tree_validates_recursively_offline` | FAILS (good): 1 failed, 22 deselected in 0.90s |
| Makefile copies flat again | `Makefile` | `test_makefile_copies_catalog_recursively` | FAILS (good): 1 failed, 22 deselected in 0.25s |
| item href broken | `src/osd/stac.py` | `test_item_ids_equal_feature_ids_with_period or test_items_independent_of_level` | FAILS (good): 1 failed, 20 deselected in 0.32s |
| one child link dropped | `src/osd/stac.py` | `test_reachable_collections_equal_record_ids` | FAILS (good): 1 failed, 22 deselected in 1.06s |
| one Item dropped | `src/osd/stac.py` | `test_item_ids_equal_feature_ids_with_period` | FAILS (good): 1 failed, 22 deselected in 0.30s |
| Items gated on level above L0 | `src/osd/stac.py` | `test_items_independent_of_level` | FAILS (good): 1 failed, 21 deselected in 0.21s |
| osd:level no longer required | `schema/stac-osd.json` | `test_osd_extension_rejects and missing-level` | FAILS (good): 1 failed, 22 deselected in 0.27s |
| level enum widened | `schema/stac-osd.json` | `test_osd_extension_rejects and l9` | FAILS (good): 1 failed, 22 deselected in 0.26s |
| unknown osd: fields allowed | `schema/stac-osd.json` | `test_osd_extension_rejects and unknown` | FAILS (good): 1 failed, 22 deselected in 0.26s |
| every level hard-coded to L0 | `src/osd/stac.py` | `test_collection_levels_equal_records_json` | FAILS (good): 1 failed, 22 deselected in 0.90s |
| null spdx mapped to proprietary | `src/osd/stac.py` | `test_licence_mapping_every_record` | FAILS (good): 1 failed, 22 deselected in 1.05s |
| file:checksum dropped | `src/osd/stac.py` | `test_collection_assets_from_verified_files` | FAILS (good): 1 failed, 22 deselected in 0.90s |
| input sha recomputed, not read from inputs | `src/osd/stac.py` | `test_item_time_and_provenance` | FAILS (good): 1 failed, 22 deselected in 0.22s |
| period end-of-interval wrong (start of last day) | `src/osd/stac.py` | `test_item_time_and_provenance` | FAILS (good): 1 failed, 22 deselected in 0.22s |
| period order unchecked | `src/osd/stac.py` | `test_period_end_before_start_fails` | FAILS (good): 1 failed, 22 deselected in 0.21s |
| duplicate check removed | `src/osd/stac.py` | `test_duplicate_feature_id_fails_build` | FAILS (good): 1 failed, 22 deselected in 0.19s |
| GeoJSON id not emitted | `src/osd/build.py` | `test_outlines_geojson_carries_feature_id` | FAILS (good): 1 failed, 22 deselected in 1.01s |
| lossy item names without hash | `src/osd/stac.py` | `test_item_file_names_are_path_safe_and_distinct` | FAILS (good): 1 failed, 22 deselected in 0.22s |
| period made required | `schema/record.schema.json` | `test_period_is_additive_to_record_2` | FAILS (good): 1 failed, 22 deselected in 0.40s |
restored: 23 passed in 2.09s
| unquoted period coercion removed | `src/osd/records.py` | `test_unquoted_yaml_period_reads_as_strings` | FAILS (good): 1 failed, 23 deselected in 0.22s |
