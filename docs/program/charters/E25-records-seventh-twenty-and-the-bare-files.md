## E25 Records: the seventh twenty, and the bare files — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026; E24's PR #32 body (section "File addresses for H1 design 8",
the "checked but not given a listing" list, the refused candidates); H1 designs 8 and 9 (merged
PR #33); OSD-D7, OSD-D9, OSD-D11, OSD-D15, OSD-D20.

**Outcome.** The map lists at least 156 datasets from at least four more countries; the records
whose `manifest_url` is a bare file reach L2 because the verifier now treats such a response as a
one-entry listing; and every dataset still below L2 says why in the verifier's words.

**Context today (verified 23 Oct, main 4dcdc56).** 140 records. E24 merged 49 record files, 33
`manifest_url`s with `samples.yaml` entries; its branch run showed 24 of its records at L2. H1
merged OSD-D20 (`blocked` when a 404/410/5xx to the verifier is a 2xx to a browser agent) and
design 8 (a `manifest_url` whose response is itself a data file, by content type or
`Content-Disposition: attachment`, is the one listing entry; `id: {file: true, sample: ["*"]}` in
`src/osd/verifier/samples.yaml` says so when the headers do not). Seven records keep a bare-file
address and were not sampled before H1: `ar-energia/trayectorias-vaca-muerta`,
`ar-energia/fractura-adjunto-iv`, `ar-energia/produccion-por-pozo`,
`gsmma/hydrogeological-drilling-database`, `gsmma/sw-offshore-core-stations-2008-2011`,
`gsmma/sw-offshore-seismic-lines-2008-2011`, `cpc/onshore-well-locations`. Verify runs on main
after both merges are 39980489177 and 39981701762; their comments show what H1 already fixed.
Refused on 23 Oct (do not retry this lane): Tasmania MRT, Greece HEREMA, Romania NAMR, Bulgaria,
Thailand DMF and data.go.th, Philippines DOE, Vietnam PVN, Tanzania PURA, Morocco ONHYM, Senegal
PETROSEN, and E24's "checked but not given a listing" hosts (TerraNubis, Volve, GFZ, LDEO, IODP,
MARUM, GEUS Havnsø, DOE GDR, NTGS, WVGES) plus E22's and E24's refused list in the E24 charter.
E26 (vocabulary) holds twelve named records (its design 4); do not edit those.

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3, E24 designs 2 and 3 stand.
   Records an open lane holds are out of reach (`CLAIMS.md`).
2. Bare files: read main's latest verify comment or `osd status` on the published results for the
   seven records above. A record sampled at L2 needs nothing. A record whose file came back as an
   HTML listing with no entries, or whose headers do not say "file", gets `file: true` in its
   `samples.yaml` entry (the H1 shape), with the response content type and size in the comment.
   A record that is `blocked` (OSD-D20) stays as it is; say so in `notes` only if the note does
   not already say it.
3. New records, in this order until twenty, each opened on the day: Canada (Saskatchewan, C-NLOPB
   Newfoundland and Labrador), Australia (NSW DIGS, Victoria GSV, South Australia SARIG beyond
   SA-DEM's one record), New Zealand NZP&M, Mexico CNH/CNIH, US states not yet listed and not
   refused (Texas RRC, North Dakota DMR, Utah DOGM if absent, Alabama OGB, Nebraska, Virginia,
   Florida), Africa (Nigeria NUPRC, Ghana Petroleum Commission, Namibia beyond NAMCOR, Egypt EUG
   beyond the one record only if a distinct dataset), Asia (Pakistan DGPC, Oman MEM, Bangladesh
   Petrobangla, Turkey MTA/MAPEG), Europe (Sweden SGU boreholes, Iceland Orkustofnun, Estonia,
   Lithuania, Ukraine Geoinform, Serbia, Bosnia, Albania AKBN), and open research sets with a file
   listing (USGS National Geothermal Data System, USGS Core Research Center, UK CO2 Stored, Zenodo
   or GitHub-hosted seismic and model sets not yet listed). Aggregator cap three per publisher;
   `unknown` cap six; at least four new countries.
4. Every new record whose publisher lists files where the verifier reads them gets a
   `manifest_url` and a `samples.yaml` entry (pattern, file, size, robots.txt line). Kinds wanted
   but absent: use the nearest kind and say so in `notes` (E26 adds the kinds; E25 does not wait).
5. `period`, `region.bbox`, licences, purchase terms in the publisher's words, as before.

**Acceptance.**
- `uv run osd validate` reports `>= 156 records, 0 problems`; `make check` green (samples
  coverage test included).
- The PR lists each bare-file record with what main's run showed and what changed (nothing,
  `file: true`, or blocked), and every new or changed `manifest_url` with its robots.txt line,
  listing shape and sample pattern.
- The `verify` workflow comment on the PR shows the bare-file records at L2 unless blocked, and
  names for each new record below L2 why.
- Hand counts: new countries (at least four), `unknown` at most six, bbox and period counts,
  records with a `manifest_url`.

**Claim.** `records/**` (new files and edits to records no open lane holds; not E26's twelve),
`src/osd/verifier/samples.yaml` (entries and `file:` flags for this lane's records),
`docs/program/evidence/e25/**`.
