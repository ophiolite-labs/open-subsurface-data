## E07 Mirror store and custody — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: `DECISIONS.md` OSD-D6 (mirror policy); Ophiolite E35 (custody registry of every copy).

**Outcome.** Small datasets whose licence allows redistribution download from the catalogue at
full speed with a checksum, and every copy we hold has a custody record saying what it is, where
it came from, under which licence, and how to ask for its removal.

**Context today (verified 23 Oct).** Nothing is mirrored. Two Hetzner S3 buckets exist for the
Ophiolite program; none for this project, and its keys must never reach this one. Records carry
`licence.redistribution`; four of nine are `allowed`.

**The design the lane must map to.**
1. Eligibility is a function, tested: `redistribution == allowed` and estimated size under 20 GB
   (OSD-D6) and `origin` reachable at L2 with checksums. Nothing else is ever copied.
2. Layout: `s3://<bucket>/mirror/<record-id>/<sha256-prefix>/<filename>`, public read, no listing.
3. Custody record `build/custody/<record-id>.json`: files, sha256, bytes, copied_at, origin href,
   licence snapshot (name, url, text sha from E02), takedown contact (a repository issue template).
4. STAC assets (E04) gain a second href with `roles: ["mirror"]`; `osd get` prefers the mirror
   when its checksum matches the origin's.
5. Takedown: an issue with the template removes the files and marks the custody record
   `removed_at`; the catalogue keeps the record at its level with `assets` pointing at origin.
6. Cost line in the PR: bytes mirrored and the monthly storage and egress estimate at Hetzner
   prices, by hand.

**Acceptance.**
- Eligibility test: F3 (allowed, 1.3 GB) eligible; Volve (unknown) not; NDR (unknown, TB) not;
  a fixture with `allowed` and 25 GB not.
- Mutation: flipping the size cap to 30 GB makes the 25 GB fixture eligible (shown, restored).
- After mirroring F3: `osd get` for F3 reports every asset `verified` from the mirror href.
- The custody record validates against `schema/custody.schema.json`.
- Takedown dry run on the fixture removes the mirror href and writes `removed_at`.

**Out of scope.** Seismic chunking (E10), anything with `redistribution: unknown` even if the
licence looks permissive.

**Stop rules.** The bucket needs a key in CI: ask the owner for the repository secret (owner
action), continue with a local directory backend meanwhile.

**Ownership and dependencies.** Coding lane; paths `src/osd/mirror.py`, `schema/custody.schema.json`,
`.github/ISSUE_TEMPLATE/takedown.yml`, `tests/test_mirror.py`. Depends on E06 and OSD-D6; the bucket
and its key on E11.

**Evidence to inspect.** The cost line; the custody record for F3; the `osd get` transcript.
