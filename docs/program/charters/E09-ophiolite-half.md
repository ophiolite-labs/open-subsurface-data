## E09-oph Ophiolite reads the catalogue, the Ophiolite half — charter for the Ophiolite program queue (handed over 23 Oct 2026)

Authority: OSD charter `E09-ophiolite-reads-the-catalogue.md` (designs 1, 3, 4, 6 and the
interface); Ophiolite E85 (one intake), E55 (upload run), E35 (rights-basis), E122 (provenance).
Classification in the Ophiolite program: Kernel, one Codex round there.

**Outcome.** A person drops an `osd.manifest` file (manifest/1, /2 or /3; `schema/manifest.schema.json`
in the open-subsurface-data repository) into E85's intake. The run fetches each entry's file from
its origin or its mirror alternate, verifies the sha256 the manifest states, lands it through the
normal E55 run with the kind decided from content, and each landed item carries: the manifest
entry's licence object verbatim (every field, absence preserved), the catalogue item identity
(collection id, asset key, sha256, Item id when present) and the snapshot (`metadata.catalog`).
The run exports a `fidelity/1` document (schema defined in the OSD repository) that the catalogue
reads back to award L4.

**Slices.** (a) Intake and landing: recognise the file by `format`, fetch with checksum
verification (a mismatch is one outcome from E55's closed list, never a landed file), land, write
E122 provenance with the catalogue identity and snapshot. (b) Fidelity export: one document per
run, every input listed with its result, output identity, converter and version, representative
values for logs (first curve mnemonic, unit, sample count). (c) Rights, after E35 merges: map
each `redistribution` state to rights-basis explicitly; `unknown` refuses publication with E35's
plain-words reason and grants nothing; allowed-publication control in the test. Until E35, the
licence object is stored verbatim and shown on the item.

**Acceptance.** Journey test with the OSD two-well LAS fixture and its manifest/3: two items
land as wellbore logs with the catalogue identity and snapshot on their provenance; the exported
fidelity file validates against `fidelity.schema.json` and `osd verify --fidelity-from` on it
awards L4 in the OSD test suite (fixture shared by path, no live coupling); a manifest whose
checksum does not match yields the mismatch outcome and no item; slice (c): publication of an
item from an `unknown` record is refused with the stated reason while an `allowed` item publishes.
NLOG: the try-it sample's kinds and licence text agree with `records/nlog/nlog.yaml`; a difference
is reported as a finding in the PR.

**Out of scope.** STAC-address intake; workspace references (E12); seismic; any change to
canonical types.

**Dependencies.** E85, E55 (merged); E35 for slice (c); OSD E09 slice 1 for the fidelity schema and
manifest/3 (fixtures live in the OSD repository, which is public).
