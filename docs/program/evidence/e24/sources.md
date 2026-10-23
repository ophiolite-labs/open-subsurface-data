# E24 sources: files the verifier can reach, and the sixth twenty (read 2026-10-23)

Every address below was opened from the lane host on 2026-10-23 at the UTC times given, with the
verifier's own user agent (`open-subsurface-data-verifier/<version> (+https://github.com/ophiolite-labs/open-subsurface-data)`)
unless the line says otherwise. robots.txt was read first for each host and evaluated with Python's
`urllib.robotparser` as `osd.verify._Robots` does (2xx obeyed, 4xx allows all, anything else disallows).
The listing was read once and parsed offline with `osd.verifier.listings.read_listing`; the sample
globs of `src/osd/verifier/samples.yaml` were applied as `check_files` applies them, and each picked
file was asked for its size with one HEAD request. Nothing was hashed here: `osd verify` was not run;
the `verify` workflow does that on the PR. Records state publisher facts only.

## Part A: repointed listings (charter design 2)

| Record | Before | After | robots.txt | Shape | Sample, file and size |
|---|---|---|---|---|---|
| spe/csp11 | `https://github.com/Simulation-Benchmarks/11thSPE-CSP` (repository HTML) | `https://api.github.com/repos/Simulation-Benchmarks/11thSPE-CSP/contents/geometries` | api.github.com/robots.txt 404 (allow all); raw.githubusercontent.com/robots.txt 404 | json (GitHub contents), 6 entries | `*.geo`: spe11a.geo 29,309 B, spe11b.geo 611 B (14:56, 15:08 UTC) |
| wa-demirs/petroleum-wells | CKAN `package_show` (lists services only) | `https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Industry_and_Mining/MapServer/13?f=json` | public-services.slip.wa.gov.au/robots.txt 404 (allow all) | arcgis-layer: "WA Onshore Petroleum Wells (DMIRS-025)", Feature Layer, maxRecordCount 10000; `returnCountOnly` 4,371 | `*`: the geojson export, 4,371 features, 1,978,900 B, no `exceededTransferLimit` (15:02, 15:08 UTC) |
| pgi/cbdg-boreholes | `https://api.dane.gov.pl/1.4/datasets/677/resources` (applications, WMS/WFS) | `https://cbdgmapa.pgi.gov.pl/arcgis/rest/services/cbdg_otwory/MapServer/0?f=json` | cbdgmapa.pgi.gov.pl/robots.txt 404 (allow all) | arcgis-layer: "Otwory wiertnicze CBDG", Feature Layer, maxRecordCount 1000; `returnCountOnly` 334,145 | `*`: one export of at most 1000 features; the server truncates, so the verifier keeps it as a partial export (no L2 expected) (15:04, 15:08 UTC) |

- WA: the CKAN package `wa-onshore-petroleum-wells-dmirs-025` (read about 15:01 UTC) names four resources:
  "GDB SHP TAB KML | Other spatial formats | https://dasc.dmirs.wa.gov.au/home?productAlias=WAPetroleumWells",
  "WFS | Web Feature Service | …/Industry_and_Mining_WFS/MapServer/WFSServer", "WMS | …",
  "API ArcGIS Server Map Service | …/SLIP_Public_Services/Industry_and_Mining/MapServer/13". The new
  `manifest_url` is that fourth resource.
- PGI: dane.gov.pl resource "CBDG Otwory wiertnicze – usługa WFS | https://cbdgmapa.pgi.gov.pl/arcgis/services/cbdg_otwory/MapServer/WFSServer?…"
  (read about 15:03 UTC). The ArcGIS REST directory of that service, `…/rest/services/cbdg_otwory/MapServer?f=json`,
  answered `"serviceDescription":"Otwory wiertnicze CBDG", … "copyrightText":"PIG-PIB"`, layer 0 "Otwory wiertnicze CBDG".
  Earlier on 23 Oct (E22) cbdgmapa answered an Incapsula challenge; at 15:04 it answered JSON.

### Left as they are (charter design 2: "else leave the record as it is and say so in `notes`")

