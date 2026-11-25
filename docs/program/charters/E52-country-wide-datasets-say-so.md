## E52 Country-wide datasets say so: every national register carries the publisher's statement that it covers the country — CHARTERED 25 Nov 2026 (Records; no strategy, no Codex round) — QUEUED after E46 slice 0

Authority: family `MAP-AS-A-SHOP-family.md` (R-S3: "a country-wide dataset counts for the
country"); OSD-D27, OSD-D35; E46 (record/6, `region.national`).

**Outcome.** The map no longer guesses which datasets are national from the size of a box. A
record whose publisher presents it as covering a country says `region.national: true`; the build
counts it for that country, and the shop draws the country for it rather than a rectangle or a
dot in the middle of the land.

**Context.** 236 records; the prototype's guess (box at least a quarter of the country's box) is
the starting list, not the answer. record/6 lands with E46 slice 0.

**The work.**

1. For every record, decide from the publisher's own page (the `origin` page already recorded,
   re-opened by the verifier's reader, never from memory): does the publisher present this as the
   register, archive or survey of the whole country (or of the whole national offshore)? If yes,
   `region.national: true` and `region.country` set. If the dataset is a state's or province's
   register, it is not national: leave it; its bbox and outlines place it (E46). If the page
   cannot be opened, leave the field out and list the record in the PR.
2. A sentence in `notes` only where the call is not obvious (for example "offshore only").
3. `docs/program/evidence/e52/national.md`: one line per record set to national, with the
   publisher's phrase quoted and the page address; and the list of records the prototype guessed
   national that are not, with the reason.

**Acceptance.**

1. Every record validates as record/6; no field other than `region.national`, `region.country`
   and `notes` changes (the diff is checked by a one-off script whose output is in the PR).
2. Each `national: true` has its quoted phrase in `national.md`; a human-check line states that
   the licence fields were not touched.
3. The PR states: how many records are national, per country; how many of the prototype's guesses
   were kept and dropped; and the build's count of datasets placed per kind before and after
   (from `areas.json`, once E46 slice 1 has merged; before that, the fixture build).
4. The verify comment on the PR shows no level changed by this lane.

**Out of scope.** New records; periods; bboxes; state and province registers as their own flag
(the province layer places them by position).

**Ownership and dependencies.** Records lane. Paths: `records/**` (`region.national`,
`region.country`, `notes` only), `docs/program/evidence/e52/**`. Depends on E46 slice 0.
