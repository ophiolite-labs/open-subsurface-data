# E25 sources: the seventh twenty, and the bare files (read 2026-10-23)

Every address below was opened from the lane host (ophiolite-epic-01) on 2026-10-23 at the UTC times
given, once, with the verifier's user agent (`open-subsurface-data-verifier/<version> (+https://github.com/ophiolite-labs/open-subsurface-data)`)
unless the line says otherwise. robots.txt was read first for each host and evaluated with Python's
`urllib.robotparser` (2xx obeyed, 4xx allows all, 5xx or no answer disallows, as `osd.verify._Robots`).
Listings were saved once and parsed offline with `osd.verifier.listings.read_listing`; the globs of
`src/osd/verifier/samples.yaml` were applied as `check_files` applies them. Nothing was hashed here;
`osd verify` was not run from this host. Records state publisher facts only.

## Part A: the seven bare-file records (charter design 2)

What main showed: verify run 39980489177 (main 5cbe7af + E24, after H1), every one of the seven at L1:

| Record | Main's run (files-checksummed) | What changed |
|---|---|---|
| ar-energia/trayectorias-vaca-muerta | skip: robots.txt disallows the listing https://datos.gob.ar/api/3/action/package_show?id=trayectoria-de-pozos | `manifest_url` → https://datos.gob.ar/dataset/trayectoria-de-pozos; sample `*/trayectorias-de-pozo-vaca-muerta.csv` |
| ar-energia/fractura-adjunto-iv | skip: robots.txt disallows the listing …package_show?id=datos-de-fractura-de-pozos-adjunto-iv | `manifest_url` → https://datos.gob.ar/dataset/datos-de-fractura-de-pozos-adjunto-iv; sample `*/datos-de-fractura-de-pozos-de-hidrocarburos-adjunto-iv-*.csv` |
| ar-energia/produccion-por-pozo | skip: robots.txt disallows the listing …package_show?id=produccion-de-petroleo-y-gas-por-pozo | `manifest_url` → https://datos.gob.ar/dataset/produccion-de-petroleo-y-gas-por-pozo; sample `*/listado-de-pozos-cargados-por-empresas-operadoras.csv` |
| gsmma/hydrogeological-drilling-database | skip: robots.txt unreadable (HTTP 500), treated as disallow: the listing https://data.gov.tw/api/v2/rest/dataset/16799 | `manifest_url` → https://www.gsmma.gov.tw/uploads/17503844515568fWuXe2C.csv, `file: true` |
| gsmma/sw-offshore-core-stations-2008-2011 | same, dataset 32564 | `manifest_url` → https://www.gsmma.gov.tw/uploads/1750385221191OCgiYACA.csv, `file: true` |
| gsmma/sw-offshore-seismic-lines-2008-2011 | same, dataset 32556 | `manifest_url` → https://www.gsmma.gov.tw/uploads/1750386139229YkEB5KuO.csv, `file: true` |
| cpc/onshore-well-locations | same, dataset 62919 | `manifest_url` → https://www3.cpc.com.tw/opendata_f00/%E6%8E%A2%E6%8E%A1%E7%A0%94%E7%A9%B6%E6%89%80%E5%8F%B0%E7%81%A3%E9%99%B8%E5%9F%9F%E9%91%BD%E4%BA%95%E4%BD%8D%E7%BD%AE.csv (探採研究所台灣陸域鑽井位置.csv), `file: true` |

None of the seven reached its file on main: the addresses were the catalogue APIs, which robots.txt
closes. The charter's premise ("a bare-file address") was E24's proposal, not the records' state, so
this lane made the change E24's PR body ("File addresses for H1 design 8") proposed:

- Argentina. `datos.gob.ar/robots.txt` (E24, 14:56): `User-agent: *` … `Disallow: /api/` … `Crawl-Delay: 10`;
  the dataset pages are allowed. Each page was read once (16:00 UTC, HTTP 200 `text/html; charset=utf-8`)
  and parses as an `html` listing: trayectoria-de-pozos 46 entries, datos-de-fractura-de-pozos-adjunto-iv
  47, produccion-de-petroleo-y-gas-por-pozo 201; each glob above picks exactly one entry, on
  `http://datos.energia.gob.ar/dataset/<uuid>/resource/<uuid>/download/<file>.csv`. A dataset page
  lists the publisher's current links, so it is a better listing than one bare CSV whose resource id
  can change; no `file:` flag is needed. `datos.energia.gob.ar` timed out (robots.txt and the
  trajectory CSV, 25 s, 15:59 UTC), as at 14:56 and 15:09 for E24; the verifier will say so.
