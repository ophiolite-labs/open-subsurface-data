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

## Dispositions (Codex review `E06-retrieval-by-manifest-CODEX-REVIEW.md`, verdict REWORK)

Supervisor rulings 23 Oct, all accepted; slice 1 (schema, reader, `osd manifest`, `osd get`) maps
them in `E06-retrieval-by-manifest-STRATEGY.md`. Where the design above and this table differ,
this table rules.

| # | Finding | Disposition |
|---|---|---|
| 2.1 | "E04's item assets" is false; Items carry `assets: {}` | Accepted. Assets come from the Collection only; an Item selection carries `assets: {}` and an `unresolved` reason naming its Collection (`test_item_selection_carries_no_assets`). |
| 2.2 | Records carry more than `origin.url` | Accepted as context. The manifest reads the built catalogue, not record addresses; `manifest_url`/`inputs` stay verifier and outline inputs. |
| 2.3 | "No fetcher" needs qualification | Accepted. `osd get` reuses `verify.http_open`; what was missing was a manifest-driven downloader. |
| 2.4 | E02 `files[]` is verification output | Accepted (ruling 2). It reaches the manifest only through the STAC Collection assets; `coverage: sampled` is required whenever assets are present, and the CLI says "the files the verifier sampled, not the whole dataset". |
| 2.5 | Confirmed: no manifest module or `get` command | No change. |
| 2.6 | F3 fixture is stale (CC-BY-SA-3.0, registration, no statement) | Accepted (ruling 8). F3 is not a fixture. Attribution is tested with two supplied statements and a missing-statement case (`test_attribution_statements_verbatim`, `test_attribution_missing_statement_invents_nothing`); the real-origin transcript uses `opm/norne` and `nopims/poseidon` (anonymous, files hashed), with F3 in the same manifest showing as a registration to-do. |
| 3.1 | `item_id` conflates datasets and wellbores | Accepted (ruling 1). `selection: collections | items`, never a mix (`test_mixed_selection_refused`); entries carry `collection_id` always, `item_id` (STAC id or `null`) and `feature_id` in Item selections; a feature without an Item stays listed as unresolved with its Collection. |
| 3.2 | Coverage implied complete | Accepted (ruling 2). `coverage: sampled | complete`; slice 1 only writes `sampled`. |
| 3.3 | Format incomplete: version, origin, reasons | Accepted. `format: "osd.manifest/1"` (const), `origin_url`, `access`, `unresolved` required when assets are empty (schema `if/then`). |
| 3.4 | Rights loss | Accepted (ruling 3). The record's licence object is copied whole; absent `share_alike`/`statement` stay absent and print "not stated" / "none stated" (`test_licence_copied_whole`). |
| 3.5 | Parallel asset vocabulary | Accepted (ruling 4). Assets keep STAC keys and `href`, `title`, `roles`, `file:size`, `file:checksum`; `read` converts multihash `1220…` to `sha256` and raises on any other algorithm (`test_read_refuses_invalid_and_non_sha256`). |
| 3.6 | Unsafe resume | Accepted (ruling 5). Paths confined to `--dest/<collection_id>/`, duplicates refused before any request, temp file in the same directory, `os.replace` after size and hash match, existing files rehashed before skipping, checksum-free downloads report `fetched` (`test_rerun_repairs_truncated_and_corrupt_files`, `test_get_refuses_escaping_paths`, `test_get_without_checksum_reports_fetched`). |
| 3.7 | Network boundary | Accepted (ruling 6). AGENTS.md names `osd get` on main (8a0803a); tests use a local 127.0.0.1 server. |
| 3.8 | Terms enforcement undefined | Accepted (ruling 7). A restriction is carried as `licence.redistribution` plus the record's `known_issues`, verbatim; nothing is inferred from prose (`test_known_issues_and_redistribution_carried`). The stop rule above reads accordingly. |
| 4.1 | Schema test permits false positives | Accepted. Negative fixtures per guard: missing licence, bad checksum, format 2, userinfo, signed query, empty assets without reason, extra field, bad rights enum, climbing asset key (`test_schema_rejects[...]`). |
| 4.2 | Download counters permit wrong bytes | Accepted. Fresh destinations per test, exact bytes asserted, bad bytes never land, a pre-existing file survives a mismatch, temp files cleaned. |
| 4.3 | Hard-coded F3 string can pass | Accepted; see 2.6. |
| 4.4 | Site count permits duplicates | Accepted for slice 2: the Playwright test asserts exact identities, assets, rights and reasons, with a wellbore and a Collection without Items. |
| 4.5 | Resume count permits truncation | Accepted. A truncated and a corrupted file are repaired with exactly two requests. |
| 4.6 | Uncovered guards | Accepted. Typed reader, credential exclusion, checksum-free outcome, 401/403 `needs-sign-in`, 404 `origin-dead` and the CLI share-alike line each have a test and a failing mutation (`docs/program/evidence/e06/mutations.txt`). |
| 5.1 | E15 owns `site/app.js` and `tests/site/**` | Accepted (ruling 9). Select mode is slice 2, a lane opened after E15 merges, with a claim update. |
| 5.2 | Do not manufacture periods for Item ids | Accepted. Collection selection works without Items; periods stay E16's. |
| 5.3 | Mirrors E07, rights mapping E09 | Accepted. The manifest preserves their inputs and implements neither. |
