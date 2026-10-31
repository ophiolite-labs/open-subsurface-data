# Interoperability gap assessment: five TerraNubis OpendTect archives (31 Oct 2026)

Read-only evidence for the owner question "limitations, epics to charter, tests to add, formats not supported".
Nothing here is decided; "unverified" marks what no cited source states. Two archives of five are listed
(F3, USGS); MNSH, Rockall Trough and Poseidon are only known by the E44 table (still copying).

## Sources and shorthand

- OSD = /home/epic/src/open-subsurface-data. F3L = OSD docs/program/evidence/e44/f3-demo-2023-listing.txt (280 lines,
  275 files, 8,131,181,824 bytes, last line). USL = same folder, usgs-central-alaska-2023-listing.txt (79 lines, 74 files).
  E44 = OSD docs/program/charters/E44-packs-after-the-proof.md. OSDH = OSD docs/program/HANDOFF.md.
- AB = /home/epic/src/arraybridge **read at origin/main** (the working checkout is on feature/workspace-onboarding, so
  all AB lines below are `git show origin/main:<path>` line numbers). EPICS = AB docs/program-2026-09-25/EPICS.md.
  MX = AB ophiolite-opendtect/src/ophiolite_opendtect/data/matrix.json (E125 capability matrix; the odbind matrix the
  E129 charter cites, EPICS:12522). VAL = AB docs/program-2026-09-25/E129-sc-starter-pack-VALIDATION.md.
  SC/SD/SF = AB docs/program-2026-09-25/E129-{sc,sd,sf}-starter-pack-COMMIT-STRATEGY.md.
  PROF = AB ophiolite-platform/contracts/profiles/v1/. REG = AB ophiolite-connectors/src/asset_connectors/readers/registry.json.
  CAPQ / CAPR = AB ophiolite-connectors/src/asset_connectors/capabilities/{qgis,resinsight}.json.
