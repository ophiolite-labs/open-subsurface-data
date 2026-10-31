## E44 Packs after the proof: every deposited TerraNubis dataset becomes a starter project, and every content kind translates to Ophiolite — QUEUED (31 Oct; slice 0 records now, packs one per dataset after E42; Records and Kernel, cross-repo; strategy at lane open; the Ophiolite half carries its own Codex round)

Authority: owner direction 28 Oct 2026 ("once that is proven we can take the next steps of selecting
other blocks / datasets"; "from the Netherlands and some other convenient and legal to use dataset");
family rule R-T7; OSD-D24 (open); E42 (the proof), E43 (the request template as evidence).

**Outcome.** Two or three more starter projects are on the site, each for the applications its data
fits, each with its decision log, oracle and fidelity record: a Dutch well pack, a Dutch 3D survey
pack and a reservoir-model pack for ResInsight are the planner's candidates. The owner picks.

**Owner ruling, 31 Oct 2026 (answers OSD-D24; replaces the candidate table below for the first
round).** The owner downloaded five TerraNubis datasets on 31 Oct and ruled: "widen the scope to include
all these datasets; all need to be able to translate to Ophiolite data types / ontology". So:

| Dataset | Record | Archive (bytes on the owner's Mac, 31 Oct) | Licence as the record reads it | Content kinds |
|---|---|---|---|---|
| F3 Demo 2023 | `terranubis/f3-demo-2020` | `F3_Demo_2023.zip` 4,782,432,978 | CC-BY-SA-3.0, redistribution allowed | seismic-3d, wellbore-logs, wellbore-headers, horizons |
| OGA Mid North Sea High | `terranubis/oga-mnsh` | `MNSH_OGA_2016_v1.zip` 11,537,303,224 | OGL-UK-3.0, allowed | seismic-2d, wellbore-logs, horizons, faults |
| OGA Rockall Trough | `terranubis/oga-rockall-trough` | `Rockall_Trough_OGA_2016_v1.zip` 9,961,960,412 | OGL-UK-3.0, allowed | seismic-2d, wellbore-logs, horizons, faults |
| USGS Central Alaska 2023 | `terranubis/usgs-central-alaska-2023` | `USGS_Central_Alaska_2023.zip` 167,571,826 | CC-BY-SA-3.0, allowed | seismic-2d |
| NW Shelf Australia Poseidon 3D | new record `terranubis/nw-shelf-australia-poseidon-3d` (slice 0; TerraNubis repackaging of `nopims/poseidon`; its page labels CC BY-SA 3.0 and quotes CC BY 3.0 AU: the lane reads the terms on the day) | `Poseidon_3D.zip` 14,236,435,784 | to be read (R-T4: never a pack while unknown) | seismic-3d, wellbore-logs, horizons |

Rules added by the ruling:

- R-44.1 *Every dataset, every kind.* Each of the five becomes a starter project, and every content
  kind in the five (seismic-3d, seismic-2d, wellbore-logs, wellbore-headers, horizons, faults) must
  have a translation into Ophiolite's data types; a kind no writer handles is a defect of the
  Ophiolite half, not a pack that quietly omits it. The two new kinds against E129 are seismic-2d
  (lines, not a cube) and faults (sticks); the Ophiolite half charters them as an E129 follow-on with
  its own Codex round.
- R-44.2 *Deposits first.* All five archives are deposited (E41 design 6, directories
  `/mnt/HC_Volume_107082112/osd-deposits/terranubis/<dataset>/` with `page.html` beside each; the
  supervisor pulled them from the Mac on 31 Oct) and reach L2 from custody before any pack; E41's
  acceptance 6 counts all five.
- R-44.3 *Order.* Slice 0 (records): the Poseidon record, the five `known_issues`/`notes` lines
  naming the deposit, the five deposits run. Then packs in the order F3 (E42, the proof), USGS Central
  Alaska (smallest, first seismic-2d), OGA MNSH, OGA Rockall Trough, Poseidon; a pack opens only when
  its kinds have writers.
- R-44.4 *Oracles.* F3: dGB's survey (E42). The others: the archive's own OpendTect survey where one
  is shipped (TerraNubis archives are OpendTect projects), read through odbind, as E42 design 4 does.

**Candidates (facts from the records on `origin/main` `4293cc8`, 28 Oct).**

| Candidate | Record | Licence | Fits | Oracle |
|---|---|---|---|---|
| Netherlands wells: headers, paths, logs, tops for one area | `nlog/nlog` (WFS listing, redistribution allowed with attribution, owner item 107) | NLOG terms, attribution | OpendTect wells, ResInsight well paths and logs, Python | NLOG's WFS values and the LAS headers |
| One NLOG-released 3D survey | `nlog/nlog` (seismic-3d among its kinds; the survey chosen at lane open from the released list) | as above | OpendTect, Python (E10 slices if merged) | the SEG-Y headers through segyio |
| Drogon, the synthetic FMU model | `equinor/drogon` (GitHub, CC-BY-SA-4.0 data, GPL code; no location) | share-alike | ResInsight (Eclipse deck), Python | Equinor's own deck and the FMU tests |
| Volve | the Equinor record on main at lane open | Equinor open-data terms as the record states | ResInsight, OpendTect, Python | the published summary files |

**The design the lane maps to.** The recipe and the targets of E42 unchanged; a new pack is a new
definition under `starters/`, a run, an upload and a comparison; a target the data does not fit is
left out and the pack says so; a dataset whose licence is `restricted` or `unknown` is never a
candidate (R-T4). Any recipe change goes back to the Ophiolite half with a Codex round.

**Acceptance.** E42's acceptance 1 to 6 per pack, with the oracle named in the table; the request
template's issues (E43 design 5) are read and counted in the PR as evidence for the choice.

**Stop rules.** E42 not published (for packs 2–5; slice 0 does not wait); a kind without a writer (the pack waits, the finding goes to the Ophiolite half); a candidate's terms read on the day do not
allow redistribution.

**Ownership and dependencies.** One coding lane per pack, paths `starters/**`, the chosen record's
`known_issues` and `notes`, `docs/program/evidence/e44/**`. Depends on E42, E43.

**Evidence to inspect.** The oracle blocks; the site screenshots; the request issues counted.
