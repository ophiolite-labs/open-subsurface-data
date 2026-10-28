## E40 Starter project contract: starter/1, custody/2, verification/7, the validity tests and the published projection — QUEUED (first in the family; before E41; Kernel; strategy at lane open; Codex round closed, REWORK reworked 28 Oct, dispositions below)

Authority: family "Ready for your tools" (owner direction 28 Oct 2026, R-T1 to R-T4); E04 (STAC and
`collections.json`), E06 (manifest/4 and `osd get`), E07 (custody/1, mirror index, tombstones), E09
and Ophiolite E127 (fidelity/1, the L4 rule in `src/osd/verify.py`); OSD-D11 (records state publisher
facts, tools state verification facts), OSD-D12 (derived documents are committed when no job here
regenerates them); the Codex round of 28 Oct (REWORK; every finding accepted, table below).

**Outcome.** The catalogue can describe a starter project: which held files went in (a verified
download or a maintainer's deposit), which decisions were taken for which object, which artefacts
came out for which application and version, under which licence, with the fidelity record that
proves the conversion and the custody that proves the artefacts are held. `make check` refuses a
pack whose inputs are not held files of its record, whose licence is not computable from its inputs,
whose decision log misses a topic for an object, whose artefacts are not in custody or whose
fidelity does not cover its inputs. The build publishes one projection the site (E43) reads whole.
This lane is slice 0 of the family: contracts, fixtures and validators; it uploads nothing.

**Context today (verified in code on `origin/main` `4293cc8`, 28 Oct; Codex-verified).**

- Schemas: record/5 (`schema/record.schema.json`; licence object with name, spdx, url,
  redistribution, attribution as an enum, share_alike, terms with `stated`), manifest/1 to /4
  (`schema/manifest.schema.json`: entries with assets, collection identity and the record-shaped
  licence; `src/osd/get.py:146` writes ATTRIBUTION.md from those fields), custody/1
  (`schema/custody.schema.json`: `origin_href` and `verifier_run` required; `src/osd/custody.py:23`
  hardcodes /1 and needs the file's `url`), fidelity/1 (`schema/fidelity.schema.json`; the L4 rule
  `apply_fidelity` in `src/osd/verify.py` needs the catalogue's own L1–L3 and every fidelity input in
  the verification inventory), verification/6 (file and layer evidence, no deposit payload; check
  names are free strings).
- Build: `src/osd/build.py:111–121` writes `records.json`, `outlines.geojson`, `mirror.json` (the
  public custody index, tombstones excluded as `src/osd/mirror.py:632` does), `collections.json`,
  `stac/`, well grids and tiles. Nothing joins a product to a record.
- Mirror: `src/osd/mirror.py` eligibility (a listing rule plus a non-empty inventory resolved
  against `files`, `:141–165`; the cap rejects 20 GB and above, `:164`), staging, digest comparison
  and tombstones (`:538–567`), `LocalDirectory` and `S3`; `osd mirror eligible|put` (`src/osd/cli.py:201`,
  `:218`); the verify workflow copies eligible records on dispatches on main (`verify.yml:121–133`).
- Tests: `tests/test_fidelity.py`, `tests/test_mirror.py`, `tests/test_schema.py` with frozen earlier
  schemas under `tests/fixtures/schema/` (hash-pinned).
- Ophiolite (`origin/main` `9e34915a8`, 28 Oct): E127 slice 1a is merged (manifest fetch with digest
  check in `ophiolite-platform/services/project_gateway/upload_runs.py`, fidelity/1 document writer
  `ophiolite-sdk/ophiolite/fidelity.py:119`); the remaining E127 slices are queued. Nothing in
  Ophiolite writes a starter document or custody. (E125's real capability matrix is in E42.)

**The design the strategy must map to.**

1. *One document per pack, committed.* `starters/<record id with / as __>__<pack>.json` validates
   against `schema/starter.schema.json` (`starter/1`). Fields: `format`; `id` (`<record id>/<pack>`);
   `record_id`; `title`; `summary`; `recipe` (id, repository, commit, tools name → version);
   `contents[]` (the objects in the pack: `kind` from record/5's enum, `ids[]` as the data names
   them, for example wells by name, one cube by survey name, horizons by name, and a count);
   `inputs[]` (name, sha256, bytes, `held` as `verified` with `verifier_run` and the inventory path,
   or `deposited` with the custody `key`; both forms bind name, size and digest to their evidence);
   `derived[]` (intermediate standard files the recipe made from an input: path, sha256, bytes,
   `from` the input sha256, `how` a sentence; they may be artefacts too); `decisions[]` (`topic` from
   a closed list: crs, vertical-datum, depth-reference, depth-kind, units, nulls, domain, velocity,
   names; `subject` a `contents` id or `pack`; `value`; `source` in publisher/data/chosen; `note`);
   `targets[]` (`application` in opendtect/resinsight/python; `version`; `artefacts[]` each with
   path, sha256, bytes and custody `key`; `import` the path of the script or notebook artefact;
   `oracle` with `compared` sentences, `values` count, `differences` count, `seed`); `licence` (a
   record/5-shaped licence object computed from the inputs, plus `sources[]` carrying each input's
   licence object whole); `fidelity` (path of the committed fidelity/1 document); `built_at`. The
   documents are written by the recipe (Ophiolite half of E42) and committed here like outlines
   (OSD-D12); no job in this repository regenerates them.
2. *custody/2, the contract for what is held.* custody/1 frozen. A custody document has exactly one
   provenance: `origin_href` plus `verifier_run` (a verified download, as /1), or `deposit`
   (`obtained_at`, `by` a role, `publisher_page_url`, `publisher_page_sha256`, `licence_text_sha256`;
   E41 writes it), or `derived` (`pack_id`, `recipe_id`, `from[]` input digests; E42's recipe output
   uploaded through E41's local source). `origin_href: null` without exactly one of `deposit` or
   `derived` is invalid. Readers (`src/osd/custody.py`, the public index in `build.py`, `mirror.py`
   sync) accept both versions; a test loads a mixed /1 and /2 set through index and build.
3. *verification/7, the deposit check shape.* verification/6 frozen. A `deposit` check at level L2
   carries `files[]` (path, sha256, bytes, custody `key`), `obtained_at`, `by`, and the two capture
   hashes; the reason sentence is "deposited by a maintainer from the publisher's download, <date>".
   E41 writes it; this lane defines it and freezes a fixture.
4. *Validity is nine tests, each with its mutation.* (a) Schema validity, live schema; (b) each
   input's digest, name and size are one file of the record's latest verification inventory with
   that `verifier_run`, or one held custody/2 document of that record with that key (tombstones
   refused); another record's file refuses naming the record; (c) each derived entry's `from`
   is an input digest; (d) licence: every input `redistribution: allowed` (any other value refuses
   naming the input and the value), one spdx shared by all inputs or `null` for all (a mixture
   refuses as "unsupported combination" until a policy exists), `attribution: required` when any
   input requires it, `share_alike: true` when any input has it, `sources[]` equal to the inputs'
   licence objects verbatim; (e) decisions: the required topics are derived from `contents` (a
   `wellbore-*` or `tops` object needs crs, vertical-datum, depth-reference, depth-kind, units,
   nulls, names with `subject` that object; a `seismic-3d` object needs crs, domain, units, nulls,
   and velocity when domain is depth; `horizons` need crs, domain, units, nulls); a missing
   (topic, subject) refuses naming both; two lines with the same (topic, subject) and different
   values refuse; (f) each artefact's key, digest and size match a held `derived` custody document
   of this pack (offline, against a captured custody snapshot under `tests/fixtures/custody/`; a
   missing object or a tombstone refuses); (g) each target's `import` names one of its artefacts;
   (h) the fidelity document validates, its `record` equals `record_id`, its input digests equal the
   pack's input digests exactly, every result is converted or partial, and every `output` names a
   `contents` kind; (i) the oracle block has `values` > 0 and `differences` = 0, or the pack is
   `unpublished: true` and the build leaves it out.
5. *The published projection.* `build/catalog/starters.json`: every published pack whole (design 1
   fields) plus the record's title and level; each record in `records.json` gains `starters[]` of
   pack ids. E43 reads these two files and nothing else. `collections.json` and STAC unchanged (a
   named follow-on).
6. *A manifest for a pack.* `osd manifest --starter <pack id>` writes a manifest/4 with one entry
   whose `collection` is the record's, whose `assets` are the pack's artefacts (name = path, href
   = the mirror public URL from custody, sha256, bytes) and the decision log and fidelity documents
   as two more assets, whose `licence` is the pack's computed object; so `osd get` fetches a pack
   and writes ATTRIBUTION.md from the same fields as today. No manifest schema change (lossless
   because the pack licence is record/5-shaped).
7. *Fixtures first.* Under `tests/fixtures/starters/`: a complete F3-shaped pack (one cube, four
   wells, two horizons, three targets, deposited inputs, derived SEG-Y and LAS), a Teapot-shaped
   single-target pack over verified inputs, a captured custody snapshot with /1 and /2 documents and
   one tombstone, and a fidelity document per pack. Frozen copies of starter/1, custody/2 and
   verification/7 under `tests/fixtures/schema/` with hash pins.

**Acceptance.**

1. Discovery: the validator that `make check` runs over `starters/` is the function the tests call;
   a test copies the fixtures into a temporary `starters/` with one invalid document and asserts
   `osd validate` exits 1 naming it; a second test asserts `osd build` refuses to publish that
   document while publishing the valid ones (`starters.json` holds only the valid packs).
2. Inputs: wrong record, wrong `verifier_run`, wrong size, wrong name, tombstoned custody key: five
   mutations, five refusals naming the field.
3. Licence: `restricted`, `unknown`, a value outside the enum, mixed spdx, a dropped `required`
   attribution, `share_alike` computed false over a true input, a `sources[]` entry edited: seven
   mutations, seven refusals.
4. Decisions: removing one well's depth-reference while another well keeps it refuses naming the
   well; a contradicting duplicate refuses; a cube in depth domain without velocity refuses.
5. Artefacts and fidelity: a missing custody object, a tombstone, a size mismatch, an `import` naming
   no artefact, a fidelity with one input missing, with one extra, with a `failed` result, with the
   wrong `record`: eight refusals.
6. Projection: on the fixture build `starters.json` holds the two packs whole and `records.json`
   has `starters` for exactly those two records; an `unpublished` pack is absent from both.
7. Pack manifest: `osd manifest --starter` output validates as manifest/4; `osd get` on it against
   a `LocalDirectory` store fetches every artefact plus the two documents into the stated layout,
   sizes and digests equal, and ATTRIBUTION.md carries the pack's attribution; a wrong path in the
   manifest fails the fetch.
8. Schemas: the three frozen copies validate the fixtures; the live starter schema rejects each of
   three permissive mutations (unknown topic, missing `subject`, artefact without `key`).

**Out of scope.** Writing a pack (Ophiolite half of E42); depositing or uploading anything (E41,
E42); the site (E43); STAC Items for packs (follow-on when a STAC client is shown wanting them);
counting downloads.

**Stop rules.** The lane stops when a validity rule in design 4 cannot be tested offline and without
Ophiolite code (ARCHITECTURE "no Ophiolite code runs here").

**Ownership and dependencies.** Coding lane; paths `schema/starter.schema.json` (new),
`schema/custody.schema.json` (custody/2, announced), `schema/verification.schema.json`
(verification/7, announced), `tests/fixtures/schema/` (frozen copies only), `src/osd/starters.py`
(new), `src/osd/custody.py` (both versions), `src/osd/build.py` (starters join, custody/2 in the
index), `src/osd/mirror.py` (reading custody/2 only), `src/osd/manifest.py` and `src/osd/cli.py`
(`--starter`; `validate` over `starters/`), `starters/README.md` (new), `tests/test_starters.py`
(new), `tests/fixtures/starters/**` and `tests/fixtures/custody/**` (new), `docs/ARCHITECTURE.md`
(one row for the Starters component). Depends on E07 (merged). Nothing else.

**Evidence to inspect.** The mutation list in the PR (one line per refusal above); `starters.json`
on the fixture build; the three frozen-schema hashes; the `osd get` transcript.

**Dispositions of the Codex round (28 Oct, REWORK).**

| # | Finding | Disposition |
|---|---|---|
| 1 | E125 does not create wells or faults; capability overstated | Accepted; the matrix is quoted in E42, E40 no longer claims it |
| 2 | E127's fidelity writer exists at the cited commit | Accepted; Context corrected (slice 1a merged) |
| 3 | manifest/4 is not the pack representation; attribution is an enum | Accepted; design 6: a manifest/4 entry with assets and the record-shaped pack licence, no schema change |
| 4 | a mirror-prefix URL is not custody evidence | Accepted; design 2 custody/2 `derived`, design 4(f) against held custody, tombstones refused |
| 5 | input provenance is only digest membership | Accepted; `held` binds run or key, name and size; design 4(b) |
| 6 | licence computation undefined for disagreement or null spdx; terms dropped | Accepted; design 4(d) policy and `sources[]` |
| 7 | decision coverage has no subject | Accepted; `contents[]` and `subject`, design 4(e) |
| 8 | fidelity matching weaker than existing validation | Accepted; design 4(h) |
| 9–14 | acceptance lines pass vacuously (discovery, digest lookup, licence values, build validation, layout, frozen schema) | Accepted; acceptance 1–8 rewritten with named mutations |
| 15 | deposited spelling and export digests undefined between E40/E41/E42 | Accepted; `derived[]` with lineage here, deposit evidence in E41, conversion in E42 |
| 16 | derived-output custody has no writer | Accepted; custody/2 `derived` here, upload transport in E41, run in E42 |
| 17 | E43 needs a complete projection | Accepted; design 5 publishes the pack whole |
