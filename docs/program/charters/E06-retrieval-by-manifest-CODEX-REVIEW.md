**1. Verdict: REWORK** — The charter assumes Item assets that do not exist and leaves selection identity, rights preservation and safe resume behavior undefined.

Verified against `381902ed825eae1bc0f716e5a593ed8d7cfa4f0d` (HEAD at review start). HEAD advanced during review; the intervening changes affect program documents and the review log, not the inspected code or charter. No files modified.

**2. Factual errors and Context verification**

- “E04’s item assets” is false: files belong to Collections because their relationship to Items is unestablished (`src/osd/stac.py:90–97`); Items explicitly contain `assets: {}` (`src/osd/stac.py:115`).
- “Records carry `origin.url` only” is false: Poseidon carries `origin.manifest_url` and `inputs[].url` (`records/nopims/poseidon.yaml:10,25`); both are schema-supported (`schema/record.schema.json:31,91`).
- “No fetcher” needs qualification: no retrieval command exists, but HTTP fetching and streaming already exist (`src/osd/verify.py:95,114`). Say “no manifest-driven downloader.”
- E02’s `files[]` already exists and contains fetch URLs, lengths and hashes (`src/osd/verify.py:363`; `schema/verification.schema.json:40–44`); it is verification output, not record content.
- Confirmed: no retrieval manifest schema/module in HEAD’s tracked tree; no `get` command in `src/osd/cli.py:91–117`. The third detail card does say retrieval is chartered (`site/app.js:238`).
- Beyond Context, the F3 acceptance fixture is stale: the record says **CC-BY-SA-3.0**, requires registration and has no `statement` (`records/terranubis/f3-demo-2020.yaml:7–16`). A successful unauthenticated F3 download and verbatim existing statement cannot be required evidence.

**3. Design objections and concrete alternatives**

- **Selection ownership:** `item_id` conflates datasets with wellbores. Items require periods (`src/osd/stac.py:141–143`), and Collection files cannot safely be assigned to each well. Distinguish Collection selection from Item selection; preserve standard STAC identities and leave unmapped feature selections unresolved.
- **Coverage:** verifier files are explicitly a sample (`src/osd/verify.py:367`). State that retrieval fetches selected published assets, not necessarily a complete dataset; carry coverage information instead of implying completeness.
- **Incomplete format:** design 2 and the stop rule need origin addresses and refusal notes absent from design 1. Define version discrimination, source links and item-level unresolved reasons in the schema; empty assets alone cannot explain anything.
- **Rights loss:** the manifest omits `url`, `redistribution` and `attribution`; E09 needs rights information including unknown redistribution (`E09-ophiolite-reads-the-catalogue.md:21–23`). Preserve the record licence object without inventing optional statements or treating missing `share_alike` as false (`schema/record.schema.json:36–45`).
- **Parallel asset vocabulary:** reuse STAC asset keys and File extension fields, or specify exact conversion from `file:size` and SHA-256 multihash `file:checksum` (`src/osd/stac.py:96–97`). Never silently discard unsupported checksum algorithms.
- **Unsafe resume contract:** define collision-safe paths confined to `--dest`, temporary writes, atomic completion and rehashing before skipping existing files. A failed or truncated file must never count as complete; checksum-free downloads must never report `verified`.
- **Network boundary:** `osd get` conflicts with the supplied repository rule limiting network entry points. Explicitly amend that boundary for intentional retrieval; inject transport in tests and retain the existing offline gate.
- **Terms enforcement:** “terms forbid automated download” has no defined input or decision owner. Carry an explicit publisher-grounded restriction and explanation; do not ask the downloader to infer legal permission from arbitrary prose.

**4. Acceptance lines that permit false positives**

- **Schema test (line 31):** rejecting missing `licence` still permits a schema accepting malformed hashes, unsupported versions and invalid nested rights. Add negative fixtures for each contract guard.
- **Three downloads (lines 32–33):** counters alone permit wrong output bytes; a corrupted source may never be requested after a successful first run. Use separate fresh destinations, assert exact bytes/hashes, and assert mismatch cleanup and preservation of pre-existing files.
- **Attribution (line 34):** a hard-coded F3 string can pass. Use two distinct supplied statements plus a missing-statement case; assert exact preservation and the correct SPDX version.
- **Site count (line 35):** two duplicates or unrelated items pass. Assert exact selected identities, asset metadata, rights and unresolved reasons; include a wellbore and a Collection without Items.
- **Resume count (line 36):** skipping every existing pathname passes despite truncation or corruption. Mutate a completed file and leave a partial file; assert repair, correct bytes and no requests for intact verified files.
- **Uncovered guards:** typed-reader validation, credential exclusion, checksum-free outcomes, denied downloads and CLI share-alike reporting have no acceptance tests. Add injected-fixture tests and failing mutations inside existing checks.

**5. Scope overlap**

- E15 already owns `site/app.js` and `tests/site/**` (`docs/program/CLAIMS.md:19`). Waiting only for E05 is insufficient; defer selection UI until E15 releases those paths and claim its Playwright test path.
- Do not manufacture acquisition periods to obtain Item IDs: publisher period curation belongs to E16. Collection selection must work independently.
- Mirror preference and custody remain E07; Ophiolite rights mapping, conversion and L4 remain E09. E06 should preserve their input facts without implementing those consumers.