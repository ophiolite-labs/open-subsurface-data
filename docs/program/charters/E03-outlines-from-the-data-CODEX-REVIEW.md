**1. Verdict: REWORK.** The charter lacks an enforceable L3 derivation contract, sufficient ownership, and acceptance checks that establish its promised coverage.

Verified against HEAD `e58e2f547715fc46d94a7e778eb142190578803c`. No files modified. References below are repository-relative; “E03” means the reviewed charter.

**2. Factual errors and Context verification**

- Confirmed all five files are hand-placed and approximate: `outlines/{equinor__volve,nopims__poseidon,nzpam__parihaka,rmotc__teapot-dome,terranubis__f3-demo-2020}.geojson:2` each explicitly states both.
- Confirmed feature-property schema exists (`schema/outline.schema.json:7`); confirmed any approximate feature produces `outline-derived: fail` (`src/osd/verify.py:85`). Non-approximate features currently produce **skip**, not pass (`:89`).
- Publisher-service claims are not code-verified: Sodir WMS/WFS is asserted in `records/sodir/factpages.yaml:12`; `records/nlog/nlog.yaml:8` supplies a landing page, with no WFS/CSV input or fixture. Label these external prerequisites, not verified implementation facts.
- SEG-Y coordinates and the cited F3/E123 proof are unsupported by this HEAD: no extraction implementation or trace-header fixture exists. F3’s record describes an OpendTect project (`records/terranubis/f3-demo-2020.yaml:4`), not proof of accessible SEG-Y headers.
- E03:23 gives the wrong literal output path: IDs contain `/`, but loading requires flattened filenames (`src/osd/paths.py:14`). Use `outline_path(record["id"])`.

**3. Design objections and concrete alternatives**

- **Record/tool boundary:** E03:22 puts our extraction algorithm into publisher-fact records. Keep publisher asset URLs/CRS in records; keep rule selection in extractor configuration and actual derivation evidence in tool output (`schema/record.schema.json:5`).
- **L3 evidence:** A rule name, input address and `approximate: false` cannot establish derivation. Require nonempty valid geometry tied to the actual input identity and extraction result; have the verifier reject missing, changed or failed evidence. Keep this evidence outside records.
- **Network ownership:** `register-wfs` leaves fetching unspecified. Acquire WFS pages through `osd verify` with an injected fetcher; pass local bytes to pure extractors. This preserves the repository’s network boundary and offline gate.
- **CRS contract:** One record CRS does not necessarily describe every register layer or asset. Bind each input to its declared CRS, coordinate fields, units and scalar; refuse ambiguous inputs. Test known transformed coordinates and axis order, not merely CRS-field presence.
- **Geometry contract:** E03:29 requires identifiers and restricts geometry, but IDs are optional (`schema/outline.schema.json:14`) and validation accepts MultiPolygon without validating coordinates (`src/osd/records.py:115`). Specify kind/geometry/identifier constraints and enforce them; retain legitimate multipart publisher geometry rather than silently dropping it.
- **Licensing boundary:** Derived publisher geometry encounters a blanket CC0 dedication (`records/LICENSE:1`), while F3 declares attribution and share-alike (`records/terranubis/f3-demo-2020.yaml:12`). Preserve applicable source terms and attribution; distinguish catalogue metadata from derived geometry before publishing it.
- **Ownership:** E03:49 omits `verify.py`, `records.py`, affected records, dependency configuration and—if retained—`build.py`. Claim the actual integration paths and relevant tests; coordinate schema versions after E02 rather than preassigning `record/2`.
- **Committed generated output:** E03:24 conflicts with ENGINEERING’s prohibition on committing regenerable output. Explicitly resolve the existing outline-contract exception, or generate derived outlines into build output while committing recipes and small fixtures.

**4. Acceptance holes and surviving mutations**

- **Counts (E03:33–35):** Duplicate one borehole and omit another: totals remain correct. Assert unique publisher IDs and exact ID-set equality against a frozen, paginated response fixture; retain live hand counts as supplementary evidence.
- **Coverage:** Exploration-well counts establish neither all Norwegian wellbores nor Norwegian/Dutch surveys promised at E03:7. Enumerate required layers, filters and IDs; test each.
- **F3 area (E03:36):** Translation, reflection or a wrong shape with equal area passes. Add independently known corner coordinates, bounds and expected hull geometry.
- **“Mutation” (E03:38):** Shuffling and adding an outlier are input variations, not implementation mutations; a bounding-box algorithm can pass both. Use an irregular point cloud with an exact expected hull, then demonstrate failure when hull construction or header decoding is altered.
- **Universal pass (E03:40):** Removing every optional `outlines` field makes this vacuous; unconditional pass also satisfies the positive case. Assert a fixed, nonempty target set and negative cases for missing/empty outlines, approximate geometry, unknown CRS and invalid provenance.
- **No approximate features (E03:41):** Deleting files/features passes. Require file existence, nonzero expected coverage, valid geometry and identifiers before checking approximation.
- **L3 evidence (E03:54):** L3 requires passing L2 (`src/osd/verify.py:56`), but the charter supplies no per-target L2 prerequisites. Define achievable prerequisite evidence and explicit outcomes for blocked targets.
- **Contradictory target set:** The outcome promises five SEG surveys; acceptance names four plus two registers and omits Volve. Login/unknown-unit exceptions also contradict unconditional six-record L3 evidence. Name exact record IDs and define conditional completion criteria.

**5. Scope overlap**

- PMTiles production (E03:27) crosses into E05’s scaling interface (`E05-map-that-scales.md:18`). It is an explicit proposed handoff, but lacks layer/property/zoom contracts and threshold tests; defer it or agree and test that boundary without adding a CI station.
- Verifier integration necessarily touches E02-owned code (`E02-verifier-to-L2.md:49`); treat this as a sequential ownership handoff, not permission to redesign L2.
- Stable outline identifiers should support E04’s shared feature/item identity (`E04-stac-catalogue.md:24`); keep STAC generation and extension design in E04.