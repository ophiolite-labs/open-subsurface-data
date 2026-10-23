## E34 Periods and extents for the eighth and ninth twenty — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026; E28 (its charter and conventions stand in full: E16 designs 1
to 3, a place name is not an extent, nothing inferred, nothing computed); E21 (the map's time
filter); E18 (Items carry their own dates); OSD-D7, OSD-D11.

**Outcome.** The 36 datasets added by E31 and E33 reach the time filter and the first zoom the way
the earlier ones do since E28: every one whose publisher states a period or an area carries it.

**Context today (verified 23 Oct, main 53cda59).** 196 records. Of the 36 records E31 and E33 added,
22 carry no `period` and 22 no `region.bbox`; both lists are in
`docs/program/evidence/e34/candidates.md` (written by the supervisor from `records/`). E32 holds
five records' `known_issues` line (va-energy, bcer, sgc, ut-dogm, nd-dmr): not in this list, do not
edit them.

**The design the lane must map to.**
1. E28 designs 1 to 4 stand, applied to the two candidate lists.
2. A register whose publisher states its coverage (first well year to today, or a stated range) gets
   that period with the sentence in `notes`; an inventory that states none gets none.
3. A bbox comes from the publisher's stated area or map (the service extent of a WFS or ArcGIS layer
   is the publisher's statement, with the request in evidence); an offshore regulator's stated
   licence area counts; a country name alone does not.

**Acceptance.**
- `uv run osd validate` 196 records, 0 problems; `make check` green.
- Periods: at least 11 of the 22 gain a publisher-stated period; a PR table lists each (record,
  start, end, the publisher's sentence) and names each record left without one and why. The count
  is a lower bound, never reached by inference.
- bbox: each of the 22 handled (given with the source, or explained), in a second table.
- Evidence `docs/program/evidence/e34/sources.md` (page, excerpt, UTC time).

**Claim.** `records/**` (`period`, `region.bbox`, `notes` only, the 36 records named in the
candidates file; a `known_issues` "no bbox" or "no period" line may be removed where this lane
gives the field), `docs/program/evidence/e34/**`.
