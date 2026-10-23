# E30 sources: listings for the datasets people can download (read 2026-10-23)

Every address below was opened from the lane host (ophiolite-epic-01) on 2026-10-23 at the UTC times
given, with the verifier's user agent (`osd.verify.USER_AGENT`). robots.txt was read first for each
host and evaluated with Python's `urllib.robotparser` as `osd.verify._Robots` does (2xx obeyed, 4xx
allows all, 5xx or no answer disallows). Each listing was read once, saved, and parsed offline with
`osd.verifier.listings.read_listing` (or `names_a_file` on its headers); the globs of
`src/osd/verifier/samples.yaml` were applied as `check_files` applies them, and the picked file was
asked for its size with one HEAD. Nothing was hashed here; `osd verify` was not run from this host.
Records state publisher facts only.

Slips, for the record: the CKAN API `https://data.ca.gov/api/3/action/package_show?id=wellstar-oil-and-gas-wells`
(17:05:48) and a HEAD of `https://ecmc.state.co.us/documents/data/downloads/gis/WELLS_SHP.ZIP`
(17:05:34) were sent before the lane's script refused robots-disallowed addresses; neither is used.
The ViDEPI SEG-Y page was read twice in the same second (17:12:34); two stray 404s went to
`ecat.ga.gov.au/geonetwork/srv/api/records/{x,72891}` (17:07:42, 17:08:03).

## Part A: records given a `manifest_url` (charter design 2)

| Record | manifest_url | robots.txt (status: deciding line) | Shape, entries | Sample → file, size (UTC) |
|---|---|---|---|---|
| nysdec/oil-and-gas-annual-production | https://data.ny.gov/api/views/mxea-iw3u.json | 200: `User-agent: *` `Crawl-delay: 1`; disallows `/api/odata/`, `/api/collocate*`, browse/catalog queries; `/api/views/` allowed | socrata, 1 (rows updated 2025-07-30) | `*` → `/api/views/mxea-iw3u/rows.csv?accessType=DOWNLOAD` (generated, size not stated) (17:05:12) |
| nysdec/oil-gas-and-other-regulated-wells | https://data.ny.gov/api/views/szye-wmt3.json | as above | socrata, 1 (rows updated 2026-10-23) | `*` → `…/szye-wmt3/rows.csv?accessType=DOWNLOAD` (17:05:13) |
| calgem/wellstar-oil-and-gas-wells | https://data.ca.gov/dataset/wellstar-oil-and-gas-wells (302 to `/@california-department-of-conservation/…`) | data.ca.gov 200: `Disallow: /api/` … `Allow: /` (the page is allowed, the CKAN API is not); gis-cnra.hub.arcgis.com 200: `Crawl-delay: 60`, disallows `/sites/`, `/admin/`, … ; hub.arcgis.com 200, same pattern | html, the entry page's links (CSV, SHP, GeoJSON, KML resources) | `*/ef53080fdf894761858dd1728610b9a0/csv?layers=0` → 302 to `https://hub.arcgis.com/api/v3/datasets/ef53080fdf894761858dd1728610b9a0_0/downloads/data?format=csv&spatialRefId=3857&where=1%3D1`, `text/csv`, `Content-Disposition: attachment; filename="WellSTAR%3A_Oil_and_Gas_Wells.csv"`, Last-Modified 2 Jul 2026, no length (17:06:01, 17:06:07) |
| tno/bro-geological-boreholes | https://service.pdok.nl/tno/bro-geologisch-booronderzoek/atom/downloads/brobhrgvolledigeset.gpkg | service.pdok.nl 200: `User-agent: *` `Disallow:` (empty) | file (`application/geopackage+sqlite3`) | `*` → 158,920,704 B, Last-Modified 25 Aug 2026 (17:11:03) |
| bgs/single-onshore-borehole-index | https://www.bgs.ac.uk/download/single-onshore-borehole-index-sobi-dataset/?wpdmdl=125849 | www.bgs.ac.uk 200: `User-agent: *` `Disallow:` (empty, Yoast block) | file (`application/zip`, `Content-Disposition: attachment;filename="sobi-borehole.zip"`) | `*` → page states 75.58 MB, created and updated 16/10/2026; no Content-Length (17:11:29) |
| swisstopo/deep-wells | https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.geologie-bohrungen_tiefer_500/items/geologie-bohrungen_tiefer_500 | data.geo.admin.ch 404 (allow all); opendata.swiss answers its robots.txt with an HTML page (200, no rules) | json (E02 walk over the STAC item: 5 links, 3 asset hrefs) | `*_2056.gpkg` → `geologie-bohrungen_tiefer_500_2056.gpkg` 237,568 B, Last-Modified 2 Sep 2026 (17:12:03, 17:12:09) |
| swisstopo/reflection-seismic | https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.geologie-reflexionsseismik/items/geologie-reflexionsseismik | as above | json, 7 (2 asset hrefs) | `*_2056.gpkg` → `geologie-reflexionsseismik_2056.gpkg` 19,189,760 B, Last-Modified 7 Oct 2026 (17:12:03, 17:12:09) |
| mase-unmig/videpi-seismic | https://www.videpi.com/videpi/cessati/sgy.asp | www.videpi.com 404 (allow all) | html, 342 (171 SEG-Y lines, each beside its `fascicolo.asp` report link) | `*/sgy/1.sgy` → 82,208,512 B `application/SEG-Y` (17:12:34, 17:12:50) |
| mase-unmig/videpi-wells | https://www.videpi.com/videpi/cessati/las.asp | as above | html, 96 (44 LAS, 4 LIS) | `*/las/55.las` → 577,512 B `application/LAS` (17:12:50, 17:12:54) |
| inp-mz/actividade-de-pesquisa-e-producao | https://services3.arcgis.com/GwpN7CU0VUHlIXMI/arcgis/rest/services/Actividades_de_Pesquisa/FeatureServer/0?f=json | services3.arcgis.com 403 (4xx: allow all) | arcgis-layer: "Poços", Feature Layer, maxRecordCount 1000, capabilities `Query`, last edit 2026-02-10 | `*` → the geojson export, 255 features, 98,427 B, no `exceededTransferLimit` (17:14:59, 17:15:04) |
| anpg/historico-de-producao | https://www.anpg.co.ao/api/production-historical | www.anpg.co.ao 200: `User-agent: *` `Allow: /` | file by `file: true` (the response is the series itself, `application/json`; the JSON walk finds no file names in it) | 29,783 B, `{"data":[{"year":1955,"oil_bopd":"5.00","source":"ANPG - Direcção de Produção",…` (17:15:12) |

