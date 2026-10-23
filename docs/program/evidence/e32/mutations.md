# E32 mutations

Each mutation applied alone to the commit named, the named tests run, then restored. Machine: the
VPS (16 cores), 23 Oct 2026.

| # | Design | Mutation | Command | Result |
|---|---|---|---|---|
| 1 | 1 shared build | `full_build` fixture `scope="session"` -> `scope="function"` (tests/conftest.py) | `pytest tests/test_stac.py tests/test_build.py -k "staged_links or reachable_collections or outlines_geojson or one_real"` | RED: `test_one_real_build_per_session`, `len(REAL_BUILDS)` 3 (three consumers, three real builds); restored: 4 passed |
| 2 | 2 shards | `_member_links` drops the last shard's `child` link (`[:-1]`) | `pytest tests/test_stac.py -k reached_items` (nine registers' outlines in the tree) | RED: `test_reached_items_are_exactly_the_outline_feature_ids`, the reached set misses the last shard's Items; restored: passed |
| 3 | 2 shards | `containment_problems` reads only the Collection's direct `item` links | `pytest tests/test_stac.py -k later_shard` | RED: `test_item_outside_its_interval_on_a_later_shard_fails_check_full` (`assert not True`: validation passes); restored: passed |
| 4 | 2 manifest | manifest item lookup reads only the Collection's direct `item` links | `pytest tests/test_manifest.py -k later_shard` | RED: `test_item_on_a_later_shard_is_found`, `('acme/alpha#w-5', None)`; restored: passed |
| 5 | 3 tiles | tippecanoe release under the fixture test (no code edit): Ubuntu `2.49.0-1build1`, `2.53.0-1build1`, `2.79.0-1`, each extracted from its `.deb` and put first on PATH | `pytest tests/test_build.py -k crossing` | 2.49.0 RED and 2.53.0 RED (`{'feature_id': 'A-001377 WELL'} != {'feature_id': 'crossing/register-b#900540'}`); 2.79.0 green |
