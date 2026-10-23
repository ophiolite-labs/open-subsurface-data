# E19 strategy: vocabulary from the records lanes (Kernel, small)

Charter: `E19-vocabulary-from-the-records-lanes.md` (Codex round dispositioned at its end). Base: main
20750f4. Claim row E19 in `CLAIMS.md`. Open questions: `~/.local/share/osd-program/inbox/e19.md`.

## Shape

```
records/*.yaml (record/3: kinds += potential-fields, access += purchase, licence.terms?)
   └─▶ osd build ─▶ records.json (licence copied whole, terms included)
         ├─▶ stac.write_catalog ─▶ Collection {osd:access: purchase, keywords: [..., potential-fields]}
         │                         stac_extensions: stac-osd v2 URL (v1 URL still maps, still validates)
         ├─▶ osd manifest ─▶ osd.manifest/4 only when an entry carries purchase or terms, else /1–/3 as today
         │     └─▶ osd.manifest.read ─▶ Licence.terms = Terms(stated, duration?, review?, expires?, present)
         │           └─▶ osd get ─▶ ATTRIBUTION.md: "- Terms, as the record states them:" under the licence lines
         └─▶ site/app.js select mode ─▶ the same entry, the same terms object, /4 with metadata.catalog
osd status ─▶ "L1 (terms expire 2027-01-01)" for an absolute licence.terms.expires (injected clock)
```

- **record/3.** `$id` `.../record/3`. `kinds` gains `potential-fields`; `origin.access` gains `purchase`;
  `licence.terms` is closed: `stated` (string, required), `duration` (string|null), `review_before_publication`
  (bool|null), `expires` (`YYYY-MM-DD` pattern and `format: date`, or null). Absent and null differ and
  both travel. record/2 is frozen at `tests/fixtures/schema/record-2.schema.json`; every current record
  minus its record/3 values validates under it. Unquoted YAML dates are not coerced (`records.py` is not in
  the claim): an unquoted `expires` is refused by the schema, never misread.
- **manifest/4.** `format` gains `osd.manifest/4`; /4 carries `metadata.catalog` like /3; access enum and the
  licence allowlist gain `purchase` and `terms`; /1–/3 refuse both, so an old manifest means what it meant.
  `from_catalog` writes /4 only when an entry needs it (the E127 /3 fixtures stay byte-equal). Python and
  browser allowlists (`LICENCE_FIELDS`) gain `terms`, copied whole: the record's keys, nothing added.
  `Licence.__post_init__` turns a terms mapping into `Terms`, so custody's attribution (E07) carries it too.
- **STAC.** stac-osd `$id` becomes `.../schema/stac-osd.json?v=2` (raw.githubusercontent ignores the query,
  so the address still resolves to main's file); `osd:access` gains `purchase`; `stac_extensions` accepts the
  v1 or v2 URL and the schema map sends both to `schema/stac-osd.json`, because online the v1 URL resolves to
  this same file. v1 is frozen at `tests/fixtures/schema/stac-osd-1.json`. `stac.py` changes the extension
  constant only; access and kinds already pass through.
- **status.** `expires` is a UTC calendar day; terms hold through its end. today < D: `terms expire D`;
  today == D: `terms expire D (today)`; today > D: `terms expired D`; null/absent: nothing; unreadable:
  `terms expire ? ('x' is not a date)`. No issue automation.
- **new.py.** The access, redistribution, attribution and listed_by comments are generated from the schema enums.
- **Records.** The six edits of design 5, each citing the record's own text (table in the PR).

## Acceptance → tests

| Acceptance line | Test |
|---|---|
| record/3: each new value validates | `test_schema.py::test_record_3_admits_the_new_values` |
| terms without `stated` refused | `test_schema.py::test_terms_without_stated_refused` |
| `expires` not a date refused | `test_schema.py::test_expires_not_a_date_refused[...]` |
| unknown kind or access refused (terms closed) | `test_schema.py::test_unknown_values_refused[...]` |
| record/2 fixtures validate under record/2 | `test_schema.py::test_record_2_files_validate_under_record_2` |
| purchase + full terms round-trip build → manifest → read, exact values and absence | `test_manifest.py::test_purchase_and_terms_round_trip`, `::test_terms_absence_and_null_travel` |
| manifest/1–3 fixtures still read; /1–/3 refuse the new values | `test_manifest.py::test_manifest_1_to_3_still_read`, `::test_new_values_refused_below_v4` |
| `osd get` writes the stated terms into ATTRIBUTION.md | `test_manifest.py::test_attribution_carries_the_terms` |
| browser path emits the same terms object | `site.test.mjs` "select: a purchase dataset with terms …" (via `manifest_roundtrip.py`) |
| STAC: Collection carries `osd:access: purchase` and the keyword, validates offline | `test_schema.py::test_stac_collection_carries_purchase_and_keyword` |
| a stac-osd/1 file still validates | `test_schema.py::test_stac_osd_1_collection_still_validates` |
| status: past, today, future, null, absent, malformed | `test_schema.py::test_status_terms_expiry[...]` |
| site: potential-fields chip appears, filters in and out | `site.test.mjs` "kinds: a potential-fields chip …" |
| verification unchanged for request → purchase | `test_schema.py::test_verification_identical_for_request_and_purchase` |
| scaffold comments read from the schema | `test_schema.py::test_new_scaffold_comments_list_the_schema_values` |
| six record diffs exact; 92 records, 0 problems | `test_schema.py::test_the_six_records_state_the_new_values`, `osd validate`, evidence diff |

## Guards and their mutations (each shown red, then restored; `docs/program/evidence/e19/mutations.txt`)

1. record schema: `terms.required` emptied → `test_terms_without_stated_refused`.
2. record schema: `expires` pattern and format dropped → `test_expires_not_a_date_refused`.
3. record schema: `terms.additionalProperties` true → `test_unknown_values_refused`.
4. `manifest.py` `LICENCE_FIELDS` without `terms` → `test_purchase_and_terms_round_trip`.
5. `site/app.js` `LICENCE_FIELDS` without `terms` → site select test.
6. manifest schema: the below-/4 refusal dropped → `test_new_values_refused_below_v4`.
7. `cli.py` expiry comparison dropped → `test_status_terms_expiry[past]`.
8. stac-osd: `purchase` not in the enum → `test_stac_collection_carries_purchase_and_keyword`.
9. stac-osd: `stac_extensions` accepts the v2 URL only → `test_stac_osd_1_collection_still_validates`.
10. `new.py` access comment hard-coded to the record/2 list → `test_new_scaffold_comments_list_the_schema_values`.
11. `get.py` terms lines dropped → `test_attribution_carries_the_terms`.
12. `manifest.py` reader fills absent terms keys with None → `test_terms_absence_and_null_travel`.
13. `records/_template.yaml` access comment without `purchase` → `test_template_access_comment_lists_the_schema_values` (added on the supervisor's ruling 7).

## Outside the claim, named

Raising `$id` to record/3 turns two existing asserts red (`tests/test_outlines.py:517`, `tests/test_stac.py:318`
read the live schema's `$id` as `/record/2`). Both are E18's paths; the one-token edits are in this PR and in
the inbox note; E18, merging second, rebases over them.
Granted with `tests/test_report.py:123` (the record/2 access enum in an `osd new` message) on the inbox answer.
