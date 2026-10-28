# Starter packs

One JSON document per starter pack, `starters/<record id with / as __>__<pack>.json`, against
`schema/starter.schema.json` (osd.starter/1), with its fidelity record at
`starters/fidelity/<the same file name>` (osd.fidelity/1). Both are written by the recipe run the
pack names and committed here (OSD-D12); nobody writes or edits them by hand (family rule R-T1: a
wrong pack is withdrawn and rebuilt, never patched).

What `osd validate` and `osd build` hold a pack to (`src/osd/starters.py`, charter E40 design 4):

- (a) the live schema;
- (b) every input is a held file of the pack's record: a file of its latest verification with that
  `verifier_run`, or a held custody/2 `deposit` document with that key; name, size and digest agree;
  a tombstone or another record's file refuses;
- (c) every `derived` entry comes `from` an input;
- (d) the licence is computed from the inputs: every input `allowed`; name, spdx, url, statement
  and terms agree across inputs; attribution `required` when any input requires it; share-alike
  when any input has it; `sources[]` carries each input's licence whole;
- (e) the decision log has every topic its `contents` need, per object, and never two values for one;
- (f) every artefact is a held custody/2 `derived` document of this pack, size and digest agreeing;
- (g) every target's `import` is one of its artefacts;
- (h) the fidelity record covers exactly the pack's inputs, every result converted or partial, every
  output a `contents` kind;
- (i) every oracle compared values and found no difference, or the pack says `unpublished: true`.

(b) and (f) need the latest verifications and the custody documents, which arrive in the Pages
build from `verification-results`; where they are absent `osd validate` says "unchecked here" and
`osd build` publishes nothing it could not check.

The build publishes the valid packs whole in `build/catalog/starters.json` (with the record's
title and level, and each artefact's mirror address), lists their ids in the record's `starters`
in `records.json`, and copies each pack document and fidelity record to `build/catalog/starters/`.
`osd manifest --starter <pack id>` writes the manifest `osd get` fetches a pack with.

## Checking one document (Ophiolite E129)

A recipe checks the pack it wrote, wherever it is on disk, with the same function:

```sh
uv run osd validate path/to/<record id with / as __>__<pack>.json \
    --vdir build/verification --custody build/mirror/custody
```

Exit 0: no problem (lines starting `unchecked here:` name what this checkout could not check, never a
pass); exit 1: each problem printed. The fidelity path resolves against the document's directory; the
file-name rule applies only to documents inside `starters/`. A pack written before its upload says
`unpublished: true` and may carry artefacts without `key`; a published pack needs every key.
