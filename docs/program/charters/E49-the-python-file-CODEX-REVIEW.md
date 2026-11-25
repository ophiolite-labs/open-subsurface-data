Verdict: **REWORK** — E49 has the right outcome, but its remote-catalogue/API contract, area subsetting, generated-file execution, and lane ownership need to be made implementable and testable first.

### Factual/context verification

- F1. “Verified on `origin/main` `fd69de4`” is stale: `origin/main` is `c3baa16c…`, so the charter must name the reviewed revision accurately.

- F2. Context says `get()` returns outcomes “per entry”; it returns one `Outcome` per *asset* ([get.py:124](/home/epic/src/open-subsurface-data/src/osd/get.py:124), [get.py:129](/home/epic/src/open-subsurface-data/src/osd/get.py:129)). The cited `attribution()` and `summary()` functions do exist ([get.py:183](/home/epic/src/open-subsurface-data/src/osd/get.py:183), [get.py:200](/home/epic/src/open-subsurface-data/src/osd/get.py:200)).

- F3. The remaining context is substantially correct: `from_catalog()` reads a local catalogue directory and local STAC collection files ([manifest.py:209](/home/epic/src/open-subsurface-data/src/osd/manifest.py:209), [manifest.py:217](/home/epic/src/open-subsurface-data/src/osd/manifest.py:217), [manifest.py:223](/home/epic/src/open-subsurface-data/src/osd/manifest.py:223)); CLI `get` accepts a manifest path, not a dataset id ([cli.py:222](/home/epic/src/open-subsurface-data/src/osd/cli.py:222)); and the package exports only `__version__` ([__init__.py:1](/home/epic/src/open-subsurface-data/src/osd/__init__.py:1)). “Not on PyPI” is not verifiable from repository HEAD; it is covered by fixed OSD-D32.

### Contract/API problems

- F4. `catalog=` is underspecified and presently unimplementable without inventing an HTTP catalogue protocol. It may mean a local directory, STAC-root URL, `records.json` URL, or arbitrary URL; current manifest generation requires `records.json` plus `stac/<collection>/collection.json`. The published layout is `data/records.json`, `data/collections.json`, and `data/stac/...` ([build.py:125](/home/epic/src/open-subsurface-data/src/osd/build.py:125), [build.py:133](/home/epic/src/open-subsurface-data/src/osd/build.py:133), [build.py:135](/home/epic/src/open-subsurface-data/src/osd/build.py:135)). Specify accepted forms, relative-address resolution, required files, failure semantics, caching lifetime/location, and an injected catalogue fetcher.

- F5. The proposed public API has no injectable transport, yet acceptance requires offline injected transport and a subprocess running the generated file. A Python object cannot be injected into that subprocess. Define a supported offline mechanism—for example explicit `catalog=` local directory plus an environment-selected fixture transport—or make the generated file use only public, serializable configuration.

- F6. `Dataset.files` is not a stable shape: “path, size, sha256, source, checked: yes/no/no checksum recorded” has neither types nor semantics. Existing retrieval distinguishes `verified`, `fetched`, `mismatch`, `needs-sign-in`, and `origin-dead`, and source can be `disk`, `origin`, or an alternate’s arbitrary name ([get.py:35](/home/epic/src/open-subsurface-data/src/osd/get.py:35), [get.py:105](/home/epic/src/open-subsurface-data/src/osd/get.py:105)). Define immutable public `File`/`Dataset` fields and enums, including partial failure and the exception object for checksum mismatch.

- F7. “Resumable” promises an outcome the existing E06 path does not provide: it writes a temporary file and deletes it after interruption/failure ([get.py:79](/home/epic/src/open-subsurface-data/src/osd/get.py:79), [get.py:100](/home/epic/src/open-subsurface-data/src/osd/get.py:100)). Either define HTTP-range resume and persisted partial-file validation, with tests, or change the promise to idempotent atomic retry.

