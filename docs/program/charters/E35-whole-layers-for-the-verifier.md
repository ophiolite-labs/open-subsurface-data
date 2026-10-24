## E35 Whole layers for the verifier — CHARTERED · Kernel · strategy at lane open · Codex round closed (REWORK, reworked 24 Oct)

Authority: owner direction 23 Oct 2026 (levels on the map are real); E23 (listing readers by shape;
a generated export the server truncates is a partial export, `src/osd/verify.py:25`, `:495-503`);
E29 (ArcGIS paging by object-id offsets, duplicate and count checks, the 50,000 cap and the
200-page cap, `src/osd/outlines/__init__.py:147-149`, `extractors.py:254, 345-352`); E06 and E07
(STAC assets carry each file's digest and `osd get` hashes the downloaded bytes,
`src/osd/stac.py:100`, `src/osd/get.py:95`); H2 (shards by origin host); OSD-D9, OSD-D11, OSD-D20;
`docs/ENGINEERING.md` (no artificial schedule).

**Outcome.** The registers whose publishers serve their data as an ArcGIS layer reach L2 on evidence
of the whole layer, not its first page, and the same unedited layer gives the same checksum on the
next run; nothing a person downloads changes.

**Context (main 70a9de0, 24 Oct).** 22 records have an ArcGIS layer as `manifest_url`
(`docs/program/evidence/e35/candidates.md`; `al-ogb/wells` is a zip and is not one). The listing
reader turns a layer into one generated query entry (`src/osd/verifier/listings.py:123-136`,
`:253-261`) that `check_files` hashes directly (`verify.py:480`). A server that flags
`exceededTransferLimit` gets a partial export and `files-checksummed` skips; a server that
truncates without the flag is not detected today. E29's evidence (`docs/program/evidence/e29/results.md`)
records the five large registers at L1 on 23 Oct; the lane re-measures. File entries in
`schema/verification.schema.json` forbid extra keys (line 64).

**The design the lane must map to.**
1. Evidence, not a file. A whole-layer check writes a new verification member `layer_exports`
   (one entry per layer: layer URL, feature count, `returnCountOnly`, bytes, SHA-256, format,
   the edit date read before and after paging), never an entry in `files`. STAC assets,
   `osd get`, manifests and the mirror do not see it. This is verification/5; verification/4 is
   frozen under `tests/fixtures/schema/` and old files keep validating.
2. Paging. One shared paging function in `src/osd/outlines/` (extracted from E29's, E29's outline
   behaviour and tests unchanged) pages a layer by object-id offsets with its checks; the verifier
   calls it requesting all fields (`outFields=*`), native Esri JSON (`f=json`), so nothing is
   reprojected. The expected id set is read independently (`returnIdsOnly=true`) and the assembled
   ids must equal it exactly.
3. Canonical bytes. Features sorted by object id, keys sorted, no whitespace, coordinates and
   attributes as the server returned them; the format is named `esri-json`.
4. Snapshot consistency. `editingInfo.lastEditDate` read before and after paging; a change makes
   the check incomplete for that layer (skip, said why). A layer that states no edit date passes
   with "stability unknown" in the detail.
5. Budget and pacing. Each page is read through the existing opener, robots check and 2 s pause
   per host, bounded by the record's 512 MiB share before decoding; an abandoned read counts.
   Layers above 50,000 features stay a partial export, said in the detail.
6. `files-checksummed` passes for an ArcGIS-listed record when its layer export is complete and
   consistent; the detail names it "whole layer checked (N features, esri-json), not a downloadable
   file".

**Acceptance.**
- Fixture tests in `tests/test_whole_layers.py` (new): pages served in shuffled order with features
  shuffled within pages give identical canonical bytes (exact bytes asserted); a changed attribute,
  a null geometry and a moved coordinate each change the digest; the assembled id set equals
  `returnIdsOnly`. Failing cases, each with its own fixture and reason: duplicate id; page error
  (HTTP and `error` JSON); a full first page and an oversized final page with unique ids (count
  guard alone); a layer above 50,000 with a page size that keeps it under the 200-page cap (feature
  cap reason); an edit date that changes during paging; a page over the budget share (injected
  opener); robots disallow. Mutations, each recorded red: sort removed; count guard removed; feature
  cap removed; duplicate check removed; page-error check removed; robots check bypassed; pacing
  removed (injected clock); budget bound removed; a layer export written into `files` (the STAC
  asset test red).
