# H1 mutations

Each mutation applied alone to the code at the lane's head, the named tests run against the
unchanged suite, the code restored (`git diff` empty afterwards). Script: `uv run python docs/program/evidence/h1/mutate.py` from the repository root.

| # | Mutation | File | Test(s) | Result |
|---|---|---|---|---|
| M1 | recovery without the L1+ test | `src/osd/report.py` | `test_report.py::test_dead_or_blocked_is_not_recovered` | red: 1 failed in 0.59s |
| M2 | title and label match dropped | `src/osd/report.py` | `test_report.py::test_recovered_needs_an_open_issue_with_the_exact_title_and_label` | red: 1 failed in 3.85s |
| M3 | verified ids ignored | `src/osd/report.py` | `test_report.py::test_retained_result_not_verified_this_run_is_not_recovered` | red: 1 failed in 0.23s |
| M4 | absent result treated as reachable | `src/osd/report.py` | `test_report.py::test_record_absent_is_not_recovered` | red: 1 failed in 0.21s |
| M5 | recovery behind the fell-from-L1+ skip | `src/osd/report.py` | `test_report.py::test_previous_L0_now_L1_counts_as_recovered` | red: 1 failed in 0.24s |
| M6 | unreadable issue list read as none open | `src/osd/report.py` | `test_report.py::test_issue_enumeration_failure_mutates_nothing, test_report.py::test_failed_issue_listing_in_the_workflow_mutates_nothing` | red: 2 failed in 0.64s |
| M7 | workflow reads the old array | `.github/workflows/verify.yml` | `test_report.py::test_workflow_consumes_open_and_recovered` | red: 1 failed in 0.64s |
| M8 | workflow skips .recovered[] | `.github/workflows/verify.yml` | `test_report.py::test_workflow_consumes_open_and_recovered` | red: 1 failed in 0.57s |
| M9 | dry guard removed from the step | `.github/workflows/verify.yml` | `test_report.py::test_dry_run_mutates_nothing` | red: 2 failed in 1.11s |
| M10 | close by title, not number | `.github/workflows/verify.yml` | `test_report.py::test_workflow_consumes_open_and_recovered` | red: 1 failed in 0.60s |
| M11 | run left out of the closing comment | `src/osd/report.py` | `test_report.py::test_recovered_closes_by_number_with_the_run_named` | red: 1 failed in 0.22s |
| M12 | open dedupe by listed issues removed | `src/osd/report.py` | `test_report.py::test_two_runs_against_one_issue_state_mutate_once` | red: 1 failed in 0.99s |
| M13 | browser asked before the retry | `src/osd/verify.py` | `test_verify.py::test_503_then_200_is_L1_without_browser_probe` | red: 1 failed in 0.23s |
| M14 | browser answer not consulted | `src/osd/verify.py` | `test_verify.py::test_terminal_dead_answering_a_browser_is_blocked` | red: 4 failed in 0.30s |
| M15 | browser asked after every dead answer | `src/osd/verify.py` | `test_verify.py::test_browser_probe_only_after_404_410_5xx` | red: 4 failed, 4 passed in 0.29s |
| M16 | any browser answer below 400 accepted | `src/osd/verify.py` | `test_verify.py::test_browser_failure_leaves_dead` | red: 1 failed, 4 passed in 0.22s |
| M17 | browser's final URL held to the origin host | `src/osd/verify.py` | `test_verify.py::test_browser_redirect_to_2xx_counts` | red: 1 failed in 0.24s |
| M18 | browser asked on a challenge too | `src/osd/verify.py` | `test_verify.py::test_challenge_after_404_is_blocked_without_browser_probe` | red: 1 failed in 0.27s |
| M19 | browser probe reads its response | `src/osd/verify.py` | `test_verify.py::test_browser_probe_never_reads_a_body` | red: 1 failed in 0.27s |
| M20 | opener sends the browser agent | `src/osd/verify.py` | `test_verify.py::test_browser_agent_only_on_the_origin_request` | red: 1 failed in 0.26s |
| M21 | browser probe unpaced | `src/osd/verify.py` | `test_verify.py::test_browser_probe_is_paced` | red: 1 failed in 0.21s |
| M22 | origin detail dropped from osd verify | `src/osd/cli.py` | `test_verify.py::test_cli_verify_prints_the_origin_detail` | red: 1 failed in 0.23s |
| M23 | blocked reason dropped from osd status | `src/osd/cli.py` | `test_verify.py::test_status_reason_names_why_blocked` | red: 1 failed in 0.58s |
| M24 | content-type rule removed | `src/osd/verifier/listings.py` | `test_verify.py::test_file_manifest_is_the_one_entry[content-type]` | red: 1 failed in 0.22s |
| M25 | attachment rule removed | `src/osd/verifier/listings.py` | `test_verify.py::test_file_manifest_is_the_one_entry[attachment]` | red: 1 failed in 0.22s |
| M26 | file: true ignored | `src/osd/verify.py` | `test_verify.py::test_file_manifest_is_the_one_entry[file-flag]` | red: 1 failed in 0.25s |
| M27 | CSV rows read as URLs | `src/osd/verifier/listings.py` | `test_verify.py::test_csv_manifest_is_a_file_not_a_url_list` | red: 1 failed in 0.23s |
| M28 | file manifest opened again to hash it | `src/osd/verify.py` | `test_verify.py::test_file_manifest_is_fetched_once` | red: 1 failed in 0.24s |
| M29 | Content-Length ignored | `src/osd/verify.py` | `test_verify.py::test_file_manifest_over_budget_is_not_hashed` | red: 1 failed in 0.24s |
| M30 | 5xx robots.txt allowed | `src/osd/verify.py` | `test_verify.py::test_robots_5xx_is_unreadable_and_treated_as_disallow` | red: 2 failed in 0.30s |
| M31 | unreadable robots called a disallow | `src/osd/verify.py` | `test_verify.py::test_robots_5xx_is_unreadable_and_treated_as_disallow` | red: 2 failed in 0.26s |
| M32 | 404 robots.txt treated as unreadable | `src/osd/verify.py` | `test_verify.py::test_robots_404_allows` | red: 1 failed in 0.24s |
