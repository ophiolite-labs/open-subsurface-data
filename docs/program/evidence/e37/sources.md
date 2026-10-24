# E37 sources: records, the tenth twenty (read 2026-10-24)

Every address below was opened from the lane host on 2026-10-24 at the UTC time given. All
requests used the verifier's user agent (`osd.verify.USER_AGENT`), and robots.txt was read first for
each host. Robots were judged as `osd.verify._Robots` judges them (2xx is obeyed, 4xx allows all, 5xx
or no answer disallows), with `urllib.robotparser`; the one `*` wildcard rule met on a used path
(geoportail.wallonie.be `Disallow: /*.metadataExport.do*`) was checked by hand and does not match the
catalogue page. Each page or listing was read once and saved, then parsed offline with
`osd.verifier.listings.read_listing`, and the `src/osd/verifier/samples.yaml` globs were matched the
way `check_files` matches them. Picked files were sized with one HEAD where a size is given. Layer
extents in a projected CRS were converted to WGS84 with pyproj on a 21 × 21 grid. Nothing was
hashed, and `osd verify` was not run from this host. Records state publisher facts only.

Slips, for the record:
- `https://www.data.qld.gov.au/api/3/action/package_search?q=petroleum%20wells` was fetched (02:24:05)
  although that robots.txt means to disallow `/api/`: its `User-agent: *` line is followed by blank
  lines, which `urllib.robotparser` reads as the end of the group, so the check passed. The answer was
  not used, and no Queensland record came from it.
- The SGU wells page was opened under two paths, `grundvatten--geologiska-data/brunnar/` (02:12:52)
  and `brunnar--geologiska-data/brunnar/` (02:13:15). The second is the record's address.
- The SGU gravity page and three of its zips (02:19:04 to 02:19:11) were opened before noticing that
  `sgu/tyngdkraft` is already a record (E33). Nothing was written for it.
- Guessed addresses that answered 404: www.gsi.ie `/en-ie/data-and-maps/Pages/default.aspx`
  (02:01:03), data.gov.ie `/organization/geological-survey-ireland` (02:01:17), NCEI
  `/products/seismic-reflection-data` and `/products/marine-geophysical-data` (02:09:16, 02:09:23),
  BGS `/datasets/gb-land-gravity-survey/` and `/datasets/gb-aeromagnetic-survey/` (02:15:51,
  02:15:52), nlog.nl `/velmod-3` and `/velmod` (02:16:45, 02:16:46). None was used.
- The first ecat.ga.gov.au CSW query (02:20:34) answered an exception (a `%` in the CQL); it was
  sent again with `%%` (02:20:49, 02:20:52).

## New records (20)

