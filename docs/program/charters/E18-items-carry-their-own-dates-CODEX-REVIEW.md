Verified against HEAD **`b0c9f6e75f7adeb3ae1b42b52db8f5fd36433610`**. Read-only review; no files modified.

**1. Verdict: REWORK.** The proposed provenance fields require unclaimed schema changes, and the proposed execution path cannot publish updated dates without rewriting committed outlines.

**2. Current-code facts and errors**

- **Confirmed:** Items inherit the record interval: `src/osd/stac.py:145` passes it to `_item`, which assigns both timestamps at line 108. The charter’s “lines 63–108” citation misses the connecting call.
- **Misleading:** outlines do not retain arbitrary publisher properties selected by WFS. The extractor explicitly emits identifiers, name, kind and geometry (`src/osd/outlines/extractors.py:32`, `:71`). Rules currently contain no date mappings.
- **Unsupported field names:** the committed Sodir evidence names `Entry_year` and `Entered_date`, not `wlbEntryDate` (`docs/program/evidence/e16/periods.jsonl:49`). Neither the asserted Sodir completion/survey fields nor NLOG’s `END_DATE_DRILLING` appears in tracked code, fixtures or E16 evidence. Label these external prerequisites, not verified Context facts.
- **Overstated placeholder evidence:** E16 reports five `1800-01-01` values as **“likely a placeholder”**, not established placeholders (`docs/program/evidence/e16/periods.jsonl:35`). It supports `START_DATE_DRILLING` only.
- **Count corroborated as build eligibility:** committed outlines yield 11,210 Sodir + 7,220 NLOG + Parihaka + Kerry = **18,432** eligible Items under `src/osd/stac.py:147`. No generated STAC tree exists in this checkout; published existence was not independently verified.
- **Confirmed:** the gate samples first/last plus up to 20 Items per Collection (`tests/test_stac.py:112`); `Makefile:20` validates the whole tree separately.

**3. Design objections and concrete alternatives**

- **Missing contract ownership:** `osd:period_source` is forbidden by `schema/stac-osd.json:87`; extra provenance members inside outline `inputs` are forbidden by `schema/outline.schema.json:109`. Claim both schemas and the offline schema map; version their `$id`s, retain old-file compatibility tests, and name the contract change in the PR title.
- **Missing publication ownership:** `--outline-inputs` derives but does not write outlines (`src/osd/verify.py:608`); build reads committed outlines (`src/osd/stac.py:137`). Claim the two register outline files, regenerate through `--outlines`, review their diffs, then build from those committed outputs.
- **Dates are excluded from requests:** `propertyName` explicitly selects geometry/identity fields (`src/osd/outlines/rules.yaml:35`, `:45`, `:60`, `:68`). Require verified date fields in those existing requests; adding `period_fields` alone cannot retrieve them.
- **“ISO dates, verbatim” is ambiguous:** E16’s Sodir example is a timestamp without a timezone (`periods.jsonl:49`). Define accepted source representations, date normalization and invalid-value handling; preserve raw evidence in stored inputs and test exact emitted RFC 3339 bounds.
- **Open-end semantics are incomplete:** a collection end can precede a feature start, and a mixed feature/collection interval is not wholly publisher-stated. Validate the resulting pair, explicitly mark mixed provenance, and specify fallback for invalid bounds.
- **Unchanged Collection extent needs a guard:** reporting outlying Item dates does not resolve their exclusion from collection-level time discovery. Add an offline containment assertion; if it fails, defer that register pending an E16-owned coverage correction.

**4. Acceptance weaknesses**

- “Start differs from `1966-01-01`” can pass unchanged: existing output is `1966-01-01T00:00:00Z` (`src/osd/stac.py:51`). Compare normalized instants and assert exact dates for named feature IDs.
- A local count does not prove “published on main.” Require matching named Items in the staged artifact and a post-publication check.
- Synthetic WFS fixtures can bypass the real `propertyName` projection. Add an injected-transport test that checks requested fields and carries responses through extraction, outline serialization and STAC output; removing date fields from requests must fail it.
- Placeholder tests can remain green if fallback reproduces the same `1800` start. Use a distinct fixture collection period and assert both timestamps, provenance and preservation of the Item.
- No acceptance covers open ends, malformed dates, mixed provenance, or start after fallback end. Add explicit cases and mutations for these guards.
- Schema validity cannot prove correct feature dates or collection containment. Assert exact Item IDs and intervals; a valid but wrong timestamp must fail.

**5. Scope overlap**

- E16 explicitly assigns per-feature dates to E03 (`docs/program/charters/E16-periods-from-the-publishers.md:19`): E18 is an E03/E04 follow-on and should say so.
- Correcting Collection periods would cross E18’s exclusion into E16; coordinate separately if containment fails.
- No identified product-scope creep into E07 or E17. The necessary schema and committed-outline paths are missing ownership, not optional expansion.