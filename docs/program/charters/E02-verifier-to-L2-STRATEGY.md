# E02 strategy: verifier to L2

Charter: `E02-verifier-to-L2.md` (Kernel). Base: main e58e2f5. Gate: `make check`, offline.

## Shape

```
records/*.yaml ──► osd verify ─┬─ probe origin.url (Fetcher: 16 KB GET, retry once on transient)
                               │     classify: ok | moved → L1 pass ; blocked → no level ; dead → L1 fail
                               ├─ L2 files   (Opener: streamed GET) manifest_url → listing →
                               │     verifier/samples.yaml globs → SHA-256 per file,
                               │     run-wide 2 GB ByteBudget, robots.txt honoured
                               ├─ L2 licence (Opener) licence.url → visible text → SHA-256,
                               │     compared with the previous run's record in the same dir
                               └─ Pacer: one request at a time, 2 s per host after the last one
                         ──► build/verification/<id>.json (schema verification/2)
                         ──► osd build: records.json level, checked_at, stale (> 30 days)
                         ──► osd status: the same levels from the same directory
```

Everything network-shaped is injected: `Fetcher` (probe) and `Opener` (stream, raises
`FetchError`). Tests pass fakes and a directory-backed opener; `make check` stays offline.

## Decisions inside the charter's design

- **Closed, exclusive reachability classes** on the final response, stored in
  `origin.reachability`, in this order: `blocked` = HTTP 403/429 or a challenge-page marker in the
  first 16 KB at any status (Cloudflare, Incapsula): outcome `skip`, no level (OSD-D9 revised),
  `origin.blocked_since` keeps the first date of an unbroken blocked run; `ok` = 2xx/3xx on the
  origin host; `moved` = 2xx/3xx on another host (pass, detail suggests a record update: tools
  never edit records); `dead` = everything else (status 0, 401, 404, 410, other 4xx, 5xx).
  Timeouts, refused connections and 5xx are retried once; DNS failures and 4xx are not.
- **Sampling policy** is tool configuration, `src/osd/verifier/samples.yaml`, keyed by record id
  (OSD-D11); `schema/record.schema.json` is unchanged. Shell globs are matched (`fnmatchcase`)
  against each listing entry as listed or as its absolute URL. Listings understood: JSON (GitHub contents, STAC
  `href`s, lists of names), S3 `ListBucketResult` XML, HTML `<a href>`, plain text lines.
  No `manifest_url` or no sample → `skip`; no match → `fail`; any selected file failing → `fail`;
  pass needs at least one completely hashed file, and the detail states the coverage
  ("sample, not the whole dataset: k of n selected files hashed; m entries listed").
- **Budget** is per run (charter: "over 2 GB per run"), shared across records. A listed size
  over the remainder is cut before download; a stream that crosses it is abandoned and not
  recorded. Detail says "sample cut at 2 GB per run: k of n files".
- **Licence text** = visible text of the page (scripts, styles removed, whitespace collapsed)
  so markup churn is not a finding; the text (≤ 100 000 characters) is stored next to its hash.
  A different hash than the previous run's record: outcome `pass`, detail "licence text changed
  since <previous date>". No URL → `skip`; failed fetch or challenge page → `fail`.
- **Every record is validated against the schema before it is written** (`verify_all`).
- **Schema**: `verification/2` adds optional `origin.reachability`, `origin.blocked_since`,
  `files[].url` and `licence_text`. v1 files still validate (test). `records.json` gains
  `stale` and `blocked_since` for E05 to render.
- **Workflow**: `verify.yml` timeout raised for hashing, and the run writes `osd status` to the
  job summary so the published levels can be compared with what the results branch holds.
- **Records** (supervisor ruling 23 Oct): `opm/norne` and `nopims/poseidon` gain the publisher's
  listing as `origin.manifest_url` (Sodir already had one); nothing else in `records/` changes.

## Acceptance → test (all in `tests/test_verify.py` unless named)

| Acceptance line | Test |
|---|---|
| Four fake fetchers 200 / 403+challenge / 404 / timeout → L1 pass, blocked (no level, OSD-D9 revised), L0, L0 | `test_classification_four_fetchers[ok,blocked,dead,timeout]`, `test_challenge_body_is_blocked_at_any_status`, `test_every_other_status_is_dead`, `test_blocked_since_keeps_the_first_date` |
| Removing the retry makes the timeout test fail | `test_timeout_is_retried_once`, `test_timeout_then_ok_is_L1` (mutation M1) |
| 3-file fixture from a local directory, SHA-256 equal to `sha256sum` | `test_l2_checksums_match_sha256sum` |
| Two runs, different licence texts → "changed" detail | `test_licence_text_change_is_a_finding`, `test_verify_all_compares_with_the_previous_run` |
| Published `records.json` levels = `osd status` levels on the results branch | `test_records_json_levels_equal_status_levels` (offline, same dir); evidence: the dispatched run's job summary after merge |
| Every real run's record validates against the schema | `test_verify_all_never_writes_an_invalid_record`, `test_verification_record_matches_schema` (L2, timeout, blocked, cut), `test_v1_verification_record_still_validates` |
| Sampling policy outside records (OSD-D11) | `test_samples_name_records_with_a_listing`, `test_record_schema_has_no_tool_policy` |

## Guards → test → mutation

| Guard | Test | Mutation |
|---|---|---|
| retry once on transient | `test_timeout_is_retried_once` | M1 drop the retry |
| challenge body = blocked | `test_challenge_body_on_503_is_blocked` | M2 empty marker list |
| moved host hint | `test_moved_host_passes_with_hint` | M3 compare final URL to itself |
| DNS failure not retried, dead | `test_dns_failure_is_dead_without_retry` | M4 retry on every error |
| allow-list only | `test_only_allow_listed_files_are_hashed` | M5 match every entry |
| empty selection fails | `test_empty_selection_fails` | (covered by M5) |
| run byte budget | `test_sample_cut_at_byte_budget` | M6 never cut |
| robots.txt disallow | `test_robots_disallow_skips_l2` | M7 robots always allows |
| licence change finding | `test_licence_text_change_is_a_finding` | M8 ignore previous hash |
| 2 s per host pacing | `test_pacer_waits_two_seconds_per_host` | M9 pause 0 |
| UA names the repository | `test_user_agent_names_the_repository` | M10 drop the repo URL |
| no sample stays L1 | `test_no_sample_stays_L1` | M11 no sample means hash everything |
| stale after 30 days | `test_stale_after_30_days` (`test_build.py` untouched; in `test_verify.py`) | M12 threshold 3000 days |
| blocked awards no level | `test_classification_four_fetchers[blocked]` | M13 blocked passes L1 |
| blocked since first date | `test_blocked_since_keeps_the_first_date` | M14 restart every run |
| licence challenge/failure blocks L2 | `test_failed_or_absent_licence_prevents_L2` | M15 challenge page passes |
| failed file blocks L2 | `test_failed_file_fetch_prevents_L2` | M16 ignore fetch errors |
| validate before write | `test_verify_all_never_writes_an_invalid_record` | M17 no validation |
| status reads the published dir | `test_records_json_levels_equal_status_levels` | M18 status reads default dir |

Each mutation is applied by sed, the named test is shown red, the file restored, and the result
listed in the PR body.

## Out of scope

Outlines (E03), mirrors (E07), schedules (R6), a results bucket, site rendering of "stale" (E05).
