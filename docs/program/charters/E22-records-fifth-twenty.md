## E22 Records, fifth twenty: US state regulators, Iberia and the Alps, Latin America, Africa, geothermal and CO2 sites — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026 (open lists plus national registers); E17 and E20 findings in
`docs/program/HANDOFF.md`; OSD-D7, OSD-D9, OSD-D15.

**Outcome.** The map lists at least 116 datasets; the US state regulators that publish well data
openly are on it beside the national registers, and the catalogue reaches Iberia, the Alps, more of
Latin America and Africa, and the open geothermal sites.

**Context today (verified 23 Oct, main a1f8832).** 96 records from 59 publishers. Refusing from the
runner and this host on 23 Oct (do not retry in this lane): BRGM, AOGCC, Kochi Core Center, GSJ
gbank, JAMSTEC J-CORES, SEG-hosted sets, NRCan GDR (its successor host is listed), SEG wiki and
NOPIMS (403, blocked). Present already: AER, BCER, KGS, OK-OCC, TX-RRC, UT-DOGM, Alaska DGGS, USGS,
RMOTC, BEG; PGI (Poland), TNO/NLOG, Sodir, NSTA, UKOGL, GEUS, LBEG, GFZ, MASE-UNMIG, IE-PAD;
ANP, ANH, SGC, Argentina Energía; NAMCOR, PASA, EUG, DGH, ESDM, PRIME; GA, GSQ, GSV, NTGS, SA-DEM,
WA-DEMIRS, NZPAM, NOPIMS; CO2 DataShare, SINTEF, TU Delft, UNISIM, SPE, TerraNubis, Equinor Volve.
record/3 admits `potential-fields`, `purchase` and `licence.terms` (E19). Kinds wanted but absent
(E20 finding; use the nearest kind and say so in `notes`): airborne EM and radiometrics, velocity
model, geological 3D model.

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3 stand (one record per
   dataset or register; origin opened on the day; blocked is not dead; licence never inferred;
   bbox and period when stated; purchase terms only in the publisher's words; wants go to `notes`
   and the PR). Every record an open lane holds is out of reach: E21 holds none (check `CLAIMS.md`).
2. Candidates, in this order until twenty, each opened on the day: US state regulators with open
   well data (North Dakota DMR, Wyoming WOGCC, Colorado ECMC, New Mexico OCD, Louisiana SONRIS,
   California CalGEM, Pennsylvania DEP, Ohio ODNR, Michigan EGLE, Illinois ISGS, West Virginia
   GES); Iberia and the Alps (Spain IGME/CNIG, Portugal ENMC or DGEG, Austria GBA, Switzerland
   swisstopo deep wells and seismic); Latin America (Mexico CNH CNIH, Peru Perupetro, Uruguay
   ANCAP, Trinidad and Tobago MEEI, Guyana or Suriname Staatsolie where a page states a licence);
   Africa (Angola ANPG, Mozambique INP, Morocco ONHYM, Tanzania PURA); geothermal and CO2 sites
   with an open archive (Utah FORGE via the DOE Geothermal Data Repository, Hontomín, Otway stages
   beyond Brumbys if GA lists them separately, Ketzin beyond the GFZ record only if a new dataset);
   Canada (Saskatchewan, Manitoba, Newfoundland C-NLOPB) and the North Atlantic (Faroe Jarðfeingi,
   Greenland via GEUS only if a page distinct from the deep subsurface one); any E13, E14, E17 or
   E20 leftover that now answers. Aggregator cap: three records per publisher.
3. A publisher that only lists other datasets gets one `source-list` record (E14 design 3).

**Acceptance.**
- `uv run osd validate` reports `>= 116 records, 0 problems`.
- Hand counts in the PR: new countries (at least five), new US states (at least six), kinds not
  present or rare before, publisher cap honoured.
- `licence.redistribution` is `unknown` on at most six of the new records.
- At least ten new records carry `region.bbox`; at least ten carry `period`.
- The `verify` workflow comment on the PR lists every new record with a level or `blocked`.
- `make check` green without edits outside the claim (the count pins are lower bounds since E20).

**Claim.** `records/**` (new files and edits to records no open lane holds), `docs/program/evidence/e22/**`.
