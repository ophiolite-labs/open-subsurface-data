## E07 Mirror store and custody — QUEUED · Kernel · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: `DECISIONS.md` OSD-D6 (mirror policy); Ophiolite E35 (custody registry of every copy);
OSD-D5 (no bucket before E07; separate Hetzner project); owner action 103 (bucket and keys).

**Outcome.** Datasets whose licence allows redistribution and whose files the catalogue has fully
enumerated and checksummed download from the mirror at full speed with the same checksum, and every
copy we hold has a durable custody document saying what it is, where it came from, under which
licence with which attribution, and how to ask for its removal. Removal leaves a tombstone, and a
removed copy is never re-mirrored by accident.

**Context today (verified 23 Oct, main after PR #9).** No mirror implementation, no custody schema.
50 of 68 records say `redistribution: allowed`. L2 hashes a sample of a listing
(`src/osd/verifier/samples.yaml`), not a whole dataset: Norne's listing names 5 entries and one is
hashed; Poseidon's sample is metadata only. STAC Collection assets carry one origin href each with
`file:checksum` (`src/osd/stac.py`); `osd get` opens that one href (`src/osd/get.py`), and the
manifest reader keeps one href per asset (`src/osd/manifest.py`). F3 is share-alike, behind
registration, without a listing: it is not eligible and not a fixture. No bucket exists for this
project; keys and bucket are owner action 103, in a Hetzner project of its own. `build/` is not
tracked and Pages restores only verification results.

**The design the lane must map to.**
1. Eligibility is a pure function over a record and its latest verification, tested with named
   negatives: `redistribution == allowed`; a complete enumeration of the files to mirror (every
   entry of the listing selected by a `mirror:` rule in `src/osd/verifier/samples.yaml`, each with
   bytes and sha256 from a verification run: `coverage: complete` for that inventory, never a
   whole-dataset claim beyond it); declared size in decimal GB under 20 GB and the summed inventory
   bytes under the same cap; origin reachable at L2. Missing size, missing checksum, blocked origin,
   restricted, forbidden or unknown rights each fail on their own.
2. Storage transport is injected: `LocalDirectory` (slice 1, tests and dry runs) and `S3`
   (slice 2, Hetzner, keys from repository secrets, only in the dispatched `verify` workflow on
   `main`, never on pull-request runs). Layout `mirror/<record-id>/<sha256>/<filename>`; beside it
   `custody/<sha256>.json` (the custody document) and `custody/<sha256>.removed.json` (tombstone).
   Objects are public-read without listing; the public index is regenerated from the custody
   documents at build time, never hand-written.
3. Publication ordering, idempotent: stream origin to a staging key, verify bytes and sha256,
   write the custody document, then move to the public key; a rerun recognises every state and
   finishes or repairs it; an interrupted upload never leaves a public href.
4. Custody document, `schema/custody.schema.json`: record id, origin href, sha256, bytes,
   copied_at, verifier run id, the record's full licence object plus the captured licence text
   sha256 (E02), the attribution lines as `osd get` writes them, takedown contact (repository
   issue template `takedown.yml`), and the removal state.
5. STAC: one logical asset with an alternate location (STAC Alternate Assets extension, `alternate:
   {mirror: {href}}`), one `file:checksum`; manifest/2 carries `alternates` per asset (manifest/1
   still reads); `osd get` tries the mirror first when present, falls back to origin on any failure,
   and reports which location served each file.
6. Takedown is a request: the issue template opens it; a maintainer (the owner, named in
   CONTRIBUTING) approves by a labelled comment; `osd mirror remove <sha256>` then deletes every
   object of that copy, writes the tombstone, and the next build drops the alternate; `osd mirror`
   refuses to mirror a digest that has a tombstone.
7. Cost line in the PR: bytes mirrored, monthly storage and egress estimate at Hetzner prices.

**Slices.** Slice 1 (this lane): everything above on the `LocalDirectory` transport, the schema,
the STAC and manifest/get integration, dry-run upload transcript, custody and tombstone tests,
eligibility over the real records (count of eligible records and their inventory bytes in the PR).
Slice 2 (after owner action 103): the `S3` transport, the workflow step with the secrets, the first
real mirror of the eligible records, the public index on the site.

**Acceptance (slice 1).**
- Eligibility: Norne (allowed, listing of 5, complete rule) eligible when its verification carries
  bytes and sha256 for all five; Volve (unknown) not; a 25 GB fixture not; an `allowed` record whose
  listing has one unhashed entry not; a blocked origin not; each its own test. The unchanged suite
  fails under a mutation that raises the cap to 30 GB and under one that drops the checksum
  requirement.
- Mirror on the local transport of a 3-file fixture: exact asset set in the custody documents,
  bytes on disk equal the origin bytes, one origin request per file, a corrupted stream fails before
  any public key exists; rerun after an interrupted staging finishes without a second origin fetch
  of completed files.
- `osd get` on a manifest/2 with alternates: every file served from the mirror, reported as such;
  with the mirror unreachable, every file served from origin; a mirror file with wrong bytes is a
  `mismatch` from the mirror and then served from origin, never written as verified from bad bytes.
- Custody schema: negative fixtures for missing origin, licence, contact, malformed hash,
  inconsistent size and an invalid removal state, each rejected.
- Takedown: `osd mirror remove` on the fixture deletes the objects (asserted absent), writes the
  tombstone, the rebuilt catalogue has no alternate, `osd mirror` refuses to re-mirror the digest.
- manifest/1 fixtures still read.

**Out of scope.** Seismic chunking (E10); `redistribution: unknown` even if the licence looks
permissive; portal authentication; the real bucket (slice 2).

**Stop rules.** None in slice 1; slice 2 waits for owner action 103.

**Ownership and dependencies.** Coding lane; paths `src/osd/mirror.py`, `src/osd/custody.py`,
`schema/custody.schema.json`, `schema/manifest.schema.json` (manifest/2, announced),
`schema/stac-osd.json` and `schema/stac/**` (alternate assets schema bundled), `src/osd/stac.py`
(alternate hrefs), `src/osd/build.py` (public index), `src/osd/manifest.py`, `src/osd/get.py`
(mirror first, fallback), `src/osd/cli.py` (`mirror` subcommands), `src/osd/verifier/samples.yaml`
(`mirror:` rules), `.github/ISSUE_TEMPLATE/takedown.yml`, `CONTRIBUTING.md` (takedown section),
`tests/test_mirror.py`, `tests/fixtures/mirror/**`. Slice 2 adds `.github/workflows/verify.yml`.
Depends on E06 slice 1 (merged), OSD-D6; slice 2 on owner action 103.

**Evidence to inspect.** The eligibility count over real records; the local-transport transcript;
the custody document for Norne; the `osd get` transcripts from mirror and from origin.

**Dispositions of the Codex round (23 Oct).** Accepted: counts corrected (50 of 68), F3 removed as
input and fixture, external bucket facts stated as owner action not as verified state, sample versus
inventory (design 1, coverage), decimal GB and summed inventory bytes with the cap, one logical asset
with alternate location and one checksum (5), durable custody beside the objects keyed by digest
with tombstones (2, 4), publication ordering and idempotent reruns (3), takedown as a request with a
named approver and no re-mirroring (6), full licence object and attribution in custody (4),
execution in the dispatched verify workflow with injected transports (2), negative acceptance cases
and mutations against the unchanged suite, ownership extended across the E04/E06 interfaces, bucket
provisioning placed here as owner action 103. Refuted: none.
