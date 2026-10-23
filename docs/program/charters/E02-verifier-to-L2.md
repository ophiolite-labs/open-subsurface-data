## E02 Verifier to L2 — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: `docs/ARCHITECTURE.md` (level ladder); owner direction 23 Oct ("verify the sources").

**Outcome.** The level on the map is real and dated: a dead origin shows L0, a reachable one L1,
a dataset whose files were hashed and whose licence text was captured shows L2, and every level
shows the date it was established.

**Context today (verified 23 Oct).** `src/osd/verify.py` implements L1 with an injected fetcher,
a single GET with a 1-byte range and a 20 s timeout, and writes `build/verification/<id>.json`
against `schema/verification.schema.json`. L2 checks are declared with outcome `skip`. The
`verify` workflow runs on records PRs and on dispatch and uploads an artifact; the published site
reads the `verification-results` branch (OSD-D5). The SEG wiki and NOPIMS
refuse the VPS with 403 (OSD-D9); five of nine origins answered on 23 Oct.

**The design the lane must map to.**
1. Reachability classes, closed: `ok` (2xx/3xx), `blocked` (403 or a challenge page body: not
   dead, level stays L1 with detail "blocked from this runner"), `dead` (404/410/DNS failure/
   timeout after one retry), `moved` (final URL host differs: pass with a `known_issues` hint).
2. L2 file check: for records with `origin.manifest_url`, fetch the listing, pick files by a
   per-record `files:` allow-list in a new optional record field `verification.sample`, stream
   each with SHA-256, store `files[]`. Full-dataset hashing is never attempted over 2 GB per run.
3. L2 licence check: fetch `licence.url`, store `licence_text_sha256`; a change in the hash
   between runs is a finding (detail "licence text changed since <date>"), not a failure.
4. Results store: the `verification-results` branch (OSD-D5), written by the verify workflow on
   dispatch and read by pages; the lane keeps that contract and adds nothing else.
5. Freshness: `checked_at` older than 30 days is rendered by the site as "stale" (E05 reads it;
   this lane emits it).
6. Rate: one request per origin at a time, a 2 s pause per host, a fixed User-Agent that names
   the repository.

**Acceptance.**
- Classification test: four fake fetchers (200, 403-with-challenge-body, 404, timeout) give
  `L1 pass`, `L1 pass + blocked detail`, `L0`, `L0` respectively.
- Mutation: removing the retry makes the timeout test fail (shown and restored in the PR).
- Checksum test on a 3-file fixture served from a local directory: `files[]` has 3 entries with
  the SHA-256 values computed independently by `sha256sum` in the test.
- Licence-change test: two runs with different fixture texts produce the "changed" detail.
- After a dispatched verify run, the published `records.json` shows the same levels `osd status`
  prints on the results branch.
- The verification record of every real run validates against the schema (existing test).

**Out of scope.** Outlines (E03), mirrors (E07), running the verifier on a schedule (R6: on
demand and on PRs only), a results bucket.

**Stop rules.** A publisher's robots.txt disallows the listing: skip L2 for it with detail, do
not work around. Hashing would exceed 2 GB: cut the sample, say so.

**Ownership and dependencies.** Coding lane; paths `src/osd/verify.py`, `src/osd/build.py`,
`src/osd/cli.py`, `schema/verification.schema.json`, `tests/test_verify.py`,
`.github/workflows/verify.yml`. Depends on E01 for records with `manifest_url`.

**Evidence to inspect.** The test names mapped to the acceptance lines in the two-page strategy;
the PR's verify comment on at least three records reaching L2.

**Dispositions** (Codex review `E02-verifier-to-L2-CODEX-REVIEW.md`, verdict REWORK; owner rulings
OSD-D9 revised and OSD-D11; strategy `E02-verifier-to-L2-STRATEGY.md` is the amended design).

| # | Finding | Disposition |
|---|---|---|
| F1 | Probe reads no bytes (`Range: bytes=0-0`) | Accepted: probe reads the first 16 KB, needed for challenge detection. |
| F2 | Output names are `<id with / as __>.json` | Accepted as a wording fact; no change, the flattening is the existing contract. |
| F3 | Schema validity is not enforced at runtime | Accepted: `verify_all` validates every record before writing (`test_verify_all_never_writes_an_invalid_record`, M17). |
| F4 | Pages imports the results branch; only dispatch on main publishes | Accepted as stated; contract kept, workflow now prints `osd status` into the job summary and PR comment. |
| F5 | 403s and "five of nine" are historical | Accepted: the PR shows a fresh run (SEG wiki blocked, 20 others reachable). |
| F6 | Only one record has `manifest_url` | Accepted: supervisor extended the claim; Norne and Poseidon gain their publisher listings. |
| C1 | Classes not closed or exclusive (401/429/5xx, moved+dead) | Accepted: exhaustive ordered table on the final response; moved only on success; 401/other 4xx/5xx dead (`test_every_other_status_is_dead`). |
| C2 | Blocked should award no L1 | Accepted per OSD-D9 revised: `blocked` is `skip`, no level, `blocked_since` emitted (M13, M14). |
| C3 | Sampling policy leaks into records | Accepted per OSD-D11: `src/osd/verifier/samples.yaml`; record schema untouched (`test_record_schema_has_no_tool_policy`). |
| C4 | Record schema change unclaimed | Moot: no record schema change. Verification schema bumped to `/2`, v1 still validates. |
| C5 | Listing and asset contracts undefined | Accepted: supported listings named (JSON, S3 XML, HTML links, text lines); `files[].url` is the resolvable address for E04/E06. |
| C6 | Sampling can overstate L2 | Accepted: pass needs one fully hashed file; any failed selected file fails; detail states coverage "sample, not the whole dataset" (M16). |
| C7 | 2 GB guard ambiguous | Accepted: run-wide budget on streamed bytes, Content-Length not trusted, partial files never recorded (M6). Streams are not retried. |
| C8 | A hash is not captured text | Accepted: visible text (≤ 100 000 chars) stored as `licence_text`; missing URL skips, failure or challenge fails (M15). |
| A1 | Retry mutation survives | Accepted: two-attempt assertion and timeout→success test (M1). |
| A2 | Challenge mutation survives | Accepted: challenge at HTTP 200 and 503 (M2). |
| A3 | Checksum test too narrow | Accepted: allow-list, empty selection, failed file, budget cut tests (M5, M6, M16). |
| A4 | Licence test permits "always changed" | Accepted: first-run and unchanged-text cases with script churn, previous date asserted (M8). |
| A5 | Publication equality can pass at L0 | Accepted: explicit ids at L2, L1, blocked L0 asserted (M18); live equality on this run's results shown in the PR. |
| A6 | Schema acceptance lacks shapes | Accepted: L2, timeout, blocked and cut records validated; v1 fixture kept. |
| A7 | No guards for robots, pacing, absent licence URL, failed file | Accepted: M7, M9, M15, M16 with injected fetchers and clock. |
| S1 | Stale rendering is E05's | Accepted: E02 emits `stale` and `blocked_since` in `records.json` only. |
| S2 | Real listings are records work | Accepted: done under the supervisor's claim extension, `manifest_url` only. |
| S3 | Record schema intersects E03's `record/2` | Moot after OSD-D11: E02 leaves the record schema at `/1`. |
| S4 | STAC assets E04, retrieval E06, issues E08 | Accepted: E02 supplies evidence fields only. |