- ODB = /home/epic/OpendTect/7.0.0/bin/python/odbind (installed odbind on this host; classes at ODB/*.py: Fault3D,
  FaultStickSet, Geom2D, Horizon2D, Horizon3D, Seismic2D, Seismic3D, Survey, Well; `grep "^class "`).
- File-extension roles (.wlt, .csmdl, .tie, .pck, .rdl, .wvlt, .flt, .sgd ...) are OpendTect convention. Neither repository
  states them (git grep over AB docs/connectors/SDK and grep over OSD docs found nothing), so they are marked "inferred".

## A. Matrix: object type x tool

Columns: **odbind headless read** (ODB class / MX row) | **Ophiolite data type** | **writer** (OD = OpendTect,
RI = ResInsight, QG = QGIS, Py = Python) | **tests** | **gap**. "none" is a finding, not a guess: it means the cited
search found nothing.

| # | Object (archive evidence) | odbind read | Ophiolite type | Writers | Tests | Gap |
|---|---|---|---|---|---|---|
| 1 | 3D cube, .cbvs (F3L:40-70 incl. `1_Original_Seismics.cbvs` 568 MB; Poseidon per E44:21) | yes, `Seismic3D` (ODB seismic3d.py; export uses it, AB ophiolite-opendtect/README "E129 slice (b)"); MX cube get supported (MX:122-146) | `seismic-volume` via `segy/1` (REG:621; PROF segy.json, seismic-volume.json) | OD: cube get (MX:122, EPICS:12607 "cube route"); export as SEG-Y; Py: pack notebook (EPICS:12618); RI: **no** (rips has no SEG-Y/seismic, SD:90, EPICS:12512); QG: **none** (CAPQ routes list has no seismic) | ophiolite-opendtect/tests/test_cube_get.py, test_export.py, test_export_live.py; ophiolite-sdk/tests/gateway/test_starter_export.py; ophiolite-connectors/tests/test_segy.py | Only time-domain, single-component cubes: `DEPTH` (export.py:39,260) and `COMPONENTS` (export.py:43,113) refuse the rest. SEG-Y scan caps 1,000,000 traces, 20,000 samples (segy.py:22) and demands a full inline x crossline grid (segy.py:186-189). Poseidon size/domain unverified. |
| 2 | Attribute and derived cubes (F3L:40-70: Similarity, Chimney, AI, Porosity, Gamma, Steering PCA/FFT, 1.1 GB `3a_Steering_PCA111_MF225.cbvs`; `.par` per cube, `.proc` F3L:47) | yes as row 1 | as row 1 (quantity/unit of an attribute is not a field of `segy/1`: unverified) | as row 1 | none specific | Steering cubes are about twice the size of the original (1.12 GB vs 568 MB, F3L) which suggests two components: inferred only; would hit `COMPONENTS`. Attribute definitions (`Attribs/*.attr`, F3L:273-278) have no odbind class: not translatable. |
| 3 | 2D seismic lines: `.cbvs` under Seismics/Seis (USL:37-53, 17 lines) and Seismics/Seismic (F3L:57-66, 10 lines) plus `Geometry/*.geom` (USL:59-77; F3L:6-17) | yes, `Seismic2D.line_info/getdata/putdata`, `Geom2D` (ODB seismic2d.py:102,120,258; EPICS:13764). 7.0.10 behaviour **not measured** (EPICS:13764). MX has **no 2D row**. | **none** (EPICS:13763: no profile, no registry kind; `segy/1` refuses non-grid traces; E53 excluded 2D SEG-Y, EPICS:5296) | none; E137 slice 1 plans it (EPICS:13778-13783) | none; fakes lack `seismic2d.py` (EPICS:13776) | Real, chartered (E137). **F3 also holds 2D lines** but E44:17 lists F3 as seismic-3d only (see G6). |
| 4 | Horizon 3D, `.hor` (F3L:98-129, 8 files; `.hov` and `.ts` companions) | yes `Horizon3D` (ODB horizon3d.py:84-140); MX horizon get/send supported (MX:71-106) | `point-set` via `points-csv/1` (REG:471; export.py docstring) | OD: horizon get (MX:71); QG: `points-csv/1`, `opendtect-horizon-ascii/1` read (CAPQ); Py: pack notebook; RI: none | test_horizon_get.py, test_horizon_send.py, test_horizons.py, test_opendtect_horizon.py | **100,000-point intake limit**: F3 horizons are 619,101 nodes, refused by `points-csv/1` ("more than 100000 points", SC:59, VAL:4); pack records a `failed` fidelity row, OD import places them anyway (SC:59, :239-241); OSD ruled in H6 (OSDH:24); F3 stays L3 while a horizon is failed. "Capacity is a later named Kernel lane": **not chartered** (grep EPICS for it: no epic). Depth horizons `not_placed` (VAL:10). Z stored on 65,534 steps (MX:82). |
| 5 | Horizon 2D (MNSH/Rockall "horizons" with seismic-2d only, E44:18-19) | yes `Horizon2D.getz/getxy/get_xarray` (ODB horizon2d.py:64-96); **no writer** in odbind, **no MX row** | **none** found (no 2D horizon profile in PROF listing) | none | none | E137 "Out" excludes 2D horizons (EPICS:13805). Whether MNSH/Rockall horizons are 2D: **unverified** (archives not listed). If so, R-44.1 ("a kind no writer handles is a defect", E44:25-28) is unmet by E137. |
| 6 | Wells: `.well` (F3L:153,193), tracks | yes `Well.track` (ODB well.py:111); MX well send supported (MX:14-33) | `trajectory` / `well-path` (PROF well-path.json, well-path-positions-csv.json; REG:194) | OD: **well get refused** (MX:8-13); well must be GUI-imported (SF:142); RI: `.dev` + rips (resinsight_starter.py); QG: `well-location/1`, `deviation-csv/1` read (CAPQ); Py: yes | test_well_send.py, test_heads.py, test_starter_import*.py; ophiolite-connectors/tests/test_resinsight_starter.py | No headless well create (VAL:9). E44:17 lists `wellbore-headers` for F3 but E129 `KINDS` holds four kinds only (EPICS:13760) and E137 does not add it (G7). |
| 7 | Well logs `.wll` (F3: 44 files, F3L:166-243; `Rawdata/Well_data/F02-01_logs.las` F3L:259) | yes `Well.logs/log_info` (ODB well.py:41,143); MX log get/send supported (MX:34-70) | `well-curve`/`las2/1` (PROF) | OD: log get onto an *existing* same-name well, GR/API/MD-KB only (MX:38-52; README); RI: LAS import via rips (SF); QG: none for curves (CAPQ lists no curve route); Py: yes | test_starter_logs_live.py, test_gr_patch.py; sdk tests/gateway/test_starter_opendtect_logs.py, test_starter_resinsight.py | Log get proven for the profile in MX:38-52 only ("outside_profile": "format not supported yet"). |
| 8 | Well markers/tops `.wlm` (F3L:168-215, 4 files; `Rawdata/Well_data/F02-01_markers.txt` F3L:258) | yes `Well.marker_names/marker_info` (ODB well.py:37,76) | `well-tops`, `well-tops-csv/1`, `petrel-well-tops/1` (PROF) | **no pack writer** (`KINDS` lacks tops, EPICS:13760); QG reads `well-tops-csv/1` (CAPQ); OD/RI none | ophiolite-connectors tests exist for tops readers only (E123 s1g strategy); none for OpendTect marker export | G7: `tops` is in OSD's kind enum (OSD schema/starter.schema.json:151) but in neither E44's table nor any E129/E137 slice. |
| 9 | Time-depth models: `.wlt` (F3L:183-209, 120-190 KB), `.csmdl` (F3L:154-221), `.tie` (F3L:181-218); Poseidon per E44:21 | **no**: odbind `well.py` has `tvd/tvdss` only, `grep d2t/t2d/checkshot` finds nothing (EPICS:13766; ODB well.py:240-246); MX:23 "no time-depth model is sent" | `time-depth`, `time-depth-csv/1` (PROF; time_depth.py:4 strict increase in depth and time, MAX_PAIRS 100,000 :16) | none; E137 slice 3 plans a standard-file route only (EPICS:13774, 13782) | test_time_depth.py (connectors, sdk gateway), test_time_depth_contract.py: reader only | D85: a model only inside OpendTect well files is refused by name (EPICS:13801). **F3 has them too** but also a standard file `Rawdata/Well_data/F02-01_DT_TVDSS.txt` (F3L:263), one well of four. |
| 10 | Fault sticks / faults: `Surfaces/Fault_A.flt` (F3L:119; inferred Fault3D), `Rawdata/Faults/FaultA.txt` (F3L:247); OGA per E44:18-19 | yes read-only: `FaultStickSet.getstick` (ODB faultstickset.py:49), `Fault3D.getstick` (ODB fault3d.py:50); MX fault get refused, fault send refused/unproven (MX:107-120: no create/put, no batch importer) | `polyline-set`, `opendtect-faultsticks/1` (PROF; grandfathered without real fixture, EPICS:13762) | OD: **none** (stated GUI import step, EPICS:13773); QG: `opendtect-faultsticks/1`, `petrel-faultsticks/1` read (CAPQ); RI/Py: Py reads file | test_faults.py (connectors); ophiolite-connectors/tests/test_resqml_surfaces.py:195 | E137 slice 2 reads `FaultStickSet` only (EPICS:13773) and excludes "Fault3D surfaces" (EPICS:13805) although `Fault3D.getstick` exists (ODB fault3d.py:50) and F3's own fault object looks like a Fault3D (G4). Readers refuse one-point sticks (faults.py:34 `>= 2 points`). |
| 11 | Pickset/locations `.pck` (F3L:140-144; `RMS_velocities.pck` 174 MB) | **no** class in ODB | `point-set` exists (REG:471) but no route from OpendTect | none | none | R-C1 forbids decoding. Not in E44. Only route: OpendTect export (unverified whether it fits headless). |
| 12 | Random line `.rdl` (F3L:146, 130 bytes) | **no** | none | none | none | Not in E44. OpendTect-only. |
| 13 | Wavelet `.wvlt` (F3L:75) | **no** | `wavelet`, `wavelet-text/1` (PROF; REG:872) | none | reader tests only | No odbind route; Ophiolite type exists. |
| 14 | Models `.sgd` (12, F3L:22-36), `.sfw`, `.stratlevels` (F3L:25,35) | **no** | none (`model-section`, `seismic-section` exist for computed wedge sections, E53) | none | none | OpendTect-native synthetic models; relation to `model-section` unverified. |
| 15 | HorizonCube `.3dhc/.hcs/.hci`, `.sti`, body `.body` (F3L:101-137, 109; 475 MB + 160 MB) | **no** | none | none | none | dGB-native; not in E44 table. |
| 16 | Shapefiles (F3: 4 shapefiles, 20 files, names with spaces, F3L:223-245); `2DLines.geojson` (USL:15) | n/a (standard files, not odbind) | `esri-shapefile/1`, `geojson/1` (PROF) | QG: read, partly-qualified (CAPQ) | registry readers tests; no archive-shaped test | Space in file names; `.disp` OpendTect side files; registry cap `companions_per_group` 8 (REG limits). Not in E44 table. |
| 17 | KML survey boundary `SurveyBoudaryFor_USGS_Central_Alaska.kml` (USL:32) | n/a | **none** (git grep -i kml over contracts, connectors, SDK: no match) | none | none | Outline already comes from record outlines (OSDH:25); KML itself needs no kind unless it must be imported. |
| 18 | Raw standard files `Rawdata/` (F3L:246-264: SEG-Y 699 MB, 7 horizon txt 137 MB, faults, wells, `Velocity_functions.txt`, `All_wells_RawData.zip`) | n/a | `segy/1`, `points-csv/1`, `las2/1` ... exist | direct intake possible | n/a | R-44.4 says oracle is odbind (E44:44-46); whether Rawdata/ may serve as a second, odbind-free input is **undecided** (Q-E4). |
| 19 | Velocity model cubes `Velocity_model__RMS_/INT_.cbvs` (F3L:84, 1.78 MB each) | yes as cube | `seismic-volume`; "velocity-model" is an OSD kind (schema/record.schema.json:67) with no Ophiolite kind | as row 1 | none | E137 Out excludes interval velocity (EPICS:13805). |
| 20 | Neural nets, `NLAs/` | n/a: folder holds only `.omf` in F3 (F3L) and USGS (USL:21-22) | none | none | none | Nothing to translate in these two archives; others unknown (Q-E1). |
| 21 | Survey definition `.survey`, `.defs`, `survey.log` (F3L:269; USL:33) | `Survey.info/inlrange/zrange` (ODB survey.py:85-103,177) | none needed | export.py:91-94 reads `.defs` and `.survey` text directly | none for a 2D-only survey | 2D-only survey (USGS has Geometry/ but no `Seismic3D` listing, USL) through `survey.grid()` (survey.py:77 `inlrange`): **unverified** whether it opens; also see Q-E3. |

Coverage by tool for the chain OpendTect -> Ophiolite -> {ResInsight, QGIS, Python}:
RI receives only wells and logs, never cube/horizon/fault/tops (SD:90; CAPR lists one route, scalar-map read, and
"unsupported: writing into ResInsight"). QG shows horizons-as-points, fault sticks, wells, paths, tops, shapefile/GeoJSON
(CAPQ), not seismic. Py reads everything the pack writes. No single test walks an archive through all three:
the nearest are the per-target starter tests above and `tools/interop/opendtect_exchange.py`,
`qgis_journey_inside.py` (contents not read: unverified that they use archive-shaped data).

## B. Limitations already known (cited)

1. No headless OpendTect survey or usable well creation on 7.0.10: odbind has no Survey create; `od_process_segyio`,
   `od_DBMan --create`, `od_WellMan` all fail (VAL:9; SC:86; MX:8-13). Consequence for the interop journey: the archive's own
   survey is the only OpendTect side that can exist headless; any "Ophiolite -> OpendTect" leg needs a GUI-created survey and
   GUI well import (SF:142).
2. Rips (ResInsight) has no seismic API and exposes no original well-path stations, only a 1 m resampled trajectory
   (SD:90, :148; EPICS:12512 amendment). ResInsight target = wells and logs only; cube is `false`.
3. Intake point limit 100,000 (`points-csv/1`; SC:59; horizons.py:25 `LIMIT`): F3 horizons (619,101 nodes) are `failed`
   rows. Other limits: faults 200,000 points / 20,000 sticks (faults.py:11), time-depth 100,000 pairs (time_depth.py:16),
   SEG-Y 1,000,000 traces (segy.py:22), upload default 8 MiB, ceiling 32 MiB per direct request
   (ophiolite-platform/services/project_gateway/payload_store.py:51-52; how a 699 MB SEG-Y travels: unverified here, E54 reads by ranges, :59).
4. Cube exchange covers single-component time cubes on the survey's own sampling (export.py:39,43; MX:127-131; "outside_profile" MX:145).
   `exchange.send` accepts `well` and `horizon` only (exchange.py:94-96): there is no cube send; the cube leaves OpendTect via
   the E129 export, not the exchange.
5. Faults: odbind can only read sticks; fault get and send are refused (MX:107-120); `opendtect-faultsticks/1` has no real
   fixture (EPICS:13762); one-point sticks refused (EPICS:13765); declarations (CRS, vertical meaning) are absent from the ASCII (EPICS:13773).
6. Time-depth models live only inside OpendTect well files unless a standard file ships (EPICS:13766, D85 :13801); odbind has no
   model access; placement has no odbind route (one GUI step, EPICS:13774).
7. 2D data: no Ophiolite data type; the E125 connector has no 2D code (EPICS:13764); geometry collision risk `creategeom=True` (EPICS:13773); 7.0.10 behaviour of the 2D calls unmeasured.
8. Attribute volumes: pack carries any named cube, but multi-component and depth cubes are refused (export.py:39,43).
9. Shapefiles / random lines / picksets / wavelets / well ties / neural nets / bodies / models: no odbind class (ODB class list);
   R-C1 bars decoding (EPICS:12522; E44:41-43); OpendTect-native only. Wavelets and shapefiles have Ophiolite types, but no archive route.
10. Pack kinds are four: `KINDS = (seismic-3d, horizons, wellbore-paths, wellbore-logs)` (EPICS:13760); a kind without a writer is today silently dropped by `export.py:244` (EPICS:13761), closed in E137 slice 0.
11. Outline today only from cubes and wells (`starter_archive.outline`, EPICS:13772): a 2D-only pack has none.
12. The OSD kind enum (starter.schema.json:151-154; record.schema.json:62-65) contains kinds with no Ophiolite writer or type: tops, core, seismic-4d, surfaces, velocity-model, geological-model, reservoir-model ... Only the five E44 kinds are tracked for writers.

## C. Candidate epics (conservative: each cites a real, uncovered gap)

**C1. Round-trip interoperability journeys from the five archives (R-44.5).** *Supervisor note, 31 Oct, after drafting: chartered by the Ophiolite planner as E138 (E44 R-44.5); C1 is therefore closed and section D item 8 belongs to E138.* Program: Ophiolite (Integration surface, journeys); OSD
supplies deposits only. Kernel-proof, no surface work. Proves: arrow *OpendTect archive -> Ophiolite workspace -> ResInsight /
QGIS / Python*, per archive, with a read-back oracle per leg and the fidelity statement for what each target cannot hold.
Depends on: E137 slices (lines, faults, time-depth), E129 (merged), E125, E123; the OSD deposits (E41; still copying).
Not covered: E44:39-43 says "the Ophiolite planner charters the round-trip epic; number recorded when known" and no number exists
(grep over EPICS and OSDH 13-18: none); E137 is the *pack* path (EPICS:13757) and says out "anything about its licence ... readers
for other formats" (13805); E129 targets are the pack, not a workspace import of an archive's native objects. Slice 0 should
fix the journey list (below, section D) before any code.

**C2. Horizon capacity beyond 100,000 nodes (Kernel, Ophiolite).** Proves: an F3-sized horizon (619,101 nodes) lands as a real
Ophiolite item (not a `failed` row) and reaches QGIS/Python. Depends on: nothing new (E129 merged). Not covered: SC:59 and :241
defer it to "a later named Kernel lane"; no epic carries it (EPICS has no such charter, searched); OSD H6 only made the failure
non-blocking (OSDH:24); F3 therefore cannot pass L4 (canonical conversion needs every file converted, OSDH:24). This one is
**blocking OSD F3 above L3 with a cited ruling**, hence the strongest candidate. Alternatives to be weighed in the strategy: raise
`MAX_POINTS`, a grid-surface type (`grid-surface`, `scalar-map` exist in PROF) instead of points.

**C3. 2D horizons (Horizon2D) translation (Kernel, Ophiolite; E137 follow-on).** Proves: *OGA MNSH/Rockall horizons -> Ophiolite
data type -> OpendTect/QGIS*. Condition: only if the MNSH/Rockall listings show `Horizon2D` objects (Q-E1). Depends on E137 slice 0
(2D line identity). Not covered: E137 Out (EPICS:13805) says "2D horizons"; E44 R-44.1 lists "horizons" for both OGA sets (E44:18-19) and
odbind reads them (ODB horizon2d.py:64-96) but cannot write them.

**C4. Wells beyond logs and paths: markers/tops, headers (Kernel, Ophiolite; E129 follow-on).** Proves: a pack carries well tops
(`marker_info`) as `well-tops-csv/1` and each well's header. Depends on E137 slice 0 (catalogue of kinds, design 1). Not covered:
EPICS:13760 four-kind list, no slice in E137 adds `tops` or `wellbore-headers`; yet F3 holds 4 `.wlm` files (F3L:168-215),
E44:17 lists `wellbore-headers`, and OSD's enum has `tops` (starter.schema.json:151). Could instead be an E137 slice 5 (see D).

**C5. OpendTect-native objects with no odbind class: an explicit omission contract (Surface/Kernel mix, OSD and Ophiolite).** Proves: a
pack/inventory names, per archive, each native object that is not translated (pickset, random line, well tie, wavelet, body, HorizonCube,
model, attribute set, neural net) with a reason, so R-44.1's "never quietly omits" holds for kinds the E44 table never named.
Not covered: R-44.1 is stated over the page-derived kind list (E44:25-28); the listing shows at least a dozen further object types
(rows 11-15 of A). Smallest form is OSD-side (a `fidelity/1`-like skipped list, check whether `fidelity/1` `skipped` rows allow it:
unverified), not a new Ophiolite kind.

**Not proposed (not enough evidence):** a ResInsight seismic/horizon/fault route (rips lacks the API, SD:90, a tool limit not an
Ophiolite gap); survey/well creation in OpendTect (matrix says none, VAL:9); pickset/wavelet/random-line writers (R-C1 and no odbind
class); KML profile; a velocity-model kind (only F3's 1.78 MB cubes; E137 Out); triangulating faults (D83 default keeps sticks).

## D. Tests to add to existing epics

1. **E137 slice 0**: extend acceptance 1 (refusal by name) with a case per object in rows 5, 8, 11-15 of section A so each is either
   written or refused by name (not dropped); add the F3 `.flt` fault as a Fault3D fake in the extended `fake_odbind` (EPICS:13776) and
   state whether `Fault3D.getstick` is in scope (gap G4).
2. **E137 acceptance 2/3 (lines)**: add (a) a 2D-only survey fake (no inline/crossline ranges) to prove `survey.grid()` / `survey_facts` (survey.py:77,
   export.py:87-98) do not require a 3D grid; (b) a line name with spaces, dots, or `^` and a fractional/duplicate shot point (listing names
   `Seis^15.cbvs`, `20021203-2-03_0033.geom`, USL:37, F3L:6) as identity cases; (c) a `.geom` count not matching the line count (USGS 17 cbvs,
   17 geom plus `A,B,C,D` names, USL:59-77).
3. **E137 acceptance 6 (faults)**: add a test that a fault from a Fault3D (not a FaultStickSet) is read or refused by name; a test that
   a stick with `>= 2` points but a duplicate point or reversed order survives the round trip; time-domain fault read as metres already listed.
4. **E137 acceptance 6a (time-depth)**: add a case where a model exists in OpendTect well files and a standard file disagree (F3 `F02-01_DT_TVDSS.txt` F3L:263
   vs `.wlt`), declared in the Validation Record; a non-strictly increasing pair is refused by `time-depth-csv/1` (time_depth.py:4) and the pack says so by name.
5. **E129 horizon test (kept)**: add the 100,000-node boundary pair (99,999/100,000/100,001) to the starter archive tests (SC:202 has one oversize case only).
6. **E129 export acceptance 3**: add a multi-component cube and a depth-domain cube fake and assert the refusal sentences (export.py:39,43,113,260) reach `fidelity.json` as `not_placed`, so F3's steering cubes (row 2) are covered before the real run.
7. **E125 matrix (MX)**: add rows, proven or refused with a sentence, for: `2d get/send`, `well tops get/send`, `time-depth get/send` (MX:23 states only the free text), `cube send`, `horizon2d`. The matrix is the bridge's declared capability list, so absent rows are silent.
8. **New journey tests under C1** (once chartered), one per archive, each with an oracle read through odbind (R-44.4): F3 (cube + 8 horizons + 4 wells + logs + tops), USGS (17 2D lines, QGIS line geometry from `2DLines.geojson`, USL:15), MNSH/Rockall (2D lines + faults + OGA wells), Poseidon (3D cube + paths + time-depth).
9. **Intake**: land F3 `Shapefiles/` with space-containing names (4 shapefiles, F3L:223-245) and with OpendTect `.disp` side files: assert groups form, `companions_per_group` (8, REG limits) is not exceeded, QGIS opens them (CAPQ `esri-shapefile/1`, partly-qualified).
10. **QGIS**: `qgis.json` shows `partly-qualified` at best and `unverified` for publish (CAPQ); add the first real-archive map check (F3 horizons as points, wells, fault sticks) to E71b-style journey tests (docs/verification/E71b-qgis-vector-journey.md).
11. **Python target** (E129 slice e): add a pack with lines and no cube (EPICS:13761 point (3): Python target refuses without a cube today); acceptance 4 of E137 states it, make it a mutation target.
12. **R-C1 guard**: a repository scan test that the connector reads no OpendTect project file by decoding; note `export.py:91-94` reads `.defs` and `.survey` as text: decide in the strategy whether that is within the rule (Q-E3).

## E. Open questions that the archives (names-only listing) can answer

Produce for MNSH, Rockall Trough, Poseidon: `unzip -l <zip> > evidence/e44/<name>-listing.txt` (names and sizes only; no decoding),
then answer from extension counts exactly as done for F3/USGS (awk on the last field).

- Q-E1 (MNSH answered 31 Oct from `oga-mnsh-listing.txt`): 7 `.hor` and **5 `.2dh` Horizon2D**, 18 `.fss` (no `.flt`), 98 `.wlt`, 32 `.csmdl`, 4 `.tie`, 0 `.pck`/`.rdl`/`.body`/`.shp`/`.kml`, 2 `.wvlt`, NLAs folder empty (2 entries). Rockall Trough (answered 31 Oct from `oga-rockall-trough-listing.txt`): 5 `.hor`, 8 `.2dh`, **2 `.flt` and 0 `.fss`** (faults exist only in the Fault3D form E137 slice 0 refuses by name), 20 `.wlt`, 4 `.csmdl`, 2 `.tie`, 2 `.wvlt`, no `.pck`/`.rdl`/`.body`/`.shp`/`.kml`. Poseidon pending.
- Q-E1. Which of these exist per archive: `.hor` (3D) vs 2D-horizon files, `.flt` vs `.fss` (Fault3D vs FaultStickSet), `.wlt/.csmdl/.tie`, `.pck`, `.rdl`, `.wvlt`, `.body`, `.nn`/NLAs contents, `.shp`, `.kml`? This decides C3, C4, C5.
- Q-E2. Poseidon: is the cube time or depth (decides `DEPTH` refusal, export.py:39)? Trace count vs the 1,000,000 cap (segy.py:22)? Are time-depth models standard files beside the survey or only `.wlt` (D85, EPICS:13801)? Does it hold any seismic-2d?
- Q-E3. Does each archive carry a *complete* `.survey` and registered survey (2D-only for USGS, MNSH, Rockall)? Is `Survey.inlrange` defined for 2D-only surveys (survey.py:77)? Does the export's read of `.defs`/`.survey` text (export.py:91-94) count as through-the-door (R-C1)?
- Q-E4. Do archives ship `Rawdata/` (F3L:246-264 does; USL shows no Rawdata): may it serve as odbind-free fixture inputs or oracle (R-44.4, E44:44-46)? Owner/planner ruling needed.
- Q-E5. Count of 2D lines per OGA archive (cbvs and geom counts) against the 500-file `files_per_run` cap (REG limits) and the per-line cap D84 (subset allowed, EPICS:13800).
- Q-E6. Are any cubes multi-component (size relative to the original; `.par` sizes F3L:72)? F3 steering cubes suggest so (inferred).
- Q-E7. F3: do any wells hold a time-depth model *only* in `.wlt`, and which of the 4 wells have a standard DT file (only F02-01 shown, F3L:258-263)?
- Q-E8. Does the CRS of each survey translate (the pack decision `crs` uses pyproj, EPICS:12590)? USGS Alaska's CRS and MNSH/Rockall UK/offshore CRSs are **unverified**.
- Q-E9. Does OpendTect 7.0.10 `Seismic2D.line_info` and `FaultStickSet.getstick` actually work on these surveys (EPICS:13764 "not measured")? This is a one-line probe on the VPS and is the first stop rule of E137 (EPICS:13803).

## Summary of gaps (count 12)

G1 round-trip epic not chartered (E44:39-43; closed 31 Oct: E138). G2 2D lines have no type/writer (E137, covered). G3 faults survey-to-file path (E137, covered).
G4 Fault3D vs FaultStickSet scope (E137 ambiguous). G5 time-depth only in well files (E137 slice 3, D85, covered but F3 also hit).
G6 F3 holds 2D lines, a fault and tops that E44's table omits (E44:17 vs F3L:6-17, 57-66, 119, 168-215). G7 `tops`/`wellbore-headers` have no writer.
G8 2D horizons unwritable and excluded. G9 100,000-node horizon cap unowned (blocks F3 above L3). G10 depth and multi-component cubes refused.
G11 native objects without odbind class have no omission contract. G12 no headless survey/well creation limits any return leg and ResInsight stays wells-only.
