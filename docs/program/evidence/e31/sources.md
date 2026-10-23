# E31 sources: records, the eighth twenty (read 2026-10-23)

Every address below was opened from the lane host on 2026-10-23 at the UTC time given. All
requests used the verifier's user agent (`osd.verify.USER_AGENT`), and robots.txt was read first for
each host. Robots were judged as `osd.verify._Robots` judges them (2xx is obeyed, 4xx allows all, 5xx
or no answer disallows), with `urllib.robotparser` plus an RFC 9309 `*` wildcard check that
robotparser itself lacks. Each page or listing was read once and saved, then parsed offline with
`osd.verifier.listings.read_listing`. The `src/osd/verifier/samples.yaml` globs were applied the way
`check_files` applies them, and each picked file was asked for its size with one HEAD (or one GET
where the server gives no length). Nothing was hashed here, and `osd verify` was not run from this
host. Records state publisher facts only.

Slips, for the record:
- The donneesquebec.ca search `https://www.donneesquebec.ca/recherche/dataset/?q=puits+gaziers+p%C3%A9troliers`
  (17:49:39) went out before the script checked wildcards. robots.txt has
  `Disallow: /recherche/dataset/*?`, and robotparser ignores the `*`. The result was not used, and
  the wildcard check was added at once.
- Five requests went to www.ogsrlibrary.com (17:48:12 to 17:49:05) before its terms were read. The
  terms forbid automated access, so the publisher was refused (see Refused).
- home-cnlopb.hub.arcgis.com and data-nbmg.opendata.arcgis.com both state `Crawl-delay: 60`. Each was
  asked once, its search API (17:46:40, 18:01:51).
- The C-NLOER well-test summary `expdwts.xlsx` was read (18:09:34) but not used, because its columns
  (test type, recovery) name no kind the schema has.

## Part A: new records (16)

Shapes and picks are from `read_listing` and `check_files` on the saved listing.

