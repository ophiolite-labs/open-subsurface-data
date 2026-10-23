**1. Verdict: REWORK.** Recovery lacks reliable issue identity and fresh-run attribution, while browser probing conflicts with existing retry behavior and the proposed proof can miss broken workflow integration.

Verified against HEAD **`1a2642c933219b1d07818d6941e76766f535e7e6`**; inspected implementation files match HEAD. No files modified.

**2. Factual errors and Context verification**

- Confirmed: report compares stored results, selects L1+ → dead/L0, excludes blocked records and skips open titles (`src/osd/report.py:60–79`).
- Confirmed: issues are created only on dispatch on main; no recovery closure exists in the workflow (`.github/workflows/verify.yml:45–60`).
- Confirmed: verifier uses its own agent, classifies 403/429 and detected challenge bodies as blocked, and otherwise classifies unsuccessful responses as dead (`src/osd/verify.py:58`, `105–123`, `208–219`).
- Context’s “404/5xx/timeouts as dead” needs qualification: challenge-bearing 404/5xx responses are blocked; transient 5xx/timeouts receive an existing retry and may recover (`src/osd/verify.py:194–219`).
- Historical claims about manual closures, browser-versus-runner responses, and current outages cannot be verified from code at HEAD. `docs/program/HANDOFF.md:9–16` repeats them but is not independent evidence; cite dated run artifacts and issue events.
- “Seven” remaining CO2 DataShare/GEUS issues is unsupported: the handoff identifies five CO2 issues plus GEUS #17, while SPE #28/#29 were closed (`docs/program/HANDOFF.md:9`, `12`, `16`). Supply the actual issue list.
- Design 1’s output “stays” an object is inaccurate: internal reporting returns a dictionary, but CLI `--out` currently writes only the issue array (`src/osd/cli.py:161–166`). This is an output-contract change.

**3. Design objections and concrete alternatives**

- **Recovery attribution:** partial runs retain earlier results (`.github/workflows/verify.yml:23–30`; `src/osd/verify.py:699–700`). Merely finding L1+ can close an issue using a result this run never observed. Pass the IDs actually verified and require a fresh successful observation; test retained, unchanged results explicitly.
- **Issue identity:** titles alone cannot reliably address closures or distinguish duplicate/user-created issues. The workflow currently retrieves only titles (`.github/workflows/verify.yml:49`). Retrieve issue numbers and `origin-dead` labels, match exact record titles, and close by number; abort mutations if issue enumeration fails.
- **Retry semantics:** “first probe” is ambiguous because `probe()` already retries transient failures (`src/osd/verify.py:202–205`). Preserve that retry; attempt the browser probe only after a terminal eligible dead result, never after challenge classification. A 503→200 ordinary retry must remain reachable.
- **Transport contract:** `Range: bytes=0-0` requests a body byte; it does not mean headers-only. Specify a GET whose response is closed without `.read()`, including error responses, and acknowledge that headers alone cannot distinguish content from a 200 challenge.
- **Injected boundary:** the existing fetcher takes only a URL, while the opener streams content (`src/osd/verify.py:89–90`). Explicitly define an injectable, paced browser probe; do not add an unmocked network fallback or change the agent used for listings/licences.
- **Evidence visibility:** `cmd_verify` prints only the original status and L2/L3 details; `status` prefers L2 failure reasons (`src/osd/cli.py:67–70`, `100–110`). Both probe statuses will not reliably reach the requested comment. Extend the CLI claim to print origin-check detail.
- **Workflow trigger:** claimed paths do not trigger PR verification (`.github/workflows/verify.yml:10–11`). Follow E23 design 7: dispatch the existing workflow on the branch and link its evidence; allow publisher outcomes to vary.

**4. Acceptance and mutation gaps**

- “Closes at least one issue **or none recovered today**” passes with closure code deleted. Require an offline workflow test with mocked `gh`, asserting the issue number, comment contents and close operation.
- Removing a title from the next fixture proves report filtering, not successful or idempotent closure. Exercise successive workflow runs against mocked issue state.
- `osd report --dry-run` itself never mutates GitHub. Its test stays green if the workflow’s dry-run guard is removed. Test PR/branch-dispatch modes produce zero issue mutations.
- Fixture output can pass while `.[]` still consumes the new JSON object incorrectly. Test actual workflow JSON consumption for both opening and recovery.
- Require negative recovery fixtures: dead, blocked, absent record, unchanged retained result, and previous-L0/current-L1. The last catches accidentally retaining `report.py:66`’s existing early skip.
- Probe tests must assert statuses, final classification, L0, both detail codes, and forbidden calls—not only request agents. Include ordinary retry recovery, browser failure, redirects, challenge responses, and a response whose `.read()` raises.

**5. Scope overlap**

- Recovery extends E08; classification extends E02. Both are declared dependencies, so this is legitimate follow-up scope.
- Keep publisher URL edits and sample-policy changes in E24; do not touch records merely to trigger PR verification.
- Keep E23’s listing/checksum behavior unchanged, with explicit proof that browser-agent requests never reach those paths.