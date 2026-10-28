## E42-oph A starter pack from a project: the recipe, three targets and the two documents — the Ophiolite half, handed to the Ophiolite program 28 Oct 2026 (to be chartered there; classification Kernel, one Codex round there)

Authority: OSD family "Ready for your tools" (owner direction 28 Oct 2026) and OSD charters E40
(starter/1) and E42 (the F3 pack and its oracle); Ophiolite E125 (OpendTect connector, merged
22 Oct), E126 (notebook adapters and gallery, merged 22 Oct), E85 (one intake), E127 (fidelity/1
writer, queued) and R-C1 ("through the door"). The OSD side promises nothing about Ophiolite's
internals; Ophiolite's own charter names the modules and the slice order.

**Outcome.** One command, run by a maintainer or in CI, takes a pack definition (the dataset's
inputs by digest, the decisions, the wanted targets) and produces: an Ophiolite project holding the
data in canonical types; an OpendTect target (a survey written through odbind by E125's get path,
plus an import script that recreates it on a user's OpendTect from the standard files in the pack);
a ResInsight target (a project written through `rips`, ResInsight's Python API, plus the script);
a Python target (a notebook on E126's adapters that runs offline against the pack); and two
documents, `starter/1` and `fidelity/1` (schemas in the OSD repository, `schema/starter.schema.json`
and `schema/fidelity.schema.json`), with sha256 and bytes for every artefact.

**Interface (fixed by OSD).** Input: a pack definition YAML (fields as starter/1 minus the computed
ones) and the input files on disk with their digests. Output: a directory with `starter.json`,
`fidelity.json`, `targets/<application>/…` and `ATTRIBUTION.md`. The recipe id, the Ophiolite
commit and every tool version (OpendTect, odbind, ResInsight, rips, segyio, lasio) are written into
`starter.recipe`. OSD validates the two documents; Ophiolite never writes a level.

**Slices suggested to the Ophiolite planner.** (a) Pack definition reader, decision application
(CRS transform with pyproj, datum and depth-reference handling, unit normalisation, null handling,
name mapping) and the `starter/1` and `fidelity/1` writers over a fixture dataset, no external
application; (b) the OpendTect target through E125 with its import script, proven in E125's CI
against OpendTect 7.0.10; (c) the ResInsight target through `rips` with headless ResInsight
v2026.09.1 on a hosted runner, or by hand with a screenshot if headless fails (stop rule mirrored in
OSD E42); (d) the Python notebook in the E126 gallery, both modes.

**Facts for the strategy (Ophiolite `origin/main` `9e34915a8`, 28 Oct; Codex-verified).** E125's matrix
(`ophiolite-opendtect/src/ophiolite_opendtect/data/matrix.json`): well get refused (odbind 7.0.10
cannot create a well), well send, log get and send, horizon get and send, cube get supported; faults
refused; no code creates a survey; the connector's CI suite runs offline with "no pinned OpendTect"
skips, live evidence is the Validation Record. `ophiolite-connectors/tools/resinsight-demo.py`
already imports well log files through rips and saves a `.rsp`. `ophiolite-sdk/ophiolite/fidelity.py`
writes fidelity/1 (E127 slice 1a). `rips` 2026.9.1.2 needs Python 3.11 or later; ResInsight v2026.09.1
has an Ubuntu 24.04 build.

**Capabilities this half must prove before OSD E42 opens (its merge notice states each).** (1) A
headless route to create an OpendTect survey and four wells from standard files (odbind, an OpendTect
command-line tool, or none: then the pack's import script says those two steps are GUI imports and
the OSD oracle runs after them). (2) Whether rips imports SEG-Y headless on v2026.09.1 (yes or no,
frozen into the pack definition). (3) The Python notebook runs standalone on segyio and lasio with
network disabled, no Ophiolite service. (4) The starter/1 and fidelity/1 writers emit documents that
pass OSD E40's validator on the F3-shaped fixture.

**What OSD needs back.** The merged command's name and invocation, the Ophiolite commit, and a run on
the F3 inputs that OSD E42 commits and compares (OSD E42 design 3). OSD E42 does not open until this
half is merged.
