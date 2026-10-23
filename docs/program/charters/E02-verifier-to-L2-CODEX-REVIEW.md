**1. Verdict: REWORK.** L2 coverage, reachability classification and ownership remain underspecified, and the acceptance tests cannot establish several promised guards.

Verified against HEAD `e58e2f547715fc46d94a7e778eb142190578803c`. No files modified.

**2. Factual errors and Context verification**

- Confirmed: injected fetcher, one initial GET with `Range: bytes=0-0`, default 20-second timeout, and skipped L2 checks (`src/osd/verify.py:40–53,67–79`). Redirects can cause additional requests; the implementation never reads response bytes.
- Output filenames flatten `/` to `__`; they are not literally `<id>.json` (`src/osd/verify.py:114`, `src/osd/paths.py:11`).
- “Against the schema” overstates runtime enforcement: `verify_all` serializes without validation (`src/osd/verify.py:103–116`). The “existing test” validates one synthetic L1 result, not every real run (`tests/test_verify.py:36–39`).
- Confirmed: PR and dispatch triggers and artifact upload (`.github/workflows/verify.yml:7–11,40–41`). PR triggers also include outlines.
- Branch consumption is indirect: pages imports results before building (`.github/workflows/pages.yml:22–29`); the browser reads generated JSON (`site/app.js:4–5`). Only dispatch **on main** publishes results (`.github/workflows/verify.yml:48–58`).
- The historical 403s and “five of nine” cannot be verified from code at HEAD. They are reported in `docs/program/DECISIONS.md:16` and PROGRAM’s scaffold history, not executable evidence. Label them historical and link the run; HEAD contains 21 dataset records.
- E01 has not supplied the stated L2 prerequisite: the only `manifest_url` is `records/sodir/factpages.yaml:11`. Three real L2 records require additional record work absent from E02’s owned paths.

**3. Design objections and concrete alternatives**

- **Classification is neither closed nor exclusive.** 401/429/5xx are unspecified; a cross-host redirect ending in 404 satisfies both “moved” and “dead.” Define an exhaustive outcome table; make relocation a separate observation subordinate to final response success.
- **Blocked → L1 changes the ladder’s meaning.** A challenge proves an intermediary answered, not that the origin content is reachable. Record `blocked` separately and award no new L1 without successful reachability evidence; explicitly revise OSD-D9 if adopting this.
- **Tool policy leaks into publisher records.** `verification.sample` configures the verifier; generated `known_issues` would mix tool findings with record facts (`schema/record.schema.json:5,84`). Keep selection policy in verifier configuration and observations in verification output; records may name publisher-declared assets.
- **Ownership omits a required contract change.** The proposed record field is rejected by `additionalProperties: false` (`schema/record.schema.json:7`), yet E02 does not claim that schema. Remove the field or claim the schema, bump `$id`, retain old-record compatibility tests and name the kernel change in the PR.
- **Listing and asset contracts are undefined.** `manifest_url` admits indexes, APIs and bucket listings (`schema/record.schema.json:31`); `files[].path` provides no explicit address semantics (`schema/verification.schema.json:40–41`). Choose supported existing listing formats, reject unsupported ones explicitly, and define resolvable asset URLs for E04/E06.
- **Sampling can overstate L2.** Empty selections, omitted files and cap-truncated files have no prescribed level outcome. Require at least one completely hashed file, record selection coverage, and distinguish sampled evidence from complete dataset coverage.
- **The 2 GB guard is ambiguous.** Specify an aggregate streamed-byte budget, including retries, enforced without trusting Content-Length; partial files must never receive successful checksums.
- **A licence hash is not captured licence text.** Preserve the bounded source text alongside its hash in the existing results store; missing URLs, failed requests and challenge bodies must not pass the licence check.

**4. Acceptance weaknesses**

- **Retry mutation survives:** permanent timeout produces L0 with or without retry. Assert exactly two attempts and add timeout→success recovery.
- **Challenge detection mutation survives:** the only challenge fixture is already HTTP 403. Add HTTP 200 challenge content and ordinary HTTP 200 content.
- **Checksum coverage is insufficient:** three correct hashes do not test allow-list enforcement, empty selection, incomplete streams or the aggregate cap. Inject streams containing selected and excluded files; assert bytes, identities and failure outcomes.
- **Licence-change test permits “always changed.”** Add first-run and unchanged-text cases, assert the previous date, and prove failed licence retrieval prevents L2.
- **Publication equality can pass with both sides at L0 or stale.** Assert explicit IDs, expected L2 outcomes and this run’s timestamp. Import branch JSON into the main checkout; the results branch contains no CLI (`.github/workflows/verify.yml:52–57`).
- **Schema acceptance lacks coverage:** validate every emitted result before writing; exercise success, blocked, partial and failed outputs, plus legacy fixtures.
- No acceptance guards robots refusal, host pacing, absent licence URLs or failed-file prevention of L2. Add injected-fetcher/clock tests and mutations inside existing pytest; no new CI station or test server.

**5. Scope across charters**

- Stale rendering belongs to E05 (`E05-map-that-scales.md:20,42–43`); E02 should own timestamp emission only, with an explicit handoff.
- Adding the required real listings is E01-style record curation; assign those paths explicitly rather than assuming E01 delivered them.
- A record-schema change intersects E03’s planned `record/2` change (`E03-outlines-from-the-data.md`, Ownership); coordinate versioning and sequential claims.
- Keep STAC asset publication in E04, retrieval in E06 and dead-link issue creation in E08; E02 should supply their evidence contracts only.