- Taiwan. `data.gov.tw/robots.txt` answered HTTP 500 (Nuxt error page) to the verifier's agent at 16:01
  UTC, so neither the API nor the dataset page can be the listing. The API (`api/v2/rest/dataset/<id>`,
  read once 16:01) names one distribution each: 16799 `…/uploads/17503844515568fWuXe2C.csv` (CSV),
  32564 `…/1750385221191OCgiYACA.csv`, 32556 `…/1750386139229YkEB5KuO.csv`, 62919
  `https://www3.cpc.com.tw/opendata_f00/探採研究所台灣陸域鑽井位置.csv`. The `manifest_url` is now that
  file, with `{file: true, sample: ["*"]}` because its headers could not be read here:
  `www.gsmma.gov.tw` answered `403 text/html` from `cloudflare` to robots.txt and to the CSV (15:59 UTC);
  `www3.cpc.com.tw` timed out (robots.txt and the CSV, 16:00 UTC). A 403 robots.txt allows all
  (4xx), so the verifier will fetch the CSV and report its status.

## Part B: geus/deep-subsurface-data (supervisor note; issue #17)

Main's run 39980489177 shows the origin dead, HTTP 404 at
https://eng.geus.dk/products-services-facilities/data-and-maps/subsurface-data-denmark. At 16:05 UTC:
`eng.geus.dk/robots.txt`, `eng.geus.dk/`, `www.geus.dk/`, `www.geus.dk/robots.txt` and the Danish page
`www.geus.dk/produkter-ydelser-og-faciliteter/data-og-kort/undergrundsdata-danmark` all answered
`404 text/html; charset=us-ascii`, 315 bytes, `Server: Microsoft-HTTPAPI/2.0` (the IIS "Not Found"
returned when no site is bound, not a page of GEUS's); `data.geus.dk/robots.txt` 200 and the map portal
`https://data.geus.dk/geusmap/?mapname=oil_and_gas&lang=en` 200. GEUS publishes no new address for the
page: its whole web host is down, the dataset has not moved. Left as it is (the record's `notes`
already names the portal and the 404).

## Part C: twenty new records (charter design 3 and 4)

Opened 16:02–16:16 UTC by four research passes (same agent, same rules); each listing saved and parsed
with `read_listing`; sizes from a listing, a HEAD or one GET of the picked file. "Shape" is
`read_listing`'s (or `file` for a bare-file address).

| Record | Page opened (UTC) | robots.txt (status: deciding line) | manifest_url, shape | Sample → file, size, type |
|---|---|---|---|---|
| nzpam/petroleum-wells | nzpam.govt.nz/maps-geoscience/using-web-services 16:05 | gis.nzpam.govt.nz 404: allow all | `…/GeodataCatalogue_Layers/MapServer/4?f=json`, arcgis-layer, 1 entry | `*` → geojson export, 1,302 features (count query), 977,308 B, application/geo+json (16:06) |
| nzpam/seismic-surveys-2d | same | same | `…/MapServer/6?f=json`, arcgis-layer, 1 | `*` → 990 features, 9,674,966 B (16:06) |
| sk-mer/drill-core | gisappl.saskatchewan.ca/…/Drill_Core.html 16:07 | gis.saskatchewan.ca 404 | `…/Economy/Petroleum/MapServer/2?f=json`, arcgis-layer, 1 | `*` → 2000 of 104,754 features, 1,388,053 B (partial export; no L2 expected) |
| gsnsw/drillholes-petroleum | data.nsw.gov.au/data/dataset/nsw-drillholes-petroleum 16:10 | public-gs.geoscience.nsw.gov.au 404 | WFS GetFeature `drilling:drilling_drillholes_petroleum`, file (`file: true`: application/json, `Content-Disposition: inline; filename=drilling_drillholes_petroleum.json`) | 1,221 features, 1,624,390 B |
| gsv/faults-latrobe-group-gippsland | discover.data.vic.gov.au/dataset/interpreted-faults-latrobe-group-gippsland-basin 16:10 | opendata.maps.vic.gov.au 404 | WFS GetFeature `open-data-platform:faults_latrobe_gp`, file (`file: true`: application/json inline) | 47 features, 15,043 B |
| petrocom-gh/fields-production-data | petrocom.gov.gh/production-volume/ 16:04 | 200: `User-agent: *` `Disallow: /wp-admin/` | `/download/2025-fields-production-data/?wpdmdl=24377`, file (xlsx content type) | 597,225 B, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet |
| ppepdr/national-data-repository | ppepdr.net/subscribe 16:06 | 404 | none (membership and login) | — |
| egt/gea-geological-database | gis.egt.ee/geoportaal/teenused 16:05 | gea-api.egt.ee 422 (4xx: allow); maps.egt.ee 503 (disallow) | none: `/puurauk` and `/manus` are JSON record arrays, `read_listing` finds 0 entries | — |
| lgt/geologiniai-tyrimai | data.gov.lt/datasets/1325/ 16:12 | 200: `User-agent: *` `Crawl-delay: 5` `Disallow: /login` `Disallow: /admin` …; get.data.gov.lt 200 `Allow: /` | the dataset page, html, 66 | `*/GeologinisTyrimas/csv/download/` → 302 to get.data.gov.lt …/:format/csv, text/csv, no length |
| fzzg/hydrocarbon-data-room | fzzg.gov.ba/soba-sa-podacima 16:11 | 404 | none (data viewed in the Data Room; rules PDF only) | — |
| sgu/borrhal | sgu.se/…/borrkarnor-och-borrhal/ 16:03 | www.sgu.se 200: `User-agent: *` `Disallow: /XFormFiles/` `Disallow: /sok/` … `Disallow: /arkiv/`; resource.sgu.se 404 | the product page, html, 183 | `*/oppnadata/borrhal/borrhal.zip` → 3,361,908 B application/zip |
| sgu/tyngdkraft | sgu.se/…/tyngdkraft/ 16:02 | as above | the product page, html, 194 | `*/geofysik-mark-tyngdkraft.zip` → 28,212,306 B application/zip |
| seg/seam-open-data | seg.org/seam/open-data/ 16:14 | 200: `User-agent: *` `Disallow:` (empty), `Crawl-delay: 10`; seam-open-data S3 403 (allow) | the page, html, 387 | `*/Phase+I/SEAM_I_Well_Log_Delivery.zip` → 16,605,942 B application/zip (literal `+` kept; `%2B` answers 403) |
| bgs/co2-stored | co2stored.co.uk/home/index 16:13 | 404 | none (data behind a login; only licence PDFs public) | — |
| usgs/ofr-2009-1021-las-gamma-ray-logs | pubs.usgs.gov/of/2009/1021/ 16:15 | 200: `User-agent: *` `Disallow: /archive/` | the index page, html, 20 | `*.zip` → C-Cfiles.zip 982,712 B application/zip |
| nogcc/well-data | nogcc.ne.gov/NOGCCPublications.aspx 16:09 (http only; https refused) | 404 | the page, html, 236 | `*/NebraskaWellData_Tops.zip` → 5,438,416 B application/x-zip-compressed |
| nd-dmr/wells | dmr.nd.gov/oilgas/subscriptionservice.asp 16:05 | gis.dmr.nd.gov 404 | `…/Wells/FeatureServer/0?f=json`, arcgis-layer, 1 | `*` → 2000 of 44,018 features, 1,118,791 B (partial; no L2 expected) |
| fl-dep/oil-gas-permit-database | floridadep.gov/water/oil-gas/documents/oil-and-gas-permit-database 16:13 | 200: `User-agent: *` `Disallow: /core/` `Disallow: /profiles/` `Disallow: /search/` … (/sites/default/files/ allowed) | the page, html, 135 | `*.xlsx` → OG_WELLS_WEBSITE_4.xlsx 703,015 B |
| al-ogb/wells | gsa.state.al.us/Scripts/OGB/gisdata/gis.html 16:07 | www.gsa.state.al.us 404 | `https://www.gsa.state.al.us/img/ogb/gis/wells.zip`, file (application/x-zip-compressed) | 3,562,207 B, Last-Modified 23 Oct 2026 02:55 GMT |
| va-energy/gas-oil-wells | energy.virginia.gov/gas-oil/GasOil.shtml 16:11 | 404 | `…/DGO/DGO_wells/MapServer/0?f=json`, arcgis-layer, 1 | `*` → 2000 of 8,605 features, 1,185,609 B (partial); HTTP 500 several times 16:11–16:12 |

Excerpts (verbatim, from the page opened above):
- nzpam: "Geodata map services ESRI Map Service: https://gis.nzpam.govt.nz/server/rest/services/Public/GeodataCatalogue_Layers/MapServer"
- sk-mer: "Locations of Phanerozoic Basin wells with cored intervals stored at the Subsurface Lab in Regina."
- gsnsw: "Publisher/Agency Department of Primary Industries and Regional Development (DPIRD) Licence Creative Commons Attribution Update Frequency Daily Temporal Coverage From 11/11/1961"
- gsv: "This dataset consists of geological faults for the Top Latrobe Group interpreted from industry seismic data compiled by the Department of Environment and Primary Industries (DEPI)."
- petrocom-gh: "2025 Fields Production Data 1 file(s) 583.23 KB Download"
- ppepdr: "All data sales are subject to DGPC approval. Seismic data US$ 4 per line kilometer Well data US$ 56 per well"
- egt: "GEA API kaudu on kättesaadavad Eesti Geoloogiateenistuses kogutavad geoloogiliste objektide (sealhulgas puuraugud -ja südamikud, proovid ja analüüside tulemused) andmed."
- lgt: "Prieigos teisės Vieši Licencija Creative Commons Attribution 4.0"
- fzzg: "Data Room is located in Federalni zavod za geologiju (Geological Survey of Federation of Bosnia and Herzegovina), adres: Ustanička 11, 71210 Ilidža."
- sgu/borrhal: "Hämta produkten som färdigpaketerad zip-fil Via länken laddas data i GeoPackage-format ned."
- sgu/tyngdkraft: "Tyngdkraftskartan är en så kallad Bougueranomalikarta (RG82) där enheten är mGal"
- sgu licence: "Öppna data från SGU har licensen Creative Commons Noll (CC0)."
- seam: "SEAM provides free access to selected data sets from past projects"; EULA: "Users must, however, obtain a license from SEG to hold and use the data, and pay a nominal fee"
- co2-stored: "Access to the CO2 Stored database is by Licence Agreement and is now free to access by all subscribers."
- usgs: "The LAS files from the gamma ray logs of 11 wells used to construct cross section C-C' are included in this report."
- nogcc: "Well Data Well Data - Access 2003 Format (6/4/2026) Well Data including formation tops - Access 2003 Format (6/4/2026)"
- nd-dmr: "As of January 1, 2026, our Basic Subscription rate is $100/year and our Premium Subscription rate is $500/year."
- fl-dep: "This spreadsheet is a compilation of information on all permitted wells in the state."
- al-ogb: "Reproduction or redistribution of digital data sets or products derived therefrom to a third party organization or entity is expressly forbidden."
- va-energy: "Gas wells in Virginia, also includes inspector areas"

### Checked and not given a record

| Host | Why |
|---|---|
| br2025.nuprc.gov.ng (Nigeria NDR via the 2025 licensing round) | reachable, terms stated (USD 10,000 per session per block), but the portal terms §2.3 forbid "any systematic or automated data collection activities ... without our express written consent", and the verifier's origin check is automated; not recorded. nuprc.gov.ng: files under `/api/` and `/upload/`, both disallowed |
| gnpcghana.com | no page stating data terms |
| mme.gov.na, gsn.gov.na (Namibia) | DNS failure / no route to host |
| dgpc.gov.pk, ppis.gov.pk | DNS failure (ppisonline.com: bidding documents and a view-only map) |
| mem.gov.om, data.gov.om (Oman) | script-only shell; macro statistics only |
| petrobangla.org.bd, bapex.com.bd, hcu.org.bd | TLS certificate verify failed |
| mapeg.gov.tr / mta.gov.tr / tpao.gov.tr | TLS failure / `Disallow: /` / timeout |
| gogn.orkustofnun.is, uos.is, gis.ust.is, isor.is (Iceland) | `Disallow: /`; JS search page; `Disallow: /geoserver/`; map viewer only |
| maps.egt.ee, fond.egt.ee | robots.txt 503; report metadata only, JS pages |
| lgt.lt, lgt.lrv.lt | Cloudflare 403 challenge |
| geoinf.kiev.ua, geo.gov.ua, data.gov.ua (Ukraine) | timeout; no downloads; no subsurface datasets |
| gzs.gov.rs, geoliss.mre.gov.rs (Serbia) | timeout; geological map and vocabularies only |
| akbn.gov.al (Albania) | TLS certificate verify failed |
| software.seg.org (BP 2004), edx.netl.doe.gov (Kimberlina) | HTTP 521; download paths disallowed |
| datos.gob.mx, hidrocarburos.gob.mx, cnh.gob.mx (Mexico) | Akamai 403; Cloudflare 522/523; DNS failure (CNH dissolved 2025) |
| geothermaldata.org (NGDS) | TLS hostname mismatch |
| sciencebase.gov | Cloudflare challenge (403) on item JSON |
| my.usgs.gov/crcwc (USGS Core Research Center) | POST search form; robots disallows /crc/ and /crc-data/ |
| dmr.nd.gov/oilgas/mpr/ (ND monthly production) | file list built by JavaScript; directory 403 (files answer directly, but the address changes monthly) |
| data.nzpam.govt.nz, geodata.nzpam.govt.nz/dataset/ | connection dropped; human-verification challenge |
| datasets.seed.nsw.gov.au, search.geoscience.nsw.gov.au | empty 202 challenge; script-only app |
| catalog.sarig.sa.gov.au dataset pages | 403 (as `sa-dem`'s known issue); SARIG petroleum wells and Otway core were left for a lane that can reach the origin |
| Zenodo, GitHub | already the manifest host of four records each (aggregator cap) |

Verifier finding (outside this lane): the Alabama OGB GIS page template starts with a UTF-8 byte-order
mark, and `read_listing` reads it as `text` (81 lines, no files) because `lstrip()` keeps the BOM.
