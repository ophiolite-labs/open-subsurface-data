## E41 Deposited origins: a person brings the files the verifier cannot fetch, and the mirror holds what a recipe makes — QUEUED (after E40; before E42; Kernel; strategy at lane open; Codex round closed, REWORK reworked 28 Oct, dispositions below)

Authority: family "Ready for your tools" (owner direction 28 Oct 2026: F3 as the proof of concept);
E40 (custody/2 with `deposit` and `derived`, verification/7 `deposit` check); E07 (mirror,
eligibility, staging, tombstones, takedown; slice 2 merged 28 Oct, PR #76); E02 and E23 (L2 means
files hashed and licence text captured); E27 (reasons); OSD-D6 (mirror only `redistribution:
allowed`, under 20 GB, with a takedown route; never `unknown`); OSD-D9, OSD-D11; OSD-D22 (this
charter's default); the Codex round of 28 Oct (REWORK; table below).

**Outcome.** A dataset whose publisher hands files only to a registered person, and whose licence
allows redistribution, reaches L2 and the mirror: a maintainer who obtained the files from the
publisher deposits them from the VPS into the mirror with custody that says who, when and from which
publisher page; the verifier, on its ordinary runs, finds those custody documents, captures the
licence text as it does for any record, and awards L2 with the sentence "deposited by a maintainer
from the publisher's download, <date>". The same local upload route lets E42 put a recipe's
artefacts into the mirror under `derived` custody. F3 Demo 2023 is the first deposit.

**Context today (verified in code on `origin/main` `4293cc8`, 28 Oct; Codex-verified).**

- `records/terranubis/f3-demo-2020.yaml:7–22`: `origin.access: registration`, no `manifest_url`,
  licence CC-BY-SA-3.0, `redistribution: allowed`, `attribution: required`, `share_alike: true`; the
  page now serves F3 Demo 2023 (7.6 GB, 4.5 GB download). Its ceiling is L1 because it has no
  `manifest_url` (`src/osd/verify.py:458–460`); the verification snapshot of 24 Oct says L0 after a
  502 (TerraNubis outage). E07 and E09 dispositions took F3 out of their fixtures.
- Verifier: runs on hosted Ubuntu (`.github/workflows/verify.yml:34`) and rewrites each record's
  document every run (`src/osd/verify.py:690`, `:742–750`, `:891–897`); `level_from_checks`
  (`verify.py:667`) awards the highest level whose every check passed with no gap; the licence text is
  fetched from `licence.url`, normalised and kept (`verify.py:639–662`, `:728–730`); reasons are
  sentences from named checks in `src/osd/reasons.py:20–36`; the build copies the stored level
  (`src/osd/build.py:85`).
- Mirror: eligibility needs a listing rule and a non-empty inventory resolved against `files`
  (`src/osd/mirror.py:141–165`; the cap refuses 20 GB and above, `:164`); `put` streams from the
  origin URL through staging, digest comparison and tombstones (`:538–567`); custody is built in
  `src/osd/custody.py:23` for /1 from the file's `url`; the build reads custody documents from the
  bucket for the public index (E07 slice 2). STAC emits top-level file assets with mirror copies as
  alternates (`src/osd/stac.py:102–113`); a record with no publisher download URL has no asset.
- Host and owner, read 28 Oct: 143 GiB free on `/mnt/HC_Volume_107082112`; no deposit directory; no
  TerraNubis account in the owner-actions file (items 1–111).

**The design the strategy must map to.**

1. *Deposit is a local upload with custody, network-free.* `osd mirror deposit <record id> <dir>
   --obtained <date> --by <role> --page-url <url> --page <captured html>` runs where the files are
   (the VPS). It refuses unless the record's `licence.redistribution` is `allowed` and the total is
   under the cap (OSD-D6, both forbidden values refused by name, the boundary tested at `CAP_BYTES`).
   It walks `<dir>` for regular files (relative paths, symlinks refused), hashes each, uploads through
   E07's staging and digest comparison to `mirror/<record id>/<sha256>/<relative path>`, and writes
   one custody/2 document per file with `origin_href: null` and a `deposit` block (E40 design 2:
   `obtained_at`, `by`, `publisher_page_url`, `publisher_page_sha256` of the captured page,
   `licence_text_sha256: null` until the verifier fills it). The record file is untouched (OSD-D11).
   The command does no network except the S3 upload, so AGENTS.md's network line gains exactly this
   clause.
2. *Durable evidence is the custody in the bucket.* The verifier, on every run, lists the record's
   custody documents (public URLs, already read for the index) and, when all are deposits, writes
   the verification/7 `deposit` check (E40 design 3) from them: `files[]` with path, sha256, bytes
   and key. Nothing on the VPS is needed after the deposit; a second ordinary verify run reproduces
   the check (acceptance 6).
3. *The ladder is unchanged.* L1 still needs the origin page to answer (a dead or blocked origin
   keeps the deposit at L0 or `blocked` with the deposit named in the reason). L2 needs L1, the
   `deposit` check and the licence text captured by the verifier's existing fetch of `licence.url`
   (its sha256 is written into the check as `licence_text_sha256`); a deposit whose licence text
   could not be fetched stays L1 with "deposited, licence text not captured". A deposit alone never
   gives L3: geometry must come from the data (E03's extractor, in E42 for F3).
4. *Deposits have assets.* For a record whose held files are deposits, STAC assets are the mirror
   copies themselves (href = the custody `href`, with the deposit block's provenance in the `osd`
   extension fields), so the manifest and `osd get` route works unchanged and no publisher URL is
   invented; `share_alike` and the attribution enum travel in the record-shaped licence as today and
   are asserted end to end (acceptance 7).
5. *Derived uploads share the route.* `osd mirror put-derived <pack id> <dir>` uses the same walker,
   staging and custody writer with a `derived` block (E40 design 2: `pack_id`, `recipe_id`, `from[]`
   digests) and keys `mirror/<record id>/<sha256>/<path>`; derived copies are never counted as the
   record's inventory and never give a level. The reason sentence for deposits is never written for
   derived copies.
6. *Where the owner puts the files.* `/mnt/HC_Volume_107082112/osd-deposits/<publisher>/<dataset>/`
   on the VPS, as downloaded, unmodified; the maintainer saves the publisher's page beside it as
   `page.html`. The owner may download on the Mac and copy with scp.

**Acceptance.**

1. On a fixture directory of three files, `deposit` to a `LocalDirectory` store writes three objects
   whose read-back sha256 and bytes equal `sha256sum` and `stat`, and three custody/2 documents with
   exact path → digest → bytes bindings; a test that swaps two digests in the writer's input, and one
   that breaks hashing, both fail validation; a symlink in `<dir>` refuses naming it.
2. Refusals by name: `redistribution: restricted`, `unknown`, total exactly `CAP_BYTES`, empty
   directory, a tombstoned key already present for the same digest (four refusals plus the
   tombstone case).
3. Verifier, offline with an injected custody listing: the `deposit` check lists the three files;
   with the licence fetch stubbed to pass, `level_from_checks` gives L2 and `reasons.reason()` gives
   the deposit sentence with the date; with the licence fetch stubbed to fail, L1 and "deposited,
   licence text not captured"; with the origin check failing, L0 or `blocked` and the deposit named;
   with an empty custody listing, no `deposit` check at all (four tests).
4. Mixed custody /1 and /2 documents load through sync, the public index and the build; a custody
   document with `origin_href: null` and no block refuses; one with two blocks refuses.
5. STAC on the fixture: the F3-shaped record gets one asset per deposited file with the mirror href
   and the provenance fields; `osd manifest` on a selection containing it and `osd get` against the
   local store fetch the files with digests equal and ATTRIBUTION.md carrying attribution
   and share-alike.
6. Real data, after the owner item: `deposit` of F3 Demo 2023 on the VPS, then two verify dispatches
   on main (not one): both show `terranubis/f3-demo-2020` at L2 with the deposit sentence on the map
   and the status page (screenshot), `osd mirror eligible` lists it, and `osd get` on its manifest
   fetches one file from the real mirror with digest equal (transcript).
7. `put-derived` on a fixture directory writes `derived` custody with the pack id and lineage; the
   verifier ignores it (no check, no level change; test).

**Out of scope.** Reading inside the deposited archive (E42, through odbind); accounts with publishers
(the person registers, never the tool); deposits for `restricted` or `unknown`; a second deposited
dataset (E44).

**Stop rules.** The lane stops when the publisher's terms, read on the day from
`https://terranubis.com/datainfo/F3-Demo-2020` and the deed it links, forbid redistribution of the
download or of the files inside it (then F3 is not deposited and E42 looks for the F3 SEG-Y and wells
on an anonymous origin first); when the download is 20 GB or more (OSD-D6).

**Ownership and dependencies.** Coding lane; paths `src/osd/mirror.py` (local walker, deposit and
derived put, eligibility over a deposit), `src/osd/custody.py` (the /2 writer), `src/osd/cli.py`
(`mirror deposit`, `mirror put-derived`), `src/osd/verify.py` (the `deposit` check from custody, the
licence sha into it), `src/osd/reasons.py` (two sentences), `src/osd/stac.py` (deposit assets),
`AGENTS.md` (the network clause), `tests/test_mirror.py`, `tests/test_verify.py`, `tests/test_stac.py`
additions, `tests/fixtures/deposits/**` (new), `docs/program/evidence/e41/**`. Depends on E40
(merged: custody/2 and verification/7 shapes). Owner item: register at TerraNubis and download F3
Demo 2023 to the path in design 6 (acceptance 6 waits for it; 1–5 and 7 do not).

**Evidence to inspect.** Read-back digests against `sha256sum`; the custody documents in the local
store; the two verify runs; the map screenshot; the publisher's terms as read on the day, quoted in
`docs/program/evidence/e41/terms.md`.

**Dispositions of the Codex round (28 Oct, REWORK).**

| # | Finding | Disposition |
|---|---|---|
| 1 | `level_from_checks` lives in `verify.py`; reasons in `reasons.py` | Accepted; Context and ownership corrected |
| 2 | inventory is not "verification files"; cap refuses 20 GB too | Accepted; design 1 and acceptance 2 |
| 3 | F3's ceiling is the missing `manifest_url`; snapshot says L0 | Accepted; Context |
| 4 | no durable ingest route: VPS files, hosted verifier, document rewritten per run | Accepted; design 2: custody in the bucket is the evidence, the verifier rebuilds the check each run; acceptance 6 needs two runs |
| 5 | licence capture incomplete; page hash is not licence capture | Accepted; design 3: the verifier's own licence fetch, page capture separate |
| 6 | ladder ambiguous | Accepted; design 3 and acceptance 3 |
| 7 | deposits have no catalogue asset route | Accepted; design 4 |
| 8 | ownership omits custody, reasons, stac | Accepted |
| 9 | `mirror deposit` fetching pages breaks the network boundary | Accepted; the command is network-free except S3; page captured by the person; AGENTS.md clause named |
| 10 | local source contract (relative paths, symlinks, rehash) | Accepted; design 1, acceptance 1 |
| 11–16 | acceptance lines miss their failures (bindings, negatives, boundary, read-back, mixed versions, real-data proof) | Accepted; acceptance 1–6 rewritten |
| 17 | design 4 had no guard | Accepted; acceptance 5 asserts share-alike and attribution end to end |
| 18 | E42's derived artefacts are not deposits | Accepted; design 5 `put-derived`, separate block, no deposit sentence, no level |
| 19 | starter inputs and pack licence belong to E40 | Accepted; removed from this charter |