| Record | Page and manifest_url (UTC) | robots.txt | Excerpt | Sample → file, size |
|---|---|---|---|---|
| gsi/tellus-airborne-geophysics | https://www.gsi.ie/data-and-maps/geophysics/ (02:01:39); licence on https://www.gsi.ie/data-and-maps/ (02:01:39) | www.gsi.ie 403 (02:01:02); gsi.geodata.gov.ie 404 (02:01:58) | "Geophysical data and maps include data from the Tellus project (magnetic, electromagnetic, radiometric data)"; "Data that is produced directly by the Geological Survey Ireland (GSI) is free for use under the conditions of Creative Commons Attribution 4.0 International license." | `*/GSI_Tellus_RAD_MERGE_DATA_2022.zip` → 151,141,164 B (HEAD 02:01:58); html, 287 links |
| gsi/mineral-exploration-boreholes | https://www.gsi.ie/data-and-maps/minerals/ (02:01:48); layer `Minerals/IE_GSI_Mineral_Exploration_Boreholes_50K_IE26_ITM/MapServer/0` (02:02:17); stats (02:02:27); count (02:02:51) | as above | "The data shows the location of the boreholes drilled in Ireland from 1957 to 2002. They were submitted to the GSI from mineral exploration companies."; 15,055 features, DRILL_YEAR 1957 to 2002 on 14,709 | `*/IE_GSI_Mineral_Exploration_Boreholes_50K_IE26_ITM.zip` → 2,115,796 B (HEAD 02:01:59); html, 165 links |
| spw/donnees-geologiques-de-base | https://geoportail.wallonie.be/catalogue/351ee778-bbbe-422d-82fd-e7f5d5b0cfbc.html (02:04:11); metawal CSW GetRecordById (02:03:40); Atom feed (02:03:55); manifest `…/GEOLOGIE_FILEGDB_31370.zip` (HEAD 02:04:11); layer 2 and count (02:04:20, 02:04:21) | geoportail.wallonie.be 200 (02:03:05): `User-agent: *` `Disallow: /tmp` `Disallow: /*.metadataExport.do*`; metawal 404 (02:03:06); geoservices 404 (02:03:46) | "Cette donnée est disponible sous les termes de la licence ouverte CC BY 4.0. Les réutilisations sont autorisées moyennant citation de la source et mention explicite des modifications apportées à la donnée."; Sondages layer 19,976 features | `*` → the zip itself (application/zip, attachment), 11,943,843 B |
| bgr/vmod-3dgeo-eu-north-sea | BGR CSW GetRecordById 872cf5ca-… (02:05:18); bucket listing `?prefix=4bc4694c-…/Untergrundmodelle/` (02:05:43); file HEAD (02:05:34) | geoportal.bgr.de 404 (02:04:41); bucket host 404 (02:05:34) | "Datenlizenz Deutschland Namensnennung 2.0"; Quellenvermerk "BGR, GEUS, TNO (2021): Harmonized, cross-border seismic velocity model …" | sentence: Vmod_3DGEO-EU_Nordsee_EPSG_23031.zip is 14,699,680,338 B, over the 512 MiB budget; s3 listing, 6 entries |
| bgr/vmod-gpdn-entenschnabel | BGR CSW GetRecordById 09332e62-… (02:05:56 to 02:05:58); same bucket listing | as above | "Datenlizenz Deutschland Namensnennung 2.0"; "Jähne-Klingberg, F., Lutz, R., Arfai, J. (2014): Seismisches Geschwindigkeitsmodell für den „Entenschnabel“ …" | sentence: Vmod_GPDN_Entenschnabel_EPSG_32631.zip is 5,778,689,048 B (as listed) |
| bgr/geostor-reservoir-model-pilot-area-a | https://download.bgr.de/bgr/geostor/82c22d89-3187-4183-981e-5b2b9e28b6d7.html (02:19:35), from https://geostor.cdrmare.de/data (02:19:30) | download.bgr.de 404 (02:04:31); geostor.cdrmare.de 200: `Disallow: /wp-admin/` (02:19:30) | "The 3D models were created by the BGR between 2021 and 2024."; Nutzungsbedingungen `"name": "Creative Commons Namensnennung - Nicht kommerziell (CC BY-NC)"`, `"quelle": "BGR, RM_P-A, 2024"` | `*/Pilotregion_A.zip` → 6,122,020 B (HEAD 02:19:44); html, 1 link |
| mgds/chicxulub-ew0501 | https://www.marine-geo.org/doi/10.1594/IEDA/500106 (02:07:20); DataCite (02:07:04); file service uid 27886 (02:07:44) | www.marine-geo.org 200 (02:06:42): `Disallow: /tools/search/download.php` among others; api.datacite.org 404 (02:06:53) | "License: Creative Commons Attribution-NonCommercial-Share Alike 3.0 United States [CC BY-NC-SA 3.0]"; 174 files, 7,562,483,056 B | none (file service names files without addresses; downloads go through the disallowed form) |
| mgds/gulf-of-corinth-ew0108 | https://www.marine-geo.org/doi/10.1594/IEDA/500094 (02:08:13); DataCite (02:07:05); file service uid 27823 (02:08:22) | as above | same licence line; 108 files, 669,907,944 B | none (as above) |
| mgds/costa-rica-margin-ew0104 | https://www.marine-geo.org/doi/10.1594/IEDA/500092 (02:08:14); DataCite (02:07:05); file service uid 27817 (02:08:23) | as above | same licence line; 96 files, 4,387,679,412 B | none (as above) |
| pangaea/oman-drilling-cm1a-cm2b-geochemistry | https://doi.pangaea.de/10.1594/PANGAEA.942402 (02:12:19); DataCite (02:12:10) | doi.pangaea.de 200 (02:11:33): `User-agent: *` `Disallow:` | "License: Creative Commons Attribution 4.0 International (CC-BY-4.0)"; "during Phase 2 of the ICDP OmanDP (Nov. 2017-Jan. 2018)" | `*?format=zip` → 37,851 B (HEAD 02:12:26) |
| pangaea/kola-superdeep-melt-inclusions-zircon | https://doi.pangaea.de/10.1594/PANGAEA.788243 (02:12:20); DataCite (02:12:11) | as above | "License: Creative Commons Attribution 3.0 Unported (CC-BY-3.0)"; "Event(s): SG-3 * Latitude: 69.395917 * Longitude: 30.610367" | `*?format=zip` → 5,347 B (HEAD 02:12:26) |
| pangaea/andrill-and-2a-downhole-log-lithostratigraphy | https://doi.pangaea.de/10.1594/PANGAEA.834632 (02:12:20); DataCite (02:12:12) | as above | "License: Creative Commons Attribution 3.0 Unported (CC-BY-3.0)"; "Date/Time Start: 2007-10-10T12:00:00 * Date/Time End: 2007-11-30T12:00:00" | `*?format=zip` → 1,276,403 B (HEAD 02:12:27); html, 49 links |
| sgu/brunnar | https://www.sgu.se/produkter-och-tjanster/geologiska-data/brunnar--geologiska-data/brunnar/ (02:13:15); licence page (02:13:29); OGC collections (02:13:37) | www.sgu.se 200 (02:12:52): `Disallow: /XFormFiles/`, `/sok/` …; resource.sgu.se 404 (02:13:28); api.sgu.se 404 (02:13:37) | "uppgifter som brunnsborrare sedan 1976 enligt lag måste skicka in till SGU"; "Öppna data från SGU har licensen Creative Commons Noll (CC0)" | `*/oppnadata/brunnar/brunnar.zip` → 232,973,938 B (HEAD 02:13:28) |
| sgu/magnetfalt-detaljerad | https://www.sgu.se/produkter-och-tjanster/geologiska-data/geofysik--geologiska-data/magnetfalt/ (02:13:17); OGC collections (02:13:38); flight areas (02:13:48) | as above | "innehåller uppmätta variationer i det magnetiska totalfältet före och efter subtraktion av det geomagnetiska referensfältet (DGRF 1965.0)"; 450 flight areas, flightyear 1960 to 2023 | `*/geofysik-flyg-magnetfalt-detaljerad.zip` → 668,787 B (HEAD 02:13:29) |
| nsta/offshore-wellbores-top-holes | arcgis.com item 33ddab463c2f436fafd2a8fbbe406348 (02:14:30); layer 0 (02:15:26); count (02:15:26); SPUDDATE stats (02:15:39); licence PDF (02:15:07) | www.arcgis.com 200: `User-agent: *` with no rules (02:14:17); services-eu1.arcgis.com 403 (02:15:18); www.nstauthority.co.uk 200: `Disallow: /app_data/` … `/data/` … (02:14:43) | "Oil and gas well header information taken directly from the NSTA's Well Operations Notification System (WONS)."; licence: "You are free to: copy, publish, distribute and transmit the Information; adapt the Information; exploit the Information non-commercially." | arcgis-layer, all 13,385 |
| nsta/production-data-by-field | arcgis.com item 5591b61ebc18422380c605ffec1a658b (02:14:31); layer 0 (02:15:27); count and URL sample (02:15:28, 02:15:40) | as above | "This requirement has been applied to all UKCS fields that have ceased production since January 2018."; item licenseInfo "NSTA Open User Licence" | arcgis-layer, all 40 |
| ga/stratdat-biostratigraphy | eCat 10ac40b7-… ISO XML (02:21:15); WFS capabilities (02:21:38); pid HEAD (02:30:42) | ecat.ga.gov.au 404 (02:20:26); services.ga.gov.au 403 (02:21:38); pid.geoscience.gov.au 404 (02:30:42) | "Geoscience Australia’s biostratigraphic database (STRADAT) provides information about the biozonation of sedimentary rocks that were intersected by offshore petroleum wells."; "Creative Commons Attribution 4.0 International Licence"; resfacs:Biostratigraphy WGS84BoundingBox 110 -45 155 -5 | none (WFS and portal) |
| ga/resfacs-porosity-permeability | eCat 7bb7352b-… ISO XML (02:21:13); same WFS capabilities; pid HEAD (02:30:45) | as above | "depth-based information regarding porosity and permeability measured or interpreted from core, sidewall core and well-log analysis"; "Creative Commons Attribution 4.0 International Licence" | none (WFS and portal) |
| ga/l072-bmr12-cockroach-velocity-survey | eCat deef3eba-… ISO XML (02:22:55); pid HEAD (02:30:47) | d28rz98at9flks.cloudfront.net 200: `User-agent: *` `Disallow: /` (02:23:10) | "The time/depth values obtained in the velocity survey were in good agreement with those obtained by integration of the sonic log."; temporal extent 1964-09-13 to 1964-11-19; bbox 137.00 / 137.50 / -22.75 / -22.25 | none (package host disallows all) |
| ga/l016-rough-range-1-velocity-survey | eCat de4ecded-… ISO XML (02:22:57); pid HEAD (02:30:50) | as above | "Geophone depths in the welI ranged from 2,000 feet to 14,000 feet"; temporal extent 1955-02-21 to 1955-02-22; bbox 114.0 / 114.5 / -22.75 / -22.0 | none (as above) |