- F8. `area=` cannot be implemented from the named inputs. E46 will say which *dataset* sits in an area; manifest assets are collection-wide ([manifest.py:231](/home/epic/src/open-subsurface-data/src/osd/manifest.py:231)). Neither the current outlines nor the manifest contract map individual downloadable files to well/block/area. Define and own a versioned per-file listing/membership contract, or remove `area=` from E49 and defer it until such a contract exists.

- F9. Reader behavior is too open-ended for a public API: “CSV and similar,” SEG-Y “handles or paths,” table type, format detection, well-name collisions, and error behavior are unspecified. Also `osd[readers]` has no declared optional-dependency group today ([pyproject.toml:8](/home/epic/src/open-subsurface-data/pyproject.toml:8), [pyproject.toml:18](/home/epic/src/open-subsurface-data/pyproject.toml:18)). Fix concrete supported extensions, return types, lazy-import errors, and optional-dependency pins before later users depend on them.

- F10. The script contract says it is a pure function of “catalogue and ids,” while its per-line source/count and reader call require a defined catalogue projection and format classification. Make the input a typed, versioned projection or have rendering consume the exact manifest/API result; define ordering, duplicate-id behavior, inaccessible datasets, and “first dataset that has a reader.”

### Acceptance and mutation gaps

- F11. Acceptance 4 cannot prove “one code path” merely by comparing byte trees and outcomes. Require a delegation/seam test—for example spy on the shared manifest-to-retrieval adapter—and test that API and CLI use it.

- F12. Acceptance 6 is not offline as written: the generated file has no stated fixture-catalogue/transport configuration. Acceptance 10 is appropriately outside the gate, but should state its network use is an intentional `osd.get` run.

- F13. The mutation list misses the high-risk guards: catalogue URL/file substitution or traversal; malformed dataset id/destination escape; removal of mirror-first ordering; removal of existing-file rehash; access-restricted records accidentally fetching; mismatch leaving an output/partial file; lazy reader import becoming eager; and `area=` falling back to whole-dataset retrieval. The existing downloader already protects asset-key escape and duplicate targets ([get.py:49](/home/epic/src/open-subsurface-data/src/osd/get.py:49), [get.py:57](/home/epic/src/open-subsurface-data/src/osd/get.py:57)); the new API must preserve equivalent protections.

### Scope, claims, and operational risk

- F14. The claims board currently has a direct open-lane path conflict: E46 and E49 both claim `src/osd/cli.py` ([CLAIMS.md:57](/home/epic/src/open-subsurface-data/docs/program/CLAIMS.md:57), [CLAIMS.md:59](/home/epic/src/open-subsurface-data/docs/program/CLAIMS.md:59)). “One function each” conflicts with the stated rule that open lanes never share a path ([CLAIMS.md:3](/home/epic/src/open-subsurface-data/docs/program/CLAIMS.md:3)). Defer E49’s CLI subcommand until E46 merges, or reassign ownership before work starts. Slice 4’s `site/shop.js` deferral is otherwise correctly sequenced after E47.

- F15. The charter should explicitly claim any new catalogue-fetching module and its tests; otherwise the remote-catalogue implementation will be forced into `manifest.py` without a clean boundary. Keep actual site-button work out until E47 merges, as already stated.

- F16. The gate/network rule needs a precise API equivalent. `make check` must remain offline ([AGENTS.md:3](/home/epic/src/open-subsurface-data/AGENTS.md:3)); current policy permits only named commands including `osd get <manifest>` ([AGENTS.md:11](/home/epic/src/open-subsurface-data/AGENTS.md:11)). Amend it to authorize `osd.get` as intentional retrieval, including only catalogue reads and asset downloads, and require injected catalogue/asset transports in all tests. Do not permit `catalog=` to create background refreshes or import-time network activity.

- F17. The “environment without readers” acceptance can accidentally turn the offline gate into dependency installation/resolution. Test lazy-import failure by blocking the optional imports in a subprocess using the already-installed project, rather than creating or synchronizing an environment during `make check`.