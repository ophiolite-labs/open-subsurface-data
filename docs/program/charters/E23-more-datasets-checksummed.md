## E23 More datasets checksummed — QUEUED · Kernel · one Codex round (done, REWORK; dispositions below)

Authority: E02 (verifier to L2) and its strategy; OSD-D9 (blocked awards no level), OSD-D11
(sampling policy is tool configuration, never a record field); OSD-D19 (schema versions frozen);
the catalogue's thesis that a level is earned by a check the catalogue ran itself.

**Outcome.** Every record whose publisher lists its files in a shape the verifier reads has its
sample attempted on each run; the ones that pass show L2 on the map, and every one that does not
says in its verification, and in `osd status`, which L2 check stopped it and why.

**Context today (verified 23 Oct; source main 3d5841c, verification results 16416ee as published in
`records.json` `catalog`).** 96 records published: 10 L0, 82 L1 (exactly L1), 3 L2 (exactly), 1 L3.
**23 records carry `origin.manifest_url`**; `src/osd/verifier/samples.yaml` names a sample for four
(Sodir FactPages, Norne, NOPIMS Poseidon, NLOG), so 19 skip with "no sample for this record in
verifier/samples.yaml". `parse_listing` (`src/osd/verify.py`) reads HTML directory listings, S3 XML,
text lists and walks any JSON recursively for `url` and integer `size`, so a CKAN `package_show`
response does yield resource URLs; what is missing is per-shape selection (resources versus
metadata links), the publisher's checksum when the listing carries one, and readers for the
shapes that are not plain file lists: Socrata views JSON (ANH, `/api/views/<id>.json`), the
data.gov.tw REST dataset API (CPC, `/api/v2/rest/dataset/<id>`), ArcGIS Feature Server queries,
Zenodo, figshare, Dataverse and GitHub releases. Each needs its own fixture from a real response.
`inventory` already exists in verification/3 (E07 owns its meaning: completeness for mirror
eligibility) and `schema/verification.schema.json` rejects additional properties on file entries.
The run budget is 2 GiB; a pass needs one fully hashed file (E02 C6). L2 also needs the licence
text captured, so a files pass alone does not reach L2. Hashing is SHA-256. Records lanes add
`manifest_url` to records; this lane edits no record (E22 holds `records/**`).

**The design the lane must map to.**
1. Listing readers, selected by the shape of the response (content type and first bytes, then a
   structural probe), never by host name: CKAN `package_show` (resources: `url`, `size`, `hash`
   or `checksum`), Socrata views JSON (one entry: the `rows.csv` export of that view; `rowsUpdatedAt`
   kept as the listing date), data.gov.tw REST (its `distribution` entries), ArcGIS Feature
   Server (one entry: a `query?where=1%3D1&outFields=*&f=geojson` export with `resultRecordCount`
   bounded by `maxRecordCount`; `editingInfo.lastEditDate` as the listing date; a truncated export,
   `exceededTransferLimit: true`, is recorded as `partial` and never counted as a hashed asset),
   Zenodo, figshare and Dataverse (files with their checksum), GitHub releases (assets), beside the
   existing HTML, S3 XML, text and generic-JSON readers. A reader returns dataset assets only:
   landing pages, API metadata, error bodies and documentation links are excluded, and a test
   per reader asserts the exact asset URLs, names and sizes and the excluded links.
2. Publisher checksums: a file entry gains `publisher_checksum: {algorithm, digest}` when the
   listing states one. Supported algorithms: sha256, sha1, md5 (the verifier computes the
   publisher's algorithm from the same stream beside SHA-256, which stays the recorded `sha256`
   for every consumer, E127 included). A stated digest that matches passes; a mismatch fails the
   check with both digests in the detail; an unsupported algorithm or a malformed digest is
   recorded verbatim with `compared: false` and does not fail. Test cases: match, mismatch,
   absent, malformed, unsupported, each asserting the computed values, the check outcome and the
   resulting level; disabling the comparison must fail a test.
3. Schema: verification/4 (`publisher_checksum` and `compared` on file entries; `partial` on
   generated exports), the /3 schema frozen under `tests/fixtures/schema/verification-3.schema.json`,
   every stored /3 document and the E127 fixtures validated against /4 in a test, the bump in the
   PR title (kernel rule). `inventory` keeps E07's meaning and is not touched.
4. `samples.yaml` gains an entry for every record with a `manifest_url`, with a comment saying
   what the sample is and roughly how large; a test derives the set from `records/` and fails
   when a `manifest_url` record has no policy (the existing test covers the reverse direction
   only). A listing that names one object samples that object.