| Record | Page and manifest_url | robots.txt (status: deciding line) | Excerpt | Sample → file, size (UTC) |
|---|---|---|---|---|
| boem/well-data | https://www.data.boem.gov/Main/Well.aspx (17:43:46) | 200, 1,345 lines naming bad bots; no group for `*` (all allowed) | "Borehole … Bottomhole Pressure Survey … eWell Submissions …"; disclaimer (17:44:30): "Some errors may exist in this data" | `*/Well/Files/5010delimit.zip` → 3,994,558 B (17:44:21); html, 188 links |
| boem/paleontologic-data | https://www.data.boem.gov/Main/Paleo.aspx (17:44:09) | as above | "all released paleontologic summary reports and header data from January 1947 to September 30, 2026" | `*/Paleo/Files/gepaldmp_all.zip` → 3,209,217 B (17:45:10); html, 155 |
| boem/ogor-a-well-production | https://www.data.boem.gov/Main/OGOR-A.aspx (17:46:20) | as above | "Well Production 1996-Current"; "Well Production Information Available for June 2026" | `*/Production/Files/ogoradelimit.zip` → 632,057 B (17:46:26); html, 235 |
| cnloer/production-statistics | https://www.cnloer.ca/information/statistics/ (17:47:02) | 200: `User-agent: *` `Disallow:` (empty) | Hibernia monthly files hib_oil_1997.pdf to hib_oil_2026.pdf; copyright (17:47:18): "Unauthorized use or reproduction of these materials … is strictly prohibited." | `*/wp-content/uploads/off_prod-1.pdf` → 377,030 B (17:47:11); html, 386 |
| cnloer/core-inventory | https://www.cnloer.ca/geoscience/ (17:46:52) | as above; www.cnlopb.ca 200, same empty Disallow (18:09:30) | "Geoscience Information. This information can now be found on the Data and Information Hub … Core Inventory" | `*/geoinfo/coreinv.xlsx` → 172,001 B (18:09:32); html, 92 |
| cnloer/source-rock-inventory | as above | as above | "Source Rock Inventory" (columns TOC Mean, Range, Kerogen Type, Maturity) | `*/geoinfo/foasourcerock.xlsx` → 469,933 B (18:09:37) |
| cnloer/geoscience-program-inventories | as above | as above | "Geological Program Inventory … C-NLOPB Geoscientific Report Inventory" | `*/geoinfo/foageol.xlsx` → 486,211 B (18:09:35); georepinv.xlsx 98,731 B (18:09:36) |
| dov/boringen | https://www.dov.vlaanderen.be/page/boringen (17:50:27); terms 17:51:04 | 200: only `User-agent: PetalBot` `Disallow: /`; no group for `*` | "In de DOV-databank is elke waarneming van grondlagen een boring." Terms: "modellicentie voor gratis hergebruik" | WFS GetFeature `dov-pub:Boringen`, 1,099,736 B, 1,000 of 188,507 (17:51:13); bbox from GetCapabilities (18:12:50) |
| dov/boringen-geothermie | metadata https://www.dov.vlaanderen.be/geonetwork/srv/api/records/95ee5bfe-29cc-415a-bcf0-8cc880ab94a1 (18:14:19) | as above | "Deze laag toont enkel de boringen met als doel 'Geothermie' met aanvangsdatum vanaf 01-01-2017." "Als enige gebruiksvoorwaarde geldt een bronvermeldingsplicht." | GetFeature `geothermie:boringen_geothermie` 1,075,964 B, 1,000 of 24,957 (18:13:43) |
| dov/formele-stratigrafie | metadata …/212af8cd-bffd-423c-9d2b-69c544ab3b04 (18:14:19) | as above | "Een formele stratigrafie van een boring of een sondering is een lithostratigrafische interpretatie …" | GetFeature `interpretaties:formele_stratigrafie` 635,336 B, 1,000 of 107,753 (18:13:44) |
| dov/graviteit-data-punten | metadata …/979b8735-9093-4fb7-a74f-a48d1ff4caf7 (18:14:20) | as above | "Deze kaartlaag geeft de nieuwe meetpunten weer … met meetwaarden van de Bouguer graviteit." | GetFeature `gravimetrie:graviteit_data_punten` 236,439 B, 1,000 of 16,915 (18:13:45) |
| geozs/kataster-raziskovalnih-vrtin | https://egeologija.si/geonetwork/srv/slv/xml.metadata.get?uuid=54cebfc7-… (17:52:55) | egeologija.si 404 (allow all); www.geo-zs.si 200 `Disallow:` (empty) | useLimitation: "Data is available under a Creative Commons - Attribution 4.0 International (CC BY 4.0) license." | the bare `VRTINE.zip` (`resources.get`), 2,823,170 B (17:53:02) |
| noc-ly/reports | https://noc.ly/reports/ (17:57:07) | 200: `User-agent: *` `Disallow: /wp-admin/` | year filter 2014, 2023, 2024, 2026; "ملخص الإنتاج والإيرادات المستلمة لشهر يونيو" | `*/NOC-SHORT-REPORT-OF-JUN-.pdf` → 4,712,018 B (17:57:21); html, 83 |
| anh-bo/exploracion-y-explotacion | https://www.anh.gob.bo/w2026/contenido.php?s=10 (17:59:06) | 404 (allow all) | 55 field sheets, each linked twice ('Abrir', and 'Descargar' via /g.php); no licence on the site | `…/Documentos_Id-592-*.pdf` → 2,607,508 B by GET, no length sent (17:59:33); html, 233 |
| nbmg/oil-gas-wells-through-2013 | https://gisweb.unr.edu/nbmg/rest/services/MineralsAndEnergy/OilAndGas/MapServer/1?f=json (18:02:07); hub item from search (18:01:51) | gisweb.unr.edu 404 (allow all); hub 200 `Crawl-delay: 60` | hub licenseInfo: CC BY 4.0, "Please credit the Nevada Bureau of Mines and Geology, University of Nevada, Reno" | `*` → geojson export 422,720 B, ≤1,000 of 1,061 (18:02:13, count 18:02:31) |
| idaho-ogcc/well-files | https://ogcc.idaho.gov/well-files/ (18:05:37) | 200: `User-agent: *` `Disallow:` (empty); gis1.idl.idaho.gov answers robots.txt with an HTML page (no rules) | "LAS files for wells drilled 2007 and later that are available for release can be downloaded from this compressed zip file." | `*/oilgas/welldata/LASFiles.zip` → 36,017,299 B (18:05:45); html, 71 |

Records written, then held back under the `unknown` cap (see `held-back.md`; the files are in `held-back/`):

| Record | Page (UTC) | robots.txt | Excerpt |
|---|---|---|---|
| fig-dmr/offshore-data-release | https://www.gov.fk/mineralresources/regulatory/data-management/ (18:00:21) | 200 `Disallow:` (empty) | "The decision to release data is made by FIG/ the Governor and only once the data are greater than 5.5 years old" |
| mra-pg/geoscientific-data | https://mra.gov.pg/investment/geoscientificdata/ (17:55:06); Shopping-List.pdf (17:55:14); terms (17:55:29) | 200 `User-agents: *` `Allow: /` (malformed line: no group, all allowed) | "Download our document to see shopping List of the Data being sold from MRA." |
| pdasl/national-petroleum-data-repository | https://www.pdasl.gov.lk/data-management (17:56:11) | 404 (allow all) | Data Room access for "qualified operators" |
| sd-danr/oil-gas-production-injection | https://danr.sd.gov/Environment/MineralsMining/OilGas/Data.aspx (18:04:56); HEAD xlsx (18:05:01) | danr.sd.gov and sddenr.net 404 | "Monthly Production Reports for Oil & Gas Wells … 1950 to Present" |

## Part B: the transient retries (once each)

