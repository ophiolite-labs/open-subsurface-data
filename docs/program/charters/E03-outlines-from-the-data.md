## E03 Outlines from the data — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: `docs/ARCHITECTURE.md`; owner direction 23 Oct ("display the outlines of known
available wellbores, seismic outlines on a map").

**Outcome.** Outlines on the map are derived from the data or the publisher's own register, with
the derivation named on every feature. Every wellbore and survey on the Norwegian and Dutch
shelves, and the five 3D surveys of the SEG list that are at L1, are drawn solid. No dashed
placeholder remains for a record at L3.

**Context today (verified 23 Oct).** Five outline files exist, all `approximate: true`, hand
placed. `schema/outline.schema.json` fixes the feature properties. The verifier marks
`outline-derived` fail when any feature is approximate. Sodir FactMaps serves WMS/WFS; NLOG
serves WFS and CSV downloads; the SEG surveys ship as SEG-Y whose trace headers carry
coordinates (verified for F3 in Ophiolite's E123 work; assumed for the others).

**The design the lane must map to.**
1. One extractor per derivation rule, each a function `(record, inputs) -> FeatureCollection`
   in `src/osd/outlines/<rule>.py`: `register-wfs` (Sodir, NLOG), `segy-hull` (trace-header
   convex hull, with `segyio`), `las-header` (wellhead lat/long or publisher CSV), `publisher-file`
   (a shapefile or GeoJSON the publisher ships).
2. A record names its rule and inputs in a new optional field `outlines: {rule, inputs}`; the
   extractor writes `outlines/<id>.geojson` with `approximate: false` and `source` naming the rule
   and the input address. Committed outlines are the contract; the extractor is rerun on demand.
3. Coordinates are transformed to EPSG:4326 with `pyproj` from the CRS the record states;
   a record without `region.crs` cannot reach L3 for SEG-Y-derived outlines.
4. Size: when the merged `outlines.geojson` exceeds 20 MB, the build also writes PMTiles via
   `tippecanoe` (E05 consumes it). The GeoJSON stays the GIS address.
5. Wellbores are Points with `uwi` or `publisher_id`; surveys are Polygons; 2D lines are
   LineStrings. Nothing else.

**Acceptance.**
- Sodir: the number of exploration wellbores in `outlines/sodir__factpages.geojson` equals the
  count on the Sodir wellbore table page on the day of the run, by hand, ±0 (recorded in the PR).
- NLOG: the number of boreholes equals the NLOG borehole count on its data page, by hand.
- `segy-hull` on the F3 volume yields a polygon whose area in EPSG:23031 is within 2 % of the
  survey's stated inline × crossline extent (computed by hand from the survey definition).
- Mutation: a shuffled trace-header fixture still yields the same hull (order independence),
  and a fixture with one outlier trace changes the hull (the test proves the hull reads the data).
- `osd verify` reports `outline-derived pass` for every record with an `outlines` field.
- No feature with `approximate: true` remains for sodir, nlog, f3, teapot, poseidon, parihaka.

**Out of scope.** Rendering (E05), tiling beyond the PMTiles write, any dataset whose files need a
login the lane does not have (record stays at L1 with a note).

**Stop rules.** A publisher's WFS has no licence statement for the outlines: stop, add a D item.
SEG-Y coordinates are in a unit the header does not declare: mark approximate, note it.

**Ownership and dependencies.** Coding lane; paths `src/osd/outlines/**`, `outlines/**`,
`schema/record.schema.json` (adds `outlines`, kernel bump to record/2 with a test that version-1
files still validate), `tests/test_outlines.py`. Depends on E02 (the level ladder it feeds).

**Evidence to inspect.** The hand counts in the PR; a screenshot of Norway with solid outlines;
`osd status` showing L3 for the six records.
