## E35 Whole layers for the verifier — CHARTERED · Kernel · strategy at lane open · one Codex round

Authority: owner direction 23 Oct 2026 (levels on the map are real); E23 (listing readers by shape;
a generated export the server truncates is a partial export, not a hashed file,
`src/osd/verify.py:25`, `:494-498`); E29 (the ArcGIS adapter: paging by object id, identity
checks, the 50,000-feature cap, `src/osd/outlines/extractors.py:185-316`); H2 (shards by origin
host; the 2 GiB budget per process); OSD-D9, OSD-D11, OSD-D20.

**Outcome.** The registers whose publishers serve their data as an ArcGIS layer reach L2 the way a
register with a downloadable file does: the verifier fetches the whole layer, not the first page,
and the same layer on two days with no edits gives the same checksum.

**Context (main dd5f549, 24 Oct).** 23 records have an ArcGIS layer as `manifest_url` (list in
`docs/program/evidence/e35/candidates.md`). The listing reader turns a layer into one generated
entry, `query?where=1=1&outFields=*&f=geojson&resultRecordCount=<maxRecordCount>`
(`src/osd/verifier/listings.py:123-136`, `:253-261`). For any layer larger than
`maxRecordCount` the server answers `exceededTransferLimit: true`, the export is kept under
`partial_exports`, and `files-checksummed` skips, so those records stop at L1 (Virginia, BCER,
SGC, Utah, North Dakota, the SK MER and PGI registers among them). E29's adapter already pages a
layer by object id with count and identity checks for outlines; the verifier does not use it.

**The design the lane must map to.**
1. A whole-layer export. For a listing of shape `arcgis-layer`, the verifier assembles the layer
   by object id pages with E29's paging and checks (count equals `returnCountOnly`, no duplicate
   or missing ids, page errors refuse), imported from `src/osd/outlines/`, not copied, and not
   modified there. Layers above E29's cap stay a partial export as today, said in the detail.
2. Canonical bytes. The hashed object is the layer's features as GeoJSON, sorted by object id,
   written with sorted keys and no whitespace, coordinates as the server returned them (no
   rounding, no reprojection), plus the layer's `editingInfo.lastEditDate` when stated. The
   SHA-256 of those bytes is the file's checksum; the entry's detail names it "assembled layer
   export (N features, canonical GeoJSON)". The server's bytes are not hashed.
3. Pacing and budget. Pages go through the existing opener, robots check and 2 s pause per host;
   the assembled bytes count against the record's share of the 2 GiB budget; a layer that would
   exceed it is abandoned as today's budget rule says.
4. Nothing else changes: other listing shapes, the levels' rules, the record schema, the
   verification schema (a new `assembled: true` key on a file entry is allowed only if the
   verification schema already permits extra keys; otherwise the strategy names the minor bump).

**Acceptance.**
- Fixture tests in a new `tests/test_whole_layers.py`: a layer of three pages assembles to the exact
  object-id set; the same features served in another page order give the same SHA-256; a changed
  attribute gives another; a missing page, a duplicate id, a count mismatch and a page error each
  fail `files-checksummed` with the reason; a layer above the cap stays partial. Mutations
  recorded: sort removed (page-order test red), count check removed (count test red), cap removed
  (cap test red).
- `make check` green, its duration stated; no other test module edited.
- An explicit-id `verify.yml` dispatch on the branch over the 23 candidates: per record the level,
  feature count, bytes and checksum, or the first failing check; a second dispatch the next hour:
  equal checksums for every layer whose `lastEditDate` did not change (a changed one named).
- The records that reach L2 are named in the PR; a record that does not is named with its reason.

**Out of scope.** Other server types (WFS, OGC API Features); layers above the cap; mirroring;
changing E29's outlines code; records edits.

**Stop rules.** If two dispatches an hour apart give different checksums for an unedited layer on
most candidates (servers that reorder or reformat coordinates), stop after design 1, record the
measurements, and name the canonicalisation question.

**Ownership and dependencies.** Coding lane, beside E32 (disjoint paths). Paths:
`src/osd/verifier/listings.py` (the ArcGIS reader), `src/osd/verify.py` (`check_files` for an
assembled entry only), a new `src/osd/verifier/layers.py`, `tests/test_whole_layers.py` (new),
`tests/fixtures/whole_layers/**` (new), `schema/verification.schema.json` only if design 4 needs
the bump (named in the PR title), `docs/program/evidence/e35/**`. Not touched:
`src/osd/outlines/**`, `records/**`, E32's paths.

**Evidence to inspect.** The two branch dispatches with per-record checksums; the mutation record;
the PR's list of records at L2.
