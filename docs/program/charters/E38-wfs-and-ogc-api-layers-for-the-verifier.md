## E38 WFS and OGC API Features layers for the verifier — CHARTERED · Kernel · strategy at lane open · Codex round closed (REWORK, reworked 24 Oct)

Authority: supervisor 24 Oct 2026 under the owner's direction of 23 Oct (levels on the map are
real); E35 (whole ArcGIS layers as verification/5 `layer_exports`, `src/osd/verifier/layers.py`,
designs 1 to 6 and its 22 dispositions); E23 (listing readers by shape); E30 finding F1 and the
E24, E31 and E37 evidence naming WFS or OGC API Features as the only machine listing a publisher
offers; H3 (robots read as RFC 9309 reads them; this lane starts after H3 merges or rebases onto
it); OSD-D9, OSD-D11, OSD-D20.

**Outcome.** Datasets whose publishers serve their features only through an OGC Web Feature Service
or an OGC API Features collection reach L2 on evidence of the whole layer, exactly as E35's ArcGIS
layers do; nothing a person downloads changes.

**Context (main 00ee199, 24 Oct; corrected by the Codex round).** 64 anonymous-access records have
no `manifest_url`. Conversion candidates named by the evidence: GA STRATDAT and RESFACS (WFS only,
`records/ga/stratdat-biostratigraphy.yaml:12`, `resfacs-porosity-permeability.yaml:11`) and WOGCC
(GeoServer WFS, `docs/program/evidence/e24/new-americas.md:28`). DOV boringen already has a WFS
`manifest_url` served as a bare file (`samples.yaml:38`, `file: true`): it moves to the new reader
(188,507 features on 23 Oct, above the cap: a partial export, now said so). BGS keeps its ZIP
download and PGI stays E35's: both are fixture or regression evidence only. The lane tabulates and
may add candidates (`docs/program/evidence/e38/candidates.md`: record, endpoint, robots line,
`numberMatched` or `hits`, CRS, paging support, revision signal).

**The design the lane must map to.**
1. Contract first: verification/6 with /5 frozen under `tests/fixtures/schema/` (hash pin) and every
   /3, /4, /5 file still validating. `layer_exports[].format` gains `ogcapi-geojson` and
   `wfs-geojson`; the expected count may be `null` only together with an explicit
   `"completeness": "unconfirmed"`; such an export never earns L2.
2. Explicit outcomes per protocol: each exporter returns complete, partial (cap, unsortable,
   unpageable, with the reason) or failed. A partial or unconfirmed export is never written to
   `files`, never earns L2, never reaches STAC or `osd get`. Completeness is never inferred from the
   absence of ArcGIS's `exceededTransferLimit`.
3. Dispatch precedence: a `manifest_url` recognised as OGC API Features (`/collections/<id>` or
   `/items`) or WFS (`service=WFS` with `typeNames`) goes to its reader before the bare-file
   classification (`verify.py:458`, `:473`); conflicting `samples.yaml` overrides (`file: true`)
   are removed for those records.
4. OGC API Features: page by the `next` link only, GeoJSON, expected count from `numberMatched`;
   no `numberMatched` gives `completeness: unconfirmed`. Ids from feature `id`; duplicates and
   paging loops fail.
5. WFS 2.0.0 only, from its capabilities: `resultType=hits` for the count, `GetFeature` with `count`,
   `startIndex` and `sortBy` on the id, GeoJSON output only. WFS 1.1, GML-only services and services
   without paging or sorting are partial with the reason (deferred, not hashed).
6. Canonical bytes as E35 design 3: features sorted by id, keys sorted, no whitespace, coordinates
   as returned. Revision signal only where the protocol states one for the collection (not response
   timestamps or per-page ETags); else "stability unknown".
7. E35 designs 4 to 6 stand (budget, pacing, robots through H3's shared interface, the 50,000 cap).
8. Records edits limited to `origin.manifest_url` and `notes` of the conversion candidates; an
   existing downloadable manifest is never replaced.

**Acceptance.**
- Exact canonical bytes asserted; shuffled pages and features within pages give identical bytes; an
  attribute, a geometry and a coordinate change each change the digest.
- Each guard isolated so removing it alone turns its test green, each with a mutation recorded red
  in `docs/program/evidence/e38/mutations.md`: `numberMatched` and `hits` mismatch (unique ids,
  valid pages), duplicate id, paging loop, missing count gives unconfirmed and no L2, cap fallback
  (partial evidence, no `files` entry, no L2, no STAC asset), unsortable WFS partial, robots refusal
  on a later page, budget exhaustion, exception responses, dispatch precedence over `file: true` and
  attachment headers, end to end through `check_files` with an injected opener.
- Schema: /6 validates new files; every /5, /4 and /3 fixture and stored result validates.
- Two branch verify dispatches: for each implemented protocol at least one eligible multi-page
  candidate passes whole on both runs with equal checksums, or that protocol's outcome is recorded
  incomplete with the publisher's reason; checksum disagreements under unknown stability are listed,
  not exempted (`docs/program/evidence/e38/results.md`).
- `make check` green and under 120 s on the PR's CI run.

**Claim.** `src/osd/verifier/layers.py`, `src/osd/verifier/listings.py` (WFS and OGC API shapes),
`src/osd/verify.py` (`check_files` dispatch and outcomes for the new formats only),
`schema/verification.schema.json` (verification/6), `tests/fixtures/schema/verification-5.schema.json`
(new), `tests/test_schema.py` (version tests), `tests/test_verify.py` (the `$id` assertion only),
`tests/test_ogc_layers.py` (new), `tests/fixtures/ogc_layers/**` (new), `records/**`
(`origin.manifest_url` and `notes` of the conversion candidates), `src/osd/verifier/samples.yaml`
(their entries and the removed overrides), `docs/program/evidence/e38/**`.

**Dispositions (Codex round, 24 Oct).**

| Objection | Disposition |
|---|---|
| Schema bump needed; /5 fixes format and count | Accepted: design 1, verification/6, /5 frozen |
| BGS already downloadable | Accepted: fixture only, ZIP kept (design 8) |
| DOV already a bare-file WFS | Accepted: moves to the reader, partial above cap (context, design 3) |
| PGI is E35's | Accepted: regression evidence only |
| Partial fallback can reach `files` and L2 | Accepted: design 2 |
| Bare-file classification precedes readers | Accepted: design 3 |
| GML rules contradict | Accepted: GML deferred (design 5) |
| WFS 1.1 differs | Accepted: 2.0.0 only, 1.1 deferred |
| Count unconfirmed weakens evidence | Accepted: unconfirmed never earns L2 (designs 1, 4) |
| Snapshot signal per protocol | Accepted: design 6 |
| Vacuous dispatch acceptance | Accepted: per-protocol pass or recorded incomplete |
| Undefined "layer did not change" | Accepted: disagreements under unknown stability listed |
| Shuffle within pages, exact bytes, digest changes | Accepted |
| Guard isolation | Accepted |
| Cap fallback assertions | Accepted |
| End-to-end dispatch cases | Accepted |
| "Inside main's spread" unbounded | Accepted: under 120 s |
| Blanket candidate rewrite | Accepted: design 8 |
| H3 dependency, not scope | Accepted: robots through H3's interface |
