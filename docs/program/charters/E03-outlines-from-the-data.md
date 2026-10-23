## E03 Outlines from the data — QUEUED · Kernel · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: `docs/ARCHITECTURE.md`; owner direction 23 Oct ("display the outlines of known
available wellbores, seismic outlines on a map"); OSD-D11, OSD-D12, OSD-D13.

**Outcome.** Outlines on the map are derived from the publisher's own register or from the data,
with the input identity and derivation named on every feature. Target set, by record id:
`sodir/factpages` (every wellbore and every seismic survey Sodir publishes), `nlog/nlog` (every
borehole and 3D survey NLOG publishes), `terranubis/f3-demo-2020`, `rmotc/teapot-dome`,
`nopims/poseidon`, `nzpam/parihaka`, `nzpam/kerry-3d` (one survey polygon each). A target the
lane cannot reach (login, blocked, undeclared units) is reported by id with the reason and stays
dashed; the epic is DONE when every target is either solid or reported.

**Context today (verified 23 Oct, main e58e2f5).** Five outline files exist, all hand placed with
`approximate: true` (`outlines/*.geojson`). `schema/outline.schema.json` fixes the properties;
`uwi` and `publisher_id` are optional. `src/osd/verify.py` marks `outline-derived` fail when any
feature is approximate and `skip` otherwise (no pass path yet). Outline validation accepts
MultiPolygon without checking coordinates (`src/osd/records.py`). External prerequisites, not
verified in code: Sodir FactMaps serves WFS (asserted in the record), NLOG serves WFS and CSV,
the four SEG-Y surveys carry coordinates in trace headers.

**The design the lane must map to.**
1. Records hold only publisher facts for inputs: an `inputs:` list, each `{name, url, crs,
   format}` as the publisher states them (schema bump to record/2 with a test that every version-1
   file still validates; claimed here, coordinated after E02 merges). Rules live in
   `src/osd/outlines/rules.yaml` keyed by record id (OSD-D11).
2. Fetching happens only through the verifier's injected fetcher (`osd verify --outlines` fetches
   the inputs, stores bytes under `build/inputs/<id>/`, records their sha256); extractors are pure
   functions over local bytes: `register-wfs`, `register-csv`, `segy-hull`, `publisher-file`.
3. Each input is bound to its own CRS, coordinate fields, units and scalar; an input whose CRS or
   units are not declared is refused with a reason (no guessing). Transform with `pyproj`; test
   known coordinates and axis order.
4. A derived feature carries `approximate: false`, `source` (rule), `input_url`,
   `input_sha256`, `feature_id` (collection-scoped: `<record-id>#<publisher_id|uwi>`, required for
   derived features, collisions refused), `licence` (from the record, OSD-D13). Point for
   wellbores, Polygon or MultiPolygon for surveys and fields, LineString for 2D lines; every ring
   validated closed and non-empty.
5. The verifier's `outline-derived` check passes only when every feature of the file is derived,
   the file's `input_sha256` values match the stored inputs, and the feature count is at least the
   count recorded in the rules file for that id (nonempty target). L3 still requires L2.
6. Committed outlines are the contract (OSD-D12); the extractor is rerun on demand and the diff
   reviewed. PMTiles is not produced here (E05 decides its own tiling).

**Acceptance.**
- Sodir: the set of wellbore `publisher_id`s equals the id set of a frozen, paginated fixture of
  the WFS response (exact set equality, unique ids); the live count on the Sodir table page on the
  day of the run is recorded by hand as supplementary evidence.
- NLOG: same shape for boreholes and 3D surveys.
- F3: the hull from an irregular trace-header fixture with a known exact hull (corner coordinates
  listed in the test) matches to 1 m; a mutation that replaces the hull with a bounding box fails
  it; a mutation that swaps the x/y header bytes fails the known-coordinate test.
- Negative cases, each its own test: missing `inputs`, empty response, undeclared CRS, undeclared
  units, a feature with `approximate: true`, a duplicate `feature_id`: none reaches
  `outline-derived pass`.
- After the run, `osd status` shows L3 for every reached target and the PR lists each unreached
  target with its reason.
- Every version-1 record still validates under record/2 (test).

**Out of scope.** Rendering and tiling (E05), STAC items (E04), any dataset not in the target set.

**Stop rules.** A publisher's WFS carries no licence statement for the outlines: stop that
target, add a D item, continue with the rest. A survey's SEG-Y headers do not declare units: report
it, keep it dashed.

**Ownership and dependencies.** Coding lane; paths `src/osd/outlines/**`, `src/osd/verify.py`
(outline checks only, after E02 merges), `src/osd/records.py` (outline validation),
`schema/record.schema.json` (record/2: `inputs`), `schema/outline.schema.json` (new required
properties for derived features), `outlines/**`, `records/<targets>.yaml` (`inputs` only),
`pyproject.toml` (pyproj, segyio), `tests/test_outlines.py`. Depends on E02 (merged).

**Evidence to inspect.** The fixture id sets; the hull test; `osd status`; a screenshot of Norway
with solid outlines.

**Dispositions of the Codex round (23 Oct).** Accepted: record/tool boundary (design 1), fetch
through the verifier (2), per-input CRS binding (3), identifier and geometry contract (4), L3
evidence beyond a rule name (5), committed-output exception made explicit (OSD-D12), licence of
derived geometry (OSD-D13), id-set equality instead of counts, exact-hull fixture and real
mutations, negative cases, named target set, ownership of verify.py/records.py/pyproject, PMTiles
removed. Refuted: "L3 prerequisite L2 undefined": L2 is E02's contract and the ladder stands;
targets that cannot reach L2 are reported, not exempted. Noted: the `outline_path` literal in the
old text was a wording error, fixed.
