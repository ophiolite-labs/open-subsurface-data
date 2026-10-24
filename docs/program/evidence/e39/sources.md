# E39 sources: records, the eleventh twenty (read 2026-10-24)

Every address below was opened from the lane host on 2026-10-24 at the UTC time given. All
requests used the verifier's user agent (`osd.verify.USER_AGENT`), and robots.txt was read first for
each host and judged as `osd.verify._Robots` judges it (`osd.verifier.robots`, RFC 9309; 2xx is
obeyed, 4xx allows all, 5xx or no answer disallows). Each page or listing was read once and saved,
then parsed offline with `osd.verifier.listings.read_listing`, and the `src/osd/verifier/samples.yaml`
globs were matched against the parsed entries. Picked files were sized with one HEAD where a size is
given. Nothing was hashed, and `osd verify` was not run from this host. Records state publisher facts
only.

Slips, for the record:
- open.canada.ca asks `Crawl-delay: 20`. The CKAN searches at 03:18:26, 03:18:28 and 03:18:31, and
  the four `package_show` calls at 03:19:12 to 03:19:18, were about 2 s apart.
- A Geonorge search with non-ASCII text (03:31:52) failed in the client (UnicodeEncodeError) and was
  not sent; it was sent again percent-encoded (03:31:59).
- A guessed catalogue.data.wa.gov.au slug, `/dataset/dmirs-core-library-drill-holes-dmirs-004`
  (03:28:16), answered the portal's not-found page (HTTP 200, 20,499 bytes). The package was found by
  `package_search` instead (03:28:24).
- resources.bgs.ac.uk robots.txt was read twice, once for http (03:16:38) and once for https
  (03:17:42); both 404.
- The first GSNSW core-library GetFeature (03:29:50) asked for the whole layer and was cut at the
  client's 8 MB cap; the count (`resultType=hits`, 03:30:03) and the first 1,000 features (03:30:06)
  were read after it.
- Sodir FactMaps layer 408 (03:27:54, 03:27:55) was opened while looking for the structural elements
  and not used.
- An AGS publication page (`ags.aer.ca/publication/dig-2023-0002`, 03:32:40) was opened and not used.
- The two Geonorge `metadata/uuid/` pages for Sodir and NGU seismic (03:46:08, 03:46:09) were opened
  after the catalogue API entries, to give each record a human page as origin.

## New records (20)

