## E09 Ophiolite reads the catalogue — QUEUED · Kernel, cross-repo · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: owner direction 23 Oct ("verified bits … pull into their workspace"); Ophiolite E85
(one intake, merged 8 Oct, release 2026.10.63), E55 (kind registry, merged 7 Oct), E35 (rights-basis,
QUEUED in the Ophiolite program on 23 Oct), E122 (provenance); OSD-D6, E06 dispositions.

**Outcome.** In an Ophiolite project a person drops an `osd.manifest` file into the intake, the
files land through the normal upload run, every landed item carries the record's full licence
object and names the catalogue item and the catalogue snapshot it came from, and a fidelity
record says which input converted to which canonical output, with what, and which did not. The
catalogue reads that fidelity record back and awards L4 only when it matches its own evidence.

**Context today (verified 23 Oct).** This repository, main after PR #13: `osd.manifest.read`
reads a local manifest/1 or /2 with schema validation; the manifest derives assets from Collection
assets and marks missing ones `unresolved`; the metadata block carries no snapshot identity;
Collections publish SPDX, licence link and redistribution but not statement, attribution or
share-alike; `records.json` is built from records plus the separately updated
`verification-results` branch; levels come from `level_from_checks`; the verification schema does
not relate `level` to checks. Ophiolite, from `docs/program-2026-09-25/PROGRAM.md` at `fb1fb485d`:
E85 one intake (file, files, folder, zip or an address) MERGED; E55 persisted upload run with one
outcome per file MERGED; E79 try-it image with an NLOG sample MERGED; E35 rights-basis QUEUED (not
merged), so no rights field exists on uploads today. F3 is registration-only, CC-BY-SA-3.0, no
statement, no addressable files: not a fixture of this epic (E06 and E07 dispositions).

**The design the lane must map to.**
1. Two halves, two repositories, one interface, which is the manifest file. STAC-address intake
   is out of this epic (Collections do not carry the full rights object). Here: snapshot identity,
   the fidelity contract, the L4 rule. There (Ophiolite lane, charter in `E09-ophiolite-half.md`,
   queued by the Ophiolite planner): the intake recognises `osd.manifest`, lands the files, writes
   provenance and exports fidelity; the rights part of that lane lands with or after E35.
2. Snapshot identity. `records.json` gains `catalog: {source_commit, verification_commit,
   built_at, records_digest}` where `records_digest` is the sha256 of the records array as
   serialised; manifest/3 copies that object into `metadata.catalog` (manifest/1 and /2 still
   validate and read; a manifest without `catalog` reads with `catalog: null`). Each manifest
   entry is identified by collection id, asset key and sha256; Item ids are added only when the
   asset belongs to an Item.
