# E07 strategy: mirror store and custody, slice 1 (Kernel)

Charter: `E07-mirror-store-and-custody.md` (Codex round dispositioned at its end). Base: main c21a47f.
Claim row E07 in `CLAIMS.md`. Slice 1 = everything on the `LocalDirectory` transport; no bucket, no
key, no S3 call anywhere. Open questions for the supervisor: `~/.local/share/osd-program/inbox/e07.md`.

## Shape

```
records/<id>.yaml ─┐   verifier/samples.yaml `mirror:` rule (globs, keyed by record id)
verification  ─────┼─▶ mirror.eligibility(rec, verification, rule)  pure: Eligibility(ok, reasons, bytes)
  files[] + inventory   │
                        ▼  osd mirror put <ids> --store D --public-url U      (opener + transport injected)
  per file: tombstone? refuse │ public+custody? present │ staging verifies? finish │ else stream origin
            → staging/<sha>/<name> → size+sha256 → custody/<sha>.json → move to mirror/<rid>/<sha>/<name>
                        ▼
osd build: custody/*.json ─▶ build/catalog/mirror.json (public index) ─▶ STAC asset `alternate.mirror.href`
osd manifest ─▶ osd.manifest/2 asset `alternates` (manifest/1 written when there are none; /1 still reads)
osd get ─▶ mirror first (checksummed assets only), origin on any failure; each file reports where it came from
osd mirror remove <sha> --request <issue> --approved-by <login> ─▶ objects deleted, custody/<sha>.removed.json
```

- **Inventory.** `mirror.inventory(rec, rule, opener)` reads the listing with the verifier's parser,
  selects every entry the rule matches, hashes each, and returns `files[]` plus
  `inventory: {rule, listed, selected[], coverage}`. `coverage` is `complete` only when every selected
  entry was hashed. The verifier does not call it yet (`verify.py` and verification/3 are outside
  this claim; inbox item 1), so eligibility over the real verifications reports "no inventory".
- **Eligibility** fails on its own, with a named reason, for each of: redistribution not `allowed`; no
  `mirror:` rule; no inventory or an inventory made under another rule; an inventory entry absent
  from `files[]` (unhashed), without bytes, or without sha256; declared `size.bytes_estimate` ≥ 20 GB
  (decimal, when declared); summed inventory bytes ≥ 20 GB; level below L2 or origin `blocked`/`dead`.
  A record that declares no size is judged by its inventory bytes (inbox item 2).
- **Store layout** (keys, `/`-separated): `staging/<sha>/<name>`, `mirror/<rid>/<sha>/<name>`,
  `custody/<sha>.json`, `custody/<sha>.removed.json`. `<name>` is the listing path's last segment,
  path-safe. Transport interface: `exists`, `size`, `open`, `upload(key, chunks)`, `move`, `delete`,
  `put_json`, `get_json`, `keys(prefix)`, `public_url(key)`.
- **Custody/1** (`schema/custody.schema.json`): `format`, `record_id`, `path`, `origin_href`, `key`,
  `href`, `sha256`, `bytes`, `copied_at`, `verifier_run {checked_at, tool_version}`, `licence` (the
  record's object whole, `redistribution: allowed` only), `licence_text_sha256` (or null),
  `attribution[]` (the lines `osd get` writes), `takedown` (issue template URL), `removal` (`held`, or
  `removed` with `removed_at`, `request`, `approved_by`). `custody.problems(doc, name, object_bytes)`
  adds what a schema cannot: key = `mirror/<rid>/<sha>/<name>`, file name agrees with the removal
  state, stored object size equals `bytes`.
- **STAC**: alternate-assets v1.2.0 bundled under `schema/stac/` and mapped; an asset gains
  `alternate: {mirror: {href, title}}` only when a held custody document has the same record and sha256.

## Acceptance to tests (`tests/test_mirror.py`)

| Acceptance line | Test |
|---|---|
| Norne eligible with bytes and sha256 for all five | `test_eligible_norne_complete_inventory` |
| Volve (unknown) not; restricted, forbidden not | `test_not_eligible_rights[unknown,restricted,forbidden]` |
| 25 GB fixture not (inventory sum; declared estimate) | `test_not_eligible_over_cap[inventory,declared]` |
| `allowed` with one unhashed entry not | `test_not_eligible_one_unhashed_entry` |
| missing size, missing checksum each fail | `test_not_eligible_missing_size`, `test_not_eligible_missing_checksum` |
| blocked origin not (and below L2) | `test_not_eligible_blocked_origin`, `test_not_eligible_below_l2` |
| no rule, stale rule | `test_not_eligible_without_inventory_or_rule` |
| 3-file fixture: exact asset set in custody, bytes equal, one request per file | `test_mirror_three_files` |
| corrupted stream fails before any public key | `test_corrupted_stream_leaves_no_public_key` |
| rerun after interrupted staging: no second fetch of completed files | `test_rerun_after_interruption`, `test_rerun_after_crash_before_move` |
| ineligible record is refused | `test_mirror_refuses_ineligible` |
| get: every file from the mirror, reported | `test_get_from_mirror` |
| get: mirror unreachable → every file from origin | `test_get_falls_back_when_mirror_unreachable` |
| get: wrong mirror bytes → `mismatch` from mirror, then origin, never written | `test_get_mirror_mismatch_then_origin` |
| custody negatives: origin, licence, contact, hash, size, removal state | `test_custody_rejects[...]`, `test_custody_fixture_valid` |
| takedown: objects absent, tombstone, no alternate, re-mirror refused | `test_takedown` |
| manifest/1 fixtures still read; /2 carries alternates; /1 with alternates refused | `test_manifest_v1_still_reads`, `test_manifest_v2_alternates`, `test_manifest_v1_refuses_alternates` |
| STAC with alternate validates offline | `test_stac_alternate_validates_offline` |
| `mirror:` rules name real, allowed records with a listing | `test_mirror_rules_name_real_records` |

## Guards and their mutations (each shown red against the unchanged suite, then restored)

cap 20→30 GB; checksum requirement dropped; redistribution check dropped; level/reachability check
dropped; completeness check dropped; hash compare before move dropped; published-state recognition
dropped; tombstone check dropped; mirror bytes accepted unverified in `get`; fallback to origin dropped;
`takedown` not required in custody; build index includes removed copies; manifest/1 alternates
allowed. The PR lists each with the test that failed.

## Evidence (PR body)

Eligibility over the 68 real records from the `verification-results` branch (expected: none, reason
"no inventory"), and again with Norne's inventory run by hand through the verifier's opener (count
and inventory bytes); `osd mirror put opm/norne` on a local directory served on 127.0.0.1 (transcript,
Norne custody document in `docs/program/evidence/e07/`); `osd get` transcripts from the mirror and,
with the server stopped, from origin. Cost line: bytes mirrored, Hetzner storage and egress estimate.
