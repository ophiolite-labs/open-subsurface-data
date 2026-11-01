# OpendTect project -> Ophiolite workspace: managed and viewed? (architecture trace, 1 Nov 2026)

Read-only. Source: `origin/main` of /home/epic/src/arraybridge at 1cc9007af (fetched 1 Nov). Paths are repo-relative; line
numbers are `origin/main` lines. "UNVERIFIED" marks what was inferred, not read. `W` = ophiolite-workspace/app/src,
`G` = ophiolite-platform/services/project_gateway, `O` = ophiolite-opendtect/src/ophiolite_opendtect.

## 0. Short answer

Per kind, today (managed = lands as an item with provenance and can be read back; viewed = a Workspace screen draws it):

| Kind | Managed | Viewed in the Workspace |
|---|---|---|
| 3D seismic cube | partial: only cubes the exporter accepts, up to the deployment's file bound; the 21.9 GB cube cannot enter | yes, one inline/crossline/sample slice at a time |
| 3D seismic as 699 MB SEG-Y | yes (`segy/1`, ranged intake; 2.77 GB real volume qualified in E54) | yes, same slice viewer |
| 2D seismic lines | yes since 1 Nov (`segy-line/1`, one item per line) | NO viewer (fallback page) |
| 3D horizon (up to 619,101 nodes) | yes since 1 Nov, default bound 1,000,000 nodes | partial: plan dots + first 500 rows; no viewer path for the >100,000-node column form |
| 2D horizon | NO writer, NO landing (E137 s6 chartered, not started) | NO |
| Fault stick set / Fault3D | yes (sticks only, FaultStickSet ASCII `opendtect-faultsticks/1`) | yes, plan view of sticks |
| Wells: path, logs | yes (native well, path as next version, LAS curves) | logs yes; path view UNVERIFIED |
| Wells: markers (tops) | NO writer (E137 s4 chartered) | tops viewer exists, nothing to show |
| Wells: time-depth | NO writer on main (E137 s3 in lane); 7 of 10 Poseidon wells only | viewer exists (`TimeDepthView`) |
| Picksets | NO (no odbind class; no catalogue kind; refused by name) | NO |

No: the whole chain does not work today for all five projects. Stage details below.

## 1. Reading from OpendTect through odbind

Two independent readers, both odbind-only and both in OpendTect's own Python (GPL package `ophiolite-opendtect`, not imported
by the SDK: `ophiolite-opendtect/tests/test_boundary.py`, PROGRAM.md:1747).

- Exporter reading path: `O/survey.py` (284 lines) + `O/export.py` (writes files). Used by `ophiolite starter export`.
- Read CLI `O/read.py` (E137 s1/E138 s1 oracle): lists and dumps arrays as JSON Lines. Its KINDS are `seismic-3d, horizon-3d,
  well, well-log, line-2d, horizon-2d, fault-3d, fault-sticks` (`O/read.py:32`); enumeration calls `Seismic3D/Horizon3D/Well/
  Seismic2D/Horizon2D/Fault3D/FaultStickSet.names` (`O/read.py:107-139`). Horizon-2d is LISTED but marked later
  (`O/read.py:37` `LATER = {'horizon-2d': 6}`); arrays are dumped only for the other seven (read.py:154-221 per-kind functions;
  no horizon-2d function).
- Picksets: no odbind class is called anywhere; `grep pickset` over opendtect/sdk/platform/web finds only a refusal test
  (`ophiolite-opendtect/tests/test_starter_kinds.py:209-211`: `'picksets'` -> "not a kind of a starter pack").
- E125 connector direction survey->project is `send`: wells (head + path) and horizons only (`O/exchange.py:10-12`,
  `O/wells.py:1`). Cubes, lines and faults go project->survey (`get`, `O/exchange.py:15-24`).
- Wells: logs read on a regular step through `Well.logs(zstep)` (`O/read.py:198`); markers are not read by the exporter
  (no `tops` writer, see stage 2). Deviation is exported as sampled positions `md,x,y,tvdss` (`O/export.py:353`), not as the
  raw deviation survey.
- Z precondition: survey must be TWT in ms, depths metres, SRD 0 (`O/export.py:127-136, 442`, `Z_UNIT`, `DEPTH`).
  Depth cubes and feet are refused by name (`O/export.py:33, 132`).

