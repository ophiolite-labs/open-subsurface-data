Verdict: **REWORK** — the intent is clear, but the E51 contract is incomplete and conflicts with current lane ownership.

**Context verification**

- **F1 — Partly true.** ArcGIS whole-layer reading exists (`src/osd/verifier/layers.py:87-132`) and WFS 2.0 GeoJSON reading exists (`src/osd/verifier/layers.py:366-416`); both have a 50,000-feature ceiling (`src/osd/outlines/extractors.py:172-175`). Robots are enforced for layer reads (`src/osd/verify.py:385-414`), and all-record verification is sharded (`.github/workflows/verify.yml:199-249`).
- **F2 — False.** “`verify.yml` runs on dispatch only” is incorrect: it also runs for pull requests changing records or outlines (`.github/workflows/verify.yml:15-23`).
- **F3 — True.** Program rule R6 says no timers (`docs/program/PROGRAM.md:98-107`), with OSD-D29 the fixed exception.
- **F4 — False at HEAD.** E46 does not yet define `area/1` or the count rule: it is an open lane (`docs/program/CLAIMS.md:57`), `schema/area.schema.json` and `src/osd/areas.py` do not exist, and the live record schema remains record/5 (`schema/record.schema.json:3-5`).
- **F5 — Not verifiable at HEAD.** The UK/Norway/US service, count, and terms statements are attributed to a controller-local prototype file, not tracked repository evidence. They cannot be verified against the codebase.

**Contract problems**

- **F6 — `area/1` is not sufficient as specified.** E46 defines area features as `area_id`, `name`, optional country, geometry, and a source block (`E46-areas-that-hold-data.md:27-34`). E51 adds `blocks`, per-country retrieval state, and a regulator configuration YAML without defining schemas, versions, or validation. Either extend E46’s contract before it lands, or version `area/1` deliberately; “adds files, not a contract” is false.
- **F7 — The regulator configuration is underspecified.** `areas/licence/<cc>.yaml` has no schema or exact shape: no required protocol, URL/layer cardinality, CRS, query/filter encoding, identifiers, paging rule, source attribution, or output provenance (`E51…:37-44`). It cannot be implemented consistently or safely tested.
- **F8 — The block join is undefined.** Norway says licence layer 616 gets names from layer 802, but gives neither join key nor cardinality/missing/duplicate behaviour (`E51…:25,37-42`). UK also has offshore plus onshore sources while output has one country-level `retrieved` value. Define source-level provenance and the exact join/dissolve rule.
- **F9 — `blocks` has no stable published shape.** The charter does not say whether it is a record field or nested under `areas.licence`, nor define the 26+ case’s object/string/count form (`E51…:51-55,76-77`). E48 and later consumers will otherwise inherit a breaking ambiguity.
- **F10 — The “current” filter is contractually important but untestable as written.** It is only named, not specified per country. Without a declared field/operator/value and a fixture for relinquished acreage, the result can quietly include out-of-scope licences.

**Acceptance and guards**

- **F11 — Acceptance 3 does not prove the stated 20% stop rule.** It tests a 30% drop, not the boundary or a 21% drop; it also does not test replacement when the count is unchanged but identifiers are wholly different (`E51…:49,73-75`). Add mutations for zero, HTTP failure, 20/21% thresholds, and identity churn.
- **F12 — Acceptance 5 is a report, not proof.** It can pass with zero licences holding datasets or zero records gaining blocks (`E51…:78-79`). Set country-specific minimum expected outcomes, or state a justified finding/stop outcome.
- **F13 — Acceptance 7 cannot prove the scheduled operational outcome offline.** A dry branch dispatch only proves diff printing; it does not prove cron triggering, PR creation/update, or standing-issue comment behaviour (`E51…:45-50,83-84`). Unit-test the decision payloads and use a workflow fixture/action test for the GitHub API branch.
- **F14 — Missing guard mutations:** absent/duplicate licence IDs; failed or many-to-many block joins; invalid/non-WGS84 geometry; dissolve failure; missing regulator credit/licence evidence; stale `retrieved`; and a changed “current” filter. Each needs a failing mutation, not only the replacement-file guard.
- **F15 — “No geometry before terms” is only a non-empty-string check.** The proposed validation accepts arbitrary `source.licence` and `source.credit` text and does not bind the file to the cited terms evidence (`E51…:66-69`). Require a source identifier and evidence reference/digest that the validator cross-checks.

**Scope and claims**

- **F16 — Slice 0 conflicts with E46’s live claim.** It requires the “Licences” section of `areas/SOURCES.md` while E46 owns `areas/**` (`E51…:97-99`; `docs/program/CLAIMS.md:57`). “Hand it to the supervisor” is not a path-claim mechanism. Keep slice 0 wholly under `docs/program/evidence/e51/**`, then have E46 or a post-E46 slice merge the source-file change.
- **F17 — Future E51 overlaps E49 today.** E51 claims `AGENTS.md` and `CLAUDE.md` (`E51…:100-103`), currently held by E49 (`docs/program/CLAIMS.md:59`). E51’s dependencies do not require E49, so add that dependency or move the network-policy change to the lane that already owns those files.
- **F18 — The workflow’s GitHub API work needs explicit scope.** The charter adds regulator network access to AGENTS, but opening/updating PRs and commenting on issues are additional network operations. State the workflow-only exception precisely, including permissions and that `make check` never invokes it.

**Gate/network risk**

- **F19 — Reusing verifier readers is not automatically safe.** The shared reader cap rejects BLM’s stated 466,838 cases (`src/osd/outlines/extractors.py:237-240`), so the charter must require the filter to be applied before count/paging and prove it in fixtures. Do not add a higher cap or whole-layer BLM read to `make check`.
- **F20 — Preserve offline build behaviour explicitly.** `make check` runs validation and build in parallel (`Makefile:4-19`). `osd areas read` must remain an explicitly invoked network command; build/validate must only consume committed files, never refresh, fetch terms, or call regulator services.