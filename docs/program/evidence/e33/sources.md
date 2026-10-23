# E33 sources: records, the ninth twenty (read 2026-10-23)

Every address below was opened from the lane host on 2026-10-23 at the UTC time given. All
requests used the verifier's user agent (`osd.verify.USER_AGENT`), and robots.txt was read first for
each host. Robots were judged as `osd.verify._Robots` judges them (2xx is obeyed, 4xx allows all, 5xx
or no answer disallows), with `urllib.robotparser` plus an RFC 9309 `*` wildcard check. Each page or
listing was read once and saved, then parsed offline with `osd.verifier.listings.read_listing`, and
the `src/osd/verifier/samples.yaml` globs were matched the way `check_files` matches them. Picked
files were sized with one HEAD where a size is given. Nothing was hashed, and `osd verify` was not
run from this host. Records state publisher facts only.

Slips, for the record:
- One curl of `https://fortress.wa.gov/robots.txt` went out with the user agent "osd-test" (about
  18:34:30; connection reset). The scripted read at 18:34:20 with the verifier's agent got no answer
  either.
- www.inhgeomin.gob.hn/ was read twice (the second GET at 18:40:05), and omnis.mg was opened under
  both www.omnis.mg (18:32:26) and omnis.mg (18:44:05).
- `Drill_Cuttings.html` on gisappl.saskatchewan.ca was read twice (18:42:36 and 18:56:44).
- Guessed addresses that answered 404: Missouri DNR pages, the GeoAtlas pages `Non_Vertical_well.html`
  (18:42:07) and `Non_vertical_well.html` (18:42:30), the opendata.gov.mn API, and a
  fis-geophysik.de licence page. None was used.
- www.dnr.wa.gov robots.txt failed once with a DNS error. The cached failure was cleared and the
  file read again once (200, 18:34:01).

## Part A: the four records E31 held back (moved by `git mv`, re-read)

The files moved unchanged from `docs/program/evidence/e31/held-back/` into `records/`; sd-danr's
samples line from `held-back.md` is in `samples.yaml`. Each page was re-read once and the E31 excerpt
is still there.

| Record | Page (UTC) | robots.txt | Excerpt still present |
|---|---|---|---|
| fig-dmr/offshore-data-release | https://www.gov.fk/mineralresources/regulatory/data-management/ (18:27:54) | 200: `User-agent: *` `Disallow:` (18:27:52) | "only once the data are greater than 5.5 years old" |
| mra-pg/geoscientific-data | https://mra.gov.pg/investment/geoscientificdata/ (18:27:55) | 200: `User-agents: *` `Allow: /` (malformed group name; nothing disallowed) (18:27:54) | "shopping List" |
| pdasl/national-petroleum-data-repository | https://www.pdasl.gov.lk/data-management (18:27:58) | 404 (18:27:57) | "qualified operators" |
| sd-danr/oil-gas-production-injection | https://danr.sd.gov/Environment/MineralsMining/OilGas/Data.aspx (18:27:58) | 404 (18:27:58); sddenr.net 404 (18:28:19) | "1950 to Present"; `*/pubs/og/Oil_Gas_Production_All_Years.xlsx` → 14,332,260 B (HEAD 18:28:19) |

## Part B: new records (16)

