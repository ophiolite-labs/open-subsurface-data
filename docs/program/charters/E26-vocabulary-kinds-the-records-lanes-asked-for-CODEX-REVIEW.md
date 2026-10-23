**1. Verdict: REWORK.** The charter requires kinds to survive a manifest contract that cannot represent them, and its record-edit and compatibility requirements need correction.

Verified against HEAD `e63a3e0515945c07cdee51a1a12396e6eac6fa9c`. No files modified.

**2. Factual errors and Context verification**

- **Manifest kinds do not exist.** Design 1 says manifest/4 carries free keywords; its entry schema forbids additional properties and defines neither `kinds` nor `keywords` (`schema/manifest.schema.json:89–105`). The typed reader likewise has neither (`src/osd/manifest.py:95–107`). STAC Collections carry keywords; the OSD extension does not define them.
- **Scaffold claim is misleading for kinds.** Schema-derived choices cover access, redistribution, attribution and listed_by (`src/osd/new.py:48–54`). Kinds only says “see schema” (`:79`); the existing test never asserts kinds (`tests/test_schema.py:127–136`). This requires new behavior, not merely maintaining existing comments.
- **Want locations are wrong.** Most are top-level `notes`, not `origin.notes`: e.g. `records/doe-gdr/utah-forge-seismic-reflection.yaml:30`, `records/lbeg/tunb-velo-2-0-ni.yaml:27`. Southampton’s is in `known_issues` (`records/soton/scanner-pockmark-velocity-models.yaml:24`).
- **Literal removal cannot cover all ten.** Bedretto has no “Want:” sentence; its equivalent is “Stress inversion results have no kind” (`records/ustc/bedrettolab-atv-logs-stress.yaml:31`). The outcome also promises twelve changes while design 4 deliberately changes ten.
- **IGME does not establish airborne EM.** Its text distinguishes airborne magnetic/radiometric flights from electrical/electromagnetic soundings (`records/igme/sigeof.yaml:7–9,30`). The condition in design 4 must therefore exclude `airborne-em` here.
- **Other Context claims checked:** record/3 contains 19 kinds including `potential-fields` (`schema/record.schema.json:3,61–65`); STAC copies kinds (`src/osd/stac.py:186`); chips derive from records (`site/app.js:105,237–240`).
- Record/3 fixtures are constructed in `tests/test_schema.py:35–67`; the record/2 compatibility test is at `:91–105`, loading the frozen schema at `:32`. The fixtures directory contains the old schema, not that test.
- Opened all twelve named records: their model, geophysics, stress and two deferred vocabulary findings exist, subject to the corrections above. Both excluded velocity records use `time-depth` as claimed (`records/azu/data-room.yaml:23,29`; `records/dgeg/petroleum-technical-data.yaml:24,34`).

**3. Design objections and concrete alternatives**

- **Impossible manifest boundary:** remove manifest kind propagation from this lane; prove record → built catalogue → STAC keywords and site filtering. If manifests must carry kinds, explicitly charter a versioned schema, writer, reader and site-export change with backward compatibility.
- **Unsupported classification:** add only `radiometrics` to IGME and preserve its unresolved electrical/EM finding. Do not delete that finding merely because another part was addressed.
- **Container versus content:** Southampton’s SEG-Y files are velocity models (`records/soton/scanner-pockmark-velocity-models.yaml:4–6,12`), so SEG-Y alone cannot justify retaining `seismic-3d`. Specify exact expected kinds per record from its stated contents.
- **Naming contract is unresolved:** design 1 demands exactly five spellings while design 2 permits replacements. Resolve registry mappings before freezing fixtures and acceptance names; cite the registry revision and file.
- **Ownership violates the no-overlap rule:** “second to merge rebases” explicitly shares `tests/site/site.test.mjs` with E27. Sequence that path’s ownership or agree disjoint test files and fixture paths before opening E26.

**4. Acceptance weaknesses**

- **Compatibility can pass vacuously:** validating old fixtures only under their frozen old schema cannot detect record/4 rejecting an old kind. Validate the same fixed old fixtures under both schemas; mutate record/4 by removing an old kind and require failure.
- **Scaffold mutation can stay green:** if expected and actual choices both read the mutated enum, removing an entry changes both equally. Assert the five agreed additions independently, alongside schema equality; separately mutate the scaffold to omit one.
- **“Exactly the kinds line and removed sentence” tests shape, not meaning:** a wrong allowed kind or retained Southampton placeholder can satisfy it. Assert exact kinds and remaining note text for each named record, including Bedretto’s nonliteral finding.
- **One-kind propagation is incomplete:** a special case preserving only `velocity-model` passes while dropping four other additions. Parameterize propagation over all five agreed values.
- The manifest acceptance is currently **unsatisfiable**, rather than vacuous; weakening it to manifest validation alone would silently abandon the promised propagation.

**5. Scope into other charters**

- Adding manifest kind storage expands into E06/E09’s retrieval and consumer contract; E19 changed that contract explicitly (`docs/program/charters/E19-vocabulary-from-the-records-lanes.md:32–34`). Defer it or declare that scope and its proof.
- E27 explicitly owns the same journey-test file and site fixtures (`docs/program/charters/E27-the-map-says-why.md:49–53`); resolve ownership, not merely merge order.
- No additional E25 records work is needed: its charter already excludes E26’s named records. Keep the lane’s edits confined to the corrected ten-record list.