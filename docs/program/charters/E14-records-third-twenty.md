## E14 Twenty records: research drilling, CO2 storage sites, state and basin archives — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026 (open lists plus national registers); E13 findings in
`docs/program/HANDOFF.md` (what was unreachable on 23 Oct); OSD-D7, OSD-D9.

**Outcome.** The map lists at least sixty datasets. The third twenty widen the kinds and regions:
scientific drilling archives (ocean and continental), CO2 storage demonstration sites, Italian,
Polish and Australian state archives, Latin American registers, and US state well archives, with at
most three new records from any one publisher or aggregator.

**Context today (verified 23 Oct, main after PR #4).** 42 records; publishers now span ten
countries. E13 could not reach BRGM, NRCan GDR, CNSOER, Queensland GSQ, AOGCC, SEG-hosted sets
(SEAM, Stratton, Viking Graben) and LBEG on 23 Oct; retrying them once is allowed, not required.
Seven records are held by lane E03 and are out of this lane's reach: `records/sodir/factpages.yaml`,
`records/nlog/nlog.yaml`, `records/terranubis/f3-demo-2020.yaml`, `records/rmotc/teapot-dome.yaml`,
`records/nopims/poseidon.yaml`, `records/nzpam/parihaka.yaml`, `records/nzpam/kerry-3d.yaml`.

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6 stand (one record per dataset or register; origin opened on
   the day; blocked is not dead; licence never inferred; bbox when the publisher states an extent;
   no schema change, wants go to `notes` and the PR).
2. Candidates, in this order until twenty, each opened on the day: IODP/JOIDES Resolution logging
   and core databases (LDEO, Texas A&M), ICDP sites (Ketzin, Outokumpu, COSC), CO2 storage sites
   not yet listed (Northern Lights, Johansen, Otway CO2CRC, Decatur IBDP, Ketzin), Italy ViDEPI,
   Poland PGI CBDG, Western Australia WAPIMS and Victoria GSV, Northern Territory STRIKE, US state
   archives with free well files (North Dakota DMR, Oklahoma OCC, Wyoming WOGCC, Colorado ECMC,
   Utah DOGM, Texas RRC), Argentina Secretaría de Energía open data, Colombia ANH, Mexico CNH CNIH,
   SPE comparative solution projects (SPE9, SPE10) where a publisher page exists, Imperial College
   and NTNU model sets, any E13 leftover that now answers. Aggregator cap: three per publisher.
3. A publisher that only lists other datasets gets one `source-list` record; its named datasets get
   their own records only with their own landing page and licence statement.

**Acceptance.**
- `uv run osd validate` reports `>= 61 records, 0 problems`.
- Hand counts in the PR: new countries not present before (at least four), kinds not present or rare
  before (`core`, `geochemistry`, `time-depth`, `pressure` among them), publisher cap honoured.
- `licence.redistribution` is `unknown` on at most six of the new records.
- At least fourteen new records carry `region.bbox`.
- The `verify` workflow comment on the PR lists every new record with a level or `blocked`.
- Existing tests pass unchanged; the lane adds no tests.

**Out of scope.** Outlines (E03), schema changes, mirrors, the seven E03 records.

**Stop rules.** As E13: forbidden redistribution is recorded and continued; login-only licence pages
are `unknown`; terms that forbid automated access are noted and the record stays at the observed level.

**Ownership and dependencies.** Records lane; paths `records/**` except the seven E03 files;
`docs/program/evidence/e14/**`. Depends on nothing; runs in parallel with E03.

**Evidence to inspect.** `uv run osd status` in the PR; the verify comment; the hand counts; the
map list screenshot with the count.
