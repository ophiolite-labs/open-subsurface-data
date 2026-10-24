**1. Verdict: REWORK.** The proposed formats require a schema change, partial exports can accidentally earn L2, and the acceptance permits every candidate to fail.

Verified against HEAD **`00ee199563a92281a32078358ccb66c6019d2214`**. No files modified.

**2. Factual errors and Context verification**

- **64 anonymous records without `manifest_url`: confirmed**, excluding the template as the loader does (`src/osd/records.py:33`).
- **BGS endpoint evidence exists**, at `docs/program/evidence/e30/sources.md:67`, but BGS is already downloadable: its record names a ZIP manifest (`records/bgs/single-onshore-borehole-index.yaml:9`). It is not an “only machine listing” candidate.
- **GA STRATDAT and RESFACS WFS claims: confirmed** by their record notes (`records/ga/stratdat-biostratigraphy.yaml:12`, `records/ga/resfacs-porosity-permeability.yaml:11`) and `docs/program/evidence/e37/sources.md:51`.
- **DOV’s 188,507 count: confirmed as historical evidence**, dated 23 October, not a current measurement (`records/dov/boringen.yaml:13`). DOV already has a WFS manifest and a `file: true` sample (`src/osd/verifier/samples.yaml:38`).
- **PGI already uses ArcGIS: confirmed** (`records/pgi/cbdg-boreholes.yaml:9`); E35 already reports its above-cap refusal (`docs/program/evidence/e35/results.md:40`).
- **Americas GeoServer: confirmed**, specifically WOGCC (`docs/program/evidence/e24/new-americas.md:28`; `records/wogcc/wyde-wells.yaml:11`).
- **Design 1’s optional schema bump is incorrect.** Verification/5 fixes `format` to `esri-json` and requires an integer `count`; all three proposed formats fail today, and an unknown expected count is unrepresentable (`schema/verification.schema.json:54–63`).

**3. Design objections and concrete alternatives**

- **Version the contract now:** require verification/6, freeze /5, represent unknown expected counts explicitly, and preserve old-file validation. Claim `tests/test_schema.py` and the frozen-schema fixture; current tests assert /5 identity and the closed format (`tests/test_schema.py:341`, `:383`).
- **Partial fallback is unsafe:** `_digest` only recognises `exceededTransferLimit` (`src/osd/verify.py:346–362`); otherwise the fallback becomes `files` and can pass L2 (`:549–571`). Carry an explicit incomplete outcome from each protocol; never infer completeness from absence of ArcGIS’s flag.
- **Dispatch must precede bare-file classification:** `file: true` and attachment headers bypass listing readers (`src/osd/verify.py:458`, `:473`). Define precedence for recognised service URLs, remove inappropriate sample overrides, and test through `check_files`.
- **GML rules contradict each other:** “hashed as returned” cannot also guarantee sorted features and whitespace-independent bytes. Defer GML with a stated unsupported-format result, or specify a standard XML canonicalisation profile plus feature ordering and envelope handling.
- **WFS versions need distinct contracts:** 1.1 uses `typeName`/`maxFeatures`; 2.0-style pagination is not portable to 1.1. Negotiate capabilities, use version-correct parameters, and support pagination extensions only when established. Otherwise defer 1.1. [OGC WFS 1.1 specification](https://docs.ogc.org/is/04-094r1/04-094r1.html)
- **“Count unconfirmed” weakens whole-layer evidence:** without a count, a missing `next` link can silently certify one page. Prefer incomplete status absent independent completeness evidence; alternatively define a separate, explicitly weaker evidence contract. OGC makes `numberMatched` optional and `next` a SHOULD. [OGC API Features](https://docs.ogc.org/is/17-069r4/17-069r4.html)
- **Snapshot evidence needs protocol-specific meaning:** define usable revision signals; do not treat response generation timestamps or page-specific ETags as collection revisions. Record stability unknown when none exists. OGC explicitly warns that pagination need not preserve dataset state. [OGC API Features](https://docs.ogc.org/is/17-069r4/17-069r4.html)

**4. Acceptance that can pass vacuously**

- **Both dispatches may fail every candidate.** Require named, eligible, multi-page candidates for each implemented protocol to pass, or mark that protocol’s outcome incomplete.
- **“Where the layer did not change” is undefined.** Require independently stated revision evidence; unknown stability must not silently exempt checksum disagreements.
- **Shuffled pages need not catch missing feature sorting.** Shuffle features within pages too; assert exact canonical bytes and digest changes for attribute, geometry and coordinate mutations.
- **Count mismatch may also trigger duplicate/short-page guards.** Use unique IDs and otherwise valid pages so removing only the count guard turns that case green.
- **Cap fallback tests can pass while awarding L2.** Assert partial evidence, no `files` entry, no L2 from that export, and no downstream asset; isolate the feature cap from page and byte limits.
- **Exporter-only fixtures miss dispatch failures.** Add end-to-end injected-opener cases for attachment headers, existing sample overrides, unknown counts, paging loops, later-page robots refusal, budget exhaustion and exception responses.
- **“Inside main’s spread” has no enforceable bound.** Retain the existing offline `make check` gate and explicitly require under 120 seconds.

**5. Scope into other charters**

- Design 6’s blanket candidate rewrite reaches **E30’s existing download selection**: replacing BGS’s ZIP with a service changes retrieval despite the stated outcome. Preserve existing downloadable manifests; use BGS as fixture evidence only.
- **PGI is already E35 territory**, above the retained cap. Keep it as a regression case, not a new E38 conversion.
- **H3 remains a dependency**, not E38 implementation scope: consume its shared robots interface after merge; avoid reimplementing its matcher.