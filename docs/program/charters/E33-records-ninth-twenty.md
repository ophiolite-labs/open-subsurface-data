## E33 Records: the ninth twenty (the four held back, the Americas and Africa that remain, geothermal and CO2 research sites) — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026; E31 (PR #41: four finished records held back under the
`unknown` cap, Tomakomai held back by its terms, the refused list); E30 and E25 refused lists;
OSD-D7, OSD-D9, OSD-D11, OSD-D15, OSD-D20; the supervisor's 23 Oct rulings (a place name is not an
extent; charter counts are lower bounds; the lane holding `samples.yaml` adds entries for its own
records).

**Outcome.** The map lists at least 196 datasets: the four records E31 finished and held back are
in, at least five more countries are listed, geothermal and CO2 research sites that publish well and
monitoring data are on the map, and every new dataset whose publisher lists files points at that
listing.

**Context today (verified 23 Oct, main 9cb8f52).** 176 records, 94 with `manifest_url`, 40 with
redistribution `unknown` in all. Held back by E31 and finished: `docs/program/evidence/e31/held-back/`
(fig-dmr, mra-pg, pdasl, sd-danr; sd-danr's samples line is in `held-back.md`). Refused on 23 Oct
(do not retry this lane): E31's refused list (Ontario OGSR, Québec SIGPEG, Algeria ALNAFT, Aquistore,
Quest CCS, Arizona AZOGCC and AZGS, Gorgon, Tennessee, GEUS Jupiter, GTK Hakku, Latvia, Cyprus, PNG
DPE, Gabon DGH, Ecuador x4, Chile ENAP, Cuba CUPET, YPFB) and the E22/E24/E25/E30/E31 lists in those
charters. Tomakomai CCS stays out (terms ask permission to link; owner default 23 Oct). GEOSPHERE's
API lists files without URLs and GFZ's robots times out: no third retry. E29 holds nine records
(`CLAIMS.md`): out of reach until it merges. The verifier reads the shapes listed in the E30 charter.

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3, E24 designs 2 and 3, E31
   designs 4 and 5 stand.
2. First: `git mv` the four held-back records into `records/`, add sd-danr's samples line, re-read
   each page once on the day and refresh `checked` evidence. They count four of this lane's
   `unknown` cap of six.
3. Then new records, in this order until twenty in all, each opened on the day with robots.txt read
   first. North America: Saskatchewan (Ministry of Energy and Resources, IRIS or the open data
   portal), New Brunswick DNRED, Yukon Geological Survey, Northwest Territories Geological Survey,
   Missouri DNR Geological Survey, Oregon DOGAMI, Washington DNR, Nebraska if not covered by
   `nogcc`. Latin America: Guatemala MEM, Honduras, Paraguay MOPC/ViceMinisterio de Minas y Energía,
   Jamaica PCJ, Barbados, Dominican Republic, Belize. Africa: Egypt EGAS/EGPC, Tunisia ETAP,
   Sierra Leone PDSL, Liberia LPRA, Cameroon SNH, Equatorial Guinea MMH, Madagascar OMNIS,
   Seychelles PetroSeychelles, Somalia SPA, Botswana, Zambia, Malawi. Middle East and Asia: Israel
   Ministry of Energy (petroleum well data), Jordan NRA/MEMR, Lebanon LPA, Mongolia MRPAM,
   Timor-Leste ANPM, Brunei, Sri Lanka's second dataset only if PRDS lists it. Geothermal and CO2
   research: Utah FORGE (if not already in `doe-gdr`), Soultz-sous-Forêts/EGS data, Germany GeotIS
   (LIAG), Italy GeoThopica (CNR), Ketzin CO2 (if GFZ's host answers, else a finding), Hontomín
   (CIUDEN), Otway (CO2CRC), Decatur IBDP (ISGS), Northern Lights, Groningen (NAM public data).
   Aggregator cap three per publisher; `unknown` cap six including the four restored; at least five
   new countries.
4. Every new record whose publisher lists files where the verifier reads them gets a `manifest_url`
   and a `samples.yaml` entry (pattern, file, size, robots line in the comment).
5. `period`, `region.bbox`, licences, purchase terms in the publisher's words, as before (E28's
   conventions: a place name is not an extent; nothing inferred).

**Acceptance.**
- `uv run osd validate` reports `>= 196 records, 0 problems`; `make check` green.
- The PR lists each new record (publisher, country, access, kinds, period, bbox, manifest_url or
  the reason there is none), the refused candidates with reasons, and hand counts (new countries,
  `unknown`, bbox, period, listings).
- The `verify` workflow comment on the PR: each new record's level with its first failing check.
- Evidence `docs/program/evidence/e33/sources.md` (page, robots line, excerpt, UTC time).

**Claim.** `records/**` (new files and the four moved from `docs/program/evidence/e31/held-back/`;
not E29's nine), `src/osd/verifier/samples.yaml` (entries for this lane's listings),
`docs/program/evidence/e33/**`, `docs/program/evidence/e31/held-back/**` (removal by move).
