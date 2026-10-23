**1. Verdict: REWORK.** The charter omits a mandatory record-schema change, promises Items that current period rules prohibit, and permits acceptance with no successful new register.

Reviewed against HEAD **`7d8601721386f02351ffdc6122cd365a20414b7b`**. No files modified.

**2. Factual errors and Context verification**

- **13 ArcGIS records, not 16.** The complete “ArcGIS layer” set is `src/osd/verifier/samples.yaml:19,20,43,50,51,56,58,61,63,64,76,77,78`; their record `manifest_url` values match the 13 names actually enumerated in the charter.
- **WFS count equality is conditional.** `src/osd/outlines/extractors.py:150–155` checks equality only when a hits part exists and contains a parseable `numberMatched`. Missing/malformed counts do not refuse the input.
- **The cited 2,000-feature truncation is not fixed.** `src/osd/verifier/listings.py:123–136` uses the layer’s `maxRecordCount`; samples include 1,000, 3,000 and 10,000. `partial_exports` storage exists (`src/osd/verify.py:625–626`).
- **Confirmed:** exactly the five stated records declare inputs: `records/sodir/factpages.yaml:25`, `records/nlog/nlog.yaml:22`, `records/nopims/poseidon.yaml:23`, `records/nzpam/kerry-3d.yaml:21`, `records/nzpam/parihaka.yaml:22`.
- **Confirmed:** WFS GeoJSON paging (`src/osd/outlines/__init__.py:115–132`), per-input field rules (`src/osd/outlines/rules.yaml:28–83`), and workflow input comparison (`.github/workflows/verify.yml:40`; `src/osd/outlines/__init__.py:278–280`).
- **Confirmed only as recorded observations:** all ten quoted feature counts match `samples.yaml`. HEAD does not establish current live counts, service pagination capabilities, or the claimed 40-minute runtime. The 60-minute timeout is established (`.github/workflows/verify.yml:15`). Label the former as prerequisites/observations and cite a run for runtime.

**3. Design objections and concrete alternatives**

- **Unclaimed contract change:** `format: arcgis` fails `schema/record.schema.json:104`. Claim that schema and compatibility tests; bump its `$id`, retain old-record validation, and name the schema change in the PR title. An optional outline-schema bump does not address this.
- **Impossible Item promise:** `src/osd/stac.py:163–165` emits no Items without a record period. Six named targets lack one: both NZP&M registers, SGUDDS, Virginia, North Dakota and BCER. E29 forbids period edits and excludes these records from E28. Arrange a sequential records-lane handoff for publisher-stated periods, or explicitly defer their Item outcome.
- **Pagination needs an identity contract:** count equality alone cannot establish complete membership. Require stable publisher IDs, deterministic paging, duplicate rejection, and explicit refusal when pagination is unsupported. Test repeated pages and changing membership; retain stored count evidence.
- **CRS boundary is ambiguous:** requesting `outSR=4326` while declaring the layer’s native CRS risks transforming coordinates twice; current extraction transforms according to `rec_input.crs` (`src/osd/outlines/extractors.py:113–131`). Keep native CRS as publisher fact and validate/use response CRS separately in the ArcGIS adapter.
- **Geometry/date conversion is underspecified:** require multipart lines, polygons with holes/disjoint exteriors, null geometry policy, raw date preservation and RFC 3339 UTC timestamps. Preserve E18’s mixed/fallback provenance (`src/osd/stac.py:109–118`), rather than demanding `feature` whenever any date exists.
- **“Keeps its level” is unsafe wording:** refusal fails `outline-derived` (`src/osd/outlines/__init__.py:250–251`). Require recomputation from current checks, including demotion of formerly L3 records; never preserve stale L3.

**4. Acceptance loopholes**

- **“Each either L3 … or refused” accepts universal refusal.** A mutation that always refuses ArcGIS inputs can satisfy the live acceptance. Require named successful registers and nonzero expected counts; distinguish outage evidence from epic completion.
- **Full STAC validation accepts zero new Items.** Printing zero counts also satisfies the wording. Assert expected feature-ID/Item-ID sets and exact dates/provenance for named examples; suppressing all new Items must fail.
- **Branch duration does not prove full-run duration.** PR verification selects changed records (`.github/workflows/verify.yml:34–40`); full-tree validation runs only on main dispatch (`:82–84`). Measure an all-record branch dispatch and run existing `make check-full` explicitly against its outputs.
- **Three listed mutations do not cover every guard.** Add failures for swallowed page errors, ignored 50,000 cap, duplicate IDs, wrong CRS, lost polygon holes and dropped date fields. Use distinct collection/feature dates so fallback cannot conceal broken conversion.
- **Missing derivation step:** `--outline-inputs` never writes outlines (`src/osd/verify.py:757–766`). Require generating/reviewing committed outlines with `--outlines`, then independently verifying them.

**5. Scope overlap**

- **E28/E16:** collection periods remain records-owned; E29’s exclusion blocks its own STAC prerequisite. Enumerate exact record paths and sequence ownership, rather than claiming “any other” eligible record.
- **E18:** reuse its date normalization, provenance and containment contract; changing Collection extents or weakening fallback would exceed this adapter’s scope.
- **Stop rule:** proposing a “hardening charter” conflicts with `docs/ENGINEERING.md:28`. Record measured limits and defer remaining inputs; any later infrastructure proposal needs a concrete user outcome, not an automatic matrix/cache expansion.