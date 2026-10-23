Verified against HEAD `030a26b3d59185e3feb73fb937e98e3c760ad35b`. No files modified. References below are repository-relative; “E07” means the reviewed charter.

**1. Verdict: REWORK** — The charter assumes an unavailable F3 input and leaves mirror identity, durable custody, deletion authority and integration ownership undefined.

**2. Factual errors and Context verification**

- E07:11 says “four of nine” records allow redistribution; HEAD has **50 of 68**, counted by opening `records/*/*.yaml`, matching the loader’s selection (`src/osd/records.py:32`). The field itself exists and is required (`schema/record.schema.json:36`, `:41`).
- “Nothing is mirrored” is consistent with the repository: no tracked mirror implementation or custody schema; catalogue assets use verifier origin URLs (`src/osd/stac.py:90`), and retrieval opens that single href (`src/osd/get.py:86`). This does **not** establish that no external copies exist.
- The two Ophiolite buckets, absence of an OSD bucket and actual credential isolation cannot be verified from HEAD. Label these external infrastructure assertions unverified; repository policy is not evidence of deployed state.
- E07:27 assumes F3 is eligible. Its record requires registration, lacks `origin.manifest_url`, and warns that the old 1.3 GB release was replaced (`records/terranubis/f3-demo-2020.yaml:7`, `:19`, `:22`). Missing listing means no checksummed files (`src/osd/verify.py:326`); F3 also has no sampling configuration (`src/osd/verifier/samples.yaml:5`). It cannot satisfy the charter’s current L2 prerequisite.

**3. Design objections → concrete alternatives**

- **Sample versus dataset:** L2 hashes a sample, not the complete dataset (`src/osd/verify.py:367`); current assets even include only Poseidon metadata (`src/osd/verifier/samples.yaml:7`). Define the exact eligible file inventory and preserve `coverage: sampled`; require complete enumeration before promising a whole dataset mirror.
- **Size enforcement:** an estimate alone cannot bound stored bytes. Define decimal GB, reject missing estimates, and enforce an aggregate streaming byte limit before publication; keep measurements in tool output.
- **Asset identity:** “a second href” (E07:19) does not specify a usable contract. The reader preserves one href and discards roles (`src/osd/manifest.py:108`); separate asset keys would download both copies. Define one logical asset with alternate locations, one expected checksum and explicit fallback behavior, using a standard STAC alternate-location representation. Version affected schemas and retain old-manifest validation.
- **Custody durability:** `build/custody/<record-id>.json` names neither durable authority nor copy history. `build/` is ignored (`.gitignore:1`), and Pages restores only verification results (`.github/workflows/pages.yml:22`). Store per-copy custody documents and removal tombstones alongside objects, keyed by full digest; regenerate the public index from those durable facts.
- **Publication ordering:** no rule prevents an uploaded object lacking custody, or a catalogue advertising an incomplete upload. Stage privately, verify bytes and persist custody before publishing the href; make retries idempotent and reconcile interrupted operations.
- **Takedown authority:** an issue must be a request, not deletion authorization (E07:21). Name a maintainer who approves removal; delete every recorded object version, retain the tombstone, rebuild the catalogue, and prevent automatic remirroring.
- **Licence evidence:** name/URL/text hash alone omits the attribution fields already carried by retrieval (`src/osd/get.py:127`). Preserve the complete licence object and captured text with each copy, and publish the required attribution beside the download.
- **Execution boundary:** E07 names neither the upload command nor its authorized network path. Place explicit mirror operations in the existing dispatched `verify` workflow, with an OSD-only credential unavailable to PR runs; inject storage transports into offline tests. No new CI station is needed.

**4. Acceptance lines that permit false positives**

- E07:27–29: the 25 GB case catches a raised cap, but removing the L2/checksum requirement still passes all named cases. Add independently failing cases for missing checksums, unreachable origin, forbidden/restricted rights, unknown size and the exact cap boundary.
- E07:29 must require the **unchanged test suite to fail** under the 30 GB mutation; merely demonstrating changed eligibility proves no guard.
- E07:30: “every asset verified” can quantify over zero assets; printed labels can also lie. Assert a nonempty exact asset set, mirror request counts, expected disk bytes and no duplicate origin fetch; corrupt mirror bytes and require failure without publication.
- E07:31: a permissive custody schema accepts the happy fixture. Require negative fixtures for missing origin/licence/contact, malformed hashes, inconsistent sizes and invalid removal state; demonstrate each guard’s failing mutation.
- E07:32: removing the href and writing `removed_at` still passes if deletion is a no-op. Assert storage objects are absent, deletion failure is reported, origin fallback survives rebuild, and rerunning mirroring does not resurrect removed copies.
- No acceptance proves custody survives restart, interrupted uploads recover, or every held copy has custody; add local-backend failure-injection tests.

**5. Scope and ownership**

- E07:42 assigns bucket/key provision to E11, but E11 explicitly assigns that work to E07 (`docs/program/charters/E11-hosting-and-domain.md:21`). Put provisioning and the owner secret action in E07.
- E07’s STAC and retrieval changes are legitimate integration work, but its claimed paths omit `stac.py`, `build.py`, `manifest.py`, `get.py`, affected schemas/tests and workflows. Extend claims explicitly across the E04/E06 interfaces before implementation.
- Do not add portal authentication to make F3 pass: E06 explicitly excludes it. Use a currently eligible anonymous source for live evidence and synthetic fixtures for eligibility; keep seismic conversion in E10.