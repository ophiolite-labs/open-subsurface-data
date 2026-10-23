**1. Verdict: REWORK** — the charter permits a paging layout that existing consumers cannot traverse, a tile change that breaks the site contract, and a weaker gate than repository policy.

Verified against HEAD `f1f05ae2756a1d89d3e8b17ea88755a4f11c130f`. No files modified. References below are repository-relative; E32 references mean the reviewed charter.

**2. Factual errors and Context verification**

- Confirmed: nine real-catalogue build call sites across the six named modules; 18,436 committed outline features; indented Collection item links (`src/osd/stac.py:193`, `:206`); tippecanoe 2.49 pin (`src/osd/build.py:125`); E18 corruption workaround (`src/osd/build.py:91`, `docs/program/evidence/e18/registers.md:41`).
- E32:15 overstates Item emission: a period alone is insufficient; each feature also needs `feature_id` (`src/osd/stac.py:163`). Consequently, **178,056 Item files from 177,895 features** cannot describe this writer’s output. Distinguish Items from total STAC JSON objects.
- E32:16–22 timings, E29 feature totals, ND/UT corruption examples, and projected publication sizes are branch measurements, **not verified HEAD facts**. HEAD contains eight outline files and no E29 outline implementation; the cited E29 measurement evidence is not present here. Supply the measured commit, commands, and run/artifact references.
- E32:22–23 is an unfulfilled dependency assumption: HEAD’s format enum excludes ArcGIS (`schema/record.schema.json:104`), and its rules end with the existing five datasets (`src/osd/outlines/rules.yaml:103`). E29 explicitly permits missing periods and deferred inputs (`E29-outlines-from-the-map-services.md:54`, `:65`); merging E29 does not guarantee all five are ready.
- E32:73 names nonexistent `.github/workflows/check.yml`; installation is in `.github/workflows/ci.yml:19` and independently in `pages.yml:30`.

**3. Design objections and concrete alternatives**

- **Gate budget:** E32:28/50 allows three minutes; `Makefile:4`, AGENTS.md, and ENGINEERING’s gate policy require two. Retain the two-minute threshold and measure the `make check` step separately from workflow setup.
- **Shared fixture:** these builds consume different verification/custody inputs (`tests/test_build.py:15`, `tests/test_stac.py:91`, `tests/test_mirror.py:469`). Copying already-built output cannot test a changed input’s join. Share one full-catalogue integration build; retain small isolated builds for behavior tests.
- **Paging contract:** arbitrary `next` link pages do not establish interoperable static traversal. Current traversal follows only `child`/`item` (`src/osd/stac.py:281`). Use standard child Catalog shards with item links, validated by an ordinary recursive client walk; preserve Item collection identity. [STAC 1.0 Catalog specification](https://raw.githubusercontent.com/radiantearth/stac-spec/v1.0.0/catalog-spec/catalog-spec.md).
- **Retrieval compatibility:** sharding removes direct Collection item links, but manifest selection reads only those links (`src/osd/manifest.py:240`). Claim that consumer and test a feature on a later shard retains its `item_id`.
- **Tile contract:** replacing string IDs and removing string attributes breaks kind filters, promoted identity, and record lookup (`site/app.js:166`, `:177`, `:289`). Prefer a corrected encoder preserving properties; otherwise explicitly claim the site adapter and its existing journey tests.
- **Production encoder:** changing only the check installation leaves Pages publishing with 2.49 (`pages.yml:30`). Pin the same corrected version in both existing workflows.
- **Schema ownership:** `schema/stac/**` contains standards contracts, not permission to redefine STAC to accept bespoke pages. Use valid standard objects; any project schema change needs the required version bump and old-file compatibility test.

**4. Acceptance loopholes and ineffective mutations**

- E32:51: a spy scoped to one consumer can still count one after fixture scope becomes function-local. Exercise multiple consumers and assert the aggregate session count.
- E32:54: counting Items permits duplicates replacing missing IDs. Compare the exact expected ID set and reject duplicate visits.
- E32:55: “paging removed → size red” is incompatible with the explicitly allowed compact, unpaged design. Deleting continuation links also makes files smaller. Test missing continuation/shard links against reachability and completeness.
- E32:57: IDs can remain correct while names, kinds, or geometry are corrupted; omission can pass a loop over surviving features. Require exact identity coverage and identity-to-geometry/property correspondence.
- E32:59: outage exceptions can excuse all five registers. Require successful evidence before claiming the five-register outcome; outage-only results remain partial.
- E32:61 requires only a size table, not the stated size ceiling/headroom. Require a bound on the complete staged site, including duplicated Collection links in `collections.json` (`src/osd/build.py:117`).
- Layout changes can bypass containment checks: they scan only `*/collection.json` and sibling `items/*.json` (`src/osd/stac.py:241`). Put an invalid dated Item in a later shard and require `check-full` to fail.

**5. Scope overlap**

- E29 already owns all nine records, rules, and generated outlines (`E29-outlines-from-the-map-services.md:60`). Require an explicit merged handoff naming the five deferred outputs and their period readiness.
- Numeric tile IDs/string removal reopens E15’s same-properties contract and site ownership (`E15-tiles-for-the-registers.md:6`, `:33`); it cannot remain a build-only change.
- A “detail panel of one well” adds feature-level behavior: today `select()` displays the dataset title (`site/app.js:287`). Specify the existing dataset panel after clicking a well, or explicitly authorize that surface expansion.