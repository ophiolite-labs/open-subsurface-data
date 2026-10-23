## E26 Vocabulary: the kinds the records lanes asked for — QUEUED · Kernel (small) · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: E20, E22 and E24 findings in `docs/program/HANDOFF.md` and the `notes` or `known_issues`
of the records named in design 4; E19 (record/3, the vocabulary rules and dispositions); AGENTS.md
schema-change rule (bump the `$id`, keep old files validating, name the change in the PR title);
OSD-D7, OSD-D11; E20 finding (tests never pin record totals or wording).

**Outcome.** A record can say that a dataset holds a velocity model, a geological 3D model, airborne
electromagnetic data, radiometric data or stress measurements, each in the publisher's terms; the
built catalogue, the STAC keywords and the map's chips carry the values through unchanged; the ten
records that asked for these kinds use them and lose the sentence that asked; existing records keep
validating.

**Context today (verified 23 Oct, main e63a3e0; Codex-checked).** `schema/record.schema.json` is
record/3 with 19 kinds. Kinds reach the built catalogue (`src/osd/build.py:89`) and STAC `keywords`
(`src/osd/stac.py:186`); site chips derive from the records present (`site/app.js:105`, E19's chip
test covers any kind). The manifest contract (manifest/4, `schema/manifest.schema.json:89-105`,
`src/osd/manifest.py:95-107`) has no kinds field and is not changed by this lane. `src/osd/new.py`
derives choices from the schema for access, redistribution, attribution and listed_by (`:48-54`);
for kinds it only says "see schema" (`:79`) and no test asserts kinds. Record/3 fixtures are built in
`tests/test_schema.py:35-67`; the record/2 compatibility test (`:91-105`) loads the frozen schema
from `tests/fixtures/schema/`. The Ophiolite kind registry (`~/src/ophiolite`, searched 23 Oct for
these names) names none of the five; the names below stand. Ten records ask for a kind, in
top-level `notes` or `known_issues` (not `origin.notes`): velocity model
(`doe-gdr/utah-forge-seismic-reflection` notes:30, `lbeg/tunb-velo-2-0-ni` notes:27,
`soton/scanner-pockmark-velocity-models` known_issues:24); geological 3D model
(`doe-gdr/utah-forge-3d-gravity`, `geosphere-at/molasse-basin-subsurface-model`, `lbeg/tunb3d-ni`);
airborne EM and radiometrics (`geosphere-at/aerogeophysics-northern-lower-austria`, `igme/sigeof`
whose text names airborne magnetic and radiometric flights and, separately, electrical and
electromagnetic *soundings*, `nrcan/canadian-airborne-geophysical-data-base`); stress
(`ustc/bedrettolab-atv-logs-stress` notes:31, "Stress inversion results have no kind", no literal
"Want:"). Two records' wants are not kinds and stay as they are (`force/ml-competition-2020-well-logs`
lithofacies labels, `ns-energy/onshore-2d-seismic-navigation` navigation only). `azu/data-room` and
`dgeg/petroleum-technical-data` record velocity *measurements* as `time-depth`; right; untouched.

**The design the lane must map to.**
1. record/4: `kinds` gains exactly `velocity-model` (a seismic velocity field or cube, interval or
   migration velocities as a model, not time-depth pairs), `geological-model` (a 3D structural or
   property model: layers, volumes, salt bodies, inverted density), `airborne-em` (airborne
   electromagnetic soundings), `radiometrics` (gamma-ray spectrometry surveys, airborne or ground),
   `stress` (in-situ stress measurements and inversions); the enum description defines each in one
   clause. No other schema changes; manifest/4 and stac-osd untouched (the diff proves it). The
   frozen record/3 copy goes to `tests/fixtures/schema/record-3.schema.json`.
2. Compatibility: one fixed set of record/3 fixtures (every record/3 kind, one each) validates under
   the frozen record/3 and under record/4; mutation: remove an old kind from record/4 → red.
3. Propagation, parameterised over all five new kinds: a fixture record with the kind → `build`
   output `records.json` kinds unchanged → STAC Collection `keywords` contains it; the site needs no
   change (chips are data-derived; E19's chip test stands; this lane adds no site test and does
   not touch `tests/site/**` or `site/**`).
4. Scaffold: `osd new` lists the schema's kinds in its kinds comment, read from the schema like the
   other choices; the test asserts the comment equals the schema enum *and* independently that
   each of the five new names is present (a literal list in the test); mutation: scaffold omits one
   entry → red.