bbox values are only extents the publisher states: the GSI layer `extent` (EPSG:2157, converted), the
metawal georss polygon, the BGR CSW extents, the DataCite geoLocationBox of each MGDS DOI, PANGAEA's
bound coverage for Oman, the SGU OGC collection extent for the magnetic data, the NSTA layer extents
(EPSG:4258 and ED50 as stated), the GA WFS WGS84BoundingBox and the GA eCat EX_GeographicBoundingBox.
No bbox where the publisher states none (Tellus, SGU wells, whose collection box reaches -3° to 45° E
and 5° to 83° N), where it states only one point (Kola SG-3, AND-2A), or where the stated extent
contradicts the stated area (GEOSTOR pilot area A: "6.833, 6.904, 54.072, 54.558" against
"~1300 km2").

## Refused or not recorded (reasons)

| Candidate | Address (UTC) | Reason |
|---|---|---|
| SONRIS, Michigan EGLE, Illinois ISGS, Kentucky KGS, Montana BOGC, Arkansas AOGC, Mississippi OGB, Indiana IGWS | not opened | On the E22 refused list; not retried. |
| Tasmania MRT, Philippines DOE, Czech ČGS | not opened | On the E24 refused list; ČGS is already `cgs/vrtna-prozkoumanost`. Not retried. |
| Orkustofnun, uos.is, ÍSOR (Iceland) | not opened | On the E25 refused list; not retried. |
| BRGM, GSJ gbank | not opened | On the E20, E22 and E24 refused lists; not retried. |
| Taiwan CGS | not opened | Now GSMMA, already a publisher. |
| Tomakomai | not opened | Charter: stays out. |
| NOAA NCEI marine seismic reflection (G00944) and GlobSed (0305030) | ISO XML (02:10:14, 02:10:15) | The metadata carries distribution and use liability disclaimers and a "Cite as" line, no licence (E33 Missouri precedent: a disclaimer is not a licence). The SCAR SDLS CD-ROMs are sold. |
| UTIG Academic Seismic Portal | ig.utexas.edu/sdc/ (02:08:33) | robots 200 (`Disallow:` empty), page timed out. |
| ICDP and GFZ data services | www.icdp-online.org, data.icdp-online.org, dataservices.gfz-potsdam.de robots (02:10:46 to 02:11:26) | robots.txt gave no answer: disallow. |
| BGR Deutscher Bohrungsnachweis (GBL), BGR processed marine seismic, BGR Speicherpotenziale Tiefenlagekarten, BGR GPDN KW-Modell depth maps | BGR CSW (02:05:57 to 02:06:19); KW-Modell page (02:23:47) | Licence is only "Allgemeine Geschäftsbedingungen, siehe https://www.bgr.bund.de/AGB"; www.bgr.bund.de answers 400 to the verifier for robots.txt (02:04:41) and for `/AGB_en` (02:06:05), so the terms cannot be read. |
| BGS UK3D | https://www.bgs.ac.uk/datasets/uk3d/ (02:15:50); licensing page (02:16:35) | The page says "Availability: Open" and names no licence; the licensing page says open data is "usually" under the OGL. The product's licence is not stated. |
| GSI geotechnical boreholes | https://www.gsi.ie/data-and-maps/geotechnical/ (02:01:40); layer (02:02:17) | Shallow engineering holes; out of scope. |
| TNO VELMOD-3.1 | https://www.nlog.nl/velmod-31 (02:16:46); https://www.nlog.nl/disclaimer (02:18:48) | The page names no licence; the NLOG disclaimer is a use and liability statement, not a licence. |
| NSTA NDR 3D seismic surveys layer | arcgis.com item 11553601620a49dc8a94442b5b325f46 (02:14:31) | "Seismic Data from the previous (V1) National Data Repository": survey outlines of the product `nsta/ndr` already lists, not a different product. |
| SGU ground seismics, SGU geoenergy | seismik page (02:13:18); geoenergi page (02:22:43) | Near-surface refraction (depth to bedrock, groundwater) and rock thermal conductivity; out of scope. |
| USGS ScienceBase items | ScienceBase search (02:20:06) | 403 to the verifier's agent. |
| GA via data.gov.au, GEUS Dataverse search | data.gov.au CKAN API (02:20:16); dataverse.geus.dk search API (02:22:15) | robots.txt disallows those API paths; the GA products were reached through eCat instead. |
| GA RESFACS hydrocarbon shows | eCat 591a4b4c-… (02:23:53) | Not needed for the count; no kind fits shows data. |
| BGR GEOSTOR pilot area B | https://download.bgr.de/bgr/geostor/8469e527-1e0b-4cfa-a5d4-2f1c79ca0be1.html (02:19:45) | Same product as pilot area A; named in that record's notes. |

