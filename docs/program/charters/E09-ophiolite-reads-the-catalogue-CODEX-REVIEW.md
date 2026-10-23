**1. Verdict: REWORK.** The charter uses a stale F3 fixture and leaves rights mapping, provenance identity and the evidence required to award L4 insufficiently defined.

Verified OSD HEAD: `524586228ce65d8e99447c2b859be8ed9a6ce338`. No files modified.

**2. Factual errors and Context verification**

- **Reader exists:** `src/osd/manifest.py:101–118` implements `read(path)` with schema validation and typed results. It reads a local file, not an address or STAC Collection; those adapters are new work.
- **External Context claims remain unverified:** E85 address intake, E35 upload rights-basis, E57 LAS/DLIS support, E123 ZGY support, E79’s shipped NLOG sample, and repository privacy cannot be established from OSD HEAD. `records/nlog/nlog.yaml:21` merely repeats the sample claim. Require an Ophiolite commit and implementation references before treating these as verified dependencies.
- **F3 acceptance contradicts the record:** `records/terranubis/f3-demo-2020.yaml:9–16` says registration, **CC-BY-SA-3.0**, and contains no statement. Lines 21–22 explicitly explain the correction from 4.0.
- **Four retrievable LAS assets are not established:** F3’s summary describes four wells, not four addressable LAS files (`records/terranubis/f3-demo-2020.yaml:3–5`). The manifest derives assets from Collection assets and represents missing assets as unresolved (`src/osd/manifest.py:163–169`). Use an explicitly supplied offline LAS fixture; retain F3’s actual access and licence facts.

**3. Design objections and concrete alternatives**

- **Rights mapping is incomplete (design 2).** It omits `attribution`, defines only one redistribution case, and turns unknown redistribution into permission for private use. The contract distinguishes allowed/restricted/forbidden/unknown (`schema/manifest.schema.json:35–44`). Preserve all fields and missingness; map each state explicitly through E35’s existing authorization rules without inventing permissions.
- **STAC intake cannot recover the promised rights object.** Collections publish SPDX, a licence link and redistribution, but not statement, attribution or share-alike (`src/osd/stac.py:156–174`). Either make the manifest the sole supported input for this slice or define a version-bound standard link from Collections to the complete rights-bearing resource.
- **A count string is not fidelity evidence (design 3).** It cannot identify converted inputs, outputs, converter version, losses or failed files. Reuse Ophiolite’s existing fidelity/provenance artifact, binding source checksums to output identities and explicit results; let OSD derive the summary.
- **L4 authority is misplaced unless constrained.** The importer must not trust an exported `level` or imported lower-level checks. OSD must retain its own L1–L3 outcomes and compute L4 with `level_from_checks` (`src/osd/verify.py:425–433`). Define partial/sample conversion coverage and rejection of stale or mismatched evidence.
- **A source commit does not uniquely identify this catalogue.** Builds join separately updated verification results (`src/osd/build.py:25–41`; `.github/workflows/pages.yml:22–27`). Preserve the source commit, but also bind provenance to the consumed artifact digest or all build-input revisions.
- **Provenance does not cross the stated interface.** Manifest metadata lacks a version (`src/osd/manifest.py:73–78`), and Collection selections have no Item identity (`:128–131`). Carry snapshot identity through the interface; identify Collection + asset key + checksum, adding Item identity only where established.
- **Ownership excludes necessary contract work.** `--fidelity-from` requires CLI changes; structured evidence/version propagation may require schema changes. Claim those paths explicitly, version changed schema `$id`s, and retain old-file validation tests under the existing `make check`.

**4. Acceptance that can pass without proving the guard**

- **Licence round-trip:** a fixture omitting optional fields passes even if their propagation is broken. Supply distinct values for every field, plus absent/null cases; assert exact values after build → manifest → reader → rights mapping.
- **Four landed files:** counts and kind labels stay green if one file is duplicated or converted values are corrupted. Assert distinct input hashes, output identities, representative values, units and conversion failures.
- **Publication refusal:** an implementation refusing every publication passes. Add an allowed-publication control and assert the specific rights refusal for each restricted case.
- **Schema-valid export + displayed L4:** the schema permits empty checks and does not relate `level` to checks (`schema/verification.schema.json:13–26`); status prints the stored level (`src/osd/cli.py:51–56`). Mutate input hashes, record identity, conversion outcomes and each prerequisite rung; none may yield L4.
- **Removing `statement`:** this is fixture mutation, not proof that the mapper preserves statements; globally requiring the optional field would also pass. Mutate the mapper to drop/replace a supplied statement, while testing legitimate absence separately.
- **Uncovered promises:** no acceptance proves STAC-address intake, provenance propagation, NLOG consistency, partial-conversion reporting or checksum-mismatch rejection. Add offline tests and failing guard mutations within the existing gate.

**5. Scope overlap**

- **E06:** its recorded dispositions already reject the stale F3 assumptions and preserve missing licence fields. Reuse that contract; do not add publisher authentication or proprietary-project extraction to manufacture four LAS files.
- **E12:** copied-input provenance belongs here; persistent source bindings, version comparison and derived-workspace behavior remain E12.
- **E10:** keep fidelity export limited to existing canonical conversions; seismic store conversion and slice serving remain E10.