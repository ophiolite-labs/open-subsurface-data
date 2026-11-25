Verdict: REWORK — the intended outcome is sound, but E46 leaves the spatial/output contract and preparation tool too undefined for E48 and E51 to implement without later kernel changes.

**Factual errors / context verification**

F1. “Context today” is not verified against HEAD: the charter names `fd69de4`, while HEAD is `c3baa16c` (25 Nov). The record totals are stale: HEAD has 238 YAML records and 225 `bbox` fields, not 236/192. The schema is still record/5 and has `country`, free-text `basin`, and `bbox`; it has no `national`. [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:13) [record schema](/home/epic/src/open-subsurface-data/schema/record.schema.json:69)

F2. The build claim is substantially correct: `build()` joins records and verification, reads committed outlines, writes `records.json`, `outlines.geojson`, well grids, and tiles only for the live catalogue. [build.py](/home/epic/src/open-subsurface-data/src/osd/build.py:83) [build.py](/home/epic/src/open-subsurface-data/src/osd/build.py:125) [build.py](/home/epic/src/open-subsurface-data/src/osd/build.py:136)

F3. The cited outline feature total is correct at HEAD: 169,295 total, 166,412 points, and 2,883 non-points. But “no point-in-polygon” is false literally: an internal ring-membership helper exists, albeit only for Esri-ring assembly and not a general containment implementation. [extractors.py](/home/epic/src/open-subsurface-data/src/osd/outlines/extractors.py:302)

F4. “No area data” is correct: `paths.py` names records, outlines, build, and verification directories only, and no committed `areas/` directory exists. [paths.py](/home/epic/src/open-subsurface-data/src/osd/paths.py:5)

F5. “Build is offline” is correct in the relevant sense: `osd build` directly invokes the local builder, while the network path is `osd verify`; `make check` runs lint, tests, validation, and build. [cli.py](/home/epic/src/open-subsurface-data/src/osd/cli.py:122) [Makefile](/home/epic/src/open-subsurface-data/Makefile:4)

**Contract problems**

F6. Define a versioned schema for `areas.json`, not just input `area/1`. E48 consumes this as its API, but its root shape, required/optional kinds, ordering, `label`, `bbox`, `n`, and `ids` are prose only. The conflict is already visible: slice 0 requires records with no `areas` key, while the outcome says every record says which areas it sits in. Choose one stable representation, including empty kinds. [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:8) [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:55)

F7. `source` cannot stay one block “per kind.” E51 needs separately retrieved regulator sources per country, and its resulting licence features need `blocks`; E46’s proposed area contract specifies neither multiple sources nor feature extensions. Specify an extensible source map/list and the licence feature/output fields now. [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:27) [E51 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E51-licences-per-country.md:37)

F8. Make area IDs globally unambiguous and enforce their invariants. “ISO / `iso_3166_2` or `adm1_code`” leaves collisions, formatting, source changes, and province country ownership unresolved. Define a namespace per kind/source, unique feature IDs, mandatory province country, and the exact USGS basin identifier.

F9. The containment definition cannot deliver “areas that hold data.” Sampling polygon/line vertices plus “one interior point” misses a feature crossing an area whose boundary contains neither; “interior point” itself is unspecified for holes, multipolygons, and dateline geometry. Define geometry intersection semantics, boundary treatment, and a deterministic geometry engine/algorithm. The existing dateline splitter explicitly handles lines only, not polygons. [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:44) [geometry.py](/home/epic/src/open-subsurface-data/src/osd/outlines/geometry.py:81)

F10. `region.national: true` must require `region.country`; today `region.country` is optional. Also define interaction with a bbox, outlines outside that country, and records containing multiple countries. The acceptance only rejects `"yes"`, not the invalid-but-implementable `national: true` without country. [record schema](/home/epic/src/open-subsurface-data/schema/record.schema.json:69) [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:41)

F11. `osd areas prepare <kind> <file>` lacks the inputs needed to produce the required source block (`url`, licence, credit, edition, retrieval date, digest). Specify flags or a checked-in preparation manifest. It also promises Shapefile support but claims neither a reader dependency nor an external-tool contract; E46 cannot amend `pyproject.toml` while E49 holds it.

**Acceptance and guards**

F12. The “valid” output acceptance is weak: it proves a golden fixture but not that production `areas.json`, fallback GeoJSON, PMTiles, and record projection conform to a machine-readable contract. Add schema validation plus deterministic-output tests for all published artefacts.

F13. The PR-only numbers and CI-duration statement can pass without proof in the repository. Keep the PR report, but add bounded fixture performance/cache tests and retain CI elapsed time as evidence; do not make an untestable assertion an acceptance criterion. [E46 charter](/home/epic/src/open-subsurface-data/docs/program/charters/E46-areas-that-hold-data.md:82)

F14. “First load unchanged” is not tested by the stated E46 acceptance and E46 does not hold the site test path. Add an offline request-list assertion in the site lane/claim, or move that acceptance to E48/E50.

F15. The required mutations omit: `national: true` without country; duplicate/colliding area IDs; wrong kind/source digest; invalid/non-WGS84 geometry; a crossing line/polygon missed by samples; index `n`/`ids` disagreement; and stale-cache reuse after an area or outline changes.

F16. The stated antimeridian mutation is not adequate evidence for polygon handling: current committed support splits only lines. Add polygon and multipolygon dateline fixtures, or explicitly reject them in `area/1` and document the limitation. [geometry.py](/home/epic/src/open-subsurface-data/src/osd/outlines/geometry.py:81)

**Scope, claims, and gate**

F17. No direct conflict exists among the current open claims: E46 owns the new area paths; E47’s Makefile claim is limited to site-test/shot lines; E49 owns the separate CLI `script` subcommand. The charter should retain E46 ownership of `areas/SOURCES.md`; E51 slice 0 currently claims evidence only. [CLAIMS.md](/home/epic/src/open-subsurface-data/docs/program/CLAIMS.md:57)

F18. Move the cache implementation detail out of the charter unless its cache format is a contract; what belongs in scope is deterministic invalidation and no published cache artefact. The build currently runs parallel to tests and validation in the gate, making an unspecified shared `build/` cache a race and timing risk. [Makefile](/home/epic/src/open-subsurface-data/Makefile:4)

F19. The network boundary is directionally safe—`prepare` is local—but add an injected-reader test proving it never opens a URL, and ensure Shapefile parsing cannot invoke an external downloader. The command must be documented as local-only; network authority must remain confined to the named commands.