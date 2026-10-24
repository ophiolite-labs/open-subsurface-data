**1. Verdict: REWORK** — the proposed checksum breaks the existing downloadable-asset contract, and the required reuse of E29 cannot preserve whole-layer data through its current interface.

Verified against HEAD `394e4fd0205d1a33e40fc8fc2c82ebd5bbb07bc1`. No files modified. References are repository-relative; “E35” means the reviewed charter.

**2. Factual errors and Context verification**

- **22 candidates, not 23.** Parsed every record’s `manifest_url` and compared the resulting layer URLs with the candidate list. `al-ogb/wells` points to `wells.zip`; its ArcGIS address appears only in notes (`records/al-ogb/wells.yaml:11`). Remove it from the ArcGIS acceptance population.
- **Generated entry confirmed:** JSON and HTML layer readers produce the stated single GeoJSON query (`src/osd/verifier/listings.py:123`, `:129`, `:253`).
- **Truncation handling confirmed, universal server behavior unproven:** the verifier detects a literal transfer-limit flag, moves that export into `partial_exports`, and skips when no files remain (`src/osd/verify.py:358`, `:495`, `:503`). It does not establish that *every* oversized server response carries that flag.
- **Named L1 outcomes are historical observations, not HEAD guarantees.** E29 evidence records the five deferred registers at L1 (`docs/program/evidence/e29/results.md:13`); current server behavior and SK MER/PGI outcomes need dated verification artifacts.
- **E29 paging exists, with a qualification:** it uses offsets ordered by object ID, not requests for an enumerated ID set (`src/osd/outlines/__init__.py:149`). Duplicate and count checks exist (`extractors.py:345`, `:349`), but do not prove equality with an independently obtained expected-ID set.
- **Verifier non-use confirmed:** `check_files` hashes the generated URL directly (`src/osd/verify.py:480`).
- Design 4’s schema uncertainty is already resolvable: file entries forbid extra keys (`schema/verification.schema.json:64`). Adding `assembled` requires a version bump and old-file compatibility proof.

**3. Design objections and concrete alternatives**

- **Checksum/address mismatch — E35:27–31.** STAC publishes every file URL with that file’s digest (`src/osd/stac.py:100`); retrieval hashes the downloaded bytes (`src/osd/get.py:95`). An assembled digest attached to the original query URL causes retrieval failure. Keep assembly evidence without a fetch URL, explicitly test that no downloadable asset is emitted, and describe it as verification evidence; alternatively authorize publication of the exact assembled artifact.
- **Reuse boundary is unavailable — E35:23–26.** E29 fetches selected outline fields as native Esri JSON (`src/osd/outlines/__init__.py:147`); its identity checks feed geometry conversion and `_features`, not a lossless layer return (`extractors.py:348`, `:352`). Permit a small shared paging/validation extraction with preserved outline behavior, then let verification request all fields.
- **Format conflict — E35:28.** Reusing E29’s native coordinates while calling the result GeoJSON conflicts with this project’s WGS84 GeoJSON contract. Explicitly request server-produced WGS84 GeoJSON, or preserve native Esri JSON and name that format.
- **Snapshot consistency unspecified.** Unique IDs and matching counts can still combine attributes from different edits. Re-read edit metadata after paging and reject changes; absent edit metadata must mean “stability unknown,” not “unedited.”
- **Budget enforcement is too late if applied only to assembled bytes.** Bound page reads before decoding and assembly, preserve the 512 MiB record share (`src/osd/verify.py:79`), and account for abandoned reads. Test oversized responses with an injected opener.
- **Timer and stop rule — E35:48, :55.** “Next hour” contradicts ENGINEERING’s no-artificial-schedule rule. Repeat when the first run completes; any unexplained instability leaves that candidate incomplete, rather than stopping only when most candidates disagree.

**4. Acceptance loopholes and ineffective mutations**

- E35:47–50 permits every candidate to fail with a reason and zero stable checksum pairs. Require successful whole-layer evidence for named eligible multi-page candidates; otherwise report the outcome incomplete.
- Removing sorting can remain green when request ordering already produces sorted features. Shuffle feature order *within* pages as well as page delivery order, and assert exact canonical bytes.
- Removing the count check can remain green if the mismatch fixture also triggers short-page rejection. Use a full first page and an oversized final page with unique IDs, isolating the final total-count guard.
- Removing the feature cap can remain green if the fixture instead hits the 200-page cap (`extractors.py:254`). Choose page size below that page-count threshold and assert the specific feature-cap reason.
- Only three mutations are required. Duplicate-ID rejection, page-error rejection, robots enforcement, pacing, budget exhaustion, and downstream asset exclusion need independent failing mutations.
- No test requires all attributes, null geometries, or coordinate changes to affect the digest. An outline-only projection could pass the proposed ID-set test.
- E35:46 states duration without requiring `<120 s`; schema changes also lack an explicit old-file validation acceptance test.

**5. Scope overlap**

- Repairing downloadable assembled assets enters **E06 retrieval** and **E07 mirror/custody** scope; an `assembled` flag alone changes neither consumer. Keep evidence non-downloadable or explicitly charter that expansion.
- The necessary shared extraction enters **E29’s outline implementation**, currently forbidden by E35. Amend ownership rather than duplicate its guards.
- **E32 owns `src/osd/stac.py` and `src/osd/manifest.py`.** Any consumer-side filtering or retrieval adaptation needs an explicit handoff; E35 cannot retain its “disjoint paths” assertion while silently requiring those changes.