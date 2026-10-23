## H2 Verify in shards — CHARTERED · Kernel (hardening) · strategy at lane open · Codex round closed (REWORK, reworked 23 Oct)

Authority: owner direction 23 Oct 2026 (levels on the map are real and current; publication on
every merge); OSD-D5 (results on the `verification-results` branch, no bucket, no secret);
OSD-D20 and H1 (dead-link report, issues close on recovery); E23 and E30 (listing readers, 2 s
pause per host); E29 (`--outline-inputs` on ArcGIS layers); `docs/ENGINEERING.md` (hosted
runners, one job class, no infrastructure).

**Outcome.** An all-record verify dispatch on main finishes in under 25 minutes with the catalogue
of today and stays under 40 minutes when it doubles, and two dispatches never overwrite each other's
results, so every merge can be followed by a verify run without watching a 60-minute ceiling.

**Context (main ee24f97, 23 Oct).** `.github/workflows/verify.yml` is one job, `timeout-minutes: 60`,
that verifies every record serially (`uv run osd verify --outline-inputs`), then runs `osd status`,
the dead-link report, `make check-full`, force-pushes `build/verification` to
`verification-results` and dispatches `pages.yml`. Measured all-record runs (historical; the lane re-measures and states run id, checked-out SHA and the
count of records verified): after E27/E28 on main, runs 39991398736 and 39991880470, 40 and 43
minutes; after E30 on main, run 39997774390, 56 minutes (it checked out main before E31 merged, so
it verified 160 records, not 176); E29's branch run 39998588144, 42.5 minutes. Verification is
serial (`src/osd/verify.py:791-807`) and reads earlier results for licence changes, blocked history
and L4 carry-forward (`verify.py:567-569, 610, 734-743, 800`); each process has a 2 GiB L2 byte
budget (`verify.py:78, 293, 789`); `verify_all(ids=[])` verifies everything. The dead-link report
gets `--verified all` for an empty selection (`verify.yml:60`; `src/osd/report.py:91-109`). `make
check-full`, the store and the Pages dispatch run only for dispatches on main. There is no
`concurrency` group: two dispatches on main both force-push `verification-results`, and the one
finishing last wins with whatever earlier results it started from.

**The design the lane must map to.**
1. Shard key. `osd verify --shard I/N` (1 <= I <= N <= 16, else refused) selects the records whose
   origin host (the host of `origin.url`, lowercased) hashes to I: SHA-256 of the UTF-8 host, first
   8 bytes big-endian, modulo N, plus one. One publisher's records stay in one shard, so the 2 s
   pause per host holds for origins; adding a record moves no other record. The strategy measures
   the hosts of listings and inputs that differ from the origin host and states how many shards can
   reach each such host at once. Explicit ids with `--shard` are refused. A shard with no records
   exits 0 without calling the verifier.
2. Budget. The 2 GiB L2 byte budget stays per process, so a dispatch of N shards may hash up to N
   times 2 GiB. Accepted: the budget bounds one runner's time and disk; origin load is bounded by
   design 1. The strategy states N and the measured bytes per shard.
3. Workflow. On a dispatch with empty `ids`, `verify.yml` runs a matrix of N shards on GitHub-hosted
   `ubuntu-24.04` with `fail-fast: false`. Every shard restores the same earlier-results snapshot
   (the `verification-results` commit fetched once by a first job and passed as an artifact, so all
   shards read one state), verifies its records, and uploads only the files of the records it
   verified plus a list of their ids. A shard that fails uploads nothing usable: the finishing job
   discards a shard whose id list is missing or whose files name records outside its shard.
4. Finishing job (needs all shards, runs when any shard failed). It overlays the accepted shards'
   files on the snapshot (a fresh file replaces the earlier one; a record without a fresh file keeps
   its earlier file), then runs `osd status`, the dead-link report with `--verified` set to exactly
   the freshly verified ids (none: issue mutation skipped and said in the summary), `make
   check-full` (on branch dispatches too, with store and issue mutation disabled), store and
   republish on main. The step summary names each failed shard and the records without a fresh
   result.
5. Concurrency. A `concurrency` group on the whole workflow for `workflow_dispatch` on main (all-record
   and explicit-id dispatches alike) with `cancel-in-progress: false`; GitHub keeps one pending run
   and replaces an older pending one. Accepted and stated in the workflow comment: a replaced
   pending dispatch is covered by the newer one when the newer one is all-record; the supervisor
   dispatches all-record runs after merges. Pull-request runs stay one job, outside the group.

