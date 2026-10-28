**1. Verdict: REWORK.** The charter relies on incorrect connector capabilities and leaves retrieval, custody and provenance contracts insufficient to enforce its promised validity.

Verified OSD HEAD: `4293cc854a9b80300db93ff1ef01ffda6f1a412f`; tracked implementation files inspected match HEAD. Ophiolite claims checked against the cited `9e34915a878a3932bee4f9e3c1bc65a819227d78`. No files modified.

**2. Factual errors about current code**

- **E125 does not create wells or faults in an OpendTect survey.** Ophiolite `ophiolite-opendtect/src/ophiolite_opendtect/data/matrix.json:8` refuses `well get`; line 112 says fault creation is unavailable; line 115 refuses fault send. Logs, horizons and cube support do not establish the claimed capability.
- **E127’s fidelity writer already exists at the cited commit.** Ophiolite `ophiolite-sdk/ophiolite/fidelity.py:119` constructs fidelity/1; line 174 writes it. `ophiolite-platform/services/project_gateway/tests/test_catalogue_fidelity_e2e.py:52` exercises the writer against the two-well fixture. The QUEUED program entry is stale evidence.
- Other OSD Context claims match the inspected schemas, build, mirror, CLI and workflow: `src/osd/build.py:111`, `src/osd/mirror.py:78`, `:172`, `:310`, `src/osd/cli.py:201`, `:218`, `.github/workflows/verify.yml:121`. Tiles are conditional (`src/osd/build.py:123`, `:230`).
- The named test files exist; `test_mirror.py` has 59 test functions, with parametrization producing additional cases. Earlier schemas and compatibility tests exist (`tests/test_schema.py:37`, `:178`, `:407`). No starter contract or writer was found.

**3. Design objections and concrete alternatives**

- **Manifest/4 is not the proposed pack representation.** Its entries contain `assets`, collection identity and publisher licence fields; attribution is an enum, not arbitrary lines (`schema/manifest.schema.json:66`, `:90`). `src/osd/get.py:146` generates attribution from those fields. Specify an exact, lossless mapping; if impossible, version the manifest contract and claim the reader/schema changes with backwards-compatibility tests.
- **A mirror-prefix URL is not custody evidence.** Design 2e admits nonexistent objects and removed copies. Match each artefact’s record, digest, size and URL against validated held custody, excluding tombstones as `src/osd/mirror.py:632` does; validate offline against a captured custody snapshot.
- **Input provenance is only digest membership.** Design 2b never binds the declared verification run/custody key, size or name to its evidence. Require those bindings and distinguish hashed files from the mirror-selection `inventory` (`src/osd/mirror.py:141`). Define behavior when the latest snapshot changes or is unavailable during offline `make check`.
- **Licence computation is undefined for disagreement or null SPDX.** Design 2c constrains SPDX only “when they agree”; it also drops publisher terms and prescribed statements (`schema/record.schema.json:44`). Preserve source licence objects; refuse unsupported combinations until an explicit policy exists, rather than infer compatibility from `share_alike`.
- **Decision coverage has no subject.** Design 1 provides neither pack kinds nor per-input/per-well scope. One `depth-reference` line can satisfy four wells. Add explicit subjects and included kinds, derive required topics from those, and reject unresolved or contradictory decisions.
- **Fidelity matching is weaker than existing validation.** Design 2f admits another record’s document with matching digests and does not bind outputs to target artefacts. Require record identity, unambiguous input coverage and explicit output linkage; reuse the relevant guards in `src/osd/verify.py:779`.

**4. Acceptance lines that permit false confidence**

- **A1:** `starters/` initially contains only README, so production discovery can validate zero documents while fixture tests pass. Inject an invalid document into the actual discovery path and require the existing gate/build to fail.
- **A2:** A global digest lookup passes both proposed tests. Add wrong-record, wrong-key/run, wrong-size and tombstoned-custody mutations.
- **A3:** Hardcoding rejection of `unknown` passes while `restricted` or `forbidden` slips through. Mutate every non-allowed value, SPDX, required attribution and preserved terms.
- **A4:** Tests only valid publication. Disabling validation inside build still passes; require an invalid pack to prevent publication.
- **A5:** Digest equality misses wrong paths, target collisions and broken import references. Assert schema validity, exact destination layout, sizes, target membership and import-to-artefact resolution.
- **A6:** A frozen schema validating fixtures does not detect a permissive live schema or altered frozen copy. Pin its hash and test live-schema rejection mutations.
- No acceptance line exercises design 2e/2f’s missing artefact metadata, absent import, missing/invalid fidelity, wrong record or failed conversion. Add these within existing pytest, without another CI station.

**5. Scope conflicts with adjacent charters**

- **E41/E42:** E40 accepts deposited spelling before its semantics exist; E42 design 1 uses exported-file digests pointing to an archive custody key. Those digests cannot satisfy E40’s exact-file membership rule. Define archive-to-derived-file provenance jointly; keep deposit implementation in E41 and conversion in E42.
- **E42 artefact publication:** E41 authorizes local upload of deposited publisher bytes, not recipe outputs. E40 implicitly requires derived-output custody without assigning its writer. Assign that contract and implementation explicitly before promising downloadable packs.
- **E43:** Its page needs kinds/counts, decisions and oracle data; E40 design 3 guarantees only targets, licence and URLs. Define the complete published projection in E40 so E43 does not invent a second data contract.