| Records | Retry (UTC) | Outcome |
|---|---|---|
| geosphere-at/aerogeophysics-northern-lower-austria, molasse-basin-subsurface-model | robots.txt 404 (18:10:42); `https://data.tethys.at/api/dataset/212` 200 JSON, 16,428 B (18:10:42); `/191` 200, 18,581 B (18:11:10) | The host is up, but the shape is not one the verifier reads. `files[]` gives only `path_name` (`files/273/file-….pdf`) and a server `filePath`, with no download URL, so `read_listing` finds 0 entries (generic JSON walk). Finding, not a `manifest_url`; the records are unchanged. Each file does state md5 and sha512 values and a size (212: 5 files; 191: DXF horizons). |
| gfz/cosc-1-zero-offset-vsp, dekorp-9n-reprocessed, ketzin-brine-injection, ktb-data | robots.txt for datapub.gfz.de: no answer within 20 s (18:10:42 to 18:11:02) | Still unreachable (as on E24 and E30). The records are unchanged. |

## Refused or held candidates

| Candidate | Evidence (UTC) | Reason |
|---|---|---|
| Ontario OGSR Library | terms page (17:49:05) | "you must not use bots, scripts, scrapers … or other automated means to access, collect, extract, download"; no republishing |
| Québec SIGPEG | robots.txt timed out (17:49:12) | no answer counts as disallow |
| Aquistore (PTRC) | ptrc.ca/resources/databases (17:50:09), /aquistore (17:50:14) | no dataset published; "For access to this data, please contact PTRC" |
| Quest CCS | open.alberta.ca robots and search 403 (17:50:21) | Cloudflare challenge |
| GEUS Jupiter | data.geus.dk robots (17:51:19) disallows `/JupiterWWW/`, `/geoserver`, `/*?`; www.geus.dk robots no answer (17:51:24) | disallowed; self-signed certificate |
| Finland GTK Hakku | hakku.gtk.fi script application (17:51:30); `/api/v1/products` 404 (17:51:43); tiedostopalvelu.gtk.fi no DNS (17:51:36) | no readable listing |
| Latvia LVĢMC | data.gov.lv organisation pages 1 and 2 (17:51:51, 17:51:59) | the 28 datasets include no borehole or well data |
| Cyprus GSD | moa.gov.cy robots `User-agent: *` `Disallow: /` (17:54:39); data.gov.cy search (17:54:23) | disallowed; nothing relevant |
| PNG petroleum (DPE) | www.petroleum.gov.pg suspended page (17:54:50); dpe.gov.pg robots no answer (17:54:52) | unreachable |
| Algeria ALNAFT | robots.txt timed out (17:56:31) | no answer |
| Gabon DGH | DNS failure (17:56:54) | unreachable |
| Ecuador | datosabiertos 403 (17:57:56); controlrecursosyenergia TLS name mismatch (17:58:03); recursosyenergia DNS (17:58:03); eppetroecuador timeout (17:58:04) | unreachable |
| Chile ENAP | www.enap.cl (17:58:44) | company site, finance and price pages only |
| Cuba CUPET | www.cupet.cu (17:58:50) | news site, no data |
| Bolivia YPFB | www.ypfb.gob.bo (17:58:36) | no data pages; ANH used instead |
| Arizona AZOGCC and AZGS | azogcc.az.gov 403 (18:03:08 robots and page, Cloudflare); library.azgs script application (18:03:25); data.azgs API timed out (18:03:27) | blocked, unreadable |
| Oregon DOGAMI | www.oregon.gov and gis.dogami robots: name resolution failed (18:04:03, 18:04:21; again 18:11:32) | unreachable |
| Tennessee | tn.gov robots connection reset (18:04:48); retry: robots 403 and page 403 (18:11:47) | blocked |
| BOEM seismic | Main/Seismic.aspx (17:43:48) | points to NAMSS, already catalogued as usgs/namss |
| Gorgon CCS | australia.chevron.com robots and page 403 (18:11:26) | blocked |
| Tomakomai CCS | see `held-back.md` | Japan CCS terms require permission to link and forbid copying; the supervisor kept it out |
| NBMG other layers | MapServer root (18:12:48) | layer 0 is the older 'through 2006' wells; the rest are maps, not data kinds |

## Findings

- F1. `urllib.robotparser` ignores `*` inside paths (RFC 9309). `Disallow: /recherche/dataset/*?`
  (donneesquebec) and `Disallow: /*?` (data.geus.dk) read as allowing everything. `osd.verify._Robots`
  is built on robotparser, so it has the same gap.
- F2. Several robots.txt files have no group for `*`: www.data.boem.gov names 1,345 lines of bad bots,
  and www.dov.vlaanderen.be names PetalBot only. Both read as allow all. mra.gov.pg writes
  `User-agents: *`, which parses as no group at all.
- F3. Tethys RDR's dataset API (`data.tethys.at/api/dataset/<id>`) lists files with checksums and sizes
  but without URLs. A reader for it would need the download path, which the API does not state.
- F4. The DOV GeoServer GetCapabilities runs past 8 MB, and each layer's WGS84BoundingBox is the
  publisher's stated extent. Many more DOV layers are reusable under the Modellicentie, including the
  G3Dv3 and H3D model layers (horizons, faults, isopachs), the groundwater wells and the CPTs.
- F5. Japan CCS serves its terms page with HTTP 404 and the full text.
- F6. www.anh.gob.bo sends PDFs with no Content-Type and no Content-Length.