**Acceptance.**
- CLI tests with an injected verifier: `--shard I/N` calls it with exactly the expected ids; an empty
  shard makes zero calls; malformed or out-of-range shards and ids with `--shard` are refused; the
  selection is identical in a separate process. Partition: for N in 1..8 every record of the
  catalogue is in exactly one shard. Stability: inserting a fixture record whose id sorts before all
  existing ids changes no other record's shard. Mutations: shard by list position → stability red;
  CLI ignores `--shard` → exact-id test red.
- Overlay tests (offline, fixtures): a fresh file replaces an earlier one; a record of a failed shard
  keeps its earlier file; a shard artifact naming a record outside its shard is rejected. Mutations
  separately: destination deleted before overlay → preservation red; overwrite suppressed →
  replacement red.
- Report test: the finishing step passes only fresh ids; with zero fresh ids it opens and closes no
  issue. Mutation: `--verified all` restored → red.
- Branch dispatch with one shard forced to fail (a branch-only input): summary names the shard and
  its records; earlier results kept; `check-full` green.
- One all-record dispatch on main after merge: fresh ids equal the checkout's record set (stated
  count), under 25 minutes, per-shard times and the slowest records stated; published level counts
  compared with the run before, every record that drops named with its first failing check.
- Scaling: per-shard time against records per shard from that run, and the projection for twice
  the catalogue under 40 minutes with the arithmetic shown (a projection, said so).
- `make check` duration unchanged.

**Out of scope.** Self-hosted runners, caches of origin responses, what a check does, the per-host
pause value, the PR-run path, outline extraction and STAC/build speed (E29, E32).

**Stop rules.** If the finishing job cannot keep results of a failed shard without a new results
layout, stop after designs 1, 2 and 5, record it, and name the layout question.

**Ownership and dependencies.** Coding lane. Paths: `.github/workflows/verify.yml` (granted, named
in the PR title), `src/osd/cli.py` (`verify` arguments and `cmd_verify`'s selection), a new `src/osd/shards.py`,
`tests/test_shards.py` (new), `tests/fixtures/shards/**` (new), `docs/program/evidence/h2/**`.
Not touched: `src/osd/verify.py` and `src/osd/verifier/**` (E29 and records lanes), `records/**`.
Opens after E29 merges (E29 changes `verify.py` dispatch and adds inputs the timing must include);
runs beside E32 (disjoint paths).

**Evidence to inspect.** The two dispatch runs with durations and per-shard times; the overlay test;
the step summary of a run with a deliberately failed shard (branch run, a shard forced to exit 1).

### Dispositions (Codex round 23 Oct, REWORK; one round, OSD-D8)

| # | Finding | Disposition |
|---|---|---|
| 1 | Store/check-full/Pages run only on main | Accepted; stated in Context |
| 2 | Durations not verified at HEAD; 176 claim wrong | Accepted; run ids kept, 160 corrected, lane re-measures with SHA and counts |
| 3 | Shards need earlier results | Accepted; one snapshot restored into every shard (design 3) |
| 4 | Upload only fresh files | Accepted; files of verified records plus an id list |
| 5 | `--verified all` closes issues without fresh observation | Accepted; exact fresh ids, none means no issue mutation (design 4, report test) |
| 6 | N shards multiply the 2 GiB budget | Accepted; per-process budget kept and stated as N x 2 GiB (design 2) |
| 7 | Empty selection verifies everything | Accepted; empty shard exits 0 with zero calls; bounds, hash and encoding defined |
| 8 | Partial failure policy | Accepted; `fail-fast: false`, failed or foreign artifacts discarded, summary names them |
| 9 | Concurrency must cover the transaction and pending replacement | Accepted; whole workflow for main dispatches; pending replacement accepted and stated |
| 10 | Host grouping vs id hash | Accepted; one rule: origin host hash; other hosts measured |
| 11 | `cmd_verify` not claimed | Accepted; claim extended |
| 12 | CLI may ignore sharding | Accepted; injected-verifier CLI test, mutation |
| 13 | Append-only mutation misses list-position sharding | Accepted; fixture id that sorts first |
| 14 | Overlay mutation imprecise | Accepted; two separate mutations |
| 15 | Retained results can fake the timing run | Accepted; fresh ids must equal the record set |
| 16 | No tests for fresh-only reporting, doubling promise | Accepted; report test; scaling projection stated as a projection |
| 17 | Branch evidence skips check-full | Accepted; check-full in the branch finishing job |
| 18 | H1, E23, E29, E32 overlaps | Accepted; H1 semantics kept via inputs, budget policy explicit, E29/E32 out of scope, re-measured after E29 |