| Record | Page and manifest_url (UTC) | robots.txt | Excerpt | Sample → file, size |
|---|---|---|---|---|
| wa-dnr/oil-gas-wells | https://dnr.wa.gov/washington-geological-survey/publications-and-data/geology-gis-data-and-databases (18:34:06, redirected from www.dnr.wa.gov); layer `Public_Geology/Oil_and_Gas_Wells/MapServer/1` (18:35:40); stats (18:35:49) | dnr.wa.gov 200, Drupal default (`Disallow: /index.php/admin/` …), page allowed; gis.dnr.wa.gov 404 (18:30:18) | "Oil and Gas Wells Feb. 2019 5 MB"; "point locations that represent oil and gas test well sites in Washington State from 1890 to present"; 830 wells, DRILL_START_DATE 1901-01-01 to 2012-09-05 | arcgis-layer: one geojson export, all 830 (maxRecordCount 2000) |
| wa-dnr/geothermal-wells | same page; layer `Geothermal/MapServer/7` (18:35:41); stats (18:35:52) | as above | "Geothermal Wells Feb. 2024 41 MB"; "known geothermal and heat flow wells in the state of Washington"; 489 wells, TEST_DATE 1930-01-01 to 2019-11-13 | arcgis-layer, all 489 |
| wa-dnr/geophysics-database | same page; layer `Geophysics/MapServer/2` (18:46:16); count (18:46:17); dates (18:46:27); seismic layer 17 (18:50:24, count 18:50:25) | as above | "Geophysics Database Apr. 2023 61 MB"; copyright "Digital Data Series 28, version 1.0, April 2023"; 7,577 gravity stations, ACQUISTION_DATE empty; 205 seismic profiles | arcgis-layer, 2000 of 7,577 |
| wa-dnr/shear-wave-database | same page; service `Shearwave_Data/MapServer` (18:50:32); layer 12 (18:50:48); count (18:50:49); dates (18:53:40) | as above | "Shear Wave Database Jun. 2021 4 MB"; "a compilation of shear-wave data from studies performed by the Washington Geological Survey, the U.S. Geological Survey, and the Environmental and Engineering Geophysical Society"; 599 sites, Date_Acquired 2007-02-26 to 2021-04-29 on 257 | arcgis-layer, all 599 |
| wa-dnr/groundwater-chemistry | same page; service `Groundwater_Chemistry/MapServer` (18:56:02); layer 0 (18:56:12); count and dates (18:56:12 to 18:56:21) | as above | "Groundwater Geochemistry Jul. 2025 4 MB"; "includes data from springs, oil and gas wells, a carbon capture well, and water wells"; 1,501 samples, COLLECTION_DATE 1916-09-16 to 2024-03-20 on 1,472 | arcgis-layer, all 1,501 |
| (licence for the five) | https://dnr.wa.gov/washington-geological-survey/publications-and-data/disclaimers-and-citation-guidelines (18:34:41) | as above | "All of the materials we produce (publications, digital content, posters, videos) are free for you to use in any way you choose, for both commercial and non-commercial purposes, including modifying or adapting anything, as long as you cite us." | |
| orogo/well-data | https://www.orogo.gov.nt.ca/en/well-data (18:40:55); well page canol-bluefish-no-1a (18:41:09) | 200, Drupal default; pages allowed (18:40:36) | 685 wells; "WID 0043 - Report - Well History Bluefish No. 1A.pdf (2.01 MB)" | none (the list links well pages) |
| orogo/geoscience-programs | https://www.orogo.gov.nt.ca/en/geophysical-programs (18:41:32) | as above | "results of geoscience programs carried out in OROGO’s jurisdiction between 1943 and 2013 (no programs have been carried out since then)"; 1,201 programs | none |
| (terms for both) | https://www.orogo.gov.nt.ca/en/terms-use (18:41:07) | as above | "Material may not be used or reproduced for commercial purposes without the prior written consent … If it is reproduced or redistributed for non-commercial purposes, the Government of the Northwest Territories copyright is to be acknowledged." | |
| sk-mer/non-vertical-wells | layer `Economy/Petroleum/MapServer/1` (18:41:58); stats (18:42:06); service root (18:42:22); licence from Vertical_well.html (18:42:15) | gis.saskatchewan.ca 404 (18:41:58); gisappl.saskatchewan.ca 404 (18:42:06) | "All feature classes from the PETROLEUM schema in the Production Data Warehouse"; 68,000 features, WELLDERIVEDSPUDDATE 1953-08-26 to 2026-10-07; "Government of Saskatchewan Standard Unrestricted Use Data License (Version 2.0)" | arcgis-layer, 2000 of 68,000 |
| sk-mer/drill-cuttings | https://gisappl.saskatchewan.ca/WebDocs/Geo_Atlas/MetaData/Drill_Cuttings.html (18:42:36); layer 3 (18:56:38) and count | as above | "Locations of Phanerozoic wells with drill cutting samples stored at the Subsurface Lab in Regina."; metadata count 69,908; 73,632 features today | arcgis-layer, 2000 of 73,632 |
| mem-gt/produccion-de-hidrocarburos | https://mem.gob.gt/que-hacemos/hidrocarburos/hidrocarburos-upstream/explotacion/produccion/ (18:37:01) | 200 (18:36:10): Cloudflare block with `User-agent: *` `Content-Signal: search=yes,ai-train=no,use=reference` `Allow: /`, and a Yoast `User-agent: *` `Disallow:` | "Producción de hidrocarburos 2025 … 2012"; 14 .xlsx links | `*/PRODUCCION-DE-HIDROCARBUROS-2025.xlsx` → 53,687 B (HEAD 18:37:15); html, 178 links |
| lpra/well-database | https://lpra.gov.lr/well-database/ (18:38:46) | 200: `User-agent: *` `Disallow: /wp-admin/` (18:38:43) | "1970 Chevron llB-1 2,930 13 Dry … Dec-16 ExxonMobil Mesurado-1 4,000+ 13 Dry"; "Copyright 2024" | none (no files) |
| drieat-idf/puits-de-geothermie | https://www.data.gouv.fr/datasets/puits-de-geothermie-1; manifest https://www.data.gouv.fr/api/1/datasets/6835e20db63a9d35e7858995/ (18:43:22); Atom zip HEAD (18:43:34), GET (18:43:42) | www.data.gouv.fr 200 (18:43:01): `/api/1/datasets/r/` disallowed, `/api/1/datasets/<id>/` allowed; atom.geo-ide.developpement-durable.gouv.fr 404 (18:43:34) | "Localisation des têtes et impacts des puits géothermiques en Île-de-France."; licence `lov2`; zip metadata: "Licence Ouverte / Open Licence Version 2.0"; 295 points | `https://atom.geo-ide.developpement-durable.gouv.fr/atomArchive/GetResource?id=e0d88ccf-*` → 23,897 B; json walk, 54 entries, one match |
| co2datashare/eos-31-5-7-thermo-mechanical | https://co2datashare.org/dataset/rock-mechanics-data-for-31-5-7-eos-well-thermo-mechanical-response (18:44:54); licence page (18:45:41) | 200 (18:44:26): `Disallow: /api/`, `Crawl-Delay: 10` | "part II of a rock mechanical testing program performed by NGI for Northern Lights JV DA"; period June 12, 2020 to May 1, 2023; licence "You may not sell the Licensed Material." | none (download is a POST behind the licence box) |
| co2datashare/svelvik-cross-well-2019 | https://co2datashare.org/dataset/svelvik-co2-field-lab-cross-well-data-2019 (18:45:05); licence page (18:45:22) | as above | "cross-well seismic measurements taken before, during, and after the CO2 injection"; period August 8, 2019 to November 6, 2019; "This license is based on CC BY 4.0 license" | none (as above) |
| liag/geotis | https://www.geotis.de/homepage/basics (18:46:55); terms https://www.geotis.de/homepage/terms (18:46:42) | 200 (18:32:56): `User-agent: *` `Disallow: /analytics/`, `/dadabik/`, `/shared/`, `/geotisapp/temp/` | "mehr als 30.000 Bohrungen"; "3D-Untergrundmodelle"; terms: "nicht mehr als ein Fünftel der Landesfläche Deutschlands in einer Veröffentlichung" | none (maps and sections) |
| cnr-igg/geothopica-bdng | https://geothopica.igg.cnr.it/index.php/it/geothopica2-0 (18:46:54); terms …/termini-dutilizzo (18:46:43) | 404 (18:40:38) | "dopo aver effettuato la registrazione ed aver accettato i termini e le condizioni di utilizzo"; "licenza Creative Commons Attribution 4.0 International (CC BY 4.0)" | none (registration) |

