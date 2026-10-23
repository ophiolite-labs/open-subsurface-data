## E29 Outlines from the registers' map services — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: owner direction 23 Oct 2026 (levels on the map are real; L3 means the outlines were
read from the data); E03 (outline extractor, record `inputs`, outline/2 and /3, the WFS format,
the stored hit count rule), E18 (`period_fields`, Items carry their own dates), E15 (tiles),
E23 (the ArcGIS listing reader and its 2,000-feature truncation, kept as `partial_exports`);
OSD-D18; AGENTS.md schema-change rule.

**Outcome.** The wells and surveys of the registers that publish an ArcGIS map service are on
the map as real points and outlines read from the service itself, their records reach L3, and
their STAC Collections hold one Item per feature with the dates the service states.

**Context today (verified 23 Oct, main e103c4c).** Five records carry outline `inputs` (Sodir,
NLOG, NOPIMS Poseidon, NZP&M Kerry 3D and Parihaka); `src/osd/outlines/` reads `format: wfs`
(GeoJSON pages of a WFS GetFeature; the stored hit count must equal the features read),
`rules.yaml` holds per-input field rules, and `osd verify --outline-inputs` in the verify
workflow compares committed outlines with today's inputs. Sixteen records point their
`manifest_url` at an ArcGIS Map or Feature Server layer (`src/osd/verifier/samples.yaml`
comments "ArcGIS layer"): nzpam/petroleum-wells (1,302 features), nzpam/seismic-surveys-2d (990),
wa-demirs/petroleum-wells (4,371), sgudds/register-geotermalnych-vrtov (307), va-energy/gas-oil-wells
(8,605), nd-dmr/wells (44,018), sk-mer/vertical-wells (119,595), sk-mer/drill-core (104,754),
pgi/cbdg-boreholes (334,145), cgs/vrtna-prozkoumanost (746,789), bcer/well-surface-holes-permitted,
sgc/banco-informacion-petrolera-pozos, ut-dogm/oil-gas-wells, and others listed there. ArcGIS
layers page with `resultOffset`/`resultRecordCount` up to `maxRecordCount` per page and answer
`f=geojson` where the server supports it; `supportsPagination` and `maxRecordCount` are in the
layer's `?f=json` description. The verify run on main takes about 40 minutes today under a
60-minute job timeout.

**The design the lane must map to.**
1. `format: arcgis` in `src/osd/outlines/`: read the layer description, page the whole layer with
   `resultOffset`, in `f=geojson` when supported else `f=json` converted, `outSR=4326`; the stored
   feature count must equal the layer's `returnCountOnly=true` count on the day (the WFS hit-count
   rule), else the input is refused and the record keeps its level. Geometry types: point, line,
   polygon, as the layer states. Dates from the fields `rules.yaml` names for the input (E18
   `period_fields`), epoch milliseconds converted to ISO dates, UTC.
2. Budget: one input is read in full or not at all; a layer above 50,000 features is out of scope
   this lane (sk-mer, pgi, cgs stay at their level; the PR names them and the count on the day).
   The verify job's total time with the new inputs stays under 60 minutes; the strategy says how
   it is measured (the branch run's duration) and the lane stops adding inputs when the run
   passes 50 minutes.
3. Records (exact edits): `inputs` added to nzpam/petroleum-wells, nzpam/seismic-surveys-2d,
   wa-demirs/petroleum-wells, sgudds/register-geotermalnych-vrtov, va-energy/gas-oil-wells,
   nd-dmr/wells, bcer/well-surface-holes-permitted, sgc/banco-informacion-petrolera-pozos,
   ut-dogm/oil-gas-wells, and any other ArcGIS-listed record under 50,000 features, each with
   `name`, `url` (the layer, not a query), `format: arcgis`, `crs` and `stated` as the publisher
   states it; rules in `rules.yaml`. No other field of those records changes.
4. STAC: one Item per feature as E18 does for WFS inputs, `osd:period_source: feature` where the
   layer states dates; the full-tree validation step (OSD-D18) stays green.
5. Site: nothing new; tiles (E15) carry the points. A phone-width screenshot of one new register
   zoomed in is evidence, not a change.

**Acceptance.**
- Fixture ArcGIS server (injected responses, offline): paged reads reassemble the layer exactly;
  a count mismatch refuses the input; a page error refuses the input; `f=json` fallback converts
  geometry correctly for point, polyline and polygon; dates from epoch ms are exact. One mutation
  per guard (count check removed, pagination stop condition broken, date conversion off by a day).
- `osd verify --outline-inputs` for the new records on the branch run: each either L3 with the
  feature count, or refused with the reason printed.
- The branch verify run completes under 60 minutes; the PR states its duration.
- The STAC tree validates (full step) with the new Items; the PR gives the Item count per record.
- The record diffs show only `inputs`.

**Out of scope.** Layers above 50,000 features; WFS or other formats; verifier listing changes
(E23's ArcGIS export reader stays as it is); any site code.

**Stop rules.** If the verify job cannot stay under 60 minutes with any new input, stop after
the fixture work and write the finding (split verify into a matrix, or cache inputs) for a
hardening charter.

**Ownership and dependencies.** Coding lane; paths `src/osd/outlines/**`, `src/osd/verify.py`
(outline input dispatch only, if needed), `tests/test_outlines.py` additions, `tests/fixtures/outlines/**`,
`outlines/**` for the new records, the records named in design 3 (`inputs` only), `schema/outline.schema.json`
only if a bump is unavoidable (name it in the PR title), `docs/program/evidence/e29/**`. Depends
on E03, E18, E23, E25 (merged). E28 (periods) must not edit the design-3 records.

**Evidence to inspect.** The fixture tests and mutations; the branch run's verify output and
duration; the record diffs; one screenshot.
