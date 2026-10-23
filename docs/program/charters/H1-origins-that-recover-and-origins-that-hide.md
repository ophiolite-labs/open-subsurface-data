## H1 Origins that recover, and origins that hide from robots — QUEUED · Kernel (hardening) · one Codex round (done, REWORK; dispositions below)

Authority: E02 (verifier levels), E08 (curation that runs itself), E23 design 7 (branch dispatch);
OSD-D9 (blocked awards no level); the E22 and E23 findings in `docs/program/HANDOFF.md`.

**Outcome.** An origin-dead issue closes by itself when a run observes the origin answering again,
with the run named in the closing comment; and a publisher that answers a browser but hides from
the verifier is called `blocked`, not dead, so no false issue is opened and the map says "blocked"
as OSD-D9 means it.

**Context today (verified 23 Oct, main 1a2642c).** `osd report` (`src/osd/report.py`) compares
stored results before and after a run, selects records that fell from L1+ to dead (blocked
excluded, titles already open skipped) and the CLI's `--out` writes the issue array only
(`src/osd/cli.py` `cmd_report`); `verify.yml` creates those issues on a dispatch on main, reading
open issue titles only. Nothing closes them. Issue events: #20 (EUG) and #28, #29 (SPE) were closed
by hand on 23 Oct with the run id 39968202244 in the comment; open today with label `origin-dead`:
#17 (GEUS), #23 to #27 (the five CO2 DataShare records; co2datashare.org answered HTTP 500 from
the runner at 13:51 UTC and from the VPS). Partial runs (`verify.yml` with `ids`) keep earlier
results for records they did not verify, so a stored L1 is not always a fresh observation. The
verifier probes with its own agent, retries transient 5xx and timeouts once, classifies 403, 429
and challenge bodies (any status) as `blocked`, and the remaining non-2xx terminal results as dead.
Observed on the E22 PR run and from the VPS on 23 Oct: NM OCD and PA DEP (ArcGIS Hub) and
ohiodnr.gov answer 404 to the verifier's agent and 200 to a browser agent (evidence in
`docs/program/evidence/e22/sources.md`; verify comment on PR #30). `cmd_verify` prints the origin
status and L2/L3 details; `status` prefers the L2 reason.

**The design the lane must map to.**
1. Recovery, attributed to a fresh observation: `osd report` takes the ids this run verified (the
   workflow passes `steps.ids.outputs.ids`, "all" meaning every record) and emits `recovered`
   entries only for records that (a) have an open `origin dead: <id>` issue, (b) were verified in
   this run, and (c) now stand at L1 or above. Open issues are read as `{number, title, labels}`
   (`gh issue list --label origin-dead --json number,title,labels`); a title matches the exact
   `origin dead: <id>` form; the close is by number. If the issue enumeration fails, the report
   step makes no mutation (no open, no close) and says so.
2. Output contract: `--out` writes one object `{"open": [...], "recovered": [...]}`; the workflow
   reads `.open[]` and `.recovered[]` (both branches changed together, one test consumes the file
   the way the workflow does, `jq`-equivalent in Python). The dry run (pull request or non-main
   dispatch) prints both lists and mutates nothing; a test proves the guard by asserting that in
   dry mode the issue-mutation command list is empty.
3. Closing comment: run id, level, `checked_at`, origin HTTP status. Idempotent: a closed issue is
   not in the next run's open list, so nothing happens (two successive runs against a mocked issue
   state tested).
4. Hiding publishers: after the existing retry has produced a terminal dead result with status
   404, 410 or 5xx (never after a `blocked` classification, never after 2xx), the verifier sends
   one paced request of the same URL with a browser-like user agent through an injected probe
   (`browser_probe(url) -> (status, final_url)`, default implementation a GET whose response is
   closed without `.read()`, error responses included); the agent constant is named for what it
   is. If that answers 2xx (after redirects), the outcome is `blocked` with detail "answers a
   browser, not the verifier (HTTP <first> to osd-verifier, HTTP <second> to a browser agent)";
   the browser agent is never used for listings, licence text, inventories or any content read,
   proven by a test on the opener's request log. Headers cannot tell a 200 challenge from
   content; the detail says "answers a browser" and no more. Record as OSD-D20 in `DECISIONS.md`.
5. Evidence visibility: `cmd_verify` prints the origin check's detail (both statuses) beside the
   level; `osd status` shows it for blocked records in the reason column (claim extended to
   `cli.py` verify and status output).
6. Tests (offline, injected): recovery positives and negatives (dead, blocked, record absent,
   retained result not verified this run, previous L0 now L1 which must count as recovered and
   must not be caught by the existing "fell from L1+" early skip); workflow JSON consumption for
   open and recovered; dry-mode zero mutations; closing by number with the comment text, two-run
   idempotence against a mocked issue state; probe: ordinary retry recovery (503 then 200 stays
   L1 with no browser probe), browser probe only after terminal 404/410/5xx, both statuses and
   the final classification and level asserted, browser failure leaves dead, redirect to 2xx
   counts, challenge body after 404 stays `blocked` with the challenge detail (no browser probe),
   a response whose `.read()` would raise is never read; forbidden calls asserted. Mutation list
   in the PR.
