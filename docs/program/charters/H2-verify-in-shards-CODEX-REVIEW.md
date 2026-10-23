**1. Verdict: REWORK.** Sharding is feasible, but the charter leaves result provenance, failure handling and verifier budgets underspecified enough to publish stale results as fresh observations.

Reviewed against HEAD **`6ce9aba725573a88261e4f4a4ce7f459a0c21819`**. No files modified.

**2. Factual errors and Context verification**

- Confirmed: one hosted job, 60-minute timeout, earlier-result restoration, `--outline-inputs`, status and dead-link reporting: `.github/workflows/verify.yml:13–60`.
- Confirmed: full validation, force-push and Pages dispatch: `.github/workflows/verify.yml:82–95`. Qualification missing from Context: these three operations run **only for dispatches on main**.
- Confirmed: verification is serial (`src/osd/verify.py:791–807`); the CLI invokes it directly (`src/osd/cli.py:66`). No concurrency group exists in the complete workflow; overlapping main dispatches can overwrite results.
- The quoted durations, concurrency of historical runs and nine ArcGIS inputs are historical observations, **not verified by HEAD**. Attach run metadata, checked-out SHA and actual processed-record counts.
- “176 records counted after E31 merged during the run” does not establish that the run verified 176 records: checkout precedes verification, with no subsequent main refresh (`.github/workflows/verify.yml:18–40`). A later merge cannot enlarge that checkout.

**3. Design objections and concrete alternatives**

- **Earlier results are needed inside each shard.** Design 2 mentions downloading them only in the finishing job. Verification reads previous results for licence changes, blocked history and L4 carry-forward (`src/osd/verify.py:567–569,610,734–743,800`). Restore one common results snapshot into every shard; upload only freshly generated files belonging to that shard, never its entire restored directory.
- **“Does what the single job does today” breaks recovery reporting after shard failure.** Today the workflow passes `--verified all` for an empty selection (`.github/workflows/verify.yml:60`); retained L1 results could then close issues without a fresh observation (`src/osd/report.py:91–109`). Pass exactly the freshly verified IDs; when none succeeded, skip issue mutation explicitly.
- **The hash/budget contract changes silently.** Every process gets a 2 GiB budget (`src/osd/verify.py:78,293,789`), so N shards permit N times the previous dispatch budget. Specify and justify a per-dispatch versus per-shard policy; preserve a dispatch cap through explicit shard allocations if that remains the contract.
- **Empty selection is dangerous.** `verify_all(ids=[])` verifies everything (`src/osd/verify.py:792`). Require an empty shard to exit successfully without invoking verification; define index bounds, hash algorithm and encoding, and reject malformed shard arguments.
- **Partial failure needs an executable policy.** Require independent shards to continue, define whether partial artifacts are discarded or accepted, validate artifact membership, and make the finishing job report incomplete coverage. Retain existing per-record JSON and use standard Actions artifacts.
- **Concurrency must cover the whole read–verify–store transaction**, including explicit-ID main dispatches. `cancel-in-progress: false` alone does not retain every pending run; default concurrency replaces an existing pending run. Explicitly accept coalescing or use the documented `queue: max`, with a stated overflow policy. [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)
- **Host grouping conflicts with the fixed ID-hash design.** Choose one rule before implementation. Origin-host grouping also misses shared listing, licence and input hosts; measure those request hosts before accepting parallel pressure.
- **Ownership is too narrow:** “`cli.py` verify arguments only” excludes the `cmd_verify` selection and empty-shard handling required at `src/osd/cli.py:63–66`. Claim that command’s dispatch logic explicitly.

**4. Acceptance loopholes**

- A partition test can pass while the CLI ignores sharding entirely. Exercise the actual CLI with an injected verifier; assert exact IDs, empty-shard zero calls, invalid-input rejection and separate-process stability.
- Adding a record at the end can leave list-position sharding unchanged. Insert a fixture ID before existing sorted IDs so the stated mutation necessarily fails.
- “Overlay replaced by copy” is not a precise mutation: copying files into an existing directory already overlays them. Assert both replacement of an existing result and preservation of a missing shard’s result; mutate destination deletion and overwrite suppression separately.
- Retaining every old file and verifying nothing can satisfy runtime, level-count and schema checks. Require fresh-result IDs to equal the complete checkout record set for the successful timing run; retained results must not count as verified.
- No acceptance test proves concurrent dispatch preservation, fresh-only recovery reporting, or the doubled-catalogue 40-minute promise. Add offline orchestration tests and a defined scaling measurement.
- Branch evidence currently skips `check-full` (`.github/workflows/verify.yml:83`). Require it explicitly for the branch finishing job, with storage and issue mutation still disabled.

**5. Scope overlap**

- **H1:** retained-result recovery semantics are an existing contract; preserve them through workflow inputs, rather than weakening `report.py`.
- **E23:** aggregate byte budgets and host pacing are verifier policy; sharding must explicitly account for changes to those guarantees.
- **E29/E32:** claimed implementation paths are otherwise disjoint. Keep outline extraction, STAC/build optimisation and tile fixes in their existing charters; remeasure H2 after E29, and identify whether E32’s larger outlines are included in its timing baseline.