5. Reasons: the `files-checksummed` and `licence-text-captured` checks each carry a one-sentence
   detail a reader can act on ("no origin.manifest_url", "listing format not recognised (content
   type …, first bytes …)", "robots.txt disallows the listing", "sample would exceed the run budget
   (… bytes)", "no sample for this record in verifier/samples.yaml", "no entry matches the sample",
   "licence page … answered 404"). `osd status` shows for every record below L2 the detail of the
   first L2 check that did not pass. Tests inject distinct causes and assert each record's text;
   a constant string or dropped propagation must fail.
6. Guards stand and are tested: a disallowed listing is never fetched (the opener records every
   URL), a cut sample leaves no partial file and says so, the sample and the E07 inventory share
   one budget; E07's mirror path through `parse_listing` keeps its selection (mirror regression
   tests claimed, `tests/test_mirror.py`, additions only).
7. The verify workflow does not run on pull requests for this lane's changes by itself: the lane
   dispatches `verify.yml` on its branch once (`gh workflow run verify.yml --ref <branch>`), links
   the run and its results in the PR, and treats origin outages as observations (ENGINEERING's
   outage policy), never as a red.

**Acceptance.**
- The dispatched verify run on the branch shows every `manifest_url` record (23 today) with
  either L2 (or higher) and the coverage sentence, or a design-5 reason; at least fifteen at L2 or
  higher unless the run names the origins that were down.
- Reader tests (design 1), checksum tests (design 2), compatibility tests (design 3), policy
  coverage test (design 4), reason tests (design 5), guard and mirror regression tests (design 6):
  all named in the PR with the mutation they catch.
- `make check` green; `make check-full` run once on the branch and reported (it validates STAC,
  not these contracts, and is not cited as their proof).
- `uv run osd status` with the reason column pasted in the PR.
- No record file changed; PR title carries "verification/4".

**Claim.** `src/osd/verify.py`, `src/osd/verifier/**`, `src/osd/cli.py` (status column only), `schema/verification.schema.json` (verification/4), `tests/fixtures/schema/verification-3.schema.json` (new, frozen), `tests/test_verify.py`, `tests/test_mirror.py` (additions only), `tests/fixtures/listings/**`, `tests/fixtures/verification/**`, `docs/program/charters/E23-*STRATEGY.md`, `docs/program/evidence/e23/**`.

**Dispositions** (Codex review `E23-more-datasets-checksummed-CODEX-REVIEW.md`, verdict REWORK; one round, OSD-D8).

| # | Point | Disposition |
|---|---|---|
| F1 | 23 records carry `manifest_url`, not ten; 19 without a policy | Accepted: Context corrected from the records; design 4 derives the set from `records/` in a test. |
| F2 | Level counts need a verification-results commit, exact versus at-least | Accepted: Context cites the published `catalog.verification_commit` and says "exactly". |
| F3 | Recursive JSON already yields CKAN resources | Accepted: Context says what is missing (selection, checksum, non-list shapes), not "nothing usable". |
| F4 | ANH is Socrata views JSON, CPC data.gov.tw REST | Accepted: named as their own shapes with their own fixtures (design 1). |
| F5 | `inventory` already exists | Accepted: removed from the additions; E07's meaning preserved (design 3, S1). |
| D1 | Schema bump mandatory | Accepted: verification/4, /3 frozen, compatibility test, PR title (design 3). |
| D2 | Checksum algorithm contract | Accepted: design 2 (sha256/sha1/md5, same stream, unsupported recorded not compared, SHA-256 kept). |
| D3 | "Every machine-readable dataset reaches L2" impossible | Accepted: Outcome reworded to "attempted and explained". |
| D4 | A files reason cannot explain every L1 | Accepted: both L2 checks carry reasons; status shows the first that did not pass (design 5). |
| D5 | Generated exports need selection and completeness rules | Accepted: bounded query, `partial` on truncation, never an asset when metadata or error (design 1). |
| D6 | Verify comment will not run on the PR | Accepted: branch dispatch, run linked, outages observational (design 7). |
| A1 | "Eight of ten" permits untested readers | Accepted: target set derived; policy coverage test; fifteen of 23 or named outages. |
| A2 | One fixture per reader does not prove selection | Accepted: exact URLs, names, sizes, excluded links; landing-page mutation. |
| A3 | Mismatch-only testing | Accepted: five cases with computed values, outcome and level. |
| A4 | Reason column permits constant text | Accepted: injected causes, per-record assertions. |
| A5 | Guards need fetch and partial-file assertions | Accepted: design 6. |
| A6 | `make check-full` is STAC only | Accepted: reported, not cited as proof. |
| S1 | E07 owns `inventory` | Accepted: untouched. |
| S2 | `parse_listing` changes affect the mirror | Accepted: `tests/test_mirror.py` additions claimed; selection regression tests. |
