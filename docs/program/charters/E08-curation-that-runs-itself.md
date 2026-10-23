## E08 Curation that runs itself — QUEUED · Surface · no strategy

Authority: `CONTRIBUTING.md`; analogues named 23 Oct (Registry of Open Data on AWS, conda-forge).

**Outcome.** An outside contributor's record merges the same day with one human reading the
licence fields; a dead origin becomes an issue with the date it died; a visitor sees when each
record was last verified and by what.

**Context today (verified 23 Oct).** `CONTRIBUTING.md`, a PR template and a dataset issue
template exist. The `verify` workflow comments levels on records PRs. No CODEOWNERS, no dead-link
report, no status page, no outside contribution yet.

**The design the lane must map to.**
1. `CODEOWNERS`: `records/**` to the records maintainers, `schema/**` and `src/**` to the kernel
   maintainers.
2. Dead-link report: a dispatch of `verify` over all records ends with one issue per record
   that fell from L1+ to L0 since the last stored result, titled "origin dead: <id>", with the
   HTTP class and date; blocked (403) never opens an issue (OSD-D9).
3. `site/status.html`: the `osd status` table with `checked_at`, sortable, from `records.json`.
4. A "Suggest a dataset" issue is turned into a record PR by a maintainer with `osd new <url>`,
   which scaffolds the YAML from the template and the page title.
5. First outside contribution: the lane asks two named people from the Software Underground
   community to add one record each and records the elapsed time from PR open to merge.

**Acceptance.**
- Two outside PRs merged, each under 24 h from open to merge (dates in the PR descriptions).
- A fixture run where one record's fetcher returns 404 after a stored L1 opens exactly one issue
  (dry-run output in the test).
- `status.html` lists every record with level and date (screenshot).
- `osd new https://example.org/x` writes a file that fails validation only on the fields a human
  must fill (test asserts the exact problem list).

**Out of scope.** Automated licence detection, scheduled runs (R6: on demand), moderation tooling.

**Stop rules.** No outside contributor answers within a week: record it, merge the rest, leave
the acceptance line open in PROGRAM.md rather than faking a contribution.

**Ownership and dependencies.** Coding lane; paths `.github/**` (announced), `site/status.html`,
`src/osd/new.py`, `src/osd/report.py`, `tests/test_report.py`. Depends on E02 (stored results).

**Evidence to inspect.** The two PR links; the status screenshot.
