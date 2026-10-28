# E40 strategy: the starter project contract (starter/1, custody/2, verification/7)

Kernel. Charter `E40-starter-project-contract.md` (Codex round closed, dispositions there win).
Written at lane open against `main` `dbd5650`, 28 Oct 2026; no further review round (brief).

**What a user can do after it merges.** Read the contract a starter pack is held to: a pack
document under `starters/` that `make check` refuses when its inputs are not held files of its
record, its licence is not the one its inputs compute, its decision log misses a (topic, object),
its artefacts are not in custody or its fidelity does not cover its inputs; a site build that
publishes the valid packs in `starters.json`; `osd manifest --starter <pack id>` and `osd get` to
fetch a pack with its ATTRIBUTION.md.

## Re-verification on open (charter context against `dbd5650`)

| Charter fact | Today | Class |
|---|---|---|
| custody/1 hardcoded in `custody.py`, needs `f["url"]` | `custody.py:21,67` unchanged | 0, holds |
| public index excludes tombstones | `mirror.py:633–646` unchanged | 0 |
| build writes records, outlines, mirror, collections, STAC | `build.py:111–121` unchanged | 0 |
| verification/6 checks are free `{name, level, outcome, detail}` | unchanged | 0 |
| fidelity/1, manifest/4 pinned by Ophiolite E127 | not touched by this lane | 0 |
| `make check` has no verification results and no custody documents (they arrive in `pages.yml` from `verification-results`) | `ci.yml`, `pages.yml:23–35` | 2, design consequence below (inbox note 1) |

## Decisions taken inside the claim (each also in the inbox note `e40.md` where it touches a neighbour)

1. **Evidence where it exists.** Rules (b), the evidence half of (d) and (f) need the latest
   verifications and the custody set, which CI's `make check` does not have. `osd validate` runs
   them when the evidence directory is present and otherwise prints one "unchecked here" line
   (records are committed, so a verified input's licence is always checked); `osd build` is strict:
   a pack whose evidence is absent is not published. Pages has the evidence, so nothing reaches the
   site unproven. Tests pass the fixture evidence explicitly (the same function `make check` calls).
2. **custody/2 is the live schema and admits /1 documents** (format enum, `if /1 then` the /1
   shape); the writer in `custody.document()` keeps writing /1 for verified downloads, E41 writes
   `deposit` and `derived`. Key shape unchanged for all three: `mirror/<record>/<sha256>/<name>`.
3. **verification/7**: a check named `deposit` must take the deposit shape (level L2, `files[]`
   with custody `key`, `obtained_at`, `by`, `publisher_page_sha256`, `licence_text_sha256`, the
   reason sentence as a pattern on `detail`); every other name keeps the /6 shape.
4. **Licence policy, made total.** Every input `allowed`; `name`, `spdx`, `url`, `statement`,
   `terms` equal across inputs (absent and null differ) or "unsupported combination" naming the
   field; `attribution` required if any input requires it, else unknown if any is unknown, else
   not-required; `share_alike` true if any is true, stated only when some input states it. The
   pack licence minus `sources` must equal that object. `sources[]` is `{input, licence}` per input,
   in input order, equal to the evidence licence (record for verified, custody for deposited).
5. **Decisions are per object.** A `pack` line is allowed but satisfies no object's topic (the
   charter's rule read literally; a recipe repeats lines for free). Identical duplicates pass.
6. **Name binding.** An input's `name` is the last path segment of its evidence path, made
   path-safe as custody names objects (`custody.object_name`).
7. **Documents as assets.** The build copies each published pack document and its fidelity document
   byte for byte to `build/catalog/starters/`; the pack manifest's two extra assets point there
   (`<site>/data/starters/…`, digest of the committed bytes). In `starters.json` each artefact gains
   `href` from its custody document, so E43 needs no second file.
8. **Fidelity path** is relative to `starters/` (`fidelity/<pack file name>`), confined to it.
9. **Keys come last while unpublished (supervisor answer 6, from Ophiolite E129, which pins the
   merge commit).** E129 writes a pack in two steps: `build` with `unpublished: true` and no
   artefact keys; after E41's derived upload, `finalise` fills each key from the held derived custody
   document (digest and size) and reruns the validator. starter/1 therefore requires `key` on every
   artefact unless `unpublished: true`; rule (f) reports a keyless artefact as unchecked, never
   passed. Acceptance 8's "artefact without key" stays a refusal on a published pack.
10. **One document by path.** E129 runs the validator as a subprocess: `osd validate <file>.json`
   checks that document alone (anywhere on disk; its fidelity path resolves against the document's
   directory; the file-name rule applies only inside `starters/`) against `records/`, the
   verifications in `--vdir` and the custody documents in `--custody`, exit 0 or 1. The command is
   stated in `starters/README.md`.

## Commits (one per design point, each with its tests and mutations in `evidence/e40/mutations.md`)

| # | Design | Content | Acceptance |
|---|---|---|---|
| C1 | — | this strategy | — |
| C2 | 2, 3, 7 | `custody.schema.json` → /2, `verification.schema.json` → /7; frozen custody-1, custody-2, verification-6, verification-7 with hash pins; old files validate | 8 (part) |
| C3 | 1, 7 | `starter.schema.json` (starter/1; C3b: keyless while unpublished, decision 9), frozen copy, fixtures (F3-shaped, Teapot-shaped, custody snapshot /1 + /2 + tombstone, fidelity per pack, generator), `starters/README.md` | 8 |
| C4 | 2 | readers: `custody.py` both versions, mixed set through `public_index`, `sync_custody` and build | design 2 |
| C5 | 4 | `src/osd/starters.py` validator (a–i), `osd validate` over `starters/` and on one document by path | 1–5 |
| C6 | 5 | `starters.json`, `records.json` `starters[]`, document copies; build refuses invalid packs | 1, 6 |
| C7 | 6 | `osd manifest --starter`, `osd get` over a `LocalDirectory` store | 7 |
| C8 | — | ARCHITECTURE row, mutation record | evidence |

Out of scope as chartered: writing packs, uploads, the site, STAC for packs. Stop rule: a rule of
design 4 that cannot be tested offline without Ophiolite code stops the lane (none expected: all
nine read committed files or captured snapshots).
