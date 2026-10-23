# H1 strategy: origins that recover, origins that hide, files as listings, unreadable robots

Charter: `H1-origins-that-recover-and-origins-that-hide.md` (designs 1 to 9). Base: main 19b7625.
Every acceptance line maps to named tests below; every guard has one mutation, shown red against
the unchanged suite and restored (the PR lists them).

## Shape of the change

```
verify.yml report step (env only, no ${{ }} in the script)
  gh issue list --label origin-dead --json number,title,labels > open-issues.json  (failure: empty file)
  osd report --open-issues open-issues.json --verified "${IDS:-all}" --run-url URL --out report.json [--dry-run]
      report.py  dead_reports()  -> open[]       (fell from L1+ to dead; exact title not already open)
                 recovered()     -> recovered[]  (open issue by number AND verified this run AND now >= L1)
                 issues unreadable -> both lists empty, the report says "no issue opened or closed"
  [ -z "$dry" ] && jq '.open[]'      -> gh issue create --label origin-dead
                   jq '.recovered[]' -> gh issue close <number> --comment <run, level, checked_at, HTTP>

verify.py  verify_record(..., browser_probe=None)
  probe() (one retry for 5xx/timeout) -> classify() -> dead with 404/410/5xx?
      -> browser_probe(url) once, paced like every request -> 2xx: blocked,
         "answers a browser, not the verifier (HTTP a to osd-verifier, HTTP b to a browser agent)"
  http_browser_probe: GET with BROWSER_USER_AGENT, response closed unread (errors too)
  check_files: manifest response with a file content type / attachment / samples.yaml {file: true}
      -> Listing("file", [Entry(manifest)]), the already-open stream is hashed (one GET)
  _Robots: 5xx/no answer -> "robots.txt unreadable (HTTP 500), treated as disallow (RFC 9309 2.3.1.4)"
```

Recovery is computed apart from the "fell from L1+" loop, so a record stored at L0 that answers
again is still recovered. The origin `http_status` stays the verifier's answer; the browser status
lives only in the check detail (verification/4 unchanged). `samples.yaml` gains one form,
`id: {file: true, sample: [globs]}` (sample defaults to `["*"]`); entries stay E24's.

## Acceptance to tests

| Acceptance line (charter) | Tests (`tests/test_report.py` R, `tests/test_verify.py` V) | Mutation it catches |
|---|---|---|
| D1 recovered only with an open issue, exact title and label | R `test_recovered_needs_an_open_issue_with_the_exact_title_and_label` | title/label match dropped |
| D1 verified this run | R `test_retained_result_not_verified_this_run_is_not_recovered` | verified ids ignored |
| D1 now at L1+ (dead, blocked negatives) | R `test_dead_or_blocked_is_not_recovered` | level test dropped |
| D1 record absent | R `test_record_absent_is_not_recovered` | absent result treated as L1 |
| D1 L0 then L1 counts | R `test_previous_L0_now_L1_counts_as_recovered` | recovery behind the fell-from-L1+ skip |
| D1 enumeration failure: no mutation | R `test_issue_enumeration_failure_mutates_nothing` | unreadable list read as "none open" |
| D2 `--out` object, workflow reads `.open[]` and `.recovered[]` | R `test_workflow_consumes_open_and_recovered` (runs the step's own script with a fake `gh`, real `jq`) | workflow reads the old array |
| D2 dry run mutates nothing | R `test_dry_run_mutates_nothing` (PR and non-main dispatch) | dry guard removed from the step |
| D3 close by number with run, level, checked_at, HTTP | R `test_recovered_closes_by_number_with_the_run_named` | comment loses the run / close by title |
| D3 idempotent over two runs | R `test_two_runs_against_one_issue_state_mutate_once` | open dedupe by open issues removed |
| D4 retry recovery, no browser | V `test_503_then_200_is_L1_without_browser_probe` | browser probe before the retry |
| D4 terminal 404/410/5xx answered to a browser is blocked, both statuses | V `test_terminal_dead_answering_a_browser_is_blocked` | probe never consulted |
| D4 never after other answers | V `test_browser_probe_only_after_404_410_5xx` | probe on every dead |
| D4 browser failure leaves dead | V `test_browser_failure_leaves_dead` | any status below 400 accepted |
| D4 redirect to 2xx counts | V `test_browser_redirect_to_2xx_counts` | final URL host compared |
| D4 challenge after 404 stays the challenge | V `test_challenge_after_404_is_blocked_without_browser_probe` | browser consulted on a challenge |
| D4 body never read | V `test_browser_probe_never_reads_a_body` | `.read()` added |
| D4 browser agent never on content | V `test_browser_agent_only_on_the_origin_request` (urlopen request log) | `http_open` sends the browser agent |
| D4 paced | V `test_browser_probe_is_paced` | probe unpaced |
| D5 verify prints detail; status reason for blocked | V `test_cli_verify_prints_the_origin_detail`, `test_status_reason_names_why_blocked` | detail dropped from either |
| D8 content type / attachment / `file: true` | V `test_file_manifest_is_the_one_entry[content-type, attachment, file-flag]` | each rule removed |
| D8 CSV as `text/csv` is a file | V `test_csv_manifest_is_a_file_not_a_url_list` | "CSV rows read as URLs" |
| D8 streamed once, under the budget | V `test_file_manifest_is_fetched_once`, `test_file_manifest_over_budget_is_not_hashed` | second GET / budget ignored |
| D9 5xx robots wording, 404 allows | V `test_robots_5xx_is_unreadable_and_treated_as_disallow[500,503]`, `test_robots_404_allows`; E23's `test_unreadable_robots_is_not_called_a_disallow` gets the new wording | 5xx allowed / wording |
| Branch run: NM OCD, PA DEP, ODNR blocked with both statuses | `gh workflow run verify.yml --ref h1-...` once; run linked in the PR | publisher outcome, not a gate |
| After merge, first main dispatch closes recovered #17, #23-#27 | the PR names the run's outcome; offline proof is D3's tests | — |
| `make check` green; verification/4 unchanged | gate; `test_verification_4_identity` untouched | — |

## Order of commits

1. Strategy (this file).
2. Origin-dead issues close on recovery: `report.py`, `cli.py` report, `verify.yml`, R tests.
3. Publishers that hide from the verifier are blocked: `verify.py` probe, `cli.py` verify/status,
   V probe tests, OSD-D20.
4. A manifest that is a file is its own listing; unreadable robots named: `verify.py`
   `check_files`/`_Robots`, `listings.py`, `samples.yaml` header, V tests.
5. Evidence: `docs/program/evidence/h1/mutations.md`, the branch run's outcome.

No records, no `samples.yaml` entries, no schema change.
