## E28 Periods and extents for the newer records — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026; E16 (periods from the publishers; its conventions stand),
E21 (the map's time filter), E18 (Items carry their own dates); R3 (records say what the publisher
says); OSD-D7, OSD-D11.

**Outcome.** The map's time filter and the STAC catalogue reach the datasets added since E16: a
person filtering by acquisition years finds the newer surveys and registers, and the first zoom of
every dataset the publisher locates is right.

**Context today (verified 23 Oct, main e103c4c).** 160 records; 90 carry `period`, 136 carry
`region.bbox`. The 70 without a period and 24 without a bbox are listed in
`docs/program/evidence/e28/candidates.md` (written by the supervisor from `records/`). E16's
conventions: one `period` per record, `{start, end}` as the publisher states it (ISO dates or
years), with the publisher's sentence in `notes`; registers get the register's own coverage period
(first year to today, or the stated range); per-feature dates are the outline extractor's (E18);
a dataset whose publisher states no period gets none, and the PR says so. `bbox` is
`[west, south, east, north]` WGS84, approximate, for the first zoom only; a synthetic or
unlocated dataset (SPE models, Marmousi2, UNISIM, Egg, Drogon) gets none and the record's notes
say why. E29 (outlines from the map services) holds the records named in its design 3; do not edit
those.

**The design the lane must map to.**
1. E16 designs 1 to 3 stand. Each record opened on the day, the publisher's sentence quoted in
   `notes` (or `period` left absent with a short "no period stated" note when the note does not
   already say so), nothing computed, nothing inferred from file names.
2. Order: records with a `manifest_url` first (their Collections hold the files people fetch), then
   national registers, then the rest. Every record at L2 without a period is checked.
3. bbox: from the publisher's stated area or map; the 24 without are each either given one with the
   publisher's words or left with a note naming why (synthetic, global repository, unlocated).
4. Nothing else in the record changes; a changed sentence elsewhere is a defect of the lane.

**Acceptance.**
- `uv run osd validate` 160 records, 0 problems; `make check` green.
- Periods: at least 35 of the 70 gain a publisher-stated period; the PR table lists each (record,
  start, end, the publisher's sentence) and names each record left without one and why.
- bbox: each of the 24 handled (given or explained), in a second table.
- Evidence `docs/program/evidence/e28/sources.md` (page, excerpt, UTC time).

**Claim.** `records/**` (`period`, `region.bbox`, `notes` only; not E29's records),
`docs/program/evidence/e28/**`.