bbox values for the WA DNR and the Saskatchewan non-vertical layers are each layer's `extent`
converted to WGS84 with pyproj on a 21 × 21 grid; each record says so. The drill-cuttings bbox is
the metadata's Bounding_Coordinates; the DRIEAT bbox is data.gouv.fr's `spatial` box. The CO2
DataShare sets state one point each, which is not an extent, so they have no bbox.

## Refused or not recorded (reasons)

| Candidate | Address (UTC) | Reason |
|---|---|---|
| Yukon Geological Survey | open.yukon.ca (18:29:08), data.geology.gov.yk.ca (18:29:09) | 202 with an empty body; Cloudflare "Just a moment..." 403 |
| NWT Geological Survey | www.nwtgeoscience.ca | robots 200, page timed out |
| Oregon DOGAMI | www.oregon.gov (18:29:42) | DNS failure |
| Missouri DNR wells | gis.dnr.mo.gov layer and info.mo.gov metadata (18:30:46, 18:30:47) | licence not stated (use constraint is a warranty disclaimer); `unknown` cap full |
| New Brunswick DNRED | geonb.snb.ca (18:40:35) | Cloudflare challenge |
| Paraguay | www.ssme.gov.py (18:31:34), www.mopc.gov.py (18:38:13) | DNS failure |
| Jamaica PCJ | www.pcj.com (18:31:34) | DNS failure |
| Barbados | energy.gov.bb (18:55:33 to 18:55:54); bnocl.com (18:55:35) | ministry pages describe services and show energy charts, no dataset; BNOCL robots gave no answer |
| Dominican Republic | sgn.gob.do (18:38:08) | Cloudflare 403 |
| Belize | www.geologyandpetroleum.gov.bz (18:38:28) | DNS failure |
| Honduras | www.inhgeomin.gob.hn | mining only, no petroleum data |
| Egypt EGAS | www.egas.com.eg (18:37:27) | news and maps, no dataset; EG already listed |
| Tunisia ETAP | www.etap.com.tn (18:31:44) | TLS certificate failure |
| Sierra Leone PDSL | www.pdsl.gov.sl (18:38:07) | DNS failure |
| Cameroon SNH | www.snh.cm (18:31:45) | timeout |
| Equatorial Guinea MMH | www.mmh.gob.gq (18:44:03) | TLS hostname mismatch |
| Madagascar OMNIS | omnis.mg | drilling services only, no data page |
| Seychelles | www.petroseychelles.sc (18:32:31) | DNS failure |
| Somalia SPA | spa.gov.so (18:44:05) | Cloudflare "Attention Required!" 403 |
| Botswana BGI | www.bgi.org.bw (18:37:51; terms 18:39:40) | purchase and request with fees, no redistribution clause; `unknown` cap full |
| Zambia, Malawi | www.mme.gov.zm, www.mines.gov.mw (18:44:05) | DNS failure |
| Jordan | www.memr.gov.jo (18:37:29), www.nra.gov.jo (18:44:07) | timeout; DNS failure |
| Lebanon LPA | lpa.gov.lb (18:36:13) | data rooms on request, no licence; `unknown` cap full |
| Mongolia MRPAM | mrpam.gov.mn (18:37:49) → opendata.gov.mn/data/5323533 | script-only page; its API paths answered 404 |
| Timor-Leste ANPM | www.anp-tl.org (18:32:34), www.anpm.tl (18:36:15) | domain for sale; DNS failure |
| Brunei PA | www.pa.gov.bn (18:38:09) | describes a data repository, no access path |
| Israel | — | PRIME already listed (prime/national-oil-gas-database) |
| Utah FORGE | — | doe-gdr already holds three FORGE records (aggregator cap) |
| Soultz-sous-Forêts | cdgp.u-strasbg.fr (robots timeout twice; 18:48:21) | robots no answer means disallow; EPISODES platform (episodesplatform.eu) is a script app |
| Ketzin | — | GFZ host: no third retry (charter) |
| Hontomín CIUDEN | www.ciuden.es (18:44:07) | no data published |
| Otway CO2CRC | www.co2crc.com.au (18:32:57) | no dataset on the page |
| Decatur IBDP | — | already co2datashare/illinois-basin-decatur |
| Groningen NAM | www.nam.nl (18:40:38) | script page, no dataset reached |
| Johansen (CO2 DataShare, University of Bergen) | co2datashare.org/dataset/the-johansen-dataset (18:52:37); ODbL page (18:52:59) | already sintef/johansen (same model, notes cite this DOI) |
| FIS Geophysik (LIAG) | www.fis-geophysik.de (18:47:35) | rich inventory, licence page 404; `unknown` cap full |
| WA DNR Subsurface Database | GIS data page ("Subsurface Database Jun. 2026 160 MB") | only the zip on fortress.wa.gov (robots no answer); no map layer; contents not stated on the page |
| TEO Pays de la Loire geothermal installations | data.gouv.fr search (18:51:37) | republishes BRGM data; BRGM is on the do-not-retry list |
| data.gouv BSS mirror | — | third-party mirror (cquest), not the publisher |

## Findings

- Washington DNR's GIS downloads sit on fortress.wa.gov, whose robots.txt gave no answer (so the
  verifier would disallow it). The same datasets are served as ArcGIS layers on gis.dnr.wa.gov
  (robots 404), and those layers are the manifests.
- data.gouv.fr disallows `/api/1/datasets/r/` (resource redirects) but not the dataset API, so the
  dataset JSON is a readable listing whose resource URLs point straight at the publisher's host.
- mem.gob.gt's robots.txt carries a Cloudflare `Content-Signal` line (`use=reference`) that the
  verifier's robots reader does not interpret; the `Allow: /` in the same group decides.
- Eleven agency hosts gave no DNS answer from this host on the day (Oregon, Paraguay twice, Jamaica,
  Belize, Sierra Leone, Seychelles, Zambia, Malawi, Jordan NRA, Timor-Leste ANPM).
