## E24 Records: files the verifier can reach, and the sixth twenty — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026; E23 findings in `docs/program/HANDOFF.md` (which listings
name no file, which robots.txt refuse the API path); E22 findings (held-back candidates, refused
hosts); OSD-D7, OSD-D9, OSD-D11, OSD-D15.

**Outcome.** More datasets show L2 because their records point the verifier at addresses that
list files and that the publisher's robots.txt allows; and the map lists at least 136 datasets.

**Context today (verified 23 Oct, main 3ece7a2).** 121 records, 4 at L2 (Sodir, Norne, NLOG, ANH),
Poseidon at L3. 23 records carry `origin.manifest_url`; E23's run shows why the rest stop:
robots.txt disallows the API path for datos.gob.ar (3 records), data.gov.tw (4) and
dggs.alaska.gov (1); ArcGIS exports truncate at 2,000 features (BCER, SGC, UT-DOGM; the verifier
keeps them as partial, a record cannot change that); seven listings name no file (GSQ, JAMSTEC,
KIGAM, PGI CBDG, SPE CSP11 repository HTML, WA DEMIRS, TU Delft DOI). The verifier reads CKAN,
Socrata, data.gov.tw, ArcGIS, Zenodo, figshare, Dataverse, GitHub releases, DataCite, JSON:API,
dane.gov.pl, HTML directory listings, S3 XML and text lists; it respects robots.txt for the
listing URL. Every `manifest_url` must have an entry in `src/osd/verifier/samples.yaml` (E23's
coverage test); this lane adds those entries (granted). Held back by E22 under the `unknown` cap:
Wyoming WOGCC, Angola ANPG, Staatsolie, PETROCI. Refused on 23 Oct (do not retry): Louisiana
SONRIS, Michigan EGLE, Arkansas AOGC, Kentucky KGS, Mississippi OGB, Montana, Indiana, Illinois
pages, BRGM, AOGCC, Kochi, GSJ, JAMSTEC J-CORES, SEG-hosted sets, NRCan GDR.

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3 stand. Every record an open
   lane holds is out of reach (check `CLAIMS.md`; H1 holds no record).
2. Repoint, each checked on the day with the publisher's robots.txt read first: CSP11 to the
   GitHub contents API of its repository; datos.gob.ar and data.gov.tw records to a direct
   resource address (the CSV or ZIP the CKAN package names, often on another host) when
   robots.txt allows it, else leave the record as it is and say so in `notes`; WA DEMIRS and PGI
   CBDG to a WFS `GetFeature` export or a file download if one is addressable; Alaska DGGS only if
   a path outside the disallowed one lists the files. A `manifest_url` that lists one file is fine
   (the verifier samples that file). Each change gets its `samples.yaml` entry (pattern and a
   comment with the file and size).
3. Add `manifest_url` to existing records whose publisher lists files where the verifier reads
   them (Zenodo, figshare, Dataverse, GitHub releases, a directory listing, S3): check at least
   agl/marmousi2, the SINTEF, UNISIM, TerraNubis, Equinor Volve, GFZ dataservices, Helsinki, LDEO,
   IODP, MARUM records. Add a `samples.yaml` entry for each.
4. New records, in this order until twenty, each opened on the day: the E22 held-backs (Wyoming
   WOGCC, Angola ANPG, Staatsolie, PETROCI; the `unknown` cap of six per lane stands), Canada
   (Saskatchewan, Newfoundland C-NLOPB, Nova Scotia onshore), Australia Tasmania MRT, Europe
   (Croatia CHA, Greece HHRM, Romania NAMR, Hungary MBFSZ or SZTFH, Czech Geofond, Bulgaria),
   Asia (Malaysia PETRONAS MyPDR, Thailand DMF, Vietnam PVN, Philippines DOE), Africa (Morocco
   ONHYM, Tanzania PURA, Uganda PAU, Kenya NOCK, Senegal Petrosen), and any open seismic or model
   set with a file listing (Zenodo, GitHub releases) that is not yet listed. Aggregator cap: three
   records per publisher. Kinds wanted but absent (E20/E22 findings): use the nearest kind and say
   so in `notes`.
5. `period`, `region.bbox`, licences, purchase terms in the publisher's words, as before.

**Acceptance.**
- `uv run osd validate` reports `>= 136 records, 0 problems`; `make check` green (the
  samples coverage test included).
- The PR lists every repointed or added `manifest_url` with the robots.txt line that allows it,
  the listing shape, and the sample pattern; at least ten records gain or change a `manifest_url`.
- The `verify` workflow comment on the PR shows at least four more records at L2 than main's
  latest run (eight or more in all), or names for each why not.
- Hand counts: new countries (at least four), `unknown` at most six, bbox and period counts.

**Claim.** `records/**` (new files and edits to records no open lane holds), `src/osd/verifier/samples.yaml` (entries for `manifest_url`s this lane adds or changes), `docs/program/evidence/e24/**`.
