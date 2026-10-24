## E39 Records: the eleventh twenty (second products and open-data portals) — OPEN · Records · no strategy, no Codex round

Authority: supervisor 24 Oct 2026 under the owner's direction of 23 Oct; E37 (PR #58, refused list in
`docs/program/evidence/e37/sources.md`); E33, E31, E30 and E25 refused lists; OSD-D7, OSD-D9, OSD-D11,
OSD-D15, OSD-D20; the supervisor's rulings (a place name is not an extent; charter counts are lower
bounds; the lane holding `samples.yaml` adds entries for its own records).

**Outcome.** The map lists at least 236 datasets. Every new dataset states its licence in the
publisher's words (none new with redistribution `unknown`),  and every new dataset whose publisher lists files points at that listing.

**Context today (verified 24 Oct, main 1f22925).** 196 records, 115 with `manifest_url`, 46 with
redistribution `unknown`. The `unknown` cap is used up: this lane's cap is zero, so a candidate
without a stated licence is refused with that reason. Do not retry anything on the E22, E24, E25,
E30, E31, E33 or E37 refused lists; Tomakomai stays out. Publishers already present are the directory
names under `records/`; a second dataset from one of them counts only if it is a different product
(aggregator cap three per publisher still holds).

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3, E24 designs 2 and 3, E31
   designs 4 and 5, E37's inbox rulings (refused lists win; a single point is not an extent; NC
   licences are restricted) stand.
2. Candidates, until twenty, each opened on the day with robots.txt read first: second and third
   products of stated-licence publishers already present (aggregator cap three), where the product
   differs (USGS: NAMSS seismic, core research center, produced waters, national geochemical
   database; NRCan: geoscience data repository products; GEUS, BGS, NSTA, Sodir, TNO/BRO, IGME,
   GA and the Australian state surveys; Equinor open datasets beyond Volve; KIGAM; NOPIMS; SGU);
   open research repositories with stated licences (Zenodo, figshare, Dataverse and PANGAEA
   collections of well logs, seismic or reservoir models, one product per record); national
   open-data portals (data.gov, data.gov.uk, data.gov.au, open.canada.ca, data.gouv.fr,
   govdata.de, dati.gov.it, datos.gob.es) searched for wells, boreholes, seismic and reservoir
   data from publishers not yet listed.
3. Every new record whose publisher lists files where the verifier reads them (H3 robots rules
   apply) gets a `manifest_url` and a `samples.yaml` entry.
4. `period`, `region.bbox`, licences, purchase terms in the publisher's words, as before.

**Acceptance.**
- `uv run osd validate` reports `>= 236 records, 0 problems`; `make check` green.
- The PR lists each new record (publisher, country, licence in the publisher's words, access,
  kinds, period, bbox, manifest_url or the reason there is none), the refused candidates with
  reasons, and hand counts (new countries, bbox, period, listings; `unknown` new = 0).
- The `verify` workflow comment on the PR: each new record's level with its first failing check.
- Evidence `docs/program/evidence/e39/sources.md` (page, robots line, licence excerpt, UTC time).

**Claim.** `records/**` (new files only), `src/osd/verifier/samples.yaml` (entries for this lane's
listings), `docs/program/evidence/e39/**`.
