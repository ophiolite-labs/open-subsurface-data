# E41 strategy: deposited origins and derived uploads

Kernel. Charter `E41-deposited-origins.md` (Codex round closed 28 Oct, dispositions there win).
Written at lane open against `main` `498adec`, 28 Oct 2026; no further review round (brief).

**What a user can do after it merges.** A maintainer who downloaded a registration-only dataset
whose licence allows redistribution runs `osd mirror deposit <record id> <dir> --obtained <date>
--by maintainer --page-url <url> --page page.html --licence-text licence.html` on the VPS; the files
go to the mirror under custody/2 `deposit`, the verifier's next runs find that custody and award L2
with "deposited by a maintainer from the publisher's download, <date>", STAC lists the mirror copies
as the record's assets and `osd manifest` plus `osd get` fetch them with ATTRIBUTION.md. A starter
recipe (Ophiolite E129) uploads its artefacts with `osd mirror put-derived <pack id> <dir>` and
fills each artefact key from the custody/2 `derived` document that matches its sha256 and bytes.

## Re-verification on open (charter context against `498adec`)

| Charter fact | Today | Class |
|---|---|---|
| F3 record: registration, no `manifest_url`, CC-BY-SA-3.0 allowed, attribution required, share-alike | `records/terranubis/f3-demo-2020.yaml` unchanged | 0 |
| custody/2 shapes (E40 design 2) | merged at 62036fa; but `deposit.licence_text_sha256` is **required, a sha256** (not null until the verifier fills it) | 2, decision 1 |
| verification/7 `deposit` check (E40 design 3) | merged; `licence_text_sha256` required; `detail` pattern on pass | 0 |
| object key `mirror/<record>/<sha256>/<name>` | `custody.object_key`: the name is the path's last segment, path-safe; the custody `path` keeps the relative path | 0, key allocation below |
| verifier reads custody "already read for the index" | custody travels on `verification-results` under `custody/`, so `build/verification/custody/` in every verify job (single and shards); the bucket is never listed anonymously | 1, design 2 reads `<vdir>/custody` |
| the mirror step syncs custody at the **end** of a dispatch on main | `verify.yml` (outside the claim) | 2, decision 2 |
| level ladder, `level_from_checks`, reasons | `verify.py:667`, `reasons.py` unchanged | 0 |
| STAC assets only from `files[]` with a `url` | `stac.py:_assets` | 0, design 4 |
| `stac-osd.json` constrains Collection and Item fields only | asset fields are not constrained; the schema is outside the claim | 1, decision 3 |
| deposit folder | `/mnt/HC_Volume_107082112/osd-deposits/terranubis/f3-demo-2023/page.html` (19,601 bytes, sha256 `edeefc36…`), equal to the live page today | 0 |
| stop rule: publisher's terms | read today, `docs/program/evidence/e41/terms.md`: the download says CC BY-SA 3.0, the deed allows redistribution; the website terms forbid mirroring the *website* | 0, decision 4 |

## Decisions taken inside the claim (each in the inbox note `e41.md` where it touches a neighbour)

1. **The licence text is captured by the person, like the page.** custody/2 requires
   `deposit.licence_text_sha256` as a digest. `deposit` takes `--licence-text <file>` (the licence
   page saved beside `page.html`, e.g. the deed) and hashes it with the verifier's own normaliser
   (`verify.licence_text`), so the two digests are comparable. The custody top-level
   `licence_text_sha256` is the same digest. The verification/7 `deposit` check carries the
   verifier's digest when its fetch of `licence.url` captured text, else the deposit's (the
   `licence-text-captured` check then fails and the level stays L1). No schema change.
2. **The verifier reads `<vdir>/custody/`** (the custody documents that travel with the results):
   offline, injected in tests by pointing at a directory. Supervisor answer 2 (28 Oct) granted
   `verify.yml`: on a dispatch on main naming ids, one step copies the bucket's custody into
   `build/verification/custody` before the verify step, so the first such dispatch after a deposit
   already awards L2 and acceptance 6 counts it. All-record dispatches (shards) keep reading the
   custody their snapshot carries, synced at the end of the previous dispatch on main.
3. **Deposit assets** carry `href` = custody `href`, `file:size`, `file:checksum`, `roles: [data]`, a
   `description` sentence and the provenance as asset fields `osd:provenance: deposit`,
   `osd:obtained_at`, `osd:deposited_by`, `osd:publisher_page_sha256`. Documenting them in
   `stac-osd.json` is a kernel change to a file outside this claim (inbox); the bundled validator
   accepts them today.
