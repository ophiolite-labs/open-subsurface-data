## E44 Packs after the proof: the next datasets, chosen by the owner — DEFERRED (after E42 publishes; Records and Kernel, cross-repo; strategy at lane open; one Codex round if the recipe changes)

Authority: owner direction 28 Oct 2026 ("once that is proven we can take the next steps of selecting
other blocks / datasets"; "from the Netherlands and some other convenient and legal to use dataset");
family rule R-T7; OSD-D24 (open); E42 (the proof), E43 (the request template as evidence).

**Outcome.** Two or three more starter projects are on the site, each for the applications its data
fits, each with its decision log, oracle and fidelity record: a Dutch well pack, a Dutch 3D survey
pack and a reservoir-model pack for ResInsight are the planner's candidates. The owner picks.

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

**Stop rules.** E42 not published; OSD-D24 not answered; a candidate's terms read on the day do not
allow redistribution.

**Ownership and dependencies.** One coding lane per pack, paths `starters/**`, the chosen record's
`known_issues` and `notes`, `docs/program/evidence/e44/**`. Depends on E42, E43.

**Evidence to inspect.** The oracle blocks; the site screenshots; the request issues counted.