Tests: unit tests on a fake odbind (`ophiolite-opendtect/tests/fake_odbind/`, `test_read.py`, `test_export*.py`,
`test_lines.py`, `test_faults.py`); live tests `test_*_live.py` need OpendTect 7.0.x and are not in hosted CI by default
(UNVERIFIED which run hosted; `ophiolite-opendtect/ci/required-offline.txt` lists the offline set).

## 2. Conversion to exchange/intake formats (starter-pack export, E129/E137)

Catalogue of 24 kinds: `ophiolite-sdk/ophiolite/starter_kinds.py:14-39`. A kind with `profile=None` has no pack file:
`wellbore-headers, tops, core, seismic-4d, surfaces, reservoir-model, velocity-model, ...`. Writers are
`O/export.py:499-500` `WRITERS = {seismic-3d, horizons, wellbore-paths, wellbore-logs, seismic-2d, faults}`; any other key
is refused by name (`O/export.py:422-427`, `starter_kinds.py:41`). SDK read-back table: `starter_archive.py:469`.

| OpendTect object | Writer (`O/export.py`) | File / profile | Limits (cited) |
|---|---|---|---|
| Seismic3D | `write_cube` :148 | SEG-Y rev1, IEEE float32, `segy/1` | single component; start/step integer ms, start <= 32767, interval <= 65535, samples uint16 (:156-159); every sample finite (:173); x,y to 0.01 m, int32 (:175); 8-bit source widened to float32 |
| Horizon3D | `write_horizon` :330 | `points-csv/1` `x,y,z,inline,crossline`, every grid node, z empty if undefined (export.py:6-12) | no horizon attributes exported (only those 5 columns, UNVERIFIED for multi-attribute grids) |
| Seismic2D | `write_line` :299 | `segy-line/1`, one SEG-Y per line | MAX_TRACES 200,000; MAX_SAMPLES 20,000; MAX_ABSENT 64 source points (:78); TWT only (:209) |
| FaultStickSet / Fault3D | `write_fault` :286 | `opendtect-faultsticks/1` (.dat) | 20,000 sticks / 200,000 points (:75); sticks of >= 2 points; time only; a Fault3D is exported as sticks, never its surface |
| Well path | `write_positions` :353 | `well-path-positions-csv/1` | positions md,x,y,tvdss |
| Well logs | `write_las` :378 | `las2/1` on a regular depth step | log name/unit must fit LAS (a unit with a space is written `_`: HANDOFF.md:56); -999.25 sentinel refused (:392) |
| Time-depth | none on main | `time-depth-csv/1` exists in the catalogue (starter_kinds.py:20) | E137 s3 in lane |
| Well markers | none | `well-tops-csv/1` exists as a standard file but no pack kind profile (starter_kinds.py:18 `profile=None`) | E137 s4 chartered (EPICS.md:13784) |
| Horizon2D | none | none | E137 s6 chartered (EPICS.md:13786); refused as unknown kind |
| PickSet | none | none | no epic |

Archive-level limits of `ophiolite starter export`: at most 200,000 members and **8 GiB uncompressed** per archive
(`ophiolite-sdk/ophiolite/starter_archive.py:46`, enforced :186-188); child-process timeout 7,200 s (:47). Poseidon
unpacks to 24.8 GB (HANDOFF/EPICS E138 s5, EPICS.md:13846) and would be refused by that bound (UNVERIFIED that s5 intends
this route, but the bound is literal).

