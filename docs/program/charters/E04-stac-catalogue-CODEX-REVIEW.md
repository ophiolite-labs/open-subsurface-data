Verified against HEAD **`e58e2f547715fc46d94a7e778eb142190578803c`**. No files modified. References below are repository-relative; E04 means `docs/program/charters/E04-stac-catalogue.md`.

**1. Verdict: REWORK**

The charter leaves temporal metadata and feature identity undefined, contradicts itself on L0 items, and does not specify how validation remains offline.

**2. Factual errors about current code**

- Context is substantively correct, but `collections.json` is a bespoke `{"collections": [...]}` wrapper, not itself a STAC object (`src/osd/build.py:63`).
- Verified every listed collection field: `type`, `stac_version`, `id`, `license`, `extent`, `providers`, `links` are emitted at `src/osd/build.py:48–56`.
- Verified absence of items/root: the builder emits only records, outlines and the collections wrapper (`src/osd/build.py:59–64`).
- Verified “unvalidated”: `osd validate` checks records/outlines only (`src/osd/cli.py:15`); the build test checks one collection licence, not STAC validity (`tests/test_build.py:23–24`).
- Verified bare `osd:level`/`osd:access` at `src/osd/build.py:57`; opened all three existing schemas—none defines a STAC extension.
- Outside Context, “same feature ids” assumes an absent contract: the builder emits no GeoJSON `id` (`src/osd/build.py:45`), and outline properties require neither `uwi` nor `publisher_id` (`schema/outline.schema.json:7–15`).

**3. Design objections and concrete alternatives**

- **Offline validation (E04:22,28,37):** a public schema URL does not supply an offline resolver. Pin the validator dependency, bundle core/transitive schemas, map the versioned extension URL to its local file, and test with network access denied within existing pytest/build targets. Claim dependency/schema-resource paths too. The validator supports [local schema mapping](https://github.com/StacLabs/stac-validator#--schema-map).
- **Missing time contract (E04:15–19):** STAC Items require a meaningful `datetime`, or bounded start/end times when it is null; current outline inputs supply none. Define publisher-sourced temporal metadata and a missing-time policy before promising one Item per feature; never substitute verification time. Any input-schema change needs the prescribed version/compatibility treatment. See [STAC 1.0 Item requirements](https://github.com/radiantearth/stac-spec/blob/v1.0.0/item-spec/item-spec.md#properties-object).
- **Conflicting item eligibility (E04:15,29–31):** L0 does not imply absent outlines; the builder defaults to L0 and still includes them (`src/osd/build.py:32–45`). Make empty collections depend on absent eligible outlines, and retain existing outlines when reachability falls to L0.
- **Identity ownership (E04:24):** define stable, collection-scoped feature keys, collision rejection and reorder stability; emit the same key in GeoJSON and STAC. Assign the upstream identity contract explicitly to E03 or claim its schema changes here.
- **Assets (E04:16–17):** origin pages alone do not satisfy E06’s file-address dependency (`E06-retrieval-by-manifest.md:11–21`). Keep landing pages as links; map E02’s known files to data assets only where their relationship to an Item is established. Preserve collection-level assets for dataset-wide files.
- **Extension semantics (E04:18–19):** specify Collection fields versus Item `properties`, enum constraints, missing verification dates, and record-level versus feature-level assurance. Copying a dataset level must not imply every well/file was checked. Preserve `approximate` explicitly.
- **Publication (E04:15,40):** nested STAC files would be omitted by the current flat copy (`Makefile:17`). Specify either a flat layout or recursive publication, then validate links from staged `site/data`, which Pages actually publishes (`.github/workflows/pages.yml:32`).

**4. Acceptance weaknesses**

- **Recursive validation:** removing child/item links can leave valid but undiscoverable objects. Assert the reachable collection/item sets against independent input expectations; mutate a link away.
- **Count equality:** deleting both outputs yields `0 == 0`; duplicating one feature while omitting another preserves counts. Assert a nonempty fixture’s exact IDs, geometry, bbox and collection membership.
- **L0 empty collection:** an emitter that suppresses every Item passes this isolated test. Pair outline-free L0 with L0-with-outline and populated collection cases.
- **QGIS screenshot:** collections can display while Items, licence, level or access mode are absent. Require opening an Item and showing the promised metadata using the staged publication tree.
- **Missing-level mutation:** a schema requiring a field but accepting nonsense values passes this guard; hardcoding every level to L0 also passes. Add invalid-enum and wrong-source-value mutations, plus extension-declaration coverage.
- **Uncovered licence rule:** retaining today’s `proprietary` fallback can pass core validation. Assert exact SPDX and bespoke-licence mappings and links.
- “Two collections and three items” is only a fixture description; require the actual builder to produce them and prove every guard’s mutation fails.

**5. Scope creep / neighbouring boundaries**

- E04:8 promises Ophiolite consumption, owned by **E09**; limit E04’s outcome to publishing its interoperable input contract.
- E04:24 risks absorbing feature-level map selection from **E05/E06**; E04 should establish matching identifiers, leaving UI behaviour there.
- Mirror implementation remains **E07**. E04 may establish asset structure, but must not implement copying or mirror preference.
- Stable feature identity needs an explicit **E03 → E04** handoff; neither charter currently guarantees it.