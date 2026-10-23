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