Measured on F3 (live, E138 s1): of 15 cubes the exporter refused 13: 7 at a start time SEG-Y cannot hold exactly, 3 with
non-finite samples, 2 with two components, 1 crash `TypeError: unable to access 3D geometry information`
(HANDOFF.md:56). The crash is the F3 main-cube path (E138 s1 strategy:378, HANDOFF.md:58 "a real defect for the next
exporter-touching lane"; no merged fix found on main, UNVERIFIED).

Tests: unit `ophiolite-opendtect/tests/test_export.py`, `test_export_lines.py`, `test_export_faults.py`,
`test_starter_kinds.py`; SDK `ophiolite-sdk/tests/gateway/test_starter_kinds.py`, `test_roundtrip_journey.py` (synthetic
journey, hosted CI). Live: E129 sa/sb/sc validation records `docs/program-2026-09-25/e129sa-VALIDATION.md`,
`e129sb-VALIDATION.md`, `E129-sc-starter-pack-VALIDATION.md`; E138 s1/s2 VRs in their strategies.

## 3. Intake into the workspace

Entry path: the pack command lands each derived file through the upload API (E85/E54): `starter.py` `build` docstring
(`ophiolite-sdk/ophiolite/starter.py:11-12`), file -> profile table `starter.py:371`.

- Request ceiling: `OPHIOLITE_MAX_UPLOAD_BYTES` default 8 MiB, max 32 MiB (`G/payload_store.py:55-56`); a response/whole-read
  bound `WHOLE = 32 MiB` (`G/payload_store.py:63`, `G/limits.py:16` `RESULT_BYTES`).
- Larger files: resumable parts, verify, finish job, then publish (`G/upload_sessions.py:1-22`). `file_bytes` (inherits
  `upload_bytes` = 8 MiB unless configured), configurable up to `FILE_MAX` 64 GiB (`G/limits.py:17, 29`); packaged example 4 GiB
  (E54 strategy:39, 375). Other defaults: `retained_bytes` 512 MiB, `upload_total_bytes` 128 MiB, `concurrent_uploads` 2,
  `finish_jobs` 1 (`G/limits.py:30-33`).
- Only `segy/1` and `points-csv/1` are RANGED (`G/upload_sessions.py:44`); everything else is read whole up to
  `WHOLE_READ = 2 x RESULT_BYTES` = 64 MiB (`G/upload_sessions.py:` `WHOLE_READ` line, UNVERIFIED line number).
  `segy-line/1` has a "gate" test for a whole read over the bound (`G/tests/test_large_seismic_line.py:262`) and E139 s4 now
  lets a line above 32 MiB describe and read by ranges (PROGRAM.md:1761).
- SEG-Y reader: full inline x crossline grid, formats 1/5, big-endian, no extended text header, anything else refused
  (`ophiolite-connectors/src/asset_connectors/segy.py:7-8`); `max_traces` 1,000,000, `max_samples` 20,000
  (`segy.py:22`, `G/limits.py:44-45`). F3 has ~619k traces (inferred from 619,101-node horizon; UNVERIFIED).
- 2D line: `segy-line/1`, at most 200,000 traces, 1,024 traces per chunk (`asset_connectors/segy_line.py:24`).
- Horizons: `horizon_nodes` default 1,000,000, max 4,000,000 (`G/limits.py:22, 46`); above 100,000 nodes stored as
  `point-columns/1` (f64 columns), refusal by number above the bound (PROGRAM.md:1761).
- Faults: reader caps 20,000 sticks / 200,000 points (`asset_connectors/faults.py:11`); mesh 200,000 vertices
  (`asset_connectors/typed_reader.py:30`).
- Disk precondition: free space >= 2.5 x `file_bytes` (`G/limits.py:25, 76`).

How a multi-GB cube could enter: only as SEG-Y through upload sessions with `OPHIOLITE_MAX_FILE_BYTES` raised.
Real evidence of size: largest real volume qualified is Q13a, 2.77 GB, with interrupt/resume, S3 parity, and a gateway peak
under 256 MiB above idle (HANDOFF.md:1901; E54 strategy:383). Nothing near 21.9 GB has run (see Missing pieces 1).

Workspace item types (the "type registry"): Workspace `TypedKind` list `W/typed/model.ts:7`: well-tops, trajectory,
regular-grid-surface, triangulated-surface, point-set, polyline-set, seismic-volume, wavelet, model-section,
seismic-section, time-depth, feature-set, table; profile->kind map `W/typed/model.ts:8-17`. Gateway/SDK also have
`seismic-line`, `well-location`, `well-path`, `well-residual`, `well-set` (`ophiolite-sdk/ophiolite/typed.py:652-660`).
A 2D line type exists (`seismic-line`, profile `segy-line/1`, scientific profile `seismic-line-source/1`:
`ophiolite-platform/contracts/connectors/v1/contract.json:22`), but it is not in `TYPED_PROFILES`.
There is no grid-surface-from-OpendTect path: a 3D horizon lands as a point set, not as `regular-grid-surface`.
No `scalar-map` or `fault` type distinct from `polyline-set`.

Tests: `G/tests/test_upload_sessions.py`, `test_range_reads.py`, `test_large_seismic_line.py`, `test_seismic_line_upload.py`,
`test_horizon_intake.py`, `test_horizon_limit_routes.py`, `test_horizon_paging.py`, `test_point_columns.py`,
`test_seismic.py`; journey `ophiolite-sdk/tests/gateway/test_roundtrip_journey.py`.

## 4. Management in the workspace

- Dataset page per item: `W/dataset/DatasetPage.tsx` (summary, panel, technical details, checks), typed inspector
  `W/typed/TypedAssetInspector.tsx`; "how this file landed" fidelity note shown from the context (`TypedAssetInspector.tsx:210`).
- Provenance (E122, MERGED 28 Oct, PROGRAM.md E122 row): a source record per item; `application:opendtect` provenance
  carried by E125 sends (PROGRAM.md:1747).
- Fidelity record (E127 MERGED; E129 writes `fidelity/1` per pack, `starter.py:485`): a document next to the pack, not a
  Workspace screen (only the one-sentence decision note above is shown, UNVERIFIED that no richer screen exists).
- Groups: `W/components/Groups.tsx:8-16` "a personal, named set of datasets in a project. It copies nothing." Manual only.
- The 8 Oct "Data page as tree + view + panel" (memory entry): NOT on main. `grep -i "data tree"` over PROGRAM.md, EPICS.md and
  `W/` finds nothing; there is no `DataTree` component and no program row. A 2D survey of 286 datasets lands as 286+ flat items.
- Companions: used for tables (`TypedAssetInspector.tsx:194-195`); no companion relation between a cube and its horizons/faults/wells.

## 5. Viewing in the workspace (ophiolite-workspace app + `@ophiolite/charts`)

Route: dataset page -> `TypedAssetInspector.tsx:218-230` switch on kind.

| Kind | Viewer | Notes |
|---|---|---|
| seismic-volume | `SeismicView` (`:143`), `SectionCanvas`, slice GET `/slices/{axis}/{label}` (`W/typed/model.ts:130-133`) | inline / crossline / time-sample slice, grey scale, one at a time, checksum verified; no overlay, no 3D |
| seismic-line | none | `NO_VIEW` includes `segy-line/1`, comment "E137 s0: the 2D seismic line has no Workspace view yet" (`W/../tests/story-address.mjs:38`); no `seismic-line` in `TYPED_PROFILES` |
| point-set (3D horizon) | `PointView` (`:98`) PlanCanvas single colour + first 500 rows (`:101-103`) | needs `data.points` whole; `point-columns` appears in the app only as generated TypeScript types (`contracts/ophiolite-contracts.ts:563, 1242`); E139 says "Not a screen" (EPICS.md:13881) |
| polyline-set (fault sticks) | `FaultView` (`:106`) plan view, arrow-key stick readout | x,y only; z in text |
| well logs | log tracks via `@ophiolite/charts` (`packages/charts/src/kinds/logtracks`), `W/charts/curveRead.ts`, windows endpoint | yes |
| well tops | `TopsView` (`:45`), `TopsOverlay`, correlation | nothing to show: no OpendTect tops writer |
| time-depth | `TimeDepthView` | no OpendTect writer on main |
| well path (`well-path-positions-csv/1`) | `NO_VIEW` too (`story-address.mjs:38`) | native well page may show the path: UNVERIFIED |
| Project map | `W/MapPage.tsx`: wells + OGC collections as layers, "up to 2,000 features" per layer (`:171-183`) | collections `wells, tops, wellbore-paths, point-sets, lines, feature-points` (`G/layers.py:36-61`, features.py:355-360) -> a 619k-node horizon draws at most 2,000 nodes |

Eight kinds, plainly: NO viewer: **2D seismic lines, 2D horizons (not even landed), picksets (not even readable)**;
partial: 3D horizon above 100,000 nodes; wells' path (unverified). Cube, faults, logs have viewers.

## 6. Evidence of real runs

- E125 (MERGED 22 Oct): journey headless in CI on Linux against the pinned free OpendTect and the F3 survey
  (PROGRAM.md:1747); F3 fixture JSON at `ophiolite-opendtect/tests/fixtures/f3/`.
- E129 a-f: F3 cube + horizons into OpendTect (horizons above 100,000 nodes not landed then, PROGRAM.md:1751); ResInsight
  read-back live A8 0 differences over 888 values; logs onto wells live A8 0 differences (PROGRAM.md:1751).
- E138 s1 (MERGED 1 Nov), live F3 Demo 2023: 3 min 52 s, peak 710 MB, 86 identities, 227 rows (140 within/equal, 36 not-yet,
  26 failed, 16 disagree, 8 unsupported, 1 absent), 42 findings (E138 s1 strategy:378).
  All eight F3 horizons hold 303,622-619,101 nodes, which were `not-yet` until E139 s2 (HANDOFF.md:~110; EPICS.md E138 slice 1).
- E138 s2 (MERGED 1 Nov), "second survey": 17 identities, 76 rows, 14 lines within, 3 lines failed (413/409 at 32 MiB, since
  fixed by E139 s4), 61,281 traces (E138 s2 strategy:80-82, 261-266). EPICS.md:13843 names this slice "USGS Central
  Alaska's 2D lines go round" with "seventeen 2D lines, no wells"; the VR keeps the dataset anonymous by design. So **a
  TerraNubis dataset (USGS Central Alaska 2023) HAS been run live, 2D lines only** (the premise "none yet" is wrong for
  that one). E137 s1 also ran "live USGS + F3 Demo 2023" (EPICS.md:13781). MNSH, Rockall Trough, Poseidon: no live run yet
  (E138 s3 strategy closed, coding; s4/s5 wait on deposits/E137 s3).
- Every journey judges numbers via the Python SDK, ResInsight and QGIS (`conformance/roundtrip/`). None drives the Workspace
  web UI. So "viewed in the workspace" has no real-data evidence for any kind (the viewer specs use synthetic fixtures:
  `ophiolite-workspace/app/tests/`, `web/tests/`).
- The 699 MB SEG-Y is F3 (E54 strategy:93, 699,003,060 B); the 21.9 GB cube is Poseidon `.cbvs`, 21,913,026,169 bytes,
  trace count unverified (HANDOFF.md:175; EPICS.md:13846). 286 2D line datasets / 5 2D horizons / 18 FaultStickSets / 98 wells
  is MNSH (EPICS.md:13786).

## 7. Epic status (docs/program-2026-09-25/PROGRAM.md, status word of each row)

| Epic | Row | Status word | State below row |
|---|---|---|---|
| E125 | :1747 | MERGED (22 Oct) | |
| E129 | :1751 | MERGED | slices a-f MERGED 28-30 Oct |
| E137 | :1759 | IMPLEMENTING (Kernel) | s0, s1, s2 MERGED; s3 time-depth in lane e137s3 (G1 green); s4 tops, s5 handoff, s6 2D horizons chartered, not started (EPICS.md:13782-13786) |
| E138 | :1760 | IMPLEMENTING (Kernel) | s0, s1, s2 MERGED; s3 MNSH strategy closed, coding; s4 Rockall, s5 Poseidon, s6 summary open (EPICS.md:13843-13848) |
| E139 | :1761 | IMPLEMENTING (Kernel) | s0, s1, s2, s4 MERGED; s3 (E15 measurement) waits on a release |

None is QUEUED or CLAIM in PROGRAM.md. (EPICS.md:13877 still says "QUEUED" in the E139 heading: stale text, PROGRAM wins.)

## 8. Retrieval by consuming applications (Python SDK, third-party HTTP, QGIS/ResInsight/OpendTect)

Surfaces: Python SDK `ophiolite-sdk/ophiolite/client.py`; public HTTP API with an OpenAPI 3 spec
`ophiolite-platform/contracts/openapi/v1/openapi.json` (453 paths, info 1.0.0-pilot); bearer auth `oph_api_...` project
delegate lasting at most five minutes, `oph_agent_...`, or provider token + application grant; browser cookie for the app
(openapi `securitySchemes`, `info.description`). The description says verbatim "Not a stable SDK or unattended
service-account contract". Access keys / service accounts E25 MERGED (PROGRAM E25 row); application registration/credential
repair E51a (PROGRAM E51 row, IMPLEMENTING: status word as of 1 Oct; may be stale, UNVERIFIED now). Check/get/send:
`ophiolite-sdk/ophiolite/exchange.py` (E70a); QGIS plugin `ophiolite-connectors/scalar_maps/qgis_plugin/`; OGC API Features
service (E29/E65: `G/features.py`, `G/layers.py`, max 100 per page `features.py:` `MAX_LIMIT`).

HTTP endpoints that return item data (`G/app.py:1682-1710`): describe `.../revisions/{r}`; representation bytes
`.../representations/{id}` (whole up to 32 MiB; above that Range-only, 206 with `Content-Range`, `X-Content-SHA256`:
`G/adapters.py:979-1002`); `/slices/{axis}/{label}` (seismic volumes); `/windows` (curves, point columns; cursor paging);
`/export?format=parquet|csv|geoparquet` (tables, tops, trajectories, points, LAS; not volumes); `/provenance`; OGC Features
items.

| Kind | External retrieval today | Operation | Format / limit | Proof |
|---|---|---|---|---|
| 3D cube | partial | `Client.read_slice` (`client.py:466`; 1-64 slices, `export_slices`), `download_original` by 8 MiB ranges (`client.py:975`) | slices as arrays (32 MiB per answer); original SEG-Y whole by ranges; `exchange.get` REFUSES volumes (`exchange.py:678`: "a seismic volume is described here, not received") | E16/E54 tests `G/tests/test_seismic.py`, `test_range_reads.py`; no >2.77 GB run |
| 2D line | partial | `read_data` -> `SeismicLine` geometry + decisions (`typed.py:305-312`); samples only via the original by ranges (`download_original`) | no sample-window API; whole-read 32 MiB bound lifted for describe by E139 s4 | E138 s2 live (14/17 then fix); `exchange.get line` into OpendTect (`O/exchange.py:19-24`) |
| 3D horizon | yes | `read_data` (>100k nodes by ranges, PROGRAM E139 s2), `export_file` parquet/csv/geoparquet (`client.py`), OGC `point-sets` | f64 point-columns above 100,000 nodes; QGIS paging with composite cursor | E139 s2 live: SDK, pack, OpendTect, QGIS 4.2.2 read a 1,000,000-node horizon (PROGRAM:1761) |
| 2D horizon | no | none | not landed | none |
| Faults | yes | `read_data` -> `PolylineSet`; OGC `lines` collection | 20,000 sticks / 200,000 points | `G/tests`, E138 s1 faults after E137 s2 |
| Wells logs/path | yes | `Client.read` curves (`client.py:391`), windows for >100k rows | LAS rows <= 1,000,000 default | E100a/b tests; E129 f live |
| Tops / time-depth | yes if present | `read_data` -> `WellTops` / `TimeDepth`; OGC `tops` | none from OpendTect today | n/a for OpendTect data |
| Picksets | no | none | none | none |

Missing for a 21.9 GB cube: server-side sub-volume/trace-range read (only whole-slice or whole-file ranges); a documented
long-download credential story (five-minute delegates, UNVERIFIED how `download_original` refreshes); format negotiation (only
SEG-Y float32 original is retrievable, no ZGY/CBVS; ZGY is `ophiolite-sdk/ophiolite/zgy.py`, scope UNVERIFIED);
streaming without full disk copy. For a 286-line survey: no list/bulk API by dataset (286 independent items, each
`download_original`; `read_many` is for curves, `client.py:502`), and no per-dataset grouping to enumerate them.

## Missing pieces

1. **Cube of 21.9 GB cannot enter.** Chain: stages 2-3. (a) `starter export` refuses archives > 8 GiB uncompressed
   (`starter_archive.py:46`; Poseidon unpacks to 24.8 GB); (b) the exporter writes IEEE float32 SEG-Y (`export.py:148-175`),
   so an 8-bit cube grows about 4x to ~88 GB (UNVERIFIED arithmetic: trace count unknown) which exceeds `FILE_MAX` 64 GiB
   (`limits.py:17`); (c) `file_bytes` default is 8 MiB until configured; `max_traces` 1,000,000; 2.5x disk factor;
   (d) never exercised above 2.77 GB. Epic: uncovered (E138 s5 would expose it as a finding, not fix it: EPICS.md:13930-style
   "findings, not repairs"). Blocks: managed (and therefore viewed).
2. **Exporter refuses most F3 cubes and crashes on the main one**: 13 of 15 refused, including a TypeError on 3D geometry
   (HANDOFF.md:56-58); start-time/step limits (`export.py:156-159`) are SEG-Y header limits, stay "documented". Epic:
   crash assigned loosely to E137 s2/s3 (HANDOFF.md:58), no merged fix found; refusals uncovered. Blocks: managed.
3. **Survey preconditions**: only TWT ms, metres, SRD 0, single-component cubes, finite samples (`export.py:127-136, 153, 173, 442`);
   depth cubes and attribute volumes with undefined samples are refused. Epic: uncovered (named velocity decision, `DEPTH`
   message). Blocks: managed.
4. **Picksets have no path at all**: no odbind class, no catalogue kind, no profile, no type, no viewer. Epic: uncovered
   (OSD R-44.6 omission rows only, HANDOFF.md:175 area). Blocks: both.
5. **2D horizons**: listed by the read CLI only (`read.py:37`); no writer, profile, type or viewer. Epic: E137 s6 (chartered,
   not started, EPICS.md:13786). Blocks: both.
6. **Well markers (tops)**: no pack profile and no writer (`starter_kinds.py:18`; refused `test_starter_kinds.py:205`).
   Epic: E137 s4 (chartered). Blocks: both (viewer exists).
7. **Time-depth models**: no writer on main. Epic: E137 s3 (in lane). 3 of 10 Poseidon wells have only OpendTect-internal models
   and are refused by name (D85, HANDOFF.md:175 area; "nothing decodes OpendTect's well files"). Blocks: managed.
8. **No 2D line viewer** in the Workspace (`story-address.mjs:38`; absent from `model.ts:8-17`). Epic: uncovered (E137
   Out/E126b do not name one: UNVERIFIED). Blocks: viewed.
9. **No viewer for horizons above 100,000 nodes**: `PointView` needs whole `data.points` and shows 500 rows (`TypedAssetInspector.tsx:98-105`);
   point-columns are only TS types; the map layer caps at 2,000 features (`MapPage.tsx:171`). E139 states "Not a screen"
   (EPICS.md:13881). Epic: uncovered. Blocks: viewed. Horizons also draw as single-colour dots, not a coloured surface/grid.
10. **Seismic viewing is single-slice only**: no horizon/fault/well overlay on a section, no time-slice map beyond a sample
    slice, no 3D (`TypedAssetInspector.tsx:143-168`). Epic: uncovered. Blocks: viewed (usable interpretation view).
11. **Managing 286 lines / 98 wells / 18 fault sets**: no dataset-level grouping type, no tree (8 Oct data-tree work is not on main;
    Groups are personal and manual, `Groups.tsx:8`). Companion relations between cube, horizons, faults and wells do not exist.
    Epic: uncovered. Blocks: managed (at survey scale). One survey is not an addressable unit in the workspace.
12. **Survey-level provenance**: items carry E122 provenance and an E129 `fidelity/1` document, but no Workspace screen shows
    which OpendTect survey/CRS/Z-domain a set of items came from together (UNVERIFIED beyond the single-item note). Epic: partly
    E122/E127; screen uncovered. Blocks: managed (explainability).
13. **No Workspace-UI validation on real data**: every real-data journey (E129, E138) judges SDK/QGIS/ResInsight read-back;
    none loads the web app. Epic: uncovered. Blocks: viewed (unproven).
14. **MNSH, Rockall, Poseidon never run live**; only F3 Demo and USGS Central Alaska (lines) have. Epic: E138 s3-s5 (in
    progress / waiting). Blocks: both (unproven for those kinds and sizes, e.g. 286-dataset lines, 18 fault sets).
15. **External retrieval of a cube is whole-slice or whole-file only**: no sub-volume/trace-range endpoint; `exchange.get`
    refuses volumes (`exchange.py:678`); 2D-line samples only through the original (`typed.py:305`). Epic: uncovered. Blocks: neither
    managed nor viewed; blocks the owner's stage-8 retrieval requirement.
16. **Public API is explicitly not a stable unattended contract**; delegates last <= 5 minutes (`openapi.json` info). Streaming a
    multi-hour 21.9 GB download needs a refresh story (UNVERIFIED in SDK). Epic: E25/E51 cover keys and service accounts; the
    API-stability promise is uncovered. Blocks: retrieval only.
17. **Horizon attributes and Fault3D surfaces are not carried** (only `x,y,z,inline,crossline`; sticks only): documented
    fidelity losses, no epic widening them. Blocks: managed completeness (neither if scope is accepted).

Count: 17 pieces. Uncovered by any epic: 1 (partly), 3, 4, 8, 9, 10, 11, 12 (screen), 13, 15, 16 (stability), 17.
