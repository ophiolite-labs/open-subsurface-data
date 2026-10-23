## E29 Outlines from the registers' map services — QUEUED · Kernel · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: owner direction 23 Oct 2026 (levels on the map are real; L3 means the outlines were
read from the data); E03 (outline extractor, record `inputs`, outline/2 and /3, the WFS format,
the stored hit count rule), E16 design 2 (a register's own coverage period, as the publisher
states it), E18 (`period_fields`, date normalisation and provenance, Items carry their own dates),
E15 (tiles), E23 (the ArcGIS listing reader; exports stop at the layer's `maxRecordCount`, kept as
`partial_exports`); OSD-D18; AGENTS.md schema-change rule; `docs/ENGINEERING.md`.

**Outcome.** Registers that publish an ArcGIS map service show their wells and surveys on the map
as points and outlines read from the service itself; their records reach L3; and where the record
carries the register's publisher-stated period, its STAC Collection holds one Item per feature
with the dates the service states.

**Context today (verified 23 Oct, main 7d86017; Codex-checked).** Five records carry outline
`inputs` (`records/sodir/factpages.yaml:25`, `nlog/nlog.yaml:22`, `nopims/poseidon.yaml:23`,
`nzpam/kerry-3d.yaml:21`, `nzpam/parihaka.yaml:22`). `src/osd/outlines/` reads `format: wfs`
(GeoJSON pages, `__init__.py:115-132`); the WFS count check (`extractors.py:150-155`) runs only
when a hits part with a parseable `numberMatched` exists; field rules live in `rules.yaml:28-83`;
`osd verify --outline-inputs` compares committed outlines with today's inputs
(`verify.yml:40`) and never writes outlines (`--outlines` does); a refused input fails
`outline-derived` (`__init__.py:250-251`). `schema/record.schema.json:104` limits
`inputs[].format` to today's values, so `arcgis` needs record/5 (record/4 landed with E26,
PR #34). `src/osd/stac.py:163-165` emits no Items for a record without `period`. Thirteen records
list an ArcGIS layer (`samples.yaml:19,20,43,50,51,56,58,61,63,64,76,77,78`), counts as observed on
23 Oct: nzpam/petroleum-wells 1,302; nzpam/seismic-surveys-2d 990; wa-demirs/petroleum-wells
4,371; sgudds/register-geotermalnych-vrtov 307; va-energy/gas-oil-wells 8,605; nd-dmr/wells
44,018; bcer/well-surface-holes-permitted, sgc/banco-informacion-petrolera-pozos and
ut-dogm/oil-gas-wells (totals not recorded); sk-mer/vertical-wells 119,595; sk-mer/drill-core
104,754; pgi/cbdg-boreholes 334,145; cgs/vrtna-prozkoumanost 746,789. Of the nine candidates,
six have no `period` (both NZP&M, SGUDDS, Virginia, North Dakota, BCER). Verify on main after
E24 (run 39981701762) took 40 minutes under the 60-minute job timeout (`verify.yml:15`).
Live counts, pagination support and run time are observations to re-establish on the day.

**The design the lane must map to.**
1. record/5: `inputs[].format` gains `arcgis`; record/4 frozen under `tests/fixtures/schema/`, one
   fixed fixture set validates under both, every stored record validates under record/5; the PR
   title names the schema change.
2. `format: arcgis` in `src/osd/outlines/`: read the layer description (`?f=json`); refuse the
   input unless `supportsPagination` is true and an `objectIdField` is named; page with
   `orderByFields=<objectIdField> ASC`, `resultOffset`, `resultRecordCount=maxRecordCount`,
   `outFields=*`, native spatial reference (no `outSR`); the response's `spatialReference.wkid`
   must match the record's declared `crs` else refuse; `f=geojson` when `supportedQueryFormats`
   lists it, else `f=json` converted (point, multipoint, polyline with several paths, polygon
   with holes and several exteriors per Esri ring orientation); a feature with null geometry is
   listed in `unplaced`. Identity: object ids must be unique across pages and their number must
   equal `returnCountOnly=true` on the day; a duplicate, a missing page, a page error or a count
   mismatch refuses the input. Coordinates are transformed from the declared `crs` exactly as the
   WFS path does today. Levels are recomputed from today's checks: a refused input fails
   `outline-derived`, and a record that was L3 is demoted if its input is refused today.
3. Dates: the fields `rules.yaml` names per input (E18 `period_fields`); epoch milliseconds to
   RFC 3339 UTC, the raw value kept in `osd:period_*_raw`; E18's provenance rules unchanged
   (`feature` when the feature states dates, else the existing fallbacks; `stac.py:109-118`).
