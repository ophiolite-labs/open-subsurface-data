**1. Verdict: REWORK.** The charter relies on a nonexistent NRCan record, contradicts schema-versioning rules, and would break manifest compatibility while dropping new licence restrictions.

Verified against HEAD **`30b75422526030422091004f6958c11a80fa3465`**. No files modified.

**2. Factual errors and Context verification**

- Confirmed: four access values, 18 kinds ending in `source-list`, and the seven-field closed licence object (`schema/record.schema.json:29`, `:36`, `:50`). Counted **92** dataset YAML records.
- Incorrect historical claim: `inputs` did **not** remain at record/2 through an additive change; commit `7ddecf0` introduced it while bumping record/1 → record/2. Compare `tests/fixtures/outlines/schema/record-1.schema.json:3` with `schema/record.schema.json:3`. Only the subsequent `period` addition retained /2.
- Incorrect vocabulary claim: the STAC extension defines access, **not kinds** (`schema/stac-osd.json:54`). Kinds become standard STAC `keywords` (`src/osd/stac.py:170`).
- The site has no independent kind/access enum: chips derive from catalogue records (`site/app.js:95`, `:212`); access displays directly from the record (`:265`).
- The E17 findings attribution is supported by `docs/program/HANDOFF.md:8`, including all named publishers and PASA restrictions. It does **not** establish seven existing records: NRCan GDR remained unreachable, and no corresponding record exists. The NRCan-related Laurentian entry describes seismic distributed by TerraNubis, not gravity/magnetics (`records/terranubis/laurentian-basin.yaml:4`, `:5`, `:16`).
- Design 4 also misstates where facts reside: PRIME gravity/magnetics appear in `summary`, with no want sentence (`records/prime/national-oil-gas-database.yaml:7`); BEG’s want is in `known_issues` (`records/beg/stratton-3d.yaml:21`).
- `osd new` has scaffolding comments, not interactive prompts; its hardcoded access choices live in `src/osd/new.py:62`, outside the proposed claim. CLI validation messages already consult the schema (`src/osd/cli.py:113`).

**3. Design objections and concrete alternatives**

- **Versioning:** “record/2 stays” violates AGENTS.md’s explicit schema-change rule. Bump changed schema identities, retain old-file compatibility tests, and name the contract change in the PR title.
- **Manifest breakage:** `purchase` is rejected by `schema/manifest.schema.json:86`; new terms disappear through Python and browser licence allowlists (`src/osd/manifest.py:42`; `site/app.js:289`). Extend/version the manifest contract and both writers/readers; prove exact licence preservation through both paths.
- **Wrong expiry model:** PASA states “at most 10 years” per purchase, not a catalogue-wide expiration date (`records/pasa/national-petroleum-exploration-database.yaml:26`). Preserve that conditional duration in `stated`, leave absolute expiry null, and never compute a purchaser’s expiry from catalogue dates. Define UTC date-boundary semantics for genuinely absolute publisher dates.
- **Unnecessary vocabulary copies:** preserve standard STAC `keywords` and data-derived site chips. Share schema choices where enumerations actually exist; test emitted STAC/access and scaffold output instead of inventing three identical kind lists.
- **Issue ownership:** the actual owner is `src/osd/report.py:60`; it consumes verification transitions, excludes unchanged levels, and deduplicates only open titles. Expiry needs an explicit record/date input and reporting policy independent of reachability. Reuse the existing dispatch workflow; define “once” precisely, including closed issues. Its current issue creation hardcodes `origin-dead` (`.github/workflows/verify.yml:49`, `:58`).
- **Record scope:** replace “seven” with exact existing IDs and field-specific edits. Defer NRCan to a records lane; do not invent a record or misclassify Laurentian seismic to satisfy acceptance.

**4. Acceptance weaknesses**

- “Issue text … exists as a fixture” passes with issue generation completely disconnected. Invoke the report path; assert one expiry issue, no duplicate on repeat, and none for future/null/absent expiry. Mutate generation and deduplication separately.
- Past-date/null status tests pass if every non-null date is flagged. Add future, today, absent, and malformed-date cases with an injected clock.
- Agreement acceptance omits `osd new`, despite design 2. A stale scaffold comment stays green. Conversely, adding an unused schema kind should not require a chip when chips correctly reflect available records.
- Filtering “lists NRCan” cannot pass honestly with current records; presence alone also permits a disabled filter. Use an existing positive record and assert exclusion of a negative record.
- “92 records, 0 problems” can pass with none of the intended optional fields added. Assert exact field values and preservation of unrelated facts for each named record.
- A live verify comment cannot prove unchanged level semantics: publisher availability varies. Compare old/new access values using identical injected responses and assert identical checks/levels.
- Missing guards: closed terms object, date/type validation, old-record compatibility, and manifest preservation. Require focused mutations within existing `make check`, not new stations.

**5. Scope crossing**

- Expiry issue automation extends **E08**, whose charter owns `src/osd/report.py`, `src/osd/new.py`, and `.github/**`. Either explicitly claim this extension and its tests or defer automation.
- Manifest compatibility and complete rights preservation cross **E06/E09** (`E06-retrieval-by-manifest.md:68`; `E09-ophiolite-reads-the-catalogue.md:37`). These are necessary integration work, not optional follow-ups.
- Creating the missing NRCan entry would reopen **E17** records acquisition and contradict E19’s “existing seven only” boundary.