| Records | Listing | robots.txt and files host | Why left |
|---|---|---|---|
| ar-energia/fractura-adjunto-iv, produccion-por-pozo, trayectorias-vaca-muerta | datos.gob.ar CKAN `package_show` | datos.gob.ar/robots.txt (200, 14:56): `User-agent: *` … `Disallow: /api/` … `Crawl-Delay: 10`. Every resource URL is on `http://datos.energia.gob.ar/dataset/<uuid>/resource/<uuid>/download/<file>.csv` (or `.zip`); datos.energia.gob.ar (168.101.26.134) timed out at 14:56 and 15:09 UTC (TLS and plain HTTP, 20–30 s) | the files' host could not be reached, so its robots.txt could not be read; and a bare file address is not a listing today (below) |
| gsmma/hydrogeological-drilling-database, sw-offshore-core-stations-2008-2011, sw-offshore-seismic-lines-2008-2011 | data.gov.tw `api/v2/rest/dataset/<id>` | data.gov.tw/robots.txt answered 404 (JSON "Page not found") to curl's agent and HTTP 500 to the verifier's agent (14:58): RFC 9309 makes 5xx a disallow. The distributions are `https://www.gsmma.gov.tw/uploads/17503844515568fWuXe2C.csv` (16799), `…/1750385221191OCgiYACA.csv` (32564), `…/1750386139229YkEB5KuO.csv` (32556); www.gsmma.gov.tw answered a Cloudflare "Attention Required!" page (403) to robots.txt and to the CSV (15:00) | blocked (OSD-D9) |
| cpc/onshore-well-locations | data.gov.tw dataset 62919 | as above; the distribution is `https://www3.cpc.com.tw/opendata_f00/探採研究所台灣陸域鑽井位置.csv`; www3.cpc.com.tw did not answer robots.txt (15:00) | unreachable |
| ak-dggs/tax-credit-well-data | `https://dggs.alaska.gov/webpubs/dggs/gmc/well_data/` | dggs.alaska.gov/robots.txt (200, 15:00): `Disallow: /webpubs/dggs/gmc/well_data/`, `Crawl-delay: 120` | the zips live under the disallowed path; no other path lists them |

Supervisor ruling (inbox `answered-e24.md`): a bare-file `manifest_url` is not sampled by today's verifier
(the body goes through `read_listing`: a CSV becomes the "text" shape, a ZIP is "format not recognised"),
so such records keep their addresses and the PR lists the file addresses under "File addresses for H1 design 8".

## Part B: listings added to existing records (charter design 3)

Each record's own `origin.url` (or the case page it names in `notes`) links the files directly, so the
page is the publisher's listing: the "html" reader returns its links and the sample picks one file.

