# E09 strategy: Ophiolite reads the catalogue, OSD slice 1 (Kernel)

Charter: `E09-ophiolite-reads-the-catalogue.md` (Codex round dispositioned at its end). Base: main
0c6e019. Claim row E09 in `CLAIMS.md`. This half defines the interface the Ophiolite half consumes
(the OSD manifest file's `metadata.catalog`, manifest/3, and fidelity/1) and the L4 rule; it never touches Ophiolite code. Open
questions for the supervisor: `~/.local/share/osd-program/inbox/e09.md`.

## Shape

```
records/*.yaml + build/verification/*.json
   └─▶ osd build ─▶ records.json {catalog: {source_commit, verification_commit, built_at, records_digest}}
                      records_digest = sha256(canonical JSON of the records array: sorted keys, "," ":", UTF-8)
   └─▶ osd manifest ─▶ osd.manifest/3 {metadata: {catalog}} (copied whole; /1 and /2 when records.json has none)
         └─▶ Ophiolite lands the files (Ophiolite's provenance record, E127), exports fidelity/1
               {format, catalog, record, inputs[]}
               └─▶ osd verify <id> --fidelity-from F [--vdir V]   (offline)
                     own L1–L3 checks kept verbatim; canonical-conversion derived from F, or `fail` + reason
                     level = level_from_checks(checks)  ─▶ verification/3 written back (schema unchanged)
                     osd status ─▶ "L4 (2 of 2 converted)"
```

- **Snapshot identity.** `build()` takes `records_dir`, `source_commit` and `verification_commit`
  (tests inject them). From the CLI: `source_commit` is `git rev-parse HEAD` of the checkout (null
  outside git); `verification_commit` is `OSD_VERIFICATION_COMMIT` (null when unset), which
  `pages.yml` sets from `origin/verification-results` (ruling 1). `verify.yml` is left alone: its build
  is never published and holds results not yet committed, so the old commit would misname them.
  `built_at` is the build's `now`, outside the digest. `osd get` writes a null attribution as "not
  stated by the source" (ruling 2).
- **Rights travel whole.** `_entry` copies the record's licence keys as stated; the manifest/3 licence
  admits `attribution: null` (the /1 and /2 branches still demand a string). `read()` returns
  `Licence.stated`, the keys the manifest states, so absence and null stay distinguishable.
- **manifest/3.** `$id` manifest/3; `format` gains `osd.manifest/3`; `/3` requires `metadata.catalog`, `/1`
  and `/2` refuse `metadata`. `Manifest.catalog` is a `Catalog` or `None`. The `catalog` definition is
  the same object in both schemas (a test compares them).
- **fidelity/1** (`schema/fidelity.schema.json`, new): `format`, `catalog`, `record`, `inputs[]` (at least
  one) of `{sha256, name, result, output: {kind, id, converter, version}, representative[], reason}`;
  `output` required for converted and partial, `reason` for partial and failed; no other key, so a file
  cannot carry a level or a check.
- **The L4 rule** (`verify.apply_fidelity(rid, doc, verification)`), rejecting with a named reason:
  record id is not the one named on the command line; an input hash is not in the verification's
  `files[]`; a file of `files[]` has no result; a partial or failed input has no reason;
  no inputs; no input converted. Named reasons come first, schema problems after them, so each named
  guard is tested by its own message. When it is accepted and the catalogue's own checks stop below
  L3, the check passes, the level stays where `level_from_checks` puts it, and the command says why.
  Coverage is "n of m" (n converted, m files of the latest verification), the first words of the
  check detail; `osd status` reads it from there. verification/3 needs no new field and is unchanged.
- **The snapshot is identity, not a criterion** (charter amended 23 Oct, ruling 3). The check detail
  names the fidelity's `records_digest` and `built_at`; neither refuses. An edit to another record
  keeps L4. A network run carries a passed check forward while it hashed the same sha256 set as the
  verification the fidelity was applied to (`verify.carried_conversion`), and declares it `skip` with
  "files changed" otherwise; Ophiolite then exports again.

## Acceptance to test

| Acceptance line | Test |
|---|---|
| `records.json` carries `catalog` with four fields | `test_build.py::test_records_json_carries_catalog_identity` |
| same inputs give the same digest | `test_build.py::test_records_digest_same_for_same_inputs` |
| one record or the verification changes it | `test_build.py::test_records_digest_changes_with_a_record_or_the_verification` |
| round trip, distinct values, every licence field | `test_manifest.py::test_licence_round_trip_every_field_exact` |
| statement absent stays absent (own test) | `test_manifest.py::test_licence_round_trip_statement_absent` |
| attribution null stays null | `test_manifest.py::test_licence_round_trip_attribution_null` |
| /1 and /2 still read, catalog null | `test_manifest.py::test_v1_and_v2_read_with_catalog_null` |
| /3 with catalog reads | `test_manifest.py::test_v3_carries_catalog_and_reads` |
| catalog on /2 refused; /3 without refused | `test_manifest.py::test_catalog_on_v2_refused`, `test_v3_without_catalog_refused` |
| Norne, the real-record case | `test_manifest.py::test_norne_manifest_3` |
| valid fidelity, L4 "2 of 2" | `test_fidelity.py::test_fixture_fidelity_awards_l4_two_of_two` |
| mismatched input hash | `test_fidelity.py::test_rejects_mismatched_input_hash` |
| mismatched record id | `test_fidelity.py::test_rejects_mismatched_record_id` |
| snapshot is identity (digest, `built_at` recorded, not refused) | `test_fidelity.py::test_snapshot_is_identity_not_a_criterion` |
| an unrelated record edit keeps L4 | `test_fidelity.py::test_unrelated_record_edit_keeps_l4` |
| a verification run with unchanged files keeps it, changed files drop it | `test_fidelity.py::test_verification_run_with_unchanged_files_keeps_the_conversion` |
| failed input without reason | `test_fidelity.py::test_rejects_failed_input_without_reason` |
| L3 absent in own checks | `test_fidelity.py::test_no_l4_when_own_l3_absent` |
| empty inputs list | `test_fidelity.py::test_rejects_empty_inputs` |
| every input has a result, one converted | `test_rejects_inventory_file_without_result`, `test_rejects_no_input_converted`, `test_partial_coverage_one_of_two_awards_l4` |
| `osd status` "L4 (2 of 2 converted)", plain level elsewhere | `test_fidelity.py::test_status_shows_coverage_beside_l4` |
| the command names the reason | `test_fidelity.py::test_cli_fidelity_from_prints_reasons` |
| schema negatives | `test_fidelity.py::test_fidelity_schema_rejects[missing_catalog,unknown_result,output_without_kind,input_without_sha256]` |

## Mutations (each against the unchanged suite, shown red, restored)

hash compare dropped; the snapshot made a criterion again (digest compare added, the amended
charter's form of "digest compare"); level copied (`"L4"` on acceptance); lower checks copied
(own L1–L3 set to pass); record-id compare dropped; carry-forward drops the file comparison; reason guard dropped;
empty-inputs guard dropped; coverage guard dropped; one-converted guard dropped; mapper drops a stated
`statement`; `catalog` allowed on /2; digest over ids only; `built_at` inside the digest. The PR body
lists each with the test that failed.

## Fixture

`tests/fixtures/fidelity/`: `well-a.las`, `well-b.las` (synthetic LAS 2.0, written here); `records/`
(`acme/two-wells` with every licence field distinct, `acme/no-statement`, `acme/null-attribution`,
which is a reader fixture and fails the record schema on purpose); `verification/acme__two-wells.json`
(L1–L3 pass, `files[]` = the two LAS hashes); `fidelity.json`, whose `catalog` is the snapshot of a build
of this fixture at a fixed `now` and fixed commits.