- Schema: verification/5 validates new files; every verification/4 fixture still validates; the
  build reads both.
- `make check` under 120 s on the PR's CI run, stated.
- Branch evidence: an explicit-id `verify.yml` dispatch over the 22 candidates (per record: level,
  features, bytes, checksum, or first failing check), then a second dispatch when the first
  completes: equal checksums for every layer whose edit date did not change. The multi-page
  candidates under the cap (the strategy lists them from the day's `returnCountOnly`) must each pass
  or carry outage evidence; any other failure leaves the outcome reported incomplete for that
  record.

**Out of scope.** Other server types; layers above the cap; publishing the assembled layer as a
downloadable asset (E06/E07 would need a charter); records edits.

**Stop rules.** If the second dispatch disagrees for an unedited layer, that candidate is incomplete
and the lane continues with the rest; if most disagree, stop after designs 1 and 2 and name the
canonicalisation question.

**Ownership and dependencies.** Coding lane, beside E36 (disjoint paths). Paths:
`src/osd/verifier/listings.py` (ArcGIS reader), `src/osd/verify.py` (`check_files` and the
`layer_exports` member), `src/osd/verifier/layers.py` (new), `src/osd/outlines/__init__.py` and
`src/osd/outlines/extractors.py` (the shared paging extraction only), `schema/verification.schema.json`
(verification/5, named in the PR title), `tests/fixtures/schema/verification-4.schema.json` (new),
`tests/test_whole_layers.py` (new), `tests/fixtures/whole_layers/**` (new), `tests/test_schema.py`
(the version test), `docs/program/evidence/e35/**`. Not touched: `src/osd/stac.py`,
`src/osd/get.py`, `src/osd/manifest.py`, `src/osd/mirror.py`, `records/**`, E36's paths.

**Evidence to inspect.** The two dispatches with per-record checksums; the mutation record; the
records at L2 named in the PR.

### Dispositions (Codex round 24 Oct, REWORK; one round, OSD-D8)

| # | Finding | Disposition |
|---|---|---|
| 1 | 22 candidates; al-ogb is a zip | Accepted; list corrected |
| 2 | Unflagged truncation not detected | Accepted; stated in Context; design 2's id-set equality catches it for the new path |
| 3 | L1 outcomes are historical | Accepted; cited as E29 evidence, lane re-measures |
| 4 | E29 pages by offset; checks do not prove the id set | Accepted; independent `returnIdsOnly` set, exact equality |
| 5 | File entries forbid extra keys | Accepted; verification/5 with a new member, old files validated |
| 6 | Assembled digest on the query URL breaks retrieval | Accepted; `layer_exports` evidence, never in `files`; asset-exclusion mutation |
| 7 | E29 interface cannot return a lossless layer | Accepted; shared paging extraction in `outlines/`, claimed, E29 behaviour preserved |
| 8 | GeoJSON vs native coordinates | Accepted; native Esri JSON named `esri-json` |
| 9 | Snapshot consistency | Accepted; edit date before and after; absent means stability unknown |
| 10 | Budget applied too late | Accepted; per-page bound before decoding, abandoned reads count, injected-opener test |
| 11 | "Next hour" is an artificial schedule | Accepted; second dispatch when the first completes |
| 12 | Stop rule only when most disagree | Accepted; each disagreeing candidate incomplete, stop if most |
| 13 | Every candidate may fail with a reason | Accepted; named multi-page candidates must pass or show outage evidence |
| 14 | Sort mutation can stay green | Accepted; shuffle within pages, exact bytes |
| 15 | Count mutation masked by short page | Accepted; isolated fixture |
| 16 | Cap mutation masked by page cap | Accepted; page size under the 200-page cap |
| 17 | Only three mutations | Accepted; nine listed |
| 18 | Attributes, nulls, coordinates must move the digest | Accepted; three tests |
| 19 | Duration without a bound; schema old-file test | Accepted; under 120 s; verification/4 fixtures validate |
| 20 | E06/E07 overlap | Accepted; no downloadable asset, out of scope |
| 21 | E29 code ownership | Accepted; shared extraction claimed |
| 22 | E32 owns stac.py/manifest.py | Accepted; E32 merged; E35 does not touch them |
