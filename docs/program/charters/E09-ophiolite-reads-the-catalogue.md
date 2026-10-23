## E09 Ophiolite reads the catalogue — QUEUED · Kernel, cross-repo · strategy at lane open · one Codex round

Authority: owner direction 23 Oct ("verified bits … pull into their workspace"); Ophiolite E85
(one intake), E35 (rights-basis), E55 (kind registry), E122 (provenance).

**Outcome.** In an Ophiolite project a person pastes a manifest or STAC collection address into
the intake, the files land through the normal upload run, every landed item carries a
rights-basis filled from the record's licence, and the fidelity record says which files converted
to which canonical type and which did not. That is level L4.

**Context today (verified 23 Oct for this repository; Ophiolite side from program memory, to be
re-verified at lane open).** Ophiolite's E85 intake accepts "an address" as a drop; E35
rights-basis/1 exists on uploads; E57 reads LAS 1.2/3.0 and DLIS; E123 reads ZGY. The Ophiolite
monorepo is private; this repository's reader interface is `osd.manifest.read` (E06). Ophiolite
ships an NLOG sample in its try-it image (E79).

**The design the lane must map to.**
1. Two halves, two repositories, one interface: here, the manifest and STAC are the contract and
   gain nothing Ophiolite-specific; there, an intake address handler recognises `osd.manifest/1`
   and STAC collections.
2. Rights: `licence.{name, spdx, url, statement, share_alike}` map to Ophiolite's rights-basis
   fields; `redistribution: unknown` becomes the rights-basis state that refuses publication
   (E35's refusal state) while allowing private use.
3. Fidelity record: written by the Ophiolite run, exported back as `verification` check
   `canonical-conversion` with detail "<n> of <m> files to <kinds>", so this repository's
   verifier can read it from a file the Ophiolite run publishes (no live coupling).
4. Provenance: each landed item's E122 record names the catalogue item id and the catalogue
   version (git commit of this repository at build time, written into `records.json`).
5. The NLOG sample in E79 and the `nlog/nlog` record agree on kinds and licence text.

**Acceptance.**
- Here: `records.json` carries `catalog_version` (commit); a manifest fixture round-trips through
  `osd.manifest.read` with every licence field intact (test).
- There (Ophiolite journey test): intake of the F3 manifest lands 4 LAS files as wellbore-logs,
  rights-basis shows CC-BY-SA-4.0 with the statement, and a publish attempt of an item from a
  `redistribution: unknown` record is refused with E35's plain-words reason.
- Fidelity: the exported check file validates against `schema/verification.schema.json` and
  `osd status` shows L4 for F3 after `osd verify --fidelity-from <file>`.
- Mutation: removing `statement` from the manifest makes the rights-basis test fail.

**Out of scope.** Workspace references without copying (E12), seismic (E10), any change to
Ophiolite's canonical types.

**Stop rules.** Ophiolite's E85 is not merged at lane open: build the half here, leave the
Ophiolite half as a charter in the Ophiolite queue, mark this epic PARTIAL.

**Ownership and dependencies.** Coding lane here (paths `src/osd/manifest.py`, `src/osd/build.py`,
`src/osd/verify.py`, tests) plus one Ophiolite lane chartered in the Ophiolite program by its
planner. Depends on E06 and Ophiolite E85.

**Evidence to inspect.** The Ophiolite journey test run; the fidelity file; `osd status`.
