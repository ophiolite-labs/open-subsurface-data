## E30 Listings for the datasets people can download — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026 (levels on the map are real; L2 means files were sampled
and checksummed); E23 (listing readers and `samples.yaml`), E24 design 3 and its "checked but not
given a listing" table (PR #32), H1 designs 8 and 9, E25 (bare files, robots.txt findings);
OSD-D7, OSD-D9, OSD-D11, OSD-D15, OSD-D20.

**Outcome.** More of the datasets anyone may download are verified at L2: each anonymous-access
record whose publisher lists files where the verifier reads them points at that listing, and the
rest say in the verifier's words why not.

**Context today (verified 23 Oct, main 16a2f5a).** 160 records, 69 with `manifest_url`, 35 at L2 on
the E25 branch run. 62 anonymous-access records have no `manifest_url`
(`docs/program/evidence/e30/candidates.md`, with the published level); 56 of them are L1, the
rest L0 (CO2 DataShare x5 and GEUS dead today, SEG wiki, NM OCD, PA DEP and ODNR blocked). The
verifier reads CKAN, Socrata, data.gov.tw, ArcGIS Map/Feature Server layers (one export up to
`maxRecordCount`, kept as partial beyond it), Zenodo, figshare, Dataverse, GitHub releases and
contents, DataCite, JSON:API, dane.gov.pl, HTML directory and link pages, S3 XML, text lists, and
a bare file (content type or `file: true`). E24 checked and did not give a listing to: TerraNubis
(11; downloads go to ShareFile share pages), GFZ (4; datapub.gfz.de timed out), LDEO (robots
`Disallow: /data/`), IODP (search and api disallowed), DOE GDR (3; file list built by script),
NTGS (maintenance page), WVGES (per-county pages); E24's `sources.md` has the reason for each.
Visible candidates with a shape the verifier reads: ECMC and NYSDEC x2 (Socrata), CalGEM (ArcGIS
layer behind CKAN), nzpam/parihaka (AWS Open Data S3 bucket), BGS single onshore borehole index
(WFS or download), swisstopo x2 (data.geo.admin.ch; its STAC API is not a reader today, its
download links may be), TNO BRO, GA x2, GSV petroleum wells, LBEG x3, ViDEPI x2 (HTML link pages),
SA-DEM, USGS NAMSS, TX RRC x2, WOGCC, IGME SIGEOF, GEOSPHERE x2, INP Mozambique, Guyana MNR, ANPG.

**The design the lane must map to.**
1. E24 designs 2 and 3 stand. Records an open lane holds are out of reach (E29's nine; check
   `CLAIMS.md`). Nothing else in a record changes except `origin.manifest_url` and, where the
   lane learns something, `notes`.
2. For every one of the 56 anonymous L1 candidates, opened on the day: robots.txt read first, then
   the publisher's download or API page; if a listing of the shapes above exists and robots.txt
   allows it, set `manifest_url` and add the `samples.yaml` entry (pattern, file, size, shape,
   robots line in the comment). E24's refused hosts are retried only where E24's reason was
   transient (timeout, maintenance); its permanent reasons (share pages, robots disallow, scripted
   lists) are not.
3. A listing shape the verifier does not read (a STAC API, an OGC API Features endpoint, a WMS
   GetCapabilities, an FTP index) is recorded in the PR as a finding with the URL and one example
   response, not added as a `manifest_url` (the coverage test would make it a dead entry).
4. The six L0 dead or blocked records are not touched.

**Acceptance.**
- `uv run osd validate` 160 records, 0 problems; `make check` green (samples coverage test).
- At least twelve records gain a `manifest_url`; the PR table lists each (record, address,
  robots.txt line, shape, sample pattern, size) and, for every other candidate, the reason in one
  line (no listing published; shape not read, with the finding; robots disallows; host refused).
- The `verify` workflow comment on the PR shows at least six more records at L2 than main's latest
  run, or names for each why not.
- Evidence `docs/program/evidence/e30/sources.md` (page, robots line, excerpt, UTC time).

**Claim.** `records/**` (`origin.manifest_url` and `notes` of anonymous-access records no open
lane holds), `src/osd/verifier/samples.yaml` (entries for this lane's listings),
`docs/program/evidence/e30/**`.