Excerpts (verbatim, from the pages opened):
- calgem: the entry page links "https://gis-cnra.hub.arcgis.com/api/download/v1/items/ef53080fdf894761858dd1728610b9a0/csv?layers=0" under the resource "CSV".
- tno: PDOK ATOM dataset feed `…/atom/bro_geologisch_booronderzoek_bhrg.xml`: `<link href="https://service.pdok.nl/tno/bro-geologisch-booronderzoek/atom/downloads/brobhrgvolledigeset.gpkg" rel="alternate" type="application/geopackage+sqlite3" hreflang="nl" length="158920704" title="BRO - Geologisch booronderzoek (BHR-G) (EPSG:4258) Geopackage - brobhrgvolledigeset.gpkg">`, `<updated>2026-08-25T00:00:00Z`.
- bgs: "Single Onshore Borehole Index (SOBI) dataset BGS download Version Download File Size 75.58 MB File Count Create Date 16/10/2026 Last Updated 16/10/2026"; the button's `data-downloadurl="https://www.bgs.ac.uk/download/single-onshore-borehole-index-sobi-dataset/?wpdmdl=125849&refresh=…"` (the `refresh` token dropped; the bare `wpdmdl` address answers the file).
- swisstopo: opendata.swiss names "https://data.geo.admin.ch/browser/index.html#/collections/ch.swisstopo.geologie-bohrungen_tiefer_500/items/geologie-bohrungen_tiefer_500" as the download; the `manifest_url` is the STAC API address of the same item.
- inp-mz: the FeatureServer lists layers 0 "Poços", 1 "Sismica 2D", 2 "Sismica 3D", 3–9 licensing rounds, 10 "Bacia Sedimentar".

## Part B: candidates not given a listing (one reason each)

