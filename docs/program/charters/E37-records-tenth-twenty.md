## E37 Records: the tenth twenty (publishers that state an open licence) — OPEN · Records · no strategy, no Codex round

Authority: supervisor 24 Oct 2026 under the owner's direction of 23 Oct; E33 (PR #44, refused list
in `docs/program/evidence/e33/sources.md`); E31, E30 and E25 refused lists; OSD-D7, OSD-D9, OSD-D11,
OSD-D15, OSD-D20; the supervisor's rulings (a place name is not an extent; charter counts are lower
bounds; the lane holding `samples.yaml` adds entries for its own records).

**Outcome.** The map lists at least 216 datasets. Every new dataset states its licence in the
publisher's words (none new with redistribution `unknown`), at least three more countries are
listed, and every new dataset whose publisher lists files points at that listing.

**Context today (verified 24 Oct, main 1f22925).** 196 records, 115 with `manifest_url`, 46 with
redistribution `unknown`. The `unknown` cap is used up: this lane's cap is zero, so a candidate
without a stated licence is refused with that reason. Do not retry anything on the E22, E24, E25,
E30, E31 or E33 refused lists; Tomakomai stays out. Publishers already present are the directory
names under `records/`; a second dataset from one of them counts only if it is a different product
(aggregator cap three per publisher still holds).

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3, E24 designs 2 and 3, E31
   designs 4 and 5 stand.
2. Candidates, in this order until twenty, each opened on the day with robots.txt read first.
   Europe: France BRGM (BSS boreholes, Etalab licence), Ireland GSI (boreholes, CC BY), Czech
   Geological Survey (boreholes), Wallonia (SPW sous-sol), Iceland (Orkustofnun or ÍSOR wells),
   Germany BGR (deep boreholes or 3D models where the licence is stated), Sweden SGU second product
   (well archive) if different from the existing record. Americas: Louisiana SONRIS, Michigan EGLE
   (oil and gas wells), Kentucky Geological Survey (oil and gas wells), Illinois ISGS (ILOIL or
   Decatur IBDP), Indiana IGWS (petroleum database), Montana MBOGC, Arkansas AOGC, Mississippi
   MOGB, NOAA NCEI marine geophysics (seismic reflection), Rutgers/LDEO MGDS (academic seismic),
   UTIG seismic data. Asia and the Pacific: Japan GSJ (AIST boreholes or seismic), Taiwan CGS,
   Tasmania MRT (open boreholes), Philippines DOE (if licence stated). Research: ICDP drilling
   projects (CC BY), PANGAEA borehole collections (one per product, aggregator cap three).
3. Every new record whose publisher lists files where the verifier reads them gets a `manifest_url`
   and a `samples.yaml` entry (pattern, file, size, robots line in the comment).
4. `period`, `region.bbox`, licences, purchase terms in the publisher's words, as before (E28's
   conventions: a place name is not an extent; nothing inferred).

**Acceptance.**
- `uv run osd validate` reports `>= 216 records, 0 problems`; `make check` green.
- The PR lists each new record (publisher, country, licence in the publisher's words, access,
  kinds, period, bbox, manifest_url or the reason there is none), the refused candidates with
  reasons, and hand counts (new countries, bbox, period, listings; `unknown` new = 0).
- The `verify` workflow comment on the PR: each new record's level with its first failing check.
- Evidence `docs/program/evidence/e37/sources.md` (page, robots line, licence excerpt, UTC time).

**Claim.** `records/**` (new files only), `src/osd/verifier/samples.yaml` (entries for this lane's
listings), `docs/program/evidence/e37/**`.