4. **Website terms are not dataset terms.** TerraNubis' "Terms & Conditions" forbid reproducing the
   website's design and "mirroring or mining this website"; the dataset page states "License:
   Creative Commons 3.0" linking the BY-SA 3.0 deed, which grants "copy and redistribute the material
   in any medium or format". The deposit stores only the page's digest, never the page. The stop
   rule is not met; the owner may overturn (OSD-D22).
5. **Key allocation** is `custody.object_key` for every route: `mirror/<record id>/<sha256>/<last
   segment of the relative path, path-safe>`; `custody/<sha256>.json` beside it. One custody document
   per digest: two files with the same bytes in one deposit refuse naming both paths, and a digest
   already held for another record, pack or provenance refuses naming the holder. A rerun with the
   same holder and bytes reports `present` and writes nothing (supervisor answer 5).
6. **The pack document gives the lineage.** `put-derived <pack id> <dir> [--pack <document>]` reads
   the starter/1 document (default `starters/<file name>`; E129 passes the one it wrote with
   `unpublished: true`): `recipe_id` = `recipe.id`; each file must be an artefact of the pack with the
   same path, sha256 and bytes, and every artefact must be in `<dir>`; `from[]` is the artefact's
   `derived[].from` when it is a derived file, else every input digest. The custody licence is the
   pack's licence without `sources`. Output: one custody/2 `derived` document per artefact, matched
   by E129 on (sha256, bytes).
7. **What replaces `files-checksummed`.** A record with held deposit custody and no verified copy
   gets the `deposit` check; a `files-checksummed` check that only skipped (no listing, origin not
   reachable, offline) is dropped, so L2 = L1 + `deposit` + `licence-text-captured`. A failing
   `files-checksummed` (a listing that broke) stays and holds the level, as today.
8. **Eligibility over a deposit.** A verification with a passing `deposit` check is eligible without
   a `mirror:` rule (redistribution, cap, L2 and origin rules unchanged); its files are the check's.
   `osd mirror put` reports them `present`, or `refused` "deposit again" when the object is gone;
   it never fetches anything for a deposited file.
9. **Excluded from the walk:** the `--page` and `--licence-text` files when they sit inside `<dir>`
   (design 6 puts `page.html` there). Every other entry must be a regular file; a symlink anywhere
   (file or directory) refuses naming it.

## Flow

```
VPS: osd mirror deposit <rid> <dir> ...          (no network but the store)
  refuse: redistribution != allowed | total >= CAP_BYTES (stat) | empty | symlink
  hash each file (pass 1) -> refuse: duplicate digest | tombstone | digest held elsewhere
  per file: stream to staging/<sha>/<name> hashing again == pass 1 ? custody/<sha>.json : refuse
            -> move to mirror/<rid>/<sha>/<name>
verify dispatch: snapshot custody/ -> verify_record(..., deposits=held deposit docs of rid)
  origin-reachable (L1) | deposit (L2, files from custody) | licence-text-captured (L2)
  -> level_from_checks; reasons: L2 "deposited by a maintainer ...", L1 "deposited, licence text
     not captured", L0/blocked names the deposit
build: STAC assets from the deposit check x mirror index -> manifest -> osd get
```

## Commits (one per design point, each with its tests; mutations in `evidence/e41/mutations.md`)

| # | Design | Content | Acceptance |
|---|---|---|---|
| C1 | — | this strategy; `evidence/e41/terms.md` | stop rule |
| C2 | 1 | `custody.deposit_document`, local walker and `mirror.deposit` with refusals, `osd mirror deposit`, AGENTS.md network clause, `tests/fixtures/deposits/` | 1, 2 |
| C3 | 2, 3 | the `deposit` check from `<vdir>/custody`, ladder, two reason sentences | 3 |
| C4 | 4 | STAC deposit assets, eligibility over a deposit, `put` on deposited files; mixed /1 and /2 through sync, index and build | 4, 5 |
| C5 | 5 | `custody.derived_document`, `mirror.put_derived`, `osd mirror put-derived`; the verifier ignores derived | 7 |
| C6 | — | mutation record, gate timing | evidence |
| C7 | 2, 5 | supervisor answers: custody sync before verify in `verify.yml`; idempotent `put-derived` rerun test | 6, 7 |

Acceptance 6 (real data) waits on owner item 112; the supervisor runs it when the files arrive
(PR body names the commands).