| Record(s) | What was found (UTC) | Reason |
|---|---|---|
| ecmc/oil-and-gas-active-and-plugged-wells | data.colorado.gov view hvzn-ur6t (17:05:32) is an `href` view with 0 columns, `accessPoints: {"download zip file": "http://cogcc.state.co.us/documents/data/downloads/gis/WELLS_SHP.ZIP"}`; ecmc.state.co.us/robots.txt (200, 17:05:33): `User-agent: *` … `Disallow: /app/` `Disallow: /documents/` | robots disallows (the file is under `/documents/`) |
| nzpam/parihaka | survey page (17:06:25): "Login to download" (RealMe) beside each file: TXT Field Navigation 17.64 MB, ZIP 4.76 GB, SGY Final Stack 64.71 GB, SGY Raw Stack 64.71 GB; `/api/` disallowed | no anonymous listing published; the copy in the `open.source.geoscience` S3 bucket names no publisher, so it is not NZP&M's listing |
| ga/brumbys-1-otway, ga/l200-southern-carnarvon-seismic | eCat record XML (17:07:29) names `https://d28rz98at9flks.cloudfront.net/146045/146045_00_0.XLSX`; that host's robots.txt (200, 17:07:41): `User-agent: *` `Disallow: /`; pid.geoscience.gov.au/dataset/ga/72891 redirects to the eCat script application; data.gov.au/robots.txt (200, 17:08:17): `Disallow: /` | robots disallows (GA's file host and data.gov.au) |
| geosphere-at/aerogeophysics-northern-lower-austria, molasse-basin-subsurface-model | tethys.at pages are a Vite application; its API `https://data.tethys.at/api/dataset/212` answered 503 "No server is available to handle this request" (17:08:40, again 17:16:18) and the OAI endpoint 503 (17:08:50); DataCite (17:16:27) states no `contentUrl` | host refused (503 today); retry in the next records lane: `data.tethys.at/api/dataset/<id>` is JSON with `files` |
| gfz/cosc-1-zero-offset-vsp, dekorp-9n-reprocessed, ketzin-brine-injection, ktb-data | datapub.gfz.de robots.txt timed out (17:08:55, 17:20:15; as for E24 at 15:05); DataCite records (17:09:32–34) state no `contentUrl`; data.icdp-online.org (KTB) timed out (17:09:39) | host unreachable |
| gsv/petroleum-wells | the entry (17:10:17) lists DWG, DXF, GDB, SHP, MIF, TAB, Extended TAB "PETWELLSVPUBLIC", each going to the Vicmap DataShare order form; no WFS is named (a guessed GeoServer layer answered 400, 17:10:33) | no listing published (order form) |
| lbeg/kw-fis, lbeg/tunb-velo-2-0-ni, lbeg/tunb3d-ni | pages (17:12:19–20) link the NIBIS map server, the DOI report, a citation PDF and two illustration PDFs; models "auf Anfrage" | no listing published (map viewer; models on request) |
| tx-rrc/full-wellbore, tx-rrc/production-data-query-dump | the data sets page (17:13:00; robots.txt empty, allow) links `https://mft.rrc.texas.gov/link/b070ce28-…` (Full Wellbore) and `…/link/1f5ddb8d-…` (PDQ dump); mft.rrc.texas.gov robots.txt timed out (17:13:10, 17:19:45) | host unreachable (robots unreadable, treated as disallow) |
| usgs/namss | the archive page and Web Services page (17:13:47, 17:13:54) offer a map application and a WMS only | shape not read (WMS; finding F3) |
| wogcc/wyde-wells | `/api/GISConfig` (17:14:10) is the viewer's configuration: GeoServer layers ("Wells - Oil Vertical", …), no file | no listing published (viewer layers) |
| nrcan/canadian-airborne-geophysical-data-base | geophysical-data.canada.ca/robots.txt (200, 17:14:25): `User-agent: *` `Disallow: /` | robots disallows |
| ntgs/core-library | data.nt.gov.au entry (17:14:38) links `CORE_SAMPLES_{csv,shp,tab,kml}.zip` on geoscience.nt.gov.au; that host answers every path, robots.txt included, with "Maintenance message - NT.GOV.AU" (200 text/html, 17:14:31), as for E24 at 15:08 | host refused (maintenance page in place of files; a listing would hash the page) |
| igme/sigeof | the application page (17:14:45) is a search form behind a licence confirmation | no listing published (finding F5 on its byte-order mark) |
| gy-mnr/well-activities | the page (17:15:20) and the Data Centre (17:21:15) link no file | no listing published (HTML table) |
| co2datashare/* (5) | co2datashare.org answered today (robots 17:15:27, `Disallow: /api/`); the Smeaheia dataset page (17:15:31) links resource pages; a resource page (17:15:38) downloads by `<form method="POST">` with a CSRF token and a `license_accepted` checkbox, no file address | no listing published (download is a POST behind licence acceptance; the other four datasets use the same portal form) |
| geus/formation-tops-denmark, geus/havnso-reservoir-model | dataverse.geus.dk/robots.txt (200, 17:15:50): `Allow: /dataset.xhtml` … `Disallow: /`, so `/api/` (listing and files) is disallowed | robots disallows |
| wvges/pipeline-oil-and-gas-well-data | `http://downloads.wvgs.wvnet.edu/welllogs/` and `/BatchInfo/` (17:15:55, 17:16:02; robots 404) list one directory per county; a county directory (`/welllogs/barbour/`, 2,775 entries) lists the TIFF logs | E24's reason stands (per-county listings; finding F4) |
| terranubis/* (10), doe-gdr/* (3), ldeo-brg/logdb, iodp-jrso/lims-expedition-data | not reopened: E24's reasons are permanent (ShareFile share pages; script-built file lists; robots `Disallow: /data/`; Zenodo search and API disallowed) | as E24 |
| geus/deep-subsurface-data, nm-ocd, odnr, pa-dep, sa-dem, seg/open-data-wiki | L0 dead or blocked (charter design 4) | not touched |

## Part C: findings (shapes the verifier does not read)

- F1. OGC API Features. `https://ogcapi.bgs.ac.uk/collections/onshoreboreholeindex/items?f=json&limit=1` (17:16:39)
  answers a GeoJSON FeatureCollection (`{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"reference":"SD20NE1","name":"FORMBY 4",…,"scan_url":"https://api.bgs.ac.uk/sobi-…`);
  E02's JSON walk reads its paging and alternate-format `links` (6 entries: `?f=jsonld`, `?f=html`, `?f=csv`, `offset=1`, …) as files.
- F2. INSPIRE ATOM feeds. `https://service.pdok.nl/tno/bro-geologisch-booronderzoek/atom/bro_geologisch_booronderzoek_bhrg.xml`
  names its file in `<link rel="alternate" type="application/geopackage+sqlite3" length="158920704" href="…gpkg">`; the HTML reader collects `<a>` only, so the feed reads as 0 entries (the record uses the file itself).
- F3. WMS GetCapabilities. `https://walrus.wr.usgs.gov/namss/wms?request=GetCapabilities&service=WMS&version=1.1.1` (named on the NAMSS Web Services page): a map service, no files.
- F4. Nested directory indexes. `http://downloads.wvgs.wvnet.edu/welllogs/` lists `barbour/`, `boone/`, … ; the files are one level down
  (`/welllogs/barbour/4700100002g.tif`). The reader reads one level; the page is not titled "Index of", so it reads as `html`.
- F5. Byte-order mark again (E25 found it on the Alabama OGB page): `http://info.igme.es/sigeof/` starts with U+FEFF and reads as `text` (381 lines of markup as URLs).
- F6. Socrata link views. `https://data.colorado.gov/api/views/hvzn-ur6t.json` is `"viewType":"href"` with no columns; the Socrata reader would still name `/api/views/hvzn-ur6t/rows.csv`, which a link view does not serve.
- F7. GeoNetwork record XML. `https://ecat.ga.gov.au/geonetwork/srv/api/records/<uuid>` answers ISO 19115-3 XML whose
  `<cit:linkage>` holds the file address; it reads as `html` with 0 entries (moot for GA today: its file host disallows all).
- F8. ArcGIS Hub downloads (CalGEM) come through a 302 to `hub.arcgis.com/api/v3/…/downloads/data`, a generated export with no length;
  gis-cnra.hub.arcgis.com states `Crawl-delay: 60`.
- F9. Record fact for a later lane: nzpam/parihaka's files need a RealMe login today ("Login to download"), though the record says `access: anonymous`.

## Retries for the next records lane (supervisor, 23 Oct)

Eleven listings accepted. Retry: `data.tethys.at` (503 to `/api/dataset/<id>` and the OAI endpoint;
geosphere-at x2) and `datapub.gfz.de` (robots.txt timed out; gfz x4).
