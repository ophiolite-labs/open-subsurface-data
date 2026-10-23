## E26 Vocabulary: the kinds the records lanes asked for — QUEUED · Kernel (small) · strategy at lane open · one Codex round

Authority: E20, E22 and E24 findings in `docs/program/HANDOFF.md` and the `notes` of the records
named in design 4 ("Want: a kind for …"); E19 (record/3, the vocabulary rules and dispositions);
AGENTS.md schema-change rule (bump the `$id`, keep old files validating, name the change in the
PR title); OSD-D7, OSD-D11.

**Outcome.** A record can say that a dataset holds a velocity model, a geological 3D model,
airborne electromagnetic data, radiometric data or stress measurements, each in the publisher's
terms; the map's chips, the STAC keywords and the manifest carry the values through unchanged;
the twelve records that wrote "Want: a kind for …" use the new kinds and lose the want sentence;
existing records and manifests keep validating.

**Context today (verified 23 Oct, main 4dcdc56).** `schema/record.schema.json` is record/3 with
19 kinds (E19 added `potential-fields`). Kinds are STAC `keywords` (`src/osd/stac.py`), site chips
derive from the records present (`site/app.js`, no vocabulary copy), `src/osd/new.py` scaffold
comments and a test read the schema's values (E19 design 3). `tests/test_schema.py` holds the
record/3 fixtures and the record/2 compatibility test under `tests/fixtures/schema/`. Twelve
records name a want in `origin.notes` or `known_issues`: velocity model
(`doe-gdr/utah-forge-seismic-reflection`, `lbeg/tunb-velo-2-0-ni`,
`soton/scanner-pockmark-velocity-models`); geological 3D model (`doe-gdr/utah-forge-3d-gravity`
"3D density model from gravity inversion", `geosphere-at/molasse-basin-subsurface-model`,
`lbeg/tunb3d-ni`); airborne electromagnetics and radiometrics
(`geosphere-at/aerogeophysics-northern-lower-austria`, `igme/sigeof`,
`nrcan/canadian-airborne-geophysical-data-base`); stress (`ustc/bedrettolab-atv-logs-stress`,
"stress_inversion.zip"); and two whose want is not a kind and stay as they are
(`force/ml-competition-2020-well-logs` lithofacies labels, `ns-energy/onshore-2d-seismic-navigation`
navigation only). `azu/data-room` and `dgeg/petroleum-technical-data` record velocity
*measurements* as `time-depth`; that is right and they are not touched.

**The design the lane must map to.**
1. record/4: `kinds` gains exactly `velocity-model` (a seismic velocity field or cube, interval or
   migration velocities as a model, not time-depth pairs), `geological-model` (a 3D structural or
   property model: layers, volumes, salt bodies, inverted density), `airborne-em` (airborne
   electromagnetic soundings), `radiometrics` (gamma-ray spectrometry surveys, airborne or ground),
   `stress` (in-situ stress measurements and inversions). The enum description defines each in one
   clause. record/3 files validate under record/3 in the compatibility test (frozen copy under
   `tests/fixtures/schema/`), every stored record validates under record/4. No other schema changes;
   `manifest/4` and `stac-osd` carry kinds as free keywords and need no bump (assert this with a
   test that a record/4 kind round-trips build → manifest → STAC keyword).
2. Names: if the Ophiolite kind registry (`~/src/ophiolite`, E55) names any of these, use its
   name and cite the file in the PR; else the names above stand and the PR says the registry has
   none.
3. No vocabulary copies: `src/osd/new.py` scaffold comments and its test read the schema; site
   chips stay data-derived (one site journey test with a fixture catalogue holding a
   `velocity-model` record shows the chip and filters by it); `how.html` is not touched
   (E27 holds the site text).
4. Records, exact edits and nothing else: the ten records above gain the kind their want names
   (`doe-gdr/utah-forge-3d-gravity` gains `geological-model` and keeps `potential-fields`;
   `igme/sigeof` and `nrcan/canadian-airborne-geophysical-data-base` gain both `airborne-em` and
   `radiometrics` only where their own text names each; `geosphere-at/aerogeophysics-…` likewise;
   `ustc/bedrettolab-atv-logs-stress` gains `stress`; velocity and geological-model records gain
   their kind and keep the nearest kind only if the dataset also holds that kind, e.g. SEG-Y
   volumes beside a velocity model) and the "Want: …" sentence is removed from `notes`, the rest
   of the note kept verbatim. The two non-kind wants are untouched. Every edit cites the record's
   own text; nothing is re-fetched.

**Acceptance.**
- record/4 fixtures: each new kind validates; an unknown kind is refused; record/3 fixtures
  validate under the frozen record/3; `uv run osd validate` 140 records (or main's count), 0 problems.
- Round trip: a fixture record with `velocity-model` reaches the manifest and the STAC Collection
  `keywords` unchanged; stac-osd and manifest schemas unchanged in the diff.
- Scaffold: the `osd new` comment lists the five new kinds, read from the schema (mutation: schema
  enum entry removed → the scaffold test is red).
- Site: fixture catalogue with one `velocity-model` record and one without; the chip appears and
  filtering includes the one and excludes the other.
- The ten record diffs show exactly the `kinds` line and the removed sentence.

**Out of scope.** Kinds for lithofacies labels or navigation-only seismic (recorded as findings,
not added); any site text; STAC or manifest schema versions.

**Stop rules.** None.

**Ownership and dependencies.** Coding lane; paths `schema/record.schema.json` (record/4),
`tests/fixtures/schema/record-3.schema.json` (frozen copy), `src/osd/new.py` (comments only),
`tests/test_schema.py`, `tests/test_new.py` or where the scaffold test lives, `tests/test_stac.py`
and `tests/test_manifest.py` (round-trip additions), `tests/site/site.test.mjs` (one journey test;
shared with E27, second to merge rebases), `tests/fixtures/**` additions, the ten records named
in design 4, `docs/program/evidence/e26/**`. Depends on E19, E24 (merged).

**Evidence to inspect.** The ten record diffs; the schema diff; the round-trip test; the chip
screenshot; the mutation.