5. Records, exact edits and nothing else, each justified by the record's own text (nothing
   re-fetched); expected `kinds` after the lane:
   | record | kinds after | note edit |
   |---|---|---|
   | `doe-gdr/utah-forge-seismic-reflection` | `seismic-3d, seismic-2d, velocity-model` | remove the Want sentence |
   | `lbeg/tunb-velo-2-0-ni` | `velocity-model` | remove the Want sentence (time-depth stood in for the model) |
   | `soton/scanner-pockmark-velocity-models` | `velocity-model` | remove the Want entry from `known_issues` (its SEG-Y files are the models) |
   | `doe-gdr/utah-forge-3d-gravity` | `potential-fields, geological-model` | remove the Want sentence |
   | `geosphere-at/molasse-basin-subsurface-model` | `geological-model, horizons` | remove the Want sentence (the model is delivered as layer surfaces) |
   | `lbeg/tunb3d-ni` | `geological-model, horizons, faults` | remove the Want sentence |
   | `geosphere-at/aerogeophysics-northern-lower-austria` | `potential-fields, airborne-em, radiometrics` | remove the Want sentence |
   | `igme/sigeof` | `seismic-2d, potential-fields, wellbore-logs, radiometrics` | remove only the radiometrics part of the want; the electrical/electromagnetic soundings finding stays in the note |
   | `nrcan/canadian-airborne-geophysical-data-base` | `potential-fields, airborne-em, radiometrics` | remove the Want sentence |
   | `ustc/bedrettolab-atv-logs-stress` | `wellbore-logs, stress` | remove "Stress inversion results have no kind" (the rest verbatim) |
   The rest of each note is kept verbatim. If a record's text contradicts a row, the lane keeps
   the record as it is and says so in the PR (no new finding is deleted).

**Acceptance.**
- record/4 fixtures: each new kind validates; an unknown kind is refused; design 2's two-schema
  compatibility test and its mutation; `uv run osd validate` main's count, 0 problems.
- Design 3's propagation test over the five kinds; `schema/manifest.schema.json`, `schema/stac-osd.json`,
  `site/**` absent from the diff.
- Design 4's scaffold test and mutation.
- The PR shows the ten record diffs beside the table above (expected vs actual kinds, the removed
  sentence, the kept note); no permanent test pins record content (E20 finding).

**Out of scope.** Kinds for lithofacies labels, navigation-only seismic or electrical/EM ground
soundings (findings stay in the records' notes); manifest kinds (E06/E09 contract; a later
charter if a consumer asks); any site or STAC schema change.

**Stop rules.** None.

**Ownership and dependencies.** Coding lane; paths `schema/record.schema.json` (record/4),
`tests/fixtures/schema/record-3.schema.json` (new), `src/osd/new.py` (kinds comment from the
schema), `tests/test_schema.py`, `tests/test_build.py` and `tests/test_stac.py` (propagation
additions; E27 adds to `tests/test_build.py` too, so E26 keeps its additions in a new test
function at the end of the file and the second to merge rebases that one hunk), `tests/fixtures/**`
additions outside `tests/fixtures/site/`, the ten records in design 5, `docs/program/evidence/e26/**`.
No `site/**`, no `tests/site/**`. Depends on E19, E24 (merged).

**Evidence to inspect.** The ten record diffs against the table; the schema diff; the
propagation and compatibility tests; the three mutations.

**Dispositions of the Codex round (23 Oct).** Accepted: manifest kind propagation removed (the
manifest has no kinds field; propagation is proven record → built catalogue → STAC keywords);
scaffold rewritten as new behaviour with an independent literal assertion and its own mutation;
want locations corrected to top-level `notes`/`known_issues`, Bedretto's non-literal sentence
named, the outcome says ten; IGME gains `radiometrics` only and keeps its soundings finding;
exact expected kinds per record in a table (Southampton `velocity-model` alone); naming resolved
(registry searched, none found, five names fixed, no replacement clause); the shared site test
dropped (E26 touches neither `site/**` nor `tests/site/**`; the remaining shared file is one new
test function in `tests/test_build.py`); compatibility now validates one fixed fixture set under
both schemas with a removal mutation; propagation parameterised over all five. Refuted: a permanent
test asserting each record's exact kinds and note text (E20 finding: tests must not pin record
wording; the PR diff beside the table is the proof).
