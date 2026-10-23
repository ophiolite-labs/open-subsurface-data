# E32 mutations

Each mutation applied alone to the commit named, the named tests run, then restored. Machine: the
VPS (16 cores), 23 Oct 2026.

| # | Design | Mutation | Command | Result |
|---|---|---|---|---|
| 1 | 1 shared build | `full_build` fixture `scope="session"` -> `scope="function"` (tests/conftest.py) | `pytest tests/test_stac.py tests/test_build.py -k "staged_links or reachable_collections or outlines_geojson or one_real"` | RED: `test_one_real_build_per_session`, `len(REAL_BUILDS)` 3 (three consumers, three real builds); restored: 4 passed |
