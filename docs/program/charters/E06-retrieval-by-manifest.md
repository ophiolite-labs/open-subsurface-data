## E06 Retrieval by manifest — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: owner direction 23 Oct ("the bridge to transfer/select assets from a map to a
retrieval"); Ophiolite exchange doctrine (intentional get, nothing applies itself).

**Outcome.** A person selects datasets or wellbores on the map, downloads one manifest, and
`osd get manifest.json` fetches the files from their origins (or mirrors, E07), verifies the
checksums the catalogue knows, and writes the attribution lines the licences require next to
the files. A Python reader opens the manifest without the CLI.

**Context today (verified 23 Oct).** No manifest format, no fetcher. The detail panel's third
card says retrieval is chartered. Records carry `origin.url` only; file-level addresses arrive
with E02's `files[]` and E04's item assets.

**The design the lane must map to.**
1. `osd.manifest/1`: JSON with `created`, `catalog_url`, `items[]` each `{item_id, record_id,
   assets[]: {href, bytes?, sha256?}, licence: {name, spdx, statement, share_alike}}`. Schema at
   `schema/manifest.schema.json`. No credentials, ever.
2. Site: a "Select" mode adds items to a basket; "Download manifest" writes the file client
   side. Items without resolvable assets (access `registration`/`request`) are included with
   `assets: []` and the origin page, so the manifest is also the to-do list.
3. `osd get <manifest> --dest <dir>`: streams each asset, verifies `sha256` when present, writes
   `ATTRIBUTION.md` from the licence statements, refuses to continue on a mismatch, resumes on
   rerun. Honest outcome per asset: fetched, verified, mismatch, needs-sign-in, origin-dead.
4. `osd.manifest.read(path)` in `src/osd/manifest.py` returns typed items; this is the interface
   Ophiolite's intake reads (E09).
5. Rights carried: every item's `licence.statement` is copied verbatim; `share_alike` is
   surfaced in the CLI summary ("2 items require derived work to carry CC BY-SA 4.0").

**Acceptance.**
- A manifest for two records validates against the schema; a mutated one (missing `licence`) fails.
- `osd get` on a fixture served locally with 3 assets: 3 fetched, 3 verified; corrupt one byte of
  one asset: exit non-zero, outcome `mismatch` for that asset, the other two untouched.
- `ATTRIBUTION.md` contains the F3 statement verbatim and names CC-BY-SA-4.0 as share-alike.
- Site: select two datasets, download, the file has two items (Playwright).
- Rerun after a partial failure fetches only the missing asset (test counts requests).

**Out of scope.** Mirrors (E07), seismic slices (E10), authentication to publisher portals,
decoding any file format.

**Stop rules.** A publisher's terms forbid automated download: that record's items get
`assets: []` and a note; continue.

**Ownership and dependencies.** Coding lane; paths `src/osd/manifest.py`, `src/osd/get.py`,
`src/osd/cli.py`, `schema/manifest.schema.json`, `site/app.js` (select mode only, claimed after
E05 merges), `tests/test_manifest.py`. Depends on E04 (item ids and assets).

**Evidence to inspect.** The strategy's test map; a terminal transcript of `osd get` on F3 with a
real origin, in the PR.
