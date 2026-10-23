# Engineering setup

Fit for purpose: a Python package, YAML records and a static page. The Ophiolite program
(docs/program-2026-09-25 in the Ophiolite monorepo) taught what to keep and what to drop; the
evidence for each line is in the Ophiolite program records of 8–22 October 2026.

## Keep (copied from Ophiolite)

| Practice | Why it earned its place |
|---|---|
| Claims board: a lane names its paths before it starts, two lanes never share a path | Overlap was the cause of merge pain; the 21 Oct simplification cut kept the board deliberately |
| Contract first: slice 0 is schema, fixtures and stubs; later slices vertical | Layer-cut slices made serial chains (18 Oct rule) |
| Kernel vs surface proof bar | Surface strategies capped at one review round after revisions ran to 8 and 18 rounds on E60 and E42c |
| Outcome-named slices: the brief says what a user can do after merge, or no lane | Success metric is slices merged per day, not green CI |
| Revert first: a red main gets one revert within the hour, the fix follows | Owner accepted a briefly red main on about one merge in five |
| No artificial schedule: act when the precondition holds, never on a timer | Nightly timers and self-set dates cost days (night 2026.10.95) |
| Small fixes batched, one push per merge, no wait on the repeat run | Loop steps 7 and 8 |
| Brief by reference, one drafting and one execution agent, small contexts | 83 % of usage was sessions over 150k tokens, 78 % subagent-heavy |
| A different model reviews kernel charters, read-only, one round | Reviews caught contract mistakes; multiple rounds did not pay |

## Drop (what cost Ophiolite more than it returned)

| Station | Evidence | Here instead |
|---|---|---|
| Self-hosted runners, pool builders, runner crews | needrestart killed runner units after any apt run; two crews and "chair out, station out" existed only to manage them | GitHub-hosted `ubuntu-24.04`, one job, under two minutes |
| Merge trains, then a merge queue | 8 workers gave 10× activity for 2–3× merges; merges per worker-day fell from 5.6 to 0.3 at 18 workers | Squash merge on a green check; at most 2 coding lanes plus 1 records lane |
| Nightly releases, release pinning, qualification | A night took 1 h 50 min at best, ARM64 70 min on the critical path; per-lane qualification 45 min serial | Every merge to main publishes the site; no version numbers |
| Hardening lanes and a growing item list | 87 hardening merges against about 10 epic slices in a week; the list grew 150 → 217 | Defects under 50 lines ride on the next lane; a red main is reverted, not hardened |
| Committed conformance results, locks, worker-check cron | Three lanes lost 30–45 min each on a dead lock; a queue stopped for an hour on a docs-only deadline | Nothing is committed that a job can regenerate; no locks; no cron |
| Multiple Codex rounds, 4-revision caps | 2–4 h of a worker per round | One round for a kernel charter; none for surface or records |
| Dispatch per commit group | Worth it for a 27-minute C++ build | A 2-minute check runs on every push; nothing to batch |
| ccache, proven-tree skip, CI spend caps | Needed for a 27-minute C++ build | Irrelevant at Python-and-static scale; revisit above 10 min per check |

## The gate

`make check` = ruff + pytest + schema validation + build, offline. It is the only required
status. Network verification (`verify` workflow) comments on pull requests and never blocks: a
publisher's outage is a finding, not a red gate. The site publishes from main on every merge.

## Proof bar by class

- **Kernel** (schemas, verifier, build, manifest, bridge): tests for every acceptance line, a
  mutation shown to fail for every guard, one Codex round on the charter. Strategy at lane open,
  at most two pages.
- **Surface** (site, docs, records): `make check` green and a screenshot or the verify comment.
  No strategy document; the charter's acceptance list is the brief.
- **Records**: the verify comment shows the level; a human checks the licence fields against
  the publisher's page. Same-day merge.

## Roles

- **Supervisor** (one): keeps `docs/program/PROGRAM.md` true, writes lane briefs by reference,
  merges on green, reverts on red, records decisions in `DECISIONS.md`. Does not write product
  code except a revert.
- **Worker** (at most three concurrent: two coding lanes, one records lane): takes a charter,
  claims paths, opens a branch `e<nn>-<slug>`, pushes when the diff is inside the claim, opens
  the pull request with the outcome sentence and the proof. Waits for nothing but its own check.
- **Reviewer** (Codex, read-only): one round per kernel charter, dispositions recorded in the
  charter.

## What is deliberately absent

No merge queue, no release branches, no version tags, no nightly, no self-hosted compute, no
lock files committed by hand, no conformance ledger, no item list. If one of these starts to look
necessary, the measured reason goes into `DECISIONS.md` first.
