## E09-oph Ophiolite reads the catalogue, the Ophiolite half — handed over 23 Oct 2026; chartered in the Ophiolite program as **E127** (Ophiolite main d01b5c95e), queued after E121, slices (a)+(b) may fill in earlier

The Ophiolite side's wording rules (planner ophiolite-32, 23 Oct): the catalogue identity and snapshot are written into Ophiolite's provenance record (E122 `source-provenance/1`, a new source-system entry for the catalogue) under a field E127's strategy names; OSD documents never promise an Ophiolite field name. A digest mismatch is a new outcome code in the upload run's closed list. Rights-basis uses are read/derive/export; the refusal for `unknown` is the act E127's strategy names against E35, not a sentence OSD promises.

Authority: OSD charter `E09-ophiolite-reads-the-catalogue.md` (designs 1, 3, 4, 6 and the
interface); Ophiolite E85 (one intake), E55 (upload run), E35 (rights-basis), E122 (provenance).
Classification in the Ophiolite program: Kernel, one Codex round there.

**Outcome.** A person drops an `osd.manifest` file (manifest/1, /2 or /3; `schema/manifest.schema.json`
in the open-subsurface-data repository) into E85's intake. The run fetches each entry's file from
its origin or its mirror alternate, verifies the sha256 the manifest states, lands it through the
normal E55 run with the kind decided from content, and each landed item carries: the manifest
entry's licence object verbatim (every field, absence preserved), the catalogue item identity
(collection id, asset key, sha256, Item id when present) and the snapshot (the manifest's `metadata.catalog`, carried in Ophiolite's provenance record).
The run exports a `fidelity/1` document (schema defined in the OSD repository) that the catalogue
reads back to award L4.

**Slices.** (a) Intake and landing: recognise the file by `format`, fetch with checksum
verification (a mismatch is one outcome from E55's closed list, never a landed file), land, write
E122 provenance with the catalogue identity and snapshot. (b) Fidelity export: one document per
run, every input listed with its result, output identity, converter and version, representative
values for logs (first curve mnemonic, unit, sample count). (c) Rights, after E35 merges: map
each `redistribution` state to rights-basis explicitly; `unknown` grants nothing and refuses the act E127 names against E35, with a plain-words reason; allowed-publication control in the test. Until E35, the
licence object is stored verbatim and shown on the item.

**Acceptance.** Journey test with the OSD two-well LAS fixture and its manifest/3: two items
land as wellbore logs with the catalogue identity and snapshot on their provenance; the exported
fidelity file validates against `fidelity.schema.json` and `osd verify --fidelity-from` on it
awards L4 in the OSD test suite (fixture shared by path, no live coupling); a manifest whose
checksum does not match yields the mismatch outcome and no item; slice (c): the E127-named act on an
item from an `unknown` record is refused with a stated reason while an `allowed` item passes it.
NLOG: the try-it sample's kinds and licence text agree with `records/nlog/nlog.yaml`; a difference
is reported as a finding in the PR.

**Out of scope.** STAC-address intake; workspace references (E12); seismic; any change to
canonical types.

**Dependencies.** E85, E55 (merged); E35 for slice (c); OSD E09 slice 1 for the fidelity schema and
manifest/3 (fixtures live in the OSD repository, which is public).

**Fixture pin (OSD E09-fx).** The static manifest/3 files E127 reads by path are
`tests/fixtures/fidelity/manifest-two-wells.json` (the two LAS files `well-a.las`, `well-b.las`),
`manifest-no-statement.json` and `manifest-null-attribution.json`, with `fidelity.json` and the LAS
files beside them. E127 pins the merge commit of the OSD pull request "E09: static manifest/3
fixtures for E127" for those files, never main. In OSD,
`test_static_manifest_3_fixtures_equal_what_osd_manifest_writes` keeps each file equal to what
`osd manifest` writes from the fixture catalogue; a change to them is a new pin.

**Pins and naming (planner ophiolite-32, 25 Oct; E127 s0 strategy rev 2, Ophiolite main 54e78248b).**
Ophiolite pins `tests/fixtures/fidelity/**` and `schema/fidelity.schema.json` at OSD 82ae556 and
`schema/manifest.schema.json` at ae7a812; its tests read those copies, never OSD main, and a parity
check runs against an OSD checkout when present. Manifests osd.manifest/1 to /4 are recognised; a
non-anonymous entry is refused per entry. A lane that moves, renames or changes one of those pinned
files tells the OSD supervisor, who tells ophiolite-13 or ophiolite-32 (E127 re-pins on purpose).
OSD documents keep saying "Ophiolite's provenance record (E127)" until ophiolite-32 reports that
e127s0 has merged; the field name is not written into OSD documents before then.
