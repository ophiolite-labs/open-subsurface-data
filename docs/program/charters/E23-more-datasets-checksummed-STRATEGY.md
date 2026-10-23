# E23 strategy: more datasets checksummed

Charter: `E23-more-datasets-checksummed.md` (Kernel; Codex round done, dispositions in the charter).
Base: main 085a7de. Gate: `make check`, offline. Fixtures: `tests/fixtures/listings/` (README: URL, date).

## Shape

```
manifest_url ──► opener ──► read_listing(body, base, content_type) ──► Listing(shape, entries, listed_at)
                              │ JSON: ckan · socrata · data.gov.tw · arcgis-layer · zenodo · figshare ·
                              │       dataverse · github-release · datacite · json:api (dane) · json (E02 walk)
                              │ HTML: arcgis-layer page · directory index · html (E02 links)
                              │ XML: s3 · text: lines · anything else: ListingError "not recognised (…)"
                              ▼
 samples.yaml globs (or a sentence: why nothing is sampled) ──► picked entries
                              ▼
 _digest(stream, share, algos) ─► sha256 (+ publisher's md5/sha1/sha256 from the same stream)
                              │   generated export: watches "exceededTransferLimit": true → partial
                              ▼
 files[] {path,url,bytes,sha256,publisher_checksum?,compared?}   partial_exports[] {…, partial: true}
                              ▼
 files-checksummed / licence-text-captured detail ──► osd status reason column (first L2 check not passed)
```

`parse_listing(body, base)` stays as the E07 entry point and returns `read_listing(...).entries`.

## Decisions inside the charter's design

- **Selection by shape**: a reader is chosen by structure (JSON keys, HTML title/markers, XML root),
  never by host. Each structured reader returns assets only: CKAN resources minus service/page formats
  (WFS, WMS, WMTS, WCS, API…, HTML, ArcGIS/ESRI REST), Socrata one `rows.csv?accessType=DOWNLOAD`,
  data.gov.tw `distribution[].resourceDownloadUrl`, ArcGIS one bounded `query` export, Zenodo
  `files[].links.self`, figshare `files[].download_url` minus link-only, Dataverse
  `/api/access/datafile/<id>` minus restricted, GitHub release `assets[]` (never zipball/tarball),
  DataCite `contentUrl` only (landing `url` excluded), JSON:API resources with a `file_url` only.
  Error bodies (`success: false`, ArcGIS `error`) raise `ListingError` with the publisher's message.
- **Checksums**: stated as `alg:hex`, `{type|algorithm, value|digest}` or bare hex (32/40/64 hex digits
  are md5/sha1/sha256, unambiguous among the supported three). Recorded verbatim; `compared` is true
  only for a supported algorithm with a well-formed digest. Mismatch fails the check, both digests named.
- **Partial exports** go to `partial_exports`, a top-level array, never to `files`: every consumer of
  `files` (STAC assets, mirror eligibility, E127 fidelity) stays outside this claim and safe by structure.
- **Per-record share** of the run budget (512 MiB), drawn from the 2 GiB run budget; the sample and the
  E07 inventory draw from the same share. A listed size over the share is "would exceed".
- **Unsampled sentence**: a `samples.yaml` value may be a string saying why the listing has nothing to
  hash; it is the reason `osd status` prints (skip, no level).
- **verification/4**: `$defs/file` gains `publisher_checksum {algorithm, digest}`, `compared`, `partial`;
  top-level `partial_exports`. `inventory` byte-identical to /3. /3 frozen in `tests/fixtures/schema/`.

## Acceptance → test (`tests/test_verify.py` unless named)

