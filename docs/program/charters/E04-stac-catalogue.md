## E04 STAC catalogue — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: `docs/ARCHITECTURE.md` ("formats, all standard"); Ophiolite connector doctrine
(SDK or standard, never bespoke).

**Outcome.** The QGIS STAC browser plug-in, and any STAC client, opens the catalogue by one
address and lists collections and items with licence, level and access mode. The map, QGIS and
Ophiolite read one catalogue, not three.

**Context today (verified 23 Oct).** `build/catalog/collections.json` is STAC-shaped (type,
stac_version, id, license, extent, providers, links) but unvalidated and has no items and no
root catalog. `osd:level` and `osd:access` are bare fields with no extension schema.

**The design the lane must map to.**
1. Static STAC 1.0: `catalog.json` root → one `Collection` per record → one `Item` per outline
   feature (wellbore or survey), with the feature geometry and bbox; assets link to the origin
   page today and to mirror files when E07 adds them.
2. An `osd` extension schema at `schema/stac-osd.json` for `osd:level`, `osd:checked_at`,
   `osd:access`, `osd:redistribution`, `osd:derivation` (the outline `source`).
3. `license`: the SPDX id when the record has one, else `other` with a `license` link, per the
   STAC spec; never `proprietary` for a bespoke open licence.
4. Validation in `make check` with `stac-validator` against the core and the osd extension; a
   fixture of two collections and three items with a known-bad mutation each.
5. The GeoJSON `outlines.geojson` stays; items reference the same feature ids so a map click and a
   STAC item agree.

**Acceptance.**
- `stac-validator catalog.json --recursive` passes on the build output.
- Item count equals outline feature count (test).
- A record at L0 still yields a collection with zero items (no vacuous pass: a test asserts both
  the collection and its empty item list).
- QGIS 3.34 STAC browser lists the collections from a local `http.server` (screenshot in the PR).
- Mutation: removing `osd:level` from one item fails validation (shown and restored).

**Out of scope.** A STAC API (static only), mirrors, search endpoints.

**Stop rules.** The STAC extension process needs a published schema URL: use the repository's
raw URL and note it; do not block on a registered extension.

**Ownership and dependencies.** Coding lane; paths `src/osd/stac.py`, `src/osd/build.py`,
`schema/stac-osd.json`, `tests/test_stac.py`, `Makefile`. Depends on E03 (items need outlines).

**Evidence to inspect.** The validator output in CI; the QGIS screenshot.
