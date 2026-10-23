# E06 strategy: retrieval by manifest, slice 1 (Kernel)

Charter: `E06-retrieval-by-manifest.md` (dispositions of the Codex review at its end). Base: main
8a0803a (E04 merged, review recorded). Claim row E06 in `CLAIMS.md`. Slice 1 = schema, reader,
`osd manifest`, `osd get`. Slice 2 = the site's select mode, a separate lane after E15 releases
`site/app.js` and `tests/site/**`.

## Shape

```
build/catalog/records.json ──┐                                   manifest.json (osd.manifest/1)
build/catalog/stac/<cid>/collection.json (assets = E02 files[]) ─┼─ osd manifest <ids> ─▶  ─┐
build/catalog/stac/<cid>/items/*.json, outlines.geojson ──────────┘                          │
                                     osd.manifest.read(path) ─▶ Manifest(entries: Entry…)  ◀─┘
                                     osd get manifest.json --dest D
                                       D/<cid>/<asset key>   (temp file, sha256 while streaming, atomic rename)
                                       D/ATTRIBUTION.md      (licence objects as stated)
```

- **Format.** `format: "osd.manifest/1"`, `created`, `catalog_url`, `selection: collections | items`,
  `entries[]`. An entry: `collection_id`, `record_id`, `item_id` (item selection: the STAC Item id, or
  `null` when the feature has no Item), `feature_id` (item selection only), `title`, `origin_url`,
  `access`, `licence` (the record's licence object whole), `known_issues` (record text, verbatim),
  `assets` (STAC asset key → `{href, title, roles, file:size, file:checksum}` copied from the
  Collection), `coverage: sampled | complete` (required when assets are present; always `sampled`
  today, since E02 hashes a sample) and `unresolved` (required when `assets` is empty: why, and the
  origin page is the to-do). Item selections carry no assets: STAC Items have `assets: {}` and a
  Collection's files are not assigned to a well. A mix of Collection and Item ids is refused.
- **No credentials.** Closed objects everywhere; `href` is http(s) without userinfo and without a
  signature/token query parameter.
- **Reader.** `read(path)` validates against the schema, then returns frozen dataclasses; a
  `file:checksum` is decoded from multihash `1220<hex>` to `sha256`; any other algorithm raises
  `ManifestError` naming the asset.
- **Get.** Paths confined to `D/<cid>/`; duplicate targets refused before any request. An existing
  file is rehashed: match → `verified`, no request. Else stream to a temp file in the same
  directory, hash, compare `file:size` and sha256, then `os.replace`. Outcomes: `verified`, `fetched`
  (no checksum: never `verified`), `mismatch` (temp removed, existing file untouched, run stops,
  later assets `not-attempted`), `needs-sign-in` (401/403), `origin-dead` (other HTTP status or no
  answer; run continues). Entries without assets print as to-do lines with the origin page. Exit
  non-zero on any mismatch, needs-sign-in asset or origin-dead asset.
- **Rights.** ATTRIBUTION.md per entry: title, publisher's licence name, SPDX, url, attribution and
  redistribution as stated, `statement` verbatim when present, "no statement stated" otherwise,
  share-alike only when `share_alike: true` (absent prints "not stated"), known issues verbatim.
  Summary line per share-alike licence: "2 items require derived work to carry CC-BY-SA-4.0".

## Acceptance → tests (`tests/test_manifest.py`)

| Acceptance line (charter, as dispositioned) | Test | Mutation shown to fail |
|---|---|---|
| Manifest for two records validates | `test_manifest_for_two_records_validates` (built from a fixture catalogue by `osd.stac.write_catalog`) | — |
| Mutated manifests fail: missing licence, bad hash, unknown format, credentials in href, empty assets without `unresolved` | `test_schema_rejects[missing-licence]`, `[bad-checksum]`, `[format-2]`, `[userinfo]`, `[signed-query]`, `[no-unresolved]`, `[extra-field]` | drop `licence` from `required`; drop the href `not` pattern; drop the `if/then` |
| Typed reader; multihash → sha256; other algorithms loud | `test_read_returns_typed_entries`, `test_read_refuses_non_sha256_multihash` | accept any multihash prefix |
| Selection identity: Collection or Item, never a mix; feature without Item unresolved with its Collection | `test_item_selection_carries_no_assets`, `test_feature_without_item_is_unresolved`, `test_mixed_selection_refused`, `test_unknown_id_refused` | let item entries copy Collection assets |
| Licence object whole, unknown stays unknown | `test_licence_copied_whole` | default `share_alike` to false |
| Restriction = redistribution + known_issues | `test_known_issues_and_redistribution_carried` | drop `known_issues` |
| 3 assets: 3 fetched, 3 verified, exact bytes | `test_get_three_assets_verified` (local HTTP server, fresh dest) | — |
| Corrupt one byte: non-zero, `mismatch`, others untouched, no bad bytes on disk | `test_get_corrupt_byte_is_mismatch` | rename before the hash comparison |
| Checksum-free download reports fetched, not verified | `test_get_without_checksum_reports_fetched` | report `verified` when sha256 is None |
| Size mismatch is a mismatch | `test_get_size_mismatch` | skip the size comparison |
| Rerun after a partial failure fetches only the missing asset (counts requests) | `test_rerun_fetches_only_missing_asset` | skip existing files without rehashing → `test_rerun_repairs_truncated_and_corrupt_files` |
| Rehash before skip; truncated and corrupted files repaired | `test_rerun_repairs_truncated_and_corrupt_files` | as above |
| Paths confined to `--dest`; duplicates refused | `test_get_refuses_escaping_paths[..]`, `[/abs]`, `test_get_refuses_duplicate_targets` | drop the containment check |
| Sign-in and dead origins honest | `test_get_401_needs_sign_in_404_origin_dead` | map 401 to origin-dead |
| ATTRIBUTION.md: two supplied statements verbatim, a missing-statement case, SPDX and share-alike | `test_attribution_statements_verbatim`, `test_attribution_missing_statement_invents_nothing` | write the record title as the statement |
| CLI summary names share-alike | `test_cli_get_summary_names_share_alike` | — |
| `osd manifest` CLI writes a valid file | `test_cli_manifest_writes_valid_file` | — |
| Site: select two datasets, download, file has two items (Playwright) | **slice 2** (after E15 merges; claim update) | — |
| F3 transcript with a real origin | F3 needs registration: PR transcript uses `opm/norne` (L2, anonymous, raw.githubusercontent.com); F3 shows as a to-do line | — |

## Commits

1. Strategy + charter dispositions. 2. Schema + reader + `osd manifest` with tests. 3. `osd get`
with tests. 4. Evidence: the real-origin transcript in `docs/program/evidence/e06/`.