| Acceptance line | Test |
|---|---|
| D1 readers: exact URLs, names, sizes, excluded links per shape | `test_reader_selects_assets_only[<shape>]` (13 shapes), `test_reader_names_no_files[<shape>]` (kigam, jamstec, pgi, gsq, datacite), `test_reader_is_chosen_by_shape_not_host`, `test_error_bodies_are_not_listings`, `test_unrecognised_listing_names_content_type_and_first_bytes` |
| D1 export: bounded, dated, truncation partial | `test_arcgis_export_is_bounded_by_max_record_count`, `test_truncated_export_is_partial_never_a_file`, `test_complete_export_is_a_file`, `test_listing_date_in_coverage` |
| D2 checksums: five cases with values, outcome, level | `test_publisher_checksum[match,mismatch,absent,malformed,unsupported]`, `test_publisher_checksum_algorithms[md5,sha1,sha256]`, `test_stated_checksum_forms` |
| D3 compatibility | `test_verification_4_identity`, `test_frozen_3_is_main_085a7de`, `test_stored_3_results_validate_against_4`, `test_fixture_verifications_validate_against_4`, `test_inventory_keeps_e07_meaning`, `test_verification_record_matches_schema` (extended) |
| D4 policy coverage | `test_every_manifest_url_record_has_a_sample_policy`, `test_samples_name_records_with_a_listing` (both directions), `test_unsampled_sentence_is_the_reason` |
| D5 reasons | `test_l2_reason_texts[<cause>]` (7 causes), `test_status_prints_each_records_own_reason`, `test_status_has_no_reason_at_L2` |
| D6 guards, mirror | `test_robots_disallow_skips_l2` (opener records every URL), `test_cut_sample_leaves_no_partial_file`, `test_sample_and_inventory_share_one_budget`, `test_record_share_of_the_run_budget`; `tests/test_mirror.py`: `test_mirror_selection_unchanged_through_readers`, `test_mirror_inventory_reads_ckan_assets_only` |
| D7 dispatched run, `make check`, `check-full`, status column, no record changed | PR body (run link, per-record outcome, status paste); `git diff --stat main -- records` empty |

## Guards → mutation (each shown red on the unchanged suite, restored, listed in the PR)

| # | Mutation | Red test |
|---|---|---|
| M1 | CKAN reader also returns the package landing `url` | `test_reader_selects_assets_only[ckan-ar]` |
| M2 | CKAN service-format exclusion dropped | `…[ckan-wa]` |
| M3 | reader chosen by base host instead of body | `test_reader_is_chosen_by_shape_not_host` |
| M4 | `exceededTransferLimit` not watched | `test_truncated_export_is_partial_never_a_file` |
| M5 | export count not bounded by `maxRecordCount` | `test_arcgis_export_is_bounded_by_max_record_count` |
| M6 | publisher digest never compared | `test_publisher_checksum[mismatch]` |
| M7 | unsupported algorithm compared as sha256 | `test_publisher_checksum[unsupported]` |
| M8 | error body falls through to the generic JSON walk | `test_error_bodies_are_not_listings` |
| M9 | unrecognised body read as text lines | `test_unrecognised_listing_names_content_type_and_first_bytes` |
| M10 | status reason a constant | `test_status_prints_each_records_own_reason` |
| M11 | status reads only the files check (licence reason dropped) | same |
| M12 | one entry removed from `samples.yaml` | `test_every_manifest_url_record_has_a_sample_policy` |
| M13 | inventory given a fresh budget | `test_sample_and_inventory_share_one_budget` |
| M14 | per-record share ignored | `test_record_share_of_the_run_budget` |
| M15 | listing fetched before the robots check | `test_robots_disallow_skips_l2` |
| M16 | abandoned stream recorded as a file | `test_cut_sample_leaves_no_partial_file` |
| M17 | `compared` removed from /4 file entries | `test_verification_record_matches_schema` |
| M18 | GitHub contents walk changed (mirror selection) | `test_mirror_selection_unchanged_through_readers` |
| M19 | unread robots.txt reported as a disallow (added after the dispatched run) | `test_unreadable_robots_is_not_called_a_disallow` |

## Out of scope

Records (E22 holds `records/**`), `mirror.py`, `stac.py`, site rendering of the reason, a figshare host.
