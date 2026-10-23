## E01 Twenty records from the open lists — QUEUED, next · Records · no strategy

Authority: owner direction 23 Oct 2026 ("combine the SEG open data list and the national
registers, verify the sources, show the real data"); this charter.

**Outcome.** The map lists at least twenty datasets. Each record states publisher, origin, access
mode, licence (name, redistribution, attribution) and kinds in the publisher's words, and each
origin was opened by a person on the day the record was written.

**Context today (verified 23 Oct, scaffold commit).** Nine records exist in `records/`
(equinor/volve, terranubis/f3-demo-2020, rmotc/teapot-dome, nopims/poseidon, nzpam/parihaka,
sodir/factpages, nlog/nlog, nsta/ndr, seg/open-data-wiki). `osd validate` passes. Licence
`redistribution` is `unknown` on five of them. The SEG wiki page cannot be fetched from the VPS
(HTTP 403, OSD-D9); it opens in an ordinary browser.

**The design the lane must map to.**
1. One record per dataset, never per file; a register (Sodir, NLOG, NDR, NOPIMS) is one record
   with `source-list` among its kinds plus one record per named dataset it carries that the SEG
   list names.
2. Candidates, in this order until twenty: the SEG open-data list entries whose origin still
   answers; Penobscot, Kerry 3D, Stratton, Groningen (NAM/NLOG), Netherlands F3 wells, Norne
   (NTNU), SEAM Phase I, Marmousi (synthetic, flagged in `notes`), Dutch and Danish (GEUS) registers,
   Geoscience Australia NOPIMS 3D surveys beyond Poseidon.
3. A dead origin is still a record: `known_issues` says "origin dead on <date>; last mirror
   <url>", and the record stays at L0. Dead links are the point of a verified list.
4. Licence fields: `unknown` when the publisher's page does not state it; never inferred from a
   country. `share_alike: true` whenever the licence is a BY-SA family.
5. Each record's `added` is the day the origin was opened by the author; the PR says who opened it.

**Acceptance.**
- `osd validate` reports `>= 20 records, 0 problems` (counted from `records/*/*.yaml`).
- Every record has `licence.redistribution` in {allowed, restricted, forbidden, unknown} and a
  `licence.url`; at most 8 of the twenty are `unknown` (hand count in the PR).
- `kinds` of every record intersect the Ophiolite E55 registry vocabulary (the schema enum).
- At least 12 records carry a `region.bbox` (the map's extent rectangles).
- The `verify` workflow comment on the PR lists every changed record with a level.
- Validity is three separate tests, each with a mutation, already in `tests/test_records.py`;
  the lane adds none unless the schema changes.

**Out of scope.** Outlines (E03), checksums (E02), mirrors (E07), any schema change (if one is
needed, stop and open a D item).

**Stop rules.** A publisher's page says redistribution is forbidden: record it, do not mirror,
continue. A licence page needs a login to read: `unknown`, note it, continue. More than three
candidates from the SEG list are dead: continue, they are records at L0.

**Ownership and dependencies.** Records lane; paths `records/**`. No dependency.

**Evidence to inspect.** `uv run osd status` output in the PR; the verify comment; a screenshot
of the map list showing the count.
