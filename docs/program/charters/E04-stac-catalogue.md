## E04 STAC catalogue — QUEUED · Kernel · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: `docs/ARCHITECTURE.md` ("formats, all standard"); Ophiolite connector doctrine
(SDK or standard, never bespoke); OSD-D14.

**Outcome.** Any STAC client, including the QGIS STAC browser, opens the catalogue by one address
and lists every dataset as a Collection with licence, level, access mode and verification date,
and lists Items for the features whose record declares a period. The catalogue is the
interoperable contract that E06 and E09 read; consuming it in Ophiolite is E09.

**Context today (verified 23 Oct, main e58e2f5).** `build/catalog/collections.json` is a bespoke
wrapper `{"collections": [...]}` whose entries carry `type`, `stac_version`, `id`, `license`,
`extent`, `providers`, `links` and bare `osd:level`/`osd:access` fields (`src/osd/build.py`); no
root catalog, no items, no extension schema, no validation (`osd validate` covers records and
outlines only; `tests/test_build.py` checks one licence string). The builder emits no GeoJSON
`id`; feature identity arrives with E03's `feature_id`. `Makefile` copies `build/catalog/*` flat
into `site/data/`, which Pages publishes.

**The design the lane must map to.**
1. Static STAC 1.0 under `build/catalog/stac/`: `catalog.json` root, one `Collection` per record,
   Items only where OSD-D14 allows (record `period` or a feature date), each Item carrying the
   feature geometry, bbox, `id` = E03's `feature_id`, and `datetime: null` with
   `start_datetime`/`end_datetime` from the period. Collections carry the temporal extent from
   `period` or `[null, null]`.
2. The `osd` extension: schema at `schema/stac-osd.json`, versioned URL mapped to the local file
   for offline validation. Collection-level fields `osd:level`, `osd:checked_at`, `osd:access`,
   `osd:redistribution`, `osd:blocked_since` (record-level assurance, stated as such); Item-level
   `osd:approximate`, `osd:derivation`, `osd:input_sha256`. Enums closed.
3. `license`: the SPDX id when the record has one, else `other` plus a `license` link; `proprietary`
   never appears. A test asserts the mapping for every record.
4. Assets: Collection `links` carry the landing page (`rel: about`) and licence; Collection
   `assets` carry E02's checksummed files (`href`, `file:size`, `file:checksum`), since their
   relation to an individual Item is not established; Items carry no data assets until E06 or E07
   establishes one. Mirror preference stays in E07.
5. Validation offline inside `make check`: `stac-validator` pinned, core and extension schemas
   bundled under `schema/stac/`, schema-map to local files, and a test that runs with network
   access denied (a fetcher that raises).
6. Publication: `Makefile` copies `build/catalog/` recursively; link validation runs over the
   staged `site/data/stac/` tree, the one Pages serves.
7. Identity: `feature_id` is the shared key between `outlines.geojson` features (emitted as
   GeoJSON `id` too) and STAC Items; duplicates fail the build.

**Acceptance.**
- `stac-validator site/data/stac/catalog.json --recursive` passes with the local schema map and
  no network; a mutation that removes one `child` link makes the reachable-set test fail (the test
  asserts the exact reachable collection ids against the record ids).
- Item ids equal the exact set of `feature_id`s of features with a period (fixture with three such
  features and two without); a mutation that drops one Item fails.
- A record with outlines but at L0 yields a collection with its Items and `osd:level: L0`; a record
  with no outlines yields an empty Item list; both asserted in one parametrised test.
- Removing `osd:level` fails validation; setting it to `L9` fails validation; hard-coding every
  level to L0 fails the test that compares collection levels to `records.json`.
- QGIS 3.34 STAC browser opens the staged tree from a local `http.server`, lists collections and
  opens one Item showing licence, level and access (screenshot in the PR).

**Out of scope.** A STAC API, mirrors (E07), manifests (E06), Ophiolite intake (E09), map UI (E05).

**Stop rules.** The STAC extension process requires a registered schema URL: use the repository's
versioned raw URL mapped locally; do not block on registration.

**Ownership and dependencies.** Coding lane; paths `src/osd/stac.py`, `src/osd/build.py`,
`schema/stac-osd.json`, `schema/stac/**` (bundled schemas), `schema/record.schema.json` (optional
`period` only, coordinated with E03's record/2), `pyproject.toml` (stac-validator pinned),
`Makefile` (recursive copy), `tests/test_stac.py`. Depends on E03 (feature ids) and E02 (files).

**Evidence to inspect.** The validator output in CI; the reachable-set and id-set tests; the QGIS
screenshot.

**Dispositions of the Codex round (23 Oct).** Accepted: offline validation with bundled schemas
and a schema map (5), the time contract (OSD-D14, design 1), item eligibility independent of
level (acceptance 3), identity ownership (E03 assigns `feature_id`, E04 emits it in both outputs),
assets at collection level from E02 with no mirror logic, extension semantics by level (2),
recursive publication and staged-tree validation (6), exact-set acceptance tests with named
mutations, licence mapping test, outcome narrowed to publishing the contract (E09 consumes).
Refuted: none.