| Record | manifest_url | robots.txt (status, rule that applies) | Shape, entries | Sample: file, size (HEAD) |
|---|---|---|---|---|
| agl/marmousi2 | https://www.agl.uh.edu/downloads/ | 404 (allow all) | directory-index ("Index of /downloads"), 16 | `vp_marmousi-ii.segy.gz` 1,766,045 B ("2004-08-18 17:44 1.7M") |
| sintef/johansen | https://www.sintef.no/projectweb/matmora/downloads/johansen/ | 200; `User-agent: *` disallows only query patterns (`*orgId=`, `*?id`, `*?page`, …) | html, 29 | `*/Sector5.zip` → /globalassets/project/matmora/johansen/sector5.zip, 3,943,155 B |
| unisim/unisim-i | https://www.unisim.cepetro.unicamp.br/benchmarks/en/unisim-i/unisim-i-d | 200; Joomla defaults (`/administrator/`, `/cache/`, …), `/benchmarks/` not disallowed | html, 48 | `https://*/UNISIM-I-D-deterministic-OPM-Flow.zip` 1,042,091 B |
| unisim/unisim-ii | …/benchmarks/en/unisim-ii/unisim-ii-d | as above | html, 44 | `*/UNISIM-II-D-BO_deterministic.ZIP` 3,540,807 B |
| unisim/unisim-iv | …/benchmarks/en/unisim-iv/unisim-iv-2019 | as above | html, 40 | `*/UNISIM-IV-2019/Nominal.rar` 4,419,578 B |
| helsinki-univ/outokumpu-deep-hole-vocs | https://zenodo.org/records/14534965 | 200; `Disallow: /api` (so not the API), `/records/` allowed | html, 45 | `*/files/*.xlsx?download=1`: Kietavainen_etal_VOC_data.xlsx 27,237 B, …supplementary_table_1.xlsx 24,059 B |
| ustc/bedrettolab-atv-logs-stress | https://zenodo.org/records/15725567 | as above | html, 45 | `*/files/stress_inversion.zip?download=1` 5,491,891 B |
| spe/csp10-model-2 | https://www.spe.org/web/csp/datasets/set02.htm | 200; disallows `/a/`, `/admin/`, `/auth/`, …, not `/web/csp/` | html, 9 | `*por_perm_case2a.zip` 19,476,344 B |
| aer/st37-list-of-wells | https://www.aer.ca/data-and-performance-reports/statistical-reports/st37 | 200, path allowed | html, 422 | `*/ST_37_Excel.zip` → static.aer.ca, 183,921,877 B (ST37_Shapefiles.zip 565,336,316 B and ST_37_GeoDB.zip 1,323,908,851 B not sampled) |
| ancap/bouguer-anomaly-map-of-uruguay | https://exploracionyproduccion.ancap.com.uy/15944/3/new-bouguer-anomaly-map-of-uruguay.html | 404 (allow all) | html, 133 | `*/bouguer_anomaly.rar` (200, no Content-Length) |
| cnloer/data-information-hub | https://www.cnloer.ca/geoscience/ | 200, path allowed | html, 92 | `*/expdwts.xlsx` (www.cnlopb.ca/wp-content/uploads/) 146,789 B |
| cnsoer/directory-of-offshore-wells | https://cnsopbdigitaldata.ca/geoviewer/dmc/public/query/0 | 404 (allow all) | html, 27 | `*/dow-2025.xlsx` 42,654 B |
| ie-pad/offshore-exploration-wells | https://data.gov.ie/dataset/exploration-wells-in-the-irish-offshore | 200, path allowed | html, 55 | `*/Exploration_Wells_Irish_Offshore.csv.zip` (atlas.marine.ie) 10,487 B |
| jardfeingi/well-data | https://jf.fo/datur/boridatur/ | 200, path allowed | html, 125 | `*FO_Offshore_Wells.zip` 3,204 B |
| kgs/oil-gas-wells | https://www.kgs.ku.edu/PRS/petroDB.html | 200, path allowed | html, 56 | `*/Ora_Archive/ks_wells.zip` 44,028,388 B |
| manitoba-petroleum/technical-well-files | https://www.manitoba.ca/iem/petroleum/gis/technical.html | 200, path allowed | html, 104 | `*/uwi_weekly.xlsx` 1,233,013 B |
| meei/historical-oil-and-gas-production | https://www.energy.gov.tt/data/historical-oil-and-gas-production-data/ | 200, path allowed | html, 106 | `*Annual-Crude-Oil-and-Condensate-Production-1908-2018-1.xlsx` 95,552 B |
| ok-occ/oil-gas-data-files | https://oklahoma.gov/occ/divisions/oil-gas/oil-gas-data.html | 200, path allowed | html, 152 | `*/esri/files/RBDMS_WELLS.zip` 45,897,943 B |
| ukogl/uk-onshore-geophysical-library | https://ukogl.org.uk/blog/archives/ | 200, path allowed | html, 43 | `*/UK-Onshore-BHT-Bottom-Hole.xlsx` 214,639 B |

Times: all Part B listings read 15:07–15:09 UTC (the two Zenodo pages again at 15:09).

### Checked and not given a listing (charter design 3 names them)

| Record(s) | What was found (23 Oct, 15:00–15:07 UTC) |
|---|---|
| terranubis/* (11) | each page's download link (`https://terranubis.com/download/<name>.zip/2`) answers 302 to a `dgbearthsciences.sharefile.com/d-…` share page (HTML application), not a file |
| equinor/volve | files behind a sign-in (`access: registration`) |
| gfz/* (4) | dataservices.gfz.de landing pages are a script application (robots `User-agent: *` `Disallow:` empty); the file directory they embed is on `https://datapub.gfz.de/download/10.5880.GFZ.…/`, and datapub.gfz.de (139.17.228.237) timed out at 15:05 UTC, so neither its robots.txt nor the listing could be read |
| ldeo-brg/logdb | mlp.ldeo.columbia.edu/robots.txt: `Disallow: /data/`, the path of its data links; per-hole Zenodo deposits are reached through the community search (`Disallow: /search`, `/api`) |
| iodp-jrso/lims-expedition-data | the JRSO page links Zenodo community searches (`Disallow: /search`, `/api`); no file links on the page |
| marum/bremen-core-repository | `access: request`; the page links only a sample spreadsheet of the repository |
| geus/havnso-reservoir-model | dataverse.geus.dk/robots.txt: `Allow: /dataset.xhtml` … `Disallow: /`, so `/api/access/datafile/…` (the files) is disallowed |
| doe-gdr/* (3) | submission pages build their file list in script; no file links in the HTML |
| ntgs/core-library | the CORE_SAMPLES_csv.zip link answered a "Maintenance message - NT.GOV.AU" HTML page (200, text/html) at 15:08 UTC |
| wvges/pipeline-oil-and-gas-well-data | the record's page links per-county LAS pages, not a file the sample could name |
