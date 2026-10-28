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
  entry was hashed. `verify_record` calls it for records with a `mirror:` rule (Norne only, ruled
  23 Oct), sharing the run's 2 GB budget, and writes verification/3 (`inventory`; /2 still reads).
  Real verifications written before this merge carry no inventory: "no inventory" until the next run.
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
| the verifier writes the inventory within the run budget; verification/2 still validates | `test_verifier_writes_complete_inventory`, `test_inventory_counts_against_the_run_budget`, `test_verification_2_still_validates` |
| no public copy without a valid custody document; interrupted takedown | `test_no_public_copy_without_a_valid_custody_document`, `test_interrupted_takedown_already_drops_the_copy_and_reruns` |

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

## Slice 2: the S3 transport, the workflow step, the first real mirror (base main aaa30e7)

Claim row E07s2. Owner action 103 done 28 Oct: secrets `OSD_S3_ACCESS_KEY`, `OSD_S3_SECRET_KEY`,
variables `OSD_S3_BUCKET` (osd-mirror), `OSD_S3_ENDPOINT` (https://fsn1.your-objectstorage.com). The
keys exist only in GitHub; no test, log or file here ever holds one. Inbox: `inbox/e07s2.md`.

```
verify dispatch on main ─▶ osd verify ─▶ osd mirror eligible ─▶ osd mirror put <ids> --store s3://osd-mirror
   (secrets by name)                                            │  S3 transport: stdlib urllib + SigV4
                                                                ▼
     staging/<sha>/<name> (private) ─ verify size+sha256 ─ custody/<sha>.json (public-read) ─ copy ─▶ mirror/<rid>/<sha>/<name> (public-read) ─ delete staging
                                                                ▼
     osd mirror custody --out build/verification/custody  (every custody document, read with the keys)
                                                                ▼
     verification-results branch (custody/ beside the results) ─▶ pages.yml moves it to build/mirror/custody ─▶ osd build ─▶ mirror.json + STAC alternates
verify dispatch on a branch ─▶ osd mirror put --dry-run: HEAD bucket, HEAD per key; nothing written
```

- **Transport, no dependency.** `mirror.S3(bucket, endpoint, region, access, secret, public_url,
  send=)`: the same methods as `LocalDirectory`, path-style requests signed with SigV4 by
  `hashlib`/`hmac` (payload sha256 signed, never `UNSIGNED-PAYLOAD`), region the endpoint host's first
  label (`fsn1`; Hetzner refuses a mismatched one). `send(method, url, headers, body)` is the one
  network seam: tests inject an in-memory S3 (`FakeS3`) that checks every signature; the signer is
  also pinned to AWS's published SigV4 example. `upload` streams: parts of 16 MiB held in memory,
  one `PutObject` when the file is smaller, multipart otherwise, aborted on any error (an origin
  failure mid-stream leaves no object). `move` = `CopyObject` (`UploadPartCopy` in 1 GiB ranges above
  5 GiB) then `DELETE`; a 200 whose body is `<Error>` is a failure. `keys` = `ListObjectsV2` with
  continuation. The `--store s3://<bucket>` spec selects it; keys and endpoint from the environment.
- **Ordering on S3** is slice 1's `_put_one`, unchanged: tombstone refuses; custody + public object
  is `present`; a complete staging object finishes without an origin fetch; else stream to
  `staging/` (private), compare size and sha256, write `custody/<sha>.json`, copy to the public key,
  delete staging. A crash at any step leaves at most a private staging object or a custody document
  without its public object; the rerun finishes either. The public key is guessable from the
  catalogue, so nothing is written there before the bytes are verified.
- **Public read without listing.** `mirror/` and `custody/` objects are written with
  `x-amz-acl: public-read`; `staging/` is private; the bucket stays unlistable. After a put the
  workflow GETs each new href anonymously and the bucket root anonymously (must be 403).
- **Custody to the build without public listing.** The key-holding step lists `custody/` and writes
  every document (live and tombstones) into `build/verification/custody/`, refreshed whole each run,
  so it travels on the `verification-results` branch (OSD-D5's channel); `pages.yml` moves it to
  `build/mirror/custody/`, where `osd build` already reads it. Pages holds no secret. A failed mirror
  step keeps the previous custody set (still true: only a takedown removes a copy, and the takedown
  job refreshes it too).
- **Where the keys are.** Only the `verify` workflow, only on `workflow_dispatch` (never
  `pull_request`); the put and the takedown run only on `refs/heads/main`; a branch dispatch runs
  `--dry-run`, which reads.
- **Takedown.** A `takedown` job (dispatch on main, inputs sha256 + issue URL) refuses unless the
  issue carries `takedown-approved` added by @tuna-soup, then `osd mirror remove` on S3 and the custody
  refresh. Inbox item 2.
- **Cost line.** First dispatch: Norne, 5 files, 1,342,194 bytes (NLOG allowed since 27 Oct but has no
  `mirror:` rule). Hetzner Object Storage: EUR 6.49/month base excl. VAT with 1 TB storage and 1 TB
  egress included, extra storage EUR 8.70/TB-month, extra egress EUR 1/TB, API calls free: the base
  fee only until the mirror passes 1 TB or 1 TB of downloads a month.

| Acceptance (slice 2) | Proof |
|---|---|
| SigV4 matches AWS's published example | `test_sigv4_matches_aws_example` |
| S3 transport passes slice 1's publication tests | `test_s3_*` against `FakeS3` (three files, corruption, reruns, takedown) |
| multipart above the part size; aborted on an origin failure | `test_s3_multipart_upload`, `test_s3_origin_failure_aborts_multipart` |
| staging private, public and custody objects public-read | `test_s3_acl_on_public_keys_only` |
| copy errors inside a 200 fail | `test_s3_copy_error_in_200` |
| dry run writes nothing | `test_put_dry_run_writes_nothing` |
| custody refresh feeds the build | `test_custody_sync_feeds_the_build` |
| keys only on a dispatch, put only on main | `test_workflow_keys_only_on_dispatch` (reads verify.yml) |
| real bucket readable from a branch dispatch | branch dispatch run id (PR) |

Mutations (slice 2 part of `evidence/e07/mutations.md`): signature over a wrong canonical request;
payload hash unsigned; no abort on failure; copy error body ignored; ACL on staging; dry run uploads;
custody refresh keeps stale documents; workflow put on a branch.