3. Rights travel whole. The manifest's licence object (`name, spdx, url, statement, attribution,
   share_alike, redistribution`) is preserved field by field, including absence; nothing is
   inferred. The Ophiolite half maps each `redistribution` state (`allowed`, `restricted`,
   `forbidden`, `unknown`) to E35's authorisation rules explicitly; `unknown` grants nothing and
   refuses the act Ophiolite E127 names against E35. Until E35 merges the Ophiolite half stores
   the object verbatim on the item and shows it. `metadata.catalog` is a field of the manifest
   file; on the Ophiolite side the identity lives in Ophiolite's provenance record (E127, `Acquisition.listed_in` in scientific-asset/1), whose
   field names are Ophiolite's.
4. Fidelity is a document, `fidelity/1` (`schema/fidelity.schema.json`, defined here, written
   there): `catalog` (the snapshot object), `record`, and per input `{sha256, name, result:
   converted|partial|failed|skipped, output: {kind, id, converter, version}, representative:
   {field, value, unit}[], reason}`. The catalogue derives the check `canonical-conversion` from
   it ("n of m inputs converted to kinds") and never copies a level or any lower check from it.
5. L4 rule, in `osd verify --fidelity-from <file>`: L4 is computed by `level_from_checks` with the
   catalogue's own L1–L3 checks retained; the fidelity file is rejected (check `failed`, level
   unchanged) when its record id does not match, when any input sha256 is not among the latest
   verification's files, or when an input is `partial` or `failed` without `reason`. The snapshot
   (`catalog`) is recorded on the check for identity and is not a rejection criterion: an edit to an
   unrelated record or a verification run that leaves this record's files unchanged keeps L4
   (amended 23 Oct on the lane's inbox note 3; a per-record digest is a later slice if needed). Partial coverage (some inputs converted) awards
   L4 only when every input of the inventory has a result and at least one `converted`;
   `osd status` shows the coverage beside L4.
6. NLOG consistency: the try-it sample's declared kinds and licence text are compared to
   `records/nlog/nlog.yaml` in the Ophiolite half; a difference is a finding there, not a
   record edit here.

**Slices.** OSD slice 1 (this lane): designs 2, 4, 5 with tests and mutations; a manifest/3 built
from Norne as the real-record case; the offline fixture is a two-well LAS set under
`tests/fixtures/fidelity/` (no publisher data). Ophiolite half: one lane in the Ophiolite program
(charter beside this file), after E35 for its rights part.

**Acceptance (OSD slice 1).**
- `records.json` carries `catalog` with four fields; two builds from the same inputs give the same
  `records_digest`; changing one record or the verification input changes it (tests).
- Round trip: a fixture manifest with distinct values in every licence field, plus one entry with
  `statement` absent and one with `attribution` null, passes build → manifest → `read` with exact
  values and exact absence asserted per field; mutation: the mapper drops a supplied statement →
  red; the absent case stays green on its own test.
- manifest/1 and /2 fixtures still read; manifest/3 with `catalog` reads; `catalog` on a /2 file
  is refused.
- Fidelity: a valid fidelity/1 for the LAS fixture whose hashes match the fixture verification
  yields L4 with coverage "2 of 2"; each of these alone yields no L4 and names the reason: a
  mismatched input hash, a mismatched record id, a `failed` input without reason, L3 absent in
  the catalogue's own checks, an empty inputs list; and a fidelity file whose inputs still match
  after an unrelated record edit keeps L4 (amended 23 Oct). Mutations: hash compare dropped, digest compare dropped, level copied from the
  file, lower checks copied from the file → each red against the unchanged suite.
- `osd status` shows "L4 (2 of 2 converted)" for the fixture and the plain level for others.
- Schema negatives for fidelity/1: missing catalog, unknown result, output without kind, input
  without sha256.

**Out of scope.** STAC-address intake; workspace references without copying (E12); seismic (E10);
any change to Ophiolite's canonical types; the Ophiolite half's code (its own lane).

**Stop rules.** None for the OSD half. The Ophiolite half's rights part waits for E35; its intake
and fidelity parts may start on E85 as merged.

**Ownership and dependencies.** Coding lane here; paths `src/osd/manifest.py`, `src/osd/build.py`,
`src/osd/verify.py`, `src/osd/cli.py` (`--fidelity-from`, status coverage), `schema/manifest.
schema.json` (manifest/3, announced), `schema/fidelity.schema.json` (new), `schema/verification.
schema.json` only if the `canonical-conversion` check needs a field (announce), `tests/test_fidelity.py`,
`tests/test_manifest.py`, `tests/test_build.py`, `tests/fixtures/fidelity/**`,
`docs/program/evidence/e09/**`. Depends on E06, E07 slice 1 (merged). The Ophiolite lane depends
on E85 (merged) and, for rights, E35.

**Evidence to inspect.** The round-trip test output; the fidelity fixture and its `osd status`
line; the rejection reasons; `records.json` `catalog` on the published site after merge.

**Dispositions of the Codex round (23 Oct).** Accepted: reader exists and reads files only
(context corrected); Ophiolite facts verified from the Ophiolite program file and the E35 gap
stated; F3 removed, offline LAS fixture and Norne used; manifest is the sole input, STAC-address
intake out; rights mapping complete with every state and `attribution`, `unknown` grants nothing;
fidelity is a structured document bound to input hashes (design 4) and the catalogue derives the
summary; L4 computed by `level_from_checks` with own L1–L3 retained, stale or mismatched evidence
rejected, coverage defined (design 5); snapshot identity binds source commit, verification commit
and a records digest (design 2); identity per entry is collection + asset key + checksum, Item id
only where established; ownership extended to the CLI and schemas with announced versions;
acceptance rewritten with distinct values, exact absence, an allowed-publication control (in the
Ophiolite half), rejection reasons and mutations; E06 contract reused, E12 and E10 boundaries kept.
Refuted: none.
