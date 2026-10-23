# E02 strategy: verifier to L2

Charter: `E02-verifier-to-L2.md` (Kernel). Base: main e58e2f5. Gate: `make check`, offline.

## Shape

```
records/*.yaml ──► osd verify ─┬─ probe origin.url (Fetcher: 16 KB GET, retry once on transient)
                               │     classify: ok | blocked | moved → L1 pass ; dead → L1 fail
                               ├─ L2 files   (Opener: streamed GET) manifest_url → listing →
                               │     verification.sample.files globs → SHA-256 per file,
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

- **Closed reachability classes**, stored in `origin.reachability`. `blocked` = HTTP 403/429 or
  a challenge-page marker in the first 16 KB (Cloudflare, Incapsula); `dead` = 404/410, DNS
  failure, and timeout/connection error/5xx after one retry; `moved` = final host differs from
  the origin host (pass, detail suggests a `known_issues` note: tools never edit records).
  429 is added to `blocked` because rate limiting is not death.
- **Allow-list** `verification.sample.files`: shell globs matched (`fnmatchcase`) against the
  entry as listed or its absolute URL. Listings understood: JSON (GitHub contents, STAC
  `href`s, lists of names), S3 `ListBucketResult` XML, HTML `<a href>`, plain text lines.
  No `manifest_url` or no `sample` → `files-checksummed` is `skip`, the record stays L1.
- **Budget** is per run (charter: "over 2 GB per run"), shared across records. A listed size
  over the remainder is cut before download; a stream that crosses it is abandoned and not
  recorded. Detail says "sample cut at 2 GB per run: k of n files".
- **Licence text** = visible text of the page (scripts, styles removed, whitespace collapsed)
  so markup churn is not a finding. A different hash than the previous run's record: outcome
  `pass`, detail "licence text changed since <previous date>".
- **Schemas**: `verification/2` adds optional `origin.reachability` and `files[].url`;
  `record/2` adds optional `verification.sample` only. v1 files still validate (test).
- **Workflow**: `verify.yml` timeout raised for hashing, and the run writes `osd status` to the
  job summary so the published levels can be compared with what the results branch holds.
- **Records** (supervisor ruling 23 Oct): `sodir/factpages`, `opm/norne`, `nopims/poseidon`
  gain `manifest_url` and `verification.sample`; nothing else in `records/` changes.

## Acceptance → test (all in `tests/test_verify.py` unless named)

| Acceptance line | Test |
|---|---|
| Four fake fetchers 200 / 403+challenge / 404 / timeout → L1 pass, L1 pass+blocked, L0, L0 | `test_classification_four_fetchers[ok,blocked,dead,timeout]` |
| Removing the retry makes the timeout test fail | `test_timeout_is_retried_once`, `test_timeout_then_ok_is_L1` (mutation M1) |
| 3-file fixture from a local directory, SHA-256 equal to `sha256sum` | `test_l2_checksums_match_sha256sum` |
| Two runs, different licence texts → "changed" detail | `test_licence_text_change_is_a_finding` |
| Published `records.json` levels = `osd status` levels on the results branch | `test_records_json_levels_equal_status_levels` (offline, same dir); evidence: the dispatched run's job summary after merge |
| Every real run's record validates against the schema | `test_verification_record_matches_schema` (now an L2 record), `test_v1_verification_record_still_validates` |
| Record schema change keeps current records valid | `test_every_current_record_validates_against_record_v2`, `test_repository_records_and_outlines_are_valid` |

## Guards → test → mutation

| Guard | Test | Mutation |
|---|---|---|
| retry once on transient | `test_timeout_is_retried_once` | M1 drop the retry |
| challenge body = blocked | `test_challenge_body_on_503_is_blocked` | M2 empty marker list |
| moved host hint | `test_moved_host_passes_with_hint` | M3 compare final URL to itself |
| DNS failure not retried, dead | `test_dns_failure_is_dead_without_retry` | M4 retry on every error |
| allow-list only | `test_only_allow_listed_files_are_hashed` | M5 match every entry |
| run byte budget | `test_sample_cut_at_byte_budget` | M6 never cut |
| robots.txt disallow | `test_robots_disallow_skips_l2` | M7 robots always allows |
| licence change finding | `test_licence_text_change_is_a_finding` | M8 ignore previous hash |
| 2 s per host pacing | `test_pacer_waits_two_seconds_per_host` | M9 pause 0 |
| UA names the repository | `test_user_agent_names_the_repository` | M10 drop the repo URL |
| no sample stays L1 | `test_no_sample_stays_L1` | M11 pass on empty sample |
| stale after 30 days | `test_stale_after_30_days` (`test_build.py` untouched; in `test_verify.py`) | M12 threshold 3000 days |

Each mutation is applied by sed, the named test is shown red, the file restored, and the result
listed in the PR body.

## Out of scope

Outlines (E03), mirrors (E07), schedules (R6), a results bucket, site rendering of "stale" (E05).
