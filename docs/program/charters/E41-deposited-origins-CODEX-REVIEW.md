**1. Verdict: REWORK** — Deposit persistence, licence evidence, and catalogue retrieval are underspecified, so the acceptance criteria can pass without delivering a durable, downloadable deposit.

Verified against HEAD **`4293cc854a9b80300db93ff1ef01ffda6f1a412f`**. Product code inspected matches HEAD. No files modified.

**2. Factual errors and Context verification**

- **Wrong function owner:** `level_from_checks` exists in `src/osd/verify.py:667`, not `build.py`. It consumes check outcomes and returns a level string; it neither inspects inventory nor produces reasons. Build reads the stored level (`src/osd/build.py:85`); reasons belong to `src/osd/reasons.py:24`.
- **Inventory is not synonymous with verification files:** eligibility requires a matching mirror rule and a nonempty selected inventory, then resolves its entries against `files` (`src/osd/mirror.py:141–165`). Files alone do not suffice. The cap rejects **equal to** 20 GB too (`:164`).
- **Confirmed F3 facts:** registration, absent manifest URL, licence and replacement-release note match `records/terranubis/f3-demo-2020.yaml:7–22`. Its current L1 ceiling follows from missing `manifest_url` (`src/osd/verify.py:458–460`), not a general prohibition on registration datasets.
- **Confirmed historical dispositions:** F3 was removed from E07 fixtures (`docs/program/charters/E07-mirror-store-and-custody.md:95`) and E09 fixtures (`docs/program/charters/E09-ophiolite-reads-the-catalogue.md:106`).
- **Confirmed mirror/schema facts:** eligibility is pure; copying streams the file URL (`src/osd/mirror.py:126`, `:560`); custody requires both provenance fields (`schema/custody.schema.json:9–10`). Verification/6 has file/layer evidence and no deposit payload (`schema/verification.schema.json:3–65`). Check names themselves are unrestricted strings (`:21`).
- **Host claims checked separately from HEAD:** `df -BG` reports 143 GiB available; the proposed deposit directory is absent. The current owner-actions master and completed file contain no recorded TerraNubis account. These are live observations, not repository facts; the publisher’s current page contents are only corroborated by the record’s note.

**3. Design objections and concrete alternatives**

- **No durable ingest/publication route.** Files live on the VPS, while verification runs on hosted Ubuntu (`.github/workflows/verify.yml:34`). Subsequent verification reconstructs and overwrites the document (`src/osd/verify.py:690`, `:742–750`, `:891–897`). Specify maintainer upload plus durable deposit evidence, import through the existing verification-results flow, and explicit carry-forward/revalidation rules. Claim the necessary workflow paths; add no CI station.
- **Licence capture is incomplete.** Design 1 records hashes; acceptance 1 supplies only one captured page. Existing verification fetches `licence.url`, normalizes and retains its text (`src/osd/verify.py:639–662`, `:728–730`). Require separately identified publisher and licence captures, source URLs, capture dates, retained text and recomputed hashes; a publisher-page hash cannot substitute for licence capture.
- **The level ladder is ambiguous.** Design 2 grants L1 without specifying successful origin reachability and L2 without stating all lower checks must pass. Preserve the sequential rule in `src/osd/verify.py:667–675`; define offline, blocked and dead-origin outcomes explicitly. “Never gives L3” should mean deposit evidence alone cannot establish geometry.
- **Deposits have no catalogue asset route.** STAC only emits top-level files carrying URLs; mirrors are alternates of those assets (`src/osd/stac.py:102–113`). Define mirror-backed STAC assets for deposits without inventing publisher download URLs, then exercise the existing manifest/get path.
- **Ownership omits essential modules.** Custody construction hardcodes `/1` and requires `f["url"]` (`src/osd/custody.py:23`, `:68–75`); reasons recognize named existing checks (`src/osd/reasons.py:20–36`). Claim custody, reasons and relevant integration tests, and provide runtime reading of both custody versions.
- **Network boundary:** `mirror deposit` fetching pages adds a network command outside the supplied AGENTS.md allowlist. Put capture under `osd verify` and keep deposit ingestion local, or explicitly revise that boundary.
- **Local source contract:** specify relative regular-file paths, symlink containment, nonempty inventory and rehashing during upload. Reuse staging, digest comparison and tombstones (`src/osd/mirror.py:538–567`) rather than creating a separate publication path.

**4. Acceptance criteria that miss their intended failures**

- **A1:** changing fixture bytes tests hashing sensitivity, not a code mutation. It permits swapped path/digest associations and wrong sizes. Assert exact path→digest→bytes mappings and demonstrate failure when hashing or association is broken.
- **A2:** tests only licence-hash presence; empty inventory, fabricated hashes, failed L1 checks and stale evidence remain untested. Test those negatives and the separate `reason()` output.
- **A3:** “over 20 GB” misses an erroneous `>` boundary check; `unknown` misses a guard allowing `restricted`. Test exactly `CAP_BYTES`, both forbidden rights values and empty inventory.
- **A4:** object/document counts permit corrupt uploaded bytes and incorrect custody bindings. Read back hashes and sizes; mutate a source after deposit; test tombstone refusal and schema-valid provenance.
- **A5:** old fixtures validating only against frozen schemas proves nothing about production readers. Load mixed custody/1 and custody/2 documents through sync, index and build.
- **A6:** L2, a screenshot and eligibility can pass without uploading any real object. Require mirror readback, custody publication, manifest/get retrieval and survival of a second ordinary verify run.
- **Design 4 has no acceptance guard:** stripping `share_alike` or attribution could leave all six lines green. Assert exact preservation through custody, manifest and ATTRIBUTION.md.

**5. Scope boundaries**

- E40 design 1 already reserves `deposited`; E41 should supply and validate its custody evidence, not redefine starter inputs or pack licence computation.
- E42 design 2 expects this local upload path for **derived artefacts**. Those are not publisher downloads: do not label them with E41’s deposit sentence. Keep derived provenance in E42 and share only transport.
- Ordinary deposit reasons belong to existing E27 presentation; starter cards remain E43. Additional datasets remain E44.