7. The lane does not edit records (E24 holds `records/**`) and does not change E23's listing or
   checksum paths; it dispatches `verify.yml` on its branch once (E23 design 7), links the run, and
   lets publisher outcomes vary.

8. (Added 23 Oct on E24's finding.) A `manifest_url` whose response is itself a data file is the
   one entry: when the response's content type is not HTML, JSON, XML or plain text, or carries
   `Content-Disposition: attachment`, or the record's `samples.yaml` entry says `file: true`, the
   listing is `[Entry(url=manifest_url, name=<last path segment>, size=<Content-Length or None>)]`
   and the sample hashes that object under the usual budget; the body is streamed once (not read
   into memory as a listing). A CSV served as `text/csv` is a file, not a text list of URLs. Tests:
   content-type path, attachment path, `file: true` path, and the mutation "CSV rows read as URLs".
   E24's PR names the records this unlocks (heading "File addresses for H1 design 8"); the records
   themselves are repointed by a later records slice, not by H1.
9. (Added 23 Oct.) robots.txt that cannot be read (data.gov.tw answers HTTP 500 to the verifier's
   agent, 404 to curl's) is reported as "robots.txt unreadable (HTTP <status>), treated as
   disallow" (RFC 9309 section 2.3.1.4), distinct from an explicit disallow; a 404 robots.txt
   allows. E23's test for this wording is extended if it does not already cover the 5xx case.

**Acceptance.**
- Offline: the recovery tests, the workflow-consumption test, the dry-mode test and the probe
  tests of design 6 green, each named with the mutation it catches.
- The dispatched branch run's results show NM OCD, PA DEP and ODNR as `blocked` with both status
  codes in the detail (or, if they answer the verifier that day, the PR says so).
- After the merge, the first dispatched run on main closes every open `origin-dead` issue whose
  origin it observed at L1+, each with the comment of design 3; the PR body names which of #17,
  #23 to #27 that was, or that none had recovered.
- Design 8: the four tests green and the mutation red; design 9: the 5xx wording test green.
- `make check` green; verification/4 unchanged (details are strings).

**Claim.** `src/osd/report.py`, `src/osd/verify.py` (origin probe classification and the injected browser probe only), `src/osd/cli.py` (report output, verify and status detail printing), `.github/workflows/verify.yml` (the report step and the ids it passes), `tests/test_report.py`, `tests/test_verify.py` (additions only), `tests/fixtures/report/**`, `docs/program/DECISIONS.md` (OSD-D20), `docs/program/charters/H1-*STRATEGY.md`, `docs/program/evidence/h1/**`.

**Dispositions** (Codex review `H1-origins-that-recover-and-origins-that-hide-CODEX-REVIEW.md`, verdict REWORK; one round, OSD-D8).

| # | Point | Disposition |
|---|---|---|
| F1 | 404/5xx qualification: challenge bodies are blocked, transient 5xx retried | Accepted: Context corrected; design 4 runs only after the terminal result and never after `blocked`. |
| F2 | Historical claims need run and issue evidence | Accepted: run id, issue numbers, evidence file and PR named in Context. |
| F3 | "Seven" open issues wrong | Accepted: #17, #23 to #27 (six). |
| F4 | `--out` writes the array today; the object is a contract change | Accepted: design 2 changes both sides together with a consumption test. |
| D1 | Recovery attribution with partial runs | Accepted: ids verified this run passed in; recovered requires a fresh observation (design 1, test in 6). |
| D2 | Issue identity by number and label | Accepted: design 1; enumeration failure means no mutation. |
| D3 | Retry semantics | Accepted: browser probe after the terminal result only; 503 then 200 stays L1 (design 4, test in 6). |
| D4 | `Range: bytes=0-0` is not headers-only | Accepted: GET closed without `.read()`; headers cannot tell a challenge (design 4). |
| D5 | Injected boundary | Accepted: `browser_probe` injected; never on content paths (design 4). |
| D6 | Evidence visibility in CLI | Accepted: design 5, claim extended. |
| D7 | Workflow trigger | Accepted: branch dispatch per E23 design 7 (design 7). |
| A1 | "or none recovered" passes with closure deleted | Accepted: offline mocked closing test with number and comment (design 6). |
| A2 | Idempotence needs successive runs | Accepted: two-run test against mocked issue state. |
| A3 | Dry-run guard | Accepted: zero-mutation test in dry mode. |
| A4 | Workflow JSON consumption | Accepted: consumption test for both lists. |
| A5 | Negative recovery fixtures | Accepted: the five cases named in design 6. |
| A6 | Probe tests must assert outcomes and forbidden calls | Accepted: design 6. |
| S1 | Records and samples stay in E24 | Accepted: design 7. |
| S2 | E23 paths unchanged, browser agent never reaches them | Accepted: request-log test (design 4). |
| E24-1 | (worker finding, after the round) a bare file address is not sampled by today's verifier | Added as design 8 (single-file listing) and design 9 (unreadable robots wording); claim extended to `check_files`/`read_listing` in `verify.py` and `src/osd/verifier/listings.py` (shape detection) and the `file:` flag in `samples.yaml` schema handling, not its entries (E24 holds the entries). |
