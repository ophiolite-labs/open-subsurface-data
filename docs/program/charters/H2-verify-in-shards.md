## H2 Verify in shards — CHARTERED · Kernel (hardening) · strategy at lane open · one Codex round

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
`verification-results` and dispatches `pages.yml`. Measured all-record runs on main: 40 and 43
minutes after E27/E28 (160 records), 56 minutes after E30 (run 39997774390, 176 records counted
after E31 merged during the run; concurrent with run 40002956457); E29's branch run 42.5 minutes
with nine ArcGIS inputs (run 39998588144). Each lane adds listings and inputs. There is no
`concurrency` group: two dispatches on main both force-push `verification-results`, and the one
finishing last wins with whatever earlier results it started from.

**The design the lane must map to.**
1. `osd verify --shard I/N` selects the records whose stable shard (a hash of the record id, not
   list order, so adding a record moves no other record) is I of N; without `--shard` nothing
   changes. Explicit ids and `--shard` together are an error.
2. On a dispatch with empty `ids`, `verify.yml` runs a matrix of N shards (N stated in the
   strategy from measured per-record times; of the order of 4 to 6) on GitHub-hosted
   `ubuntu-24.04`, each uploading its `build/verification` files as an artifact. One finishing job
   (needs: all shards, runs even when one shard failed) downloads the earlier results, overlays the
   shards' files, then does what the single job does today: `osd status`, dead-link report,
   `make check-full`, store, republish. A shard that times out or fails leaves its records'
   earlier results in place, and the finishing job names the failed shard in the step summary.
   Pull-request runs (changed records only) stay one job.
3. A `concurrency` group for dispatches on main (`cancel-in-progress: false`), so a second
   dispatch queues behind the first and starts from its stored results.
4. A host's 2 s pause holds within a shard; the strategy states how many shards may hit one host at
   once (records of one publisher hash to different shards) and either accepts it with the measured
   counts per host or groups records by origin host in the shard key.

**Acceptance.**
- Unit tests: shard selection is a partition (every record in exactly one shard for N in 1..8);
  adding a record changes no other record's shard; `--shard` with ids is refused. Mutation: shard
  by list position → the stability test red.
- Overlay test: a fixture with earlier results and two shard artifacts, one shard missing →
  finishing step keeps the missing shard's earlier files and reports it. Mutation: overlay replaced
  by copy → red.
- One all-record dispatch on the branch (results not stored: the store step is gated on main) and
  then one on main after merge: durations, per-shard times and the slowest records stated; the
  main run under 25 minutes; the published level counts equal to or above the run before (any
  record that drops is named with its first failing check).
- `make check` unchanged in duration; `make check-full` green in the finishing job.

**Out of scope.** Self-hosted runners, caches of origin responses, changing what a check does,
the per-host pause value, the PR-run path.

**Stop rules.** If the finishing job cannot keep results of a failed shard without a new results
layout, stop after designs 1 and 3, record it, and name the layout question.

**Ownership and dependencies.** Coding lane. Paths: `.github/workflows/verify.yml` (granted, named
in the PR title), `src/osd/cli.py` (`verify` arguments only), a new `src/osd/shards.py`,
`tests/test_shards.py` (new), `tests/fixtures/shards/**` (new), `docs/program/evidence/h2/**`.
Not touched: `src/osd/verify.py` and `src/osd/verifier/**` (E29 and records lanes), `records/**`.
Opens after E29 merges (E29 changes `verify.py` dispatch and adds inputs the timing must include);
runs beside E32 (disjoint paths).

**Evidence to inspect.** The two dispatch runs with durations and per-shard times; the overlay test;
the step summary of a run with a deliberately failed shard (branch run, a shard forced to exit 1).
