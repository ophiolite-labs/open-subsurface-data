**1. Verdict: REWORK.** The charter assumes unavailable connector capabilities and an L4 transition that contradicts the current verifier; its derived-input custody chain is undefined.

Verified OSD HEAD: `4293cc854a9b80300db93ff1ef01ffda6f1a412f`.
Ophiolite files inspected at the charter’s cited commit: `9e34915a878a3932bee4f9e3c1bc65a819227d78`. Ophiolite paths below refer to that snapshot. No files modified.

**2. Factual errors about current code**

- **E125 is overstated** (Context lines 23–25). `ophiolite-opendtect/src/ophiolite_opendtect/exchange.py:85` implements well/horizon send; `:94` implements log/horizon get and refuses other directions. Cube/fault exchange is not implemented there. `heads.py:4` explicitly says odbind 7.0.10 cannot create wells; logs require existing survey wells.
- **CI does not establish the claimed live coverage.** Ophiolite `.github/workflows/visual.yml:345` runs the connector suite with explicitly permitted “no pinned OpendTect” skips; `ophiolite-opendtect/ci/complete.py:50` reports live tests skipped. Distinguish offline tests, native qualification evidence, and implemented exchange.
- **“Nothing … drives ResInsight” is false.** `ophiolite-connectors/tools/resinsight-demo.py:13` connects through rips, imports well logs and saves a project; `:36` reopens it. `src/asset_connectors/resinsight.py:68` discovers live logs. A complete starter writer remains new work.
- **E127 is partly implemented, not wholly queued.** `ophiolite-platform/services/project_gateway/upload_runs.py:1649` fetches manifest-listed files, checks digests and ingests them; `intake.py:294` recognizes manifests. No fidelity/1 writer was found.
- **F3’s asserted L1 is not established by HEAD.** Records contain no level. The locally available verification snapshot `3e42932978615aeb6ce818a1a6fbd69aa7ccaea1`, `terranubis__f3-demo-2020.json:5`, says L0 following HTTP 502 on 24 October. Cite the actual newer verification snapshot if L1 is intended.
- **“Next build” does not award L4** (design 6). `src/osd/build.py:84` copies the stored verification level; `src/osd/cli.py:35` applies fidelity explicitly. `src/osd/verify.py:667` requires every lower rung, and `:820` refuses L4 without L1–L3.
- **A failed input does not necessarily remove L4.** `src/osd/verify.py:789` requires reasons for failures and at least one converted input; mixed converted/failed results can pass. All-partial results fail. Removing conversion evidence after genuine L3 would leave L3, not L2.
- **Other Context checks:** both record identities, rights/access fields and IBM’s image-section distinction match their YAML files; no starter schema, implemented deposit command or pack exists at HEAD. E85 intake, E126 lasio/pandas adapters and notebook tests exist (`intake.py:277`, `lasio.py:69`, `scientific.py:114`, `tests/test_gallery.py:41`).
- **Non-code claims:** all five named package versions exist in PyPI metadata; [rips metadata](https://pypi.org/pypi/rips/2026.9.1.2/json) requires Python ≥3.11. The historical installation failure is unproven. The [ResInsight release](https://github.com/OPM/ResInsight/releases/tag/v2026.09.1) confirms 24 September; its asset listing was unavailable. TerraNubis timed out, so survey contents, sample rate and current distribution were not independently verified.

**3. Design objections and concrete alternatives**

- **Exports are not deposited originals** (design 1). An archive custody key cannot authenticate different SEG-Y/LAS digests. E40 validity 2(b) requires each digest in verification or custody; `src/osd/verify.py:781` additionally requires fidelity inputs in the verification inventory. Keep the archive as the source input and record exported files as derived outputs with explicit lineage; settle that contract in E40/E41 before E42.
- **Derived artefact upload has no defined eligibility path** (design 2). E41 extends copying deposited publisher files; it does not authorize treating generated targets as publisher deposits. Define derived-output custody and local upload eligibility in the owning kernel charter, with offline transport tests.
- **L3 has no owner.** E41 explicitly stops at L2, and E42 claims neither outline production nor outline paths. Add a data-derived GeoJSON outline and verification step before fidelity application; preserve the ladder and make failed-pack publication distinct from dataset level.
- **Fresh-survey creation is an unresolved dependency.** Require the Ophiolite half to prove survey creation, four new wells and cube import through supported APIs/standard imports before merging. Do not assume E125 already supplies them.
- **The Python target needs a standalone contract.** `ophiolite-sdk/ophiolite/gallery.py:9` defaults to a synthetic server or connects to a project service. Require the downloaded notebook to read local SEG-Y/LAS using standard libraries with network disabled; gallery execution alone cannot establish this.

**4. Acceptance lines that can pass despite defects**

- **A1:** unchanged well heads can hide missing/deformed trajectories and wrong logs. Assert well/log identities, depth axes, values, units and path stations; mutate a station and a log sample. Require independent SEG-Y/LAS checks from design 3 explicitly.
- **A1:** “200 seeded horizon values” permits one horizon or null-only coverage. Freeze the horizon inventory, sampling population, non-null counts and numeric tolerances; deleting a horizon or changing a sampled value must fail.
- **A2:** a screenshot can show four incorrectly located paths with wrong logs. Add numeric read-back comparisons and mutations; freeze whether seismic is supported rather than allowing an untested omission.
- **A3:** a PNG with four arbitrary markers passes the wording. Assert the inline identity, sample values and well-coordinate projection; corrupt an input and shift a well. Run against downloaded artefacts without a service or synthetic fallback.
- **A4:** a fixture with prewritten L4 can bypass fidelity application entirely. Exercise deposit → genuine outline → fidelity application → build, then mutate fidelity and rebuild. Assert pack rejection separately from the verifier’s resulting level.
- **A5:** matching every listed artefact can pass while omitting the decision log or fidelity document promised in the outcome. Require both in the retrieved inventory and open targets from the retrieved directory.
- **A6:** matching a `chosen` count proves bookkeeping only. Require per-object decisions with stable well identifiers; deleting one well’s depth reference must fail even when another well has that topic.

**5. Scope overlap**

- Source/derived identity, generated-output custody and any changed L4 policy belong in **E40/E41/E09**, not silently inside E42’s `tests/test_starters.py` claim.
- Connector completion and notebook runtime changes belong in **E42-ophiolite-half.md**; its dependency contract must name the missing capabilities above.
- A2’s site wording and the website outcome belong to **E43**, which owns `site/**`. Make them an explicit E43 handoff/DONE condition, not an unclaimed E42 implementation obligation.