| Record | Page and manifest_url (UTC) | robots.txt | Excerpt | Sample → file, size |
|---|---|---|---|---|
| gsni/tellus-airborne-electromagnetics | https://admin.opendatani.gov.uk/dataset/gsni-tellus-regional-airborne-geophysical-survey-electromagnetics (03:17:24), page and manifest | admin.opendatani.gov.uk 200 (03:15:56): `User-agent: *` `Disallow: /api/` `Crawl-Delay: 10`; resources.bgs.ac.uk 404 (03:17:42) | "License UK Open Government Licence (OGL)" (link https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/); "flown by the Geological Survey of Northern Ireland in 2005 and 2006 as part of the Tellus project" | `*/gsni/geophysics/Electromagnetics.zip` → 383,666,252 B (HEAD 03:17:43); html, 54 links |
| gsni/tellus-airborne-radiometrics | …-radiometrics (03:17:36) | as above | same licence line; "Magnetic, electromagnetic and radiometric data were acquired at 200 m line spacing and a flying height of 56 m" | `*/gsni/geophysics/Radiometrics.zip` → 58,395,852 B (HEAD 03:17:44) |
| gsni/tellus-airborne-magnetics | …-magnetics (03:16:29); JSON-LD 88d90c6f-… (03:17:05) | as above; resources.bgs.ac.uk 404 (03:16:38) | same licence line; "In total, 82,000 line-km of data were acquired." | sentence: Magnetics.zip is 997,778,640 B (HEAD 03:16:39), over the 512 MiB budget; html, 55 links |
| nrcan/west-coast-marine-seismic-repository | https://open.canada.ca/data/en/dataset/b9400595-b5b6-4a76-b34e-b437178adb45 (03:35:00); `package_show` (03:19:12); licence page (03:20:47) | open.canada.ca 200 (03:17:55): `Crawl-delay: 20`, `Disallow: /core/` …; ftp.maps.canada.ca 200 (03:20:24): `User-agent: *` `Disallow: /pub` | `"license_title": "Open Government Licence - Canada"`; "scan and convert all our inventory of analog marine survey field records (seismic, sidescan and sounder) to digital format"; time_period_coverage 1960-01-01 to 2016-01-01 | none (resources under ftp.maps.canada.ca/pub, disallowed; SKIP 03:20:45) |
| ns-energy/onshore-petroleum-wells | https://data.novascotia.ca/Energy/Onshore-Petroleum-Wells/5q4c-27fh (03:33:32); manifest `/api/views/5q4c-27fh.json` (03:19:47); open.canada.ca `package_show` 542f8d90-… (03:19:16) | data.novascotia.ca 200 (03:19:45): `Crawl-delay: 1`, `Disallow: /browse?*&q=` …; novascotia.ca 200 (03:19:48) | `"license": {"name": "Nova Scotia Open Government Licence", "termsLink": "http://novascotia.ca/opendata/licence.asp"}`; "Listing of petroleum wells drilled onshore in NS as of February 1, 2016."; "Time Period Coverage": "1869-01-01/2016-02-01" | `*` → Socrata rows.csv |
| on-mnr/petroleum-wells | https://data.ontario.ca/dataset/235fcd04-6632-4cce-a403-556089cc4276 (03:33:30); open.canada.ca `package_show` (03:19:18); layer `LIO_Open08/MapServer/22?f=json` (03:20:21); count (03:21:06); SPUD_DATE stats (03:21:08, 03:21:21, 03:21:23); licence page (03:20:23) | data.ontario.ca 200 (03:33:28): `Disallow: /api/`, `Crawl-Delay: 10`; ws.lioservices.lrc.gov.on.ca 404 (03:20:20); www.ontario.ca 200 (03:20:22) | "Licence Open Government Licence – Ontario"; "You are free to: Copy, modify, publish, translate, adapt, distribute or otherwise use the Information in any medium, mode or format for any lawful purpose."; 27,639 features | arcgis-layer, all 27,639 |
| miterd/sondeos-hidrocarburos | datos.gob.es entry (API `title/sondeos` 03:18:00; page timed out 03:34:07); IDEE record spaminetadpermisosysondeos (03:21:41); WMS and WFS capabilities (03:21:57, 03:22:20); manifest hits (03:22:54) and COUNT=2 (03:23:09) | datos.gob.es 200 (03:17:59); www.idee.es 200 (03:21:40): `User-Agent: *` `Disallow:`; geoportal.minetur.gob.es 404 (03:21:56) | "MITERD CC BY 4.0"; "No se aplican condiciones de acceso y uso."; "Conjunto de datos de localización de Permisos de Investigación y Concesiones de Explotación activos así como de campañas sísmicas y sondeos de hidrocarburos en España"; numberMatched 810 | `{file: true}`: GML (`text/xml; subtype="gml/3.2.1"`) |
| drieat-idf/puits-de-petrole | https://www.data.gouv.fr/datasets/puits-de-petrole-en-ile-de-france (03:35:02); manifest `/api/1/datasets/6835e107b63a9d35e78588c8/` (03:23:42); WFS capabilities and one feature (03:23:55, 03:24:03) | www.data.gouv.fr 200 (03:17:57): `Disallow: /admin`, `Disallow: /datasets/search?*` …; atom host 404 (03:23:51); ogc host 404 (03:23:54) | `"license": "lov2"`; "Puits de pétrole en Ile-de-France"; created_at 2022-03-18, last_modified 2022-03-03 | `…GetResource?id=81471c16-*` → the Atom shapefile download (HEAD 200, no length, 03:23:52); json walk |
| ispra/boreholes | https://catalogosgi.isprambiente.it/geoportalAdm2/rest/document?id=ispra_rm%3ABoreholes_DT (03:34:40); RNDT CSW GetRecordById (03:24:39); Atom feed (03:24:57); manifest HEAD (03:25:31); ArcGIS service (03:25:36) | catalogosgi 200 (03:34:38) with an HTML page, no rules; geodati.gov.it 404 (03:24:38); sgi3 404 (03:24:55); sgi2 404 (03:25:34) | "Dato concesso con licenza CC-BY-4.0 - https://creativecommons.org/licenses/by/4.0/deed.it"; "Nessuna Limitazione al Pubblico Accesso"; "dati dell'attività di Esplorazione e Produzione degli idrocarburi in Italia depositati presso l'UNMIG dal 1957 a oggi" | `*` → Boreholes_INSPIRE.zip (application/x-gmz), 824,982 B |
| csulb/san-pedro-basin-fault-mcs-2018 | https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/EGB21M (202, empty, 03:34:41); manifest dataset API (03:26:28) | dataverse.harvard.edu 202 with an empty body (03:25:52): allow | `"license": {"name": "CC0 1.0", "rightsIdentifier": "CC0-1.0"}`; "We collected 33 new profiles totaling 365 line-km"; dateOfCollection 2018-04-28 to 2018-06-29 | `*SPB_104a_fkmigr_1500_50_150hz.sgy` → datafile 5251204, 7,310,240 B (as listed); dataverse, 160 files |
| csulb/san-diego-trough-fault-mcs-2018 | dataset.xhtml doi:10.7910/DVN/5PXHWK; manifest dataset API (03:26:30) | as above | `"license": {"name": "CC0 1.0"}`; "We collected six new profiles totaling 50 line-km"; dateOfCollection 2018-04-22 to 2018-04-23 | `*SDT_11_fkmigr_1500_30_150hz.sgy` → datafile 5216916, 21,599,680 B (as listed); dataverse, 30 files |
| sodir/faults-and-boundaries | https://kartkatalog.geonorge.no/metadata/uuid/d19c485f-8b42-4dda-b2b2-b1cbe2d613cb (03:46:08); Geonorge API getdata (03:27:09); manifest FactMaps layer 702 (03:27:48); count (03:27:50); layer 704 and count (03:27:51, 03:27:53) | kartkatalog.geonorge.no 200 (03:26:58): `User-agent: *`, no rules; www.sodir.no 200 (03:27:19): `Disallow: /EPiServer/` `Disallow: /Util/`; factmaps.sodir.no 404 (03:27:41) | `"OtherConstraintsLinkText": "Norsk lisens for offentlige data (NLOD)"`, link http://data.norge.no/nlod/no/1.0; UseLimitations "The contents on the website of the Norwegian Offshore Directorate may be copied and used free of charge as long as all material subject to copyright contains a reference to the source." | arcgis-layer, all 3,590 (www.sodir.no zip HEAD 403, Cloudflare, 03:27:20) |
| wa-demirs/core-library-drill-holes | https://catalogue.data.wa.gov.au/dataset/mineral-drill-holes-dmirs-004 (03:34:52); CKAN `package_search` (03:28:24); manifest layer 1 (03:28:35); count (03:28:37); spud_date stats (03:28:49) | catalogue.data.wa.gov.au 200 (03:28:13) with an HTML page, no rules; public-services.slip.wa.gov.au 404 (03:28:04) | `"license_title": "Creative Commons Attribution 4.0"`; "Index to mineral core stored by the Department of Mines, Industry Regulation and Safety."; 4,143 points | arcgis-layer, all 4,143 |
| wa-demirs/2d-seismic-surveys | https://catalogue.data.wa.gov.au/dataset/2d-seismic-surveys (03:34:48); manifest layer 23 (03:28:39); count (03:28:40); one row (03:35:19) | as above | `"license_title": "Creative Commons Attribution 4.0"`; "This dataset is a reference system for petroleum exploration 2D seismic surveys conducted in Western Australia."; 35,082 polylines | arcgis-layer, all 35,082 |
| wa-demirs/3d-seismic-survey-polygons | https://catalogue.data.wa.gov.au/dataset/3d-seismic-survey-polygons (03:34:56); manifest layer 24 (03:35:14); count (03:35:16); one row (03:35:20); date stats (03:35:29) | as above | `"license_title": "Creative Commons Attribution 4.0"`; "reference system for petroleum exploration 3D seismic surveys"; start_date 1981-10-29 to end_date 2024-03-23 | arcgis-layer, all 209 |
| gsnsw/coal-seam-gas-boreholes | https://data.nsw.gov.au/data/dataset/coal-seam-gas-borehole (03:34:46); CKAN `package_search` (03:29:18); WFS capabilities (03:29:38); manifest GetFeature (03:29:46) | data.nsw.gov.au 200 (03:29:09): `User-agent: *` `Allow: /`; public-gs.geoscience.nsw.gov.au 404 (03:29:35) | "Licence Creative Commons Attribution"; "Information about and locations of wells drilled to explore for, assess or extract potential coal seam gas resources."; "Temporal Coverage From 11/11/1961"; data-extent polygon 141/-37.7/154/-28.8 | `{file: true}`: application/json, inline filename=drilling_drillholes_csg.json, 905 features, 1,175,106 B |
| gsnsw/drillholes-core-library | https://data.nsw.gov.au/data/dataset/nsw-drillholes-core-library (03:34:43); hits (03:30:03); manifest `count=1000` (03:30:06) | as above | "Licence Creative Commons Attribution"; "Approximately 8% of the drillholes are physically held (either wholly or in part) at the Department’s core library facilities across the state"; "Temporal Coverage From 30/06/2011"; numberMatched 11,955 | `{file: true}`: application/json, first 1,000 features, 1,252,987 B |
| kigam/coastal-marine-geological-map-gangneung-samcheok | https://data.kigam.re.kr/data/d7b6565a-0ba7-4658-bd03-4fe95928ceb4 (03:30:53); listing `search/metadata?subject=OilUndersea` (03:30:38) | data.kigam.re.kr 400 (03:30:35): allow | License badge `href="http://creativecommons.org/licenses/by-nc-nd/4.0/deed.ko"`; "이 데이터의 저작권은 한국지질자원연구원에게 있습니다."; "대한민국 연안해저지질도 제1집(2019, 강릉-삼척, 1:100,000) GIS 구축"; 수치연안해저지질도1집.zip ( 1.00 Gb ) | sentence: the search lists the dataset with no file addresses |
| ngu/grunnvannsborehull | https://kartkatalog.geonorge.no/metadata/grunnvannsborehull/82cd33ef-52dd-4c83-b2d6-e55a0941b33b (03:32:42); Geonorge API getdata (03:32:13); download capabilities (03:32:22) | kartkatalog 200 (03:26:58); nedlasting.ngu.no 404 (03:32:21); geo.ngu.no 503 (03:32:23): disallow | `"OtherConstraintsLinkText": "Norsk lisens for offentlige data (NLOD)"`, link http://data.norge.no/nlod/no/1.0; "Ingen begrensninger på bruk er oppgitt."; "landsdekkende oversikt over borede grunnvannsbrønner, energibrønner og naturlige oppkommer av grunnvann" | none (Geonorge order API, a POST; no file address) |
| ngu/seismiske-linjer-2d | https://kartkatalog.geonorge.no/metadata/uuid/a8390c01-62a7-4582-9b77-f42c51656107 (03:46:09); Geonorge API getdata (03:32:11) | kartkatalog 200; geo.ngu.no 503 (03:32:23): disallow (SKIP of the WMS capabilities) | `"OtherConstraintsLinkText": "Norsk lisens for offentlige data (NLOD) 2.0"`, link https://data.norge.no/nlod/no/2.0; "Seismiske linjer, 2D viser hvor NGU har samlet inn seismiske data og sedimentekkoloddata." | none (WMS only, on a host whose robots.txt answers 503) |