## Findings

- Countries new to the catalogue: MX, GR, CR, OM, RU, AQ (six). IE and BE had records before.
- Redistribution: allowed 14, restricted 6 (MGDS ×3 CC BY-NC-SA 3.0 US, NSTA ×2 non-commercial
  user agreement, BGR GEOSTOR CC BY-NC), unknown 0.
- manifest_url on 13 of 20. The seven without one: MGDS ×3 (form downloads, robots), GA STRATDAT
  and RESFACS (WFS only), and GA L072 and L016 (package host `Disallow: /`).
- The two BGR velocity models are one zip each, 14.7 GB and 5.8 GB, so their samples are sentences;
  the bucket listing is read, nothing is hashed.
- Aggregators: MGDS 3 and PANGAEA 3, at the cap.
- ArcGIS Online items carry the publisher's licence name (`licenseInfo`), which led to the NSTA user
  agreement. The NSTA open-data hub answered 401 and data.nstauthority.co.uk did not resolve.
- GA eCat ISO records state CC BY 4.0 even where the data.gov.au copy does not (as E33 found for L200);
  GA's file host (CloudFront) disallows all robots, so GA packages cannot be sampled.
- `urllib.robotparser` ends a group at a blank line, so a robots.txt with blank lines between
  `User-agent: *` and its rules (data.qld.gov.au) reads as allow-all. `osd.verify._Robots` parses with
  `urllib.robotparser` too, so it shares this reading; worth a test and an owner decision.