4. Budget: an input is read in full or refused; the four layers above 50,000 features (SK MER x2,
   PGI, CGS) are not given inputs this lane. The duration proof is one all-record dispatch of
   `verify.yml` on the branch; it must finish under 60 minutes and `make check-full` must pass on
   its outputs. The lane adds inputs in order of size (SGUDDS, NZP&M x2, WA DEMIRS, Virginia,
   BCER, SGC, UT DOGM, North Dakota) and stops adding when the dispatch passes 50 minutes; the
   remaining ones are deferred with the measured time, no infrastructure proposal.
5. Records, exact edits, these nine and no others: `nzpam/petroleum-wells`,
   `nzpam/seismic-surveys-2d`, `wa-demirs/petroleum-wells`, `sgudds/register-geotermalnych-vrtov`,
   `va-energy/gas-oil-wells`, `nd-dmr/wells`, `bcer/well-surface-holes-permitted`,
   `sgc/banco-informacion-petrolera-pozos`, `ut-dogm/oil-gas-wells`: `inputs` (name, the layer
   URL without a query, `format: arcgis`, `crs` and `stated` from the service description), and
   `period` for the six without one where the register's page or service description states its
   coverage (E16 design 2; the publisher's sentence in `notes`); a register that states none keeps
   no period and no Items, said in the PR. Outlines for these records are generated with
   `--outlines`, reviewed, committed under `outlines/`, then verified with `--outline-inputs`.
6. Site: nothing new; tiles (E15) carry the points. One phone-width screenshot of a new register
   is evidence.

**Acceptance.**
- Fixture ArcGIS server (injected responses, offline), per input: pages reassemble the layer with
  the exact object-id set; duplicates, a missing page, a page error, a count mismatch, missing
  pagination support, a wkid mismatch each refuse; `f=json` conversion of a point, a two-path
  polyline, a polygon with a hole and a two-exterior polygon matches GeoJSON fixtures; epoch-ms
  dates match given RFC 3339 strings with distinct feature and collection dates so a fallback
  cannot hide a broken conversion. Mutations, one per guard: count check removed; duplicate check
  removed; page error swallowed; cap ignored; wkid check removed; hole dropped; date field
  dropped; off-by-a-day conversion.
- STAC fixture: for one fixture record with a period, the Item id set equals the object-id set and
  named Items carry exact dates and `osd:period_source: feature`; suppressing the Items fails.
- Live: at least four of the nine records at L3 on the branch dispatch with their feature counts
  stated (the expected count is the day's `returnCountOnly`), or per-record outage evidence
  (HTTP status and time) for those that are not; universal refusal is a failed lane.
- The all-record branch dispatch finishes under 60 minutes, `make check-full` passes on its
  outputs; both stated in the PR with the run id.
- Record diffs show only `inputs` and, where added, `period` and the `notes` sentence.

**Out of scope.** Layers above 50,000 features; WFS or other formats; the verifier's ArcGIS
listing reader; Collection extents; any site code; any infrastructure change (ENGINEERING.md:28).

**Stop rules.** If no new input fits under the 60-minute dispatch, the lane ships the fixture
work, the schema and the record `inputs` behind refusal (no outlines), records the measured
times per input, and defers the rest; no charter for infrastructure is proposed by this lane.

**Ownership and dependencies.** Coding lane; paths `schema/record.schema.json` (record/5),
`tests/fixtures/schema/record-4.schema.json` (new), `tests/test_schema.py` (compatibility
additions), `tests/test_outlines.py` (its `$id` lines and additions), `src/osd/outlines/**`,
`src/osd/verify.py` (outline input dispatch only, if needed), `tests/fixtures/outlines/**`,
`outlines/**` for the nine records, the nine records in design 5, `docs/program/evidence/e29/**`.
Depends on E03, E18, E23, E25, E26 (merged). E28 (periods) holds no record of these nine.

**Evidence to inspect.** The fixture tests and the eight mutations; the dispatch run id, its
duration and `check-full`; the record diffs; one screenshot.

**Dispositions of the Codex round (23 Oct).** Accepted: thirteen ArcGIS records, nine candidates
named exactly; record/5 for `inputs[].format` with frozen record/4 and compatibility tests; the
period prerequisite resolved inside the lane (E16 design 2 register periods for the six records,
publisher-stated, else no Items and said so); identity contract (objectIdField, ordered paging,
duplicates and count both checked, refusal when pagination is unsupported); native CRS with a
wkid check and the existing transform; geometry and date conversion specified with provenance per
E18; "keeps its level" replaced by recomputation and demotion; acceptance requires named live
successes with counts, exact Item id sets and dates in fixtures, an all-record branch dispatch
with `make check-full`, eight mutations, and the `--outlines` derivation step; the truncation
sentence corrected to `maxRecordCount`; the stop rule records limits and defers, proposing no
infrastructure. Refuted: none.
