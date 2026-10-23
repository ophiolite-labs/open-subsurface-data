## E17 Twenty records: Africa, the Middle East, Asia, Canada, and the open seismic and model sets — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026 (open lists plus national registers); E13 and E14 findings in
`docs/program/HANDOFF.md`; OSD-D7, OSD-D9, OSD-D15.

**Outcome.** The map lists at least eighty-five datasets and the list of countries grows past the
Atlantic and North Sea basins: Africa, the Middle East, South and East Asia, Canada, and the open
seismic and reservoir model sets that researchers cite but have no catalogue entry.

**Context today (verified 23 Oct, main after PR #12).** 68 records from 41 publishers in 18
countries. Unreached on 23 Oct (retry once, not required): BRGM, NRCan GDR, CNSOER, Queensland GSQ,
AOGCC, SEG-hosted sets (SEAM, Stratton, Viking Graben), LBEG. SEG wiki and NOPIMS answer 403 from
this host (blocked, OSD-D9). Periods (E16) are part of record/2: a new record states `period` when
the publisher states one, else leaves it out. Every record that an open lane holds is out of this
lane's reach: none at lane open (E07 touches no records; check `CLAIMS.md`).

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1 stand (one record per dataset or register; origin
   opened on the day; blocked is not dead; licence never inferred; bbox when the publisher states
   an extent; `period` when stated; no schema change; wants go to `notes` and the PR).
2. Candidates, in this order until twenty, each opened on the day: Canada (NRCan GDR retry, Alberta
   AER open data, BC Energy Regulator, Nova Scotia offshore data, Newfoundland C-NLOPB data
   centre), Africa (Petroleum Agency South Africa, Namibia NAMCOR open data, Nigeria NUPRC where a
   licence is stated, Ghana Petroleum Commission data), Middle East (Oman MEM open data, Israel
   Ministry of Energy petroleum data), South and East Asia (India NDR, Indonesia MIGAS open data,
   Japan JOGMEC open data, Korea KIGAM geoscience data), open seismic sets with a publisher page
   (SEAM Phase I, Stratton 3D, Viking Graben line 12 via SEG retry, the Overthrust model, the
   SEG/EAGE salt model, the Marmousi original), reservoir model sets (OLYMPUS, UNISIM-I and II,
   Egg model, Brugge, PUNQ-S3, the SPE11 CSP), ocean drilling archives not yet listed (IODP Bremen
   Core Repository, Kochi), and any E13 or E14 leftover that now answers. Aggregator cap: three
   records per publisher; a university host counts as one publisher.
3. A publisher that only lists other datasets gets one `source-list` record (E14 design 3).

**Acceptance.**
- `uv run osd validate` reports `>= 86 records, 0 problems`.
- Hand counts in the PR: new countries not present before (at least six), of which at least two in
  Africa and two in Asia; kinds not present or rare before; publisher cap honoured.
- `licence.redistribution` is `unknown` on at most six of the new records.
- At least twelve new records carry `region.bbox`; at least twelve carry `period`.
- The `verify` workflow comment on the PR lists every new record with a level or `blocked`.
- Existing tests pass unchanged; the lane adds no tests.

**Out of scope.** Outlines, schema changes, mirrors, records held by an open lane.

**Stop rules.** As E13 and E14: forbidden redistribution is recorded and continued; login-only
licence pages are `unknown`; terms that forbid automated access are noted and the record stays at
the observed level.

**Ownership and dependencies.** Records lane; paths `records/**` except files held by an open lane;
`docs/program/evidence/e17/**`. Depends on E16 (merged first so `period` is in the record schema in
use). Runs in the records slot.

**Evidence to inspect.** `uv run osd status` in the PR; the verify comment; the hand counts; the
map list screenshot with the count.
