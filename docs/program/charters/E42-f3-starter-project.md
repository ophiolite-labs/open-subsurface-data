## E42 The F3 starter project: one dataset through the whole chain, judged against dGB's own survey — QUEUED (after E41 and the Ophiolite half; before E44; Kernel, cross-repo; strategy at lane open; Codex round closed, REWORK reworked 28 Oct, dispositions below)

Authority: owner direction 28 Oct 2026 ("F3 for us may be a useful test case to try and replicate as
a proof of concept"; OSD-D21); family rules R-T1 to R-T5 and R-T7; E40 (starter/1, custody/2
`derived`, the validity tests), E41 (F3 deposited and at L2, `put-derived`), E03 (outlines from the
data), E09 (the L4 rule, `osd verify <id> --fidelity-from`); Ophiolite E125, E126, E85, E127 slice 1a
(facts below); the Ophiolite half chartered from `E42-ophiolite-half.md`; Ophiolite R-C1; the Codex
round of 28 Oct (REWORK; table below).

**Outcome.** A person finds F3 (Dutch North Sea) on opensubsurfacedata.org and downloads a starter
project for OpendTect, for ResInsight or for Python. The OpendTect pack gives a survey with the F3
cube, the four wells with their logs and the horizons, in the right place, in metres, in time, under
CC BY-SA 3.0 with dGB named. The ResInsight pack gives a project with the four well paths and logs,
and the cube when ResInsight's API imports it (frozen at lane open, not left open). The Python pack
is a notebook that reads the pack's SEG-Y and LAS with segyio and lasio, offline, and draws one named
inline with the four wells projected onto it. Each pack ships its decision log, its oracle and its
fidelity record; F3 reaches L3 from its data and L4 from the fidelity record. The site shows it
(E43's DONE condition).

**Context today (verified 28 Oct; Codex-verified against the cited commits).**

- OSD `origin/main` `4293cc8`: F3 is `terranubis/f3-demo-2020` (CC-BY-SA-3.0, share-alike,
  registration-only; L0 in the 24 Oct snapshot after a 502, ceiling L1 until E41);
  `ibm-research/netherlands-f3-interpretation` (Zenodo, CC-BY-4.0, labelled image sections, not the
  cube) is a second F3 record. No outline from data for F3 (E03: behind a login). L4 is applied
  offline by `osd verify <id> --fidelity-from <doc>` (`src/osd/cli.py:35`, `apply_fidelity` in
  `src/osd/verify.py`): it needs the catalogue's own L1–L3, every fidelity input in the verification
  inventory, a reason for every failure and at least one converted input; the build copies the
  stored level.
- Ophiolite `origin/main` `9e34915a8`. E125's capability matrix
  (`ophiolite-opendtect/src/ophiolite_opendtect/data/matrix.json`): well get **refused** ("odbind
  7.0.10 cannot create a well", `heads.py:4`), well send supported, log get and send supported (onto
  an existing survey well with the same name and head), horizon get and send supported (written
  beside), fault get and send refused, cube get supported at the survey's sampling. `exchange.py:85–100`
  implements exactly these. CI runs the connector's offline suite with "no pinned OpendTect" skips
  (`.github/workflows/visual.yml:345`); live odbind evidence is the lane's Validation Record, by hand.
  No code creates a survey. `ophiolite-connectors/tools/resinsight-demo.py:13–17` connects to
  ResInsight through rips, imports well log files and saves a `.rsp` project; `src/asset_connectors/resinsight.py:68`
  reads live logs. E126 adapters and gallery exist (`ophiolite-sdk/ophiolite/lasio.py`,
  `gallery.py`, which defaults to a synthetic server or a project service). E85 intake exists; E127
  slice 1a (manifest fetch with digest check, fidelity/1 writer `ophiolite-sdk/ophiolite/fidelity.py:119`)
  is merged. Nothing writes starter/1.
- Non-code, read 28 Oct, unverified until the deposit: F3 Demo 2023 is an OpendTect survey behind
  registration; four wells (F02-1, F03-2, F03-4, F06-1). ResInsight v2026.09.1 (24 Sep 2026);
  `rips` 2026.9.1.2 on PyPI requires Python 3.11 or later. segyio 1.9.14, lasio 0.32, openvds 3.4.9,
  multidimio 1.2.3 on PyPI.

**The design the strategy must map to.**

1. *The archive is the input; exports are derived.* The deposited F3 Demo 2023 download (E41) is the
   pack's one input (`held: deposited`, custody key). The recipe reads it only through odbind (R-T2)
   and exports the cube as SEG-Y, each well as LAS plus a deviation file, each horizon as OpendTect
   ASCII; these are `derived[]` entries with `from` the archive digest and are also the artefacts of
   the Python target. The fidelity/1 document names the archive as its input with result converted or
   partial and `output` the kinds produced; so E09's inventory rule holds. If the lane finds the F3
   SEG-Y and wells on an anonymous origin whose terms allow it, that record's verified files become
   inputs beside the archive.
2. *L3 before L4.* The recipe writes the survey outline (the cube's inline and crossline corners,
   through odbind, transformed from EPSG:23031 to WGS84) and the four well positions as
   `outlines/terranubis__f3-demo-2020.geojson` with `derivation` naming the deposit; the verifier's
   outline check gives L3; then `osd verify terranubis/f3-demo-2020 --fidelity-from` gives L4. The
   placeholder outline goes.
3. *The recipe is the Ophiolite half.* One command there takes the pack definition
   (`starters/terranubis__f3-demo-2020__f3.yaml`, this lane's), applies the decisions (CRS EPSG:23031
   as the survey states, checked against the well heads; time domain; metres; publisher log names
   kept with a mapping to the catalogue's vocabulary), writes the three targets and the two
   documents. This lane runs it on the VPS, uploads the artefacts with `osd mirror put-derived`
   (E41), commits the starter, fidelity and outline documents, and runs the oracle.
4. *OpendTect target, honestly.* odbind 7.0.10 creates no wells and E125 creates no survey. The
   target is the standard files plus an import script that uses odbind for what it can write (cube,
   horizons, logs onto existing wells) and OpendTect's own documented import for the survey and the
   four wells; the Ophiolite half proves a headless route for both or states that the two steps are
   GUI imports. The oracle (design 5) runs after the import on the VPS's OpendTect 7.0.10 and is the
   proof either way; a screenshot of the opened survey is attached. Faults are not in the pack.
5. *The oracle is dGB's survey, and a second reader.* Through odbind on the original survey and on
   the imported one: the frozen horizon inventory (names, count) with z at 200 seeded bin positions
   per horizon and the non-null count asserted; the cube's inline, crossline and time ranges and 100
   seeded traces sample by sample; for each of the four wells the head x and y, the station count,
   the first and last station (dah, tvdss, x, y), the log inventory and 50 seeded log samples with
   their depths and units. A second check reads the SEG-Y with segyio and the LAS with lasio and
   compares the same values. Seeds, counts and differences are the `oracle` block; `differences`
   must be 0 or the pack is `unpublished` (E40 design 4(i)).
6. *ResInsight target, frozen.* The Ophiolite half establishes at its lane open whether rips imports
   SEG-Y headless; the pack definition then says `cube: true|false` and the acceptance below tests
   what it says, with numeric read-back through rips (well path stations, log samples), not a
   screenshot alone.
7. *Python target, standalone.* The notebook reads the pack's SEG-Y and LAS from the pack directory
   with segyio and lasio, network disabled, no Ophiolite service, and writes the inline image with
   the wells projected by the pack's CRS; it asserts the inline number, three sample values and the
   four projected positions against values in the pack (so it is a test, not a picture).
8. *Decisions per object.* The log (R-T3) has one line per (topic, subject) that E40 design 4(e)
   requires for one cube, four wells and the horizons; `chosen` lines carry the reason and their
   count is in the summary.
9. *Licence.* Computed from the archive: CC-BY-SA-3.0, attribution required, share-alike;
   ATTRIBUTION.md names dGB Earth Sciences and the F3 Demo 2023 page.

**Acceptance (values frozen at lane open from the deposited survey through odbind, by hand).**

1. OpendTect: after the pack's import on OpendTect 7.0.10 Linux, the oracle of design 5 reports 0
   differences over its frozen counts; mutating one station, one log sample and one horizon value in
   a copy of the pack makes it report 3 (test on the comparison code); deleting a horizon from the
   copy fails the inventory check. Screenshot attached.
2. ResInsight v2026.09.1: the rips script imports the pack; read-back through rips gives four well
   paths whose station counts and first and last stations equal the frozen values, logs whose 50
   seeded samples equal; the cube is present if and only if the pack says `cube: true` (test).
3. Python: the notebook runs top to bottom with network disabled against the pack directory and its
   assertions hold; corrupting one trace in the SEG-Y copy fails it; shifting one well head fails it.
4. Catalogue: on the fixture build, the committed outline, fidelity and starter documents give F3
   L3 then L4 through `osd verify --fidelity-from`; with the fidelity input's result mutated to
   `failed` the record stays L3 and E40's validator refuses the pack (two assertions, separate).
5. `osd manifest --starter terranubis/f3-demo-2020/f3` then `osd get` from the real mirror fetches
   every artefact plus the decision log and the fidelity document into the stated layout with digests
   equal and ATTRIBUTION.md naming dGB (transcript); the OpendTect import of acceptance 1 runs from
   that fetched directory, not from the recipe's output.
6. The decision log has every (topic, subject) line E40 requires for the pack's `contents`;
   deleting one well's depth-reference while the other three keep theirs fails E40's validator naming
   the well (fixture mutation).

**Out of scope.** A second dataset (E44); the site (E43 owns `site/**`; this lane's merge is E43's
DONE condition); a seismic store for slicing (E10); faults; Petrel (Ophiolite E123); selling anything
(R-T6).

**Stop rules.** The lane stops and returns to the supervisor when: the F3 deposit (E41 acceptance 6)
is not on main; the Ophiolite half is not merged with its capability statement (survey and well
import routes, rips SEG-Y yes or no); the oracle shows a difference the decision log cannot explain
(the pack stays `unpublished` and the finding goes to the Ophiolite half as a defect); the outline
derivation cannot read the corners through odbind (then the SEG-Y export's headers through segyio).

**Ownership and dependencies.** Coding lane here; paths `starters/terranubis__f3-demo-2020__f3.*`
(definition, starter and fidelity documents), `outlines/terranubis__f3-demo-2020.geojson`,
`records/terranubis/f3-demo-2020.yaml` (`known_issues` and `notes` only), `records/**` (one new
record only if design 1's anonymous origin is found), `docs/program/evidence/e42/**` (oracle output,
transcripts, screenshots), `tests/test_starters.py` (the F3 fixture's L3→L4 and decision tests
only). Everything else is the Ophiolite half. Depends on E40, E41 (merged), the Ophiolite half
(merged), the owner's F3 download (owner item).

**Evidence to inspect.** The oracle block and its seeds; the two screenshots; the ATTRIBUTION.md
written by `osd get`; the decision log; the L3 and L4 reason sentences on the map.

**Dispositions of the Codex round (28 Oct, REWORK).**

| # | Finding | Disposition |
|---|---|---|
| 1 | E125 overstated (no well or fault creation, no survey creation) | Accepted; matrix quoted; design 4 and the half's proof obligation |
| 2 | CI does not establish live coverage | Accepted; Context says offline suite with skips, live by hand |
| 3 | "nothing drives ResInsight" false | Accepted; `resinsight-demo.py` cited |
| 4 | E127 partly implemented | Accepted; slice 1a cited |
| 5 | F3's L1 not established | Accepted; L0 in the snapshot, ceiling L1 |
| 6 | "next build" does not award L4; L4 needs L1–L3 | Accepted; design 2 (L3 from the data) and `--fidelity-from` |
| 7 | a failed input does not necessarily remove L4 | Accepted; acceptance 4 separates the record's level from the pack's refusal |
| 8 | exports are not deposited originals | Accepted; design 1: archive input, `derived[]` with lineage |
| 9 | derived upload has no eligibility path | Accepted; E41 design 5 `put-derived` |
| 10 | L3 has no owner | Accepted; design 2, outline path claimed |
| 11 | fresh-survey and well creation unresolved | Accepted; design 4 and stop rule 2 |
| 12 | Python target needs a standalone contract | Accepted; design 7 |
| 13–18 | acceptance lines pass despite defects | Accepted; acceptance 1–6 rewritten with read-back and mutations |
| 19 | identity, custody and L4 policy belong to E40/E41/E09 | Accepted; removed from this lane's claim |
| 20 | connector completion belongs to the half | Accepted; `E42-ophiolite-half.md` lists the capabilities to prove |
| 21 | site wording belongs to E43 | Accepted; out of scope names E43's DONE condition |