bbox values are only extents the publisher states: the open.canada.ca spatial polygons (NRCan west
coast, Nova Scotia wells), the ArcGIS layer extent for Ontario (NAD83, EPSG:4269, which is within a
metre of WGS84 at map scale), the INSPIRE bounding boxes of the IDEE and RNDT records (MITERD, ISPRA),
the data.gouv.fr spatial polygon (DRIEAT), the Geonorge bounding boxes (Sodir, NGU ×2), the CKAN
spatial polygons of the three WA packages, and the data.nsw `data-extent` polygon (GSNSW ×2). No
bbox where the publisher states only a place: Tellus ("the whole of Northern Ireland"; the JSON-LD
carries no extent), the two CSULB surveys ("Offshore Southern California Inner Continental
Borderland") and KIGAM (강릉삼척해역).

## Refused or not recorded (reasons)

| Candidate | Address (UTC) | Reason |
|---|---|---|
| E22, E24, E25, E30, E31, E33, E37 refused candidates; Tomakomai | not opened | On a refused list; not retried. The Yukon datasets met in the open.canada.ca searches are on the E33 list. |
| Open Data NI catalogue search API | admin.opendatani.gov.uk `/api/3/action/package_search` (SKIP 03:15:56); www.opendatani.gov.uk robots 500 (03:15:56) | robots.txt disallows `/api/` (and 5xx disallows all on www); the GSNI datasets were found through the HTML search page (03:16:08). |
| govdata.de and data.gov.uk (ckan.publishing.service.gov.uk) search APIs | SKIP 03:17:59, 03:18:03 | robots.txt disallows them (govdata.de: `User-agent: *` `Disallow: /`; data.gov.uk: `Disallow: /api/`). |
| borealisdata.ca and dataverse.nl searches | SKIP 03:25:56 | robots.txt disallows (`dataverse.nl`: `User-agent: *` `Disallow: /`). |
| figshare | api.figshare.com robots and search (03:25:50, 03:25:52) | 403 to the verifier's agent. |
| NRCan gravity point data (Geophysical Data Repository) | gdr.agg.nrcan.gc.ca robots (03:20:46) | Connection refused: robots unreadable, so disallowed. |
| NRCan Lithoprobe and other scanned seismic lines | open.canada.ca searches (03:18:26) | One dataset per line, files under ftp.maps.canada.ca `/pub`, which is disallowed. |
| USGS National Geochemical Database (rock) | mrdata.usgs.gov (SKIP 03:30:25) | robots.txt `User-agent: *` `Disallow: /`. USGS data releases sit on ScienceBase, which answered 403 in E37. |
| Queensland (data.qld.gov.au) | dataset search (03:28:59) | HTTP 202 with an empty body (a challenge): blocked (OSD-D9). |
| IGME Litoteca (core library) | https://info.igme.es/litoteca/ (03:31:13); datos.gob.es searches (03:18:00, 03:18:37) | The page is a script-only application, and the datos.gob.es entry states no licence: the cap is zero. |
| Bolzano sondaggi, Friuli PUL geothermal wells | dati.gov.it searches (03:18:41, 03:18:43) | Shallow geotechnical and small local wells; out of scope. |
| Emilia-Romagna hydrocarbon manifestations and fluids, DBGR mining wells | dati.gov.it searches (03:18:43); `package_show` 403 (03:24:14 to 03:24:18) | Surface seeps and historical field polygons, no kind fits; the package pages answered 403 (rate limit), so the licences could not be read. |
| SIG-GR Forages de référence | data.gouv.fr search (03:18:36) | Licence "notspecified": the cap is zero. |
| Sodir deep-sea data (dyphavsdata) | Geonorge getdata fe943f30-… (03:27:11) | Seabed-minerals data through an order form; not taken. |
| Sodir structural elements | FactMaps layer 704 (03:27:51); Geonorge f1680c76-… (03:27:22) | The same zip as faults and boundaries; named in that record's notes. |
| AGS (Alberta Geological Survey) digital data | https://ags.aer.ca/publication/dig-2023-0002 (03:32:40) | No licence found on the page. |
| Harvard Dataverse well-log, reservoir-model and geothermal searches | dataverse.harvard.edu search API (03:25:53 to 03:26:18) | No single product with a stated licence beyond the two CSULB surveys. |
| catalog.data.gov | CKAN API (03:18:05) 404; HTML search (03:31:23) | The API path answered 404; the HTML search's first results were national statistics (EIA wells by state), not a well, seismic or model product. |

## Findings

- Countries new to the catalogue: none. New publishers: six (GSNI, ISPRA, MITERD, NGU, Ontario MNR,
  CSULB authors on Harvard Dataverse).
- Redistribution: allowed 19, restricted 1 (KIGAM, CC BY-NC-ND 4.0), unknown 0.
- bbox on 14 of 20, period on 20 of 20, manifest_url on 17 of 20. The three without one: NRCan west
  coast (ftp `/pub` disallowed), NGU groundwater (order API, no file address) and NGU seismic (WMS
  only, robots 503).
- samples.yaml: 17 entries; two are sentences (Tellus magnetics over budget, KIGAM search without
  file addresses).
- Aggregators: Harvard Dataverse 2 (new). Zenodo, PANGAEA and MGDS untouched.
- Two catalogue hosts (catalogue.data.wa.gov.au, catalogosgi.isprambiente.it) answer `/robots.txt`
  with an HTML page and HTTP 200; parsed as RFC 9309 reads it, that is no rules, so allow all.
- Geonorge links NLOD 1.0 for the Sodir faults and NGU groundwater entries and NLOD 2.0 for NGU
  seismic; spdx is set only where the link is 2.0.
- The Nova Scotia licence page (novascotia.ca/opendata/licence.asp) timed out twice (03:19:49,
  03:33:35); open.canada.ca names the same licence "Open Government Licence – Nova Scotia".
