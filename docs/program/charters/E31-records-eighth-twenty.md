## E31 Records: the eighth twenty (offshore regulators, Canadian provinces, CCS sites, the rest of Europe) — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026; E25 (PR #35: refused hosts, the BOM finding), E30 (PR #40:
retries for tethys.at and datapub.gfz.de, listing shapes the verifier does not read); E24 and E22
refused lists; OSD-D7, OSD-D9, OSD-D11, OSD-D15, OSD-D20.

**Outcome.** The map lists at least 176 datasets, with the large offshore regulators (US BOEM and
Canada's C-NLOPB) and the Canadian provinces that publish well data, at least four more countries,
and every new dataset whose publisher lists files pointed at that listing.

**Context today (verified 23 Oct, main 641f750).** 160 records, 80 with `manifest_url`, 45 or so at
L2 on the latest branch runs. Refused on 23 Oct (do not retry this lane): Nigeria NUPRC (terms
forbid automated collection), GNPC, Namibia MME/GSN, Pakistan DGPC/PPIS, Oman MEM, Petrobangla,
MAPEG/MTA/TPAO, Iceland Orkustofnun/ÍSOR, Ukraine Geoinform, Serbia GZS, Albania AKBN, Mexico
CNH/CNIH/datos.gob.mx, NGDS, ScienceBase, USGS CRC, software.seg.org, EDX, SARIG petroleum wells,
and the E22/E24/E25 lists in those charters (Tasmania MRT, HEREMA, NAMR, Bulgaria, Thailand,
Philippines, Vietnam, Tanzania, Morocco, Senegal, Louisiana SONRIS, Michigan, Arkansas, Kentucky,
Mississippi, Montana, Indiana, Illinois, BRGM, AOGCC, Kochi, GSJ, JAMSTEC J-CORES, NRCan GDR).
Transient on 23 Oct, retry once: data.tethys.at (503; JSON with `files`, GEOSPHERE x2 listings),
datapub.gfz.de (timeout; GFZ x4 listings). The verifier reads the shapes listed in the E30 charter;
a shape it does not read (STAC API collection, OGC API Features, WMS, FTP) is a finding, not a
`manifest_url`. Every `manifest_url` needs a `samples.yaml` entry (coverage test).

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3, E24 designs 2 and 3 stand.
   Records an open lane holds are out of reach (E29's nine, `CLAIMS.md`).
2. New records, in this order until twenty, each opened on the day with robots.txt read first:
   US BOEM/BSEE Gulf of Mexico data (well, seismic, field data at data.boem.gov; one record per
   distinct dataset, cap three); C-NLOPB (Newfoundland and Labrador offshore); Ontario OGSR
   Library; Québec SIGPEG; Aquistore (PTRC, Saskatchewan CCS); Quest CCS (Alberta); Belgium DOV
   Vlaanderen boreholes; GEUS at data.geus.dk (Jupiter boreholes; the eng.geus.dk pages answer
   404 today); Finland GTK Hakku; Latvia LVĢMC; Slovenia GeoZS; Cyprus; Papua New Guinea;
   Sri Lanka PRDS; Algeria ALNAFT; Libya NOC; Gabon DGH; Ecuador; Bolivia YPFB/ANH; Chile ENAP;
   Falkland Islands; Cuba; Tomakomai and Gorgon CCS data pages if public; US states not yet
   listed and not refused (Nevada NBMG, Arizona AZGS, Oregon DOGAMI, Idaho, Tennessee, South
   Dakota). Aggregator cap three per publisher; `unknown` cap six; at least four new countries.
3. The two transient retries (design: context) are made once; on success the `manifest_url` and
   entry are added to the existing records (GEOSPHERE x2, GFZ x4; these are not E29's records).
4. Every new record whose publisher lists files where the verifier reads them gets a
   `manifest_url` and a `samples.yaml` entry (pattern, file, size, robots line in the comment).
5. `period`, `region.bbox`, licences, purchase terms in the publisher's words, as before (E28's
   conventions: a place name is not an extent; nothing inferred).

**Acceptance.**
- `uv run osd validate` reports `>= 176 records, 0 problems`; `make check` green.
- The PR lists each new record (publisher, country, access, kinds, period, bbox, manifest_url or
  the reason there is none), the retry outcomes, the refused candidates with reasons, and hand
  counts (new countries, `unknown`, bbox, period, listings).
- The `verify` workflow comment on the PR: each new record's level with its first failing check.
- Evidence `docs/program/evidence/e31/sources.md` (page, robots line, excerpt, UTC time).

**Claim.** `records/**` (new files; `origin.manifest_url` and `notes` of the GEOSPHERE x2 and GFZ x4
records on a successful retry; not E29's nine), `src/osd/verifier/samples.yaml` (entries for this
lane's listings), `docs/program/evidence/e31/**`.
