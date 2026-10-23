# E24 new records, group "americas" (read 2026-10-23, 15:15 to 15:20 UTC)

Every page below was opened from the lane host on 2026-10-23 with curl (browser user agent), at the
UTC times given. Status codes are the final answer after redirects. Records state publisher facts only;
no level, checksum or verification word is written into a record. `osd verify` was not run.

## Hosts tried

| Host | Address opened | Answer | Result |
|---|---|---|---|
| WOGCC site | https://wogcc.wyo.gov/ , /public-resources , /public-resources/oil-gas-resources , /robots.txt | 200 (robots.txt 404), 15:15 UTC | answered; links "WYDE (Data Explorer)"; no licence or reuse terms |
| WOGCC Data Explorer | https://dataexplorer.wogcc.wyo.gov/ , /api/GISConfig , /robots.txt | 200 (robots.txt 404), 15:15 to 15:16 UTC | answered: record `wogcc/wyde-wells` (redistribution unknown, no listing) |
| WOGCC Data Site | https://pipeline.wyo.gov/ , /robots.txt | 200, 15:15 UTC | robots.txt `User-agent: *` `Disallow: /`; not used |
| Staatsolie GeoPortal (ArcGIS Hub) | https://geoportal-staatsolie.hub.arcgis.com/robots.txt , /api/search/v1/collections/all/items , /pages/open-door-offering , /pages/downloadables | 200, 15:15 to 15:19 UTC | answered: record `staatsolie/open-door-data-offering` (purchase, redistribution unknown) |
| ArcGIS Online item data | https://www.arcgis.com/sharing/rest/content/items/{262b5d99…,71caac14…,fb42dcb4…,3c52a4d0…}/data?f=json | 200, 15:16 UTC | page content of the Hub pages (prices, downloads) |
| Staatsolie store | https://geoportalstore.com/ , /robots.txt | 200 (redirects to staatsolie.hub.arcgis.com/pages/lease-store), 15:16 UTC | robots.txt `Disallow: /` for all; no terms page found |
| Saskatchewan GIS | https://gis.saskatchewan.ca/robots.txt , /arcgis/rest/services/Economy?f=json , /Economy/Petroleum/MapServer?f=json , /0?f=json , /2?f=json , /0/query (count; one 2000-feature geojson export) | robots.txt 404; others 200, 15:17 to 15:18 UTC | answered: record `sk-mer/vertical-wells` |
| Saskatchewan GeoAtlas metadata | https://gisappl.saskatchewan.ca/WebDocs/Geo_Atlas/MetaData/{NonVertical_well,Vertical_well,Drill_Core}.html , /Html5Ext/Resources/GOS_Standard_Unrestricted_Use_Data_Licence_v2.0.pdf | 200 (robots.txt 404), 15:17 UTC | licence and extent; Drill_Core metadata states no licence, so no core record |
| Nova Scotia onshore atlas | https://novascotia.ca/robots.txt , /onshore-atlas/ , docs/Disclaimer(15).txt , docs/Disclaimer(16).txt , HEAD of four zips | 200, 15:18 to 15:19 UTC | answered: records `ns-energy/onshore-petroleum-well-log-database` and `ns-energy/onshore-2d-seismic-navigation` |
| Mineral Resources Tasmania | https://www.mrt.tas.gov.au/ , /robots.txt | 403 "Just a moment..." (Cloudflare challenge), 15:18 UTC | refused (blocked); no record |
| data.gov.au (MRT datasets) | https://data.gov.au/robots.txt , /data/api/3/action/package_search?q=organization:mineral-resources-tasmania | robots.txt `User-agent: *` `Disallow: /`; search 200 with 0 results, 15:18 UTC | not usable as a listing; no record |
| C-NLOPB | not opened | — | already present as `records/cnloer/`; skipped |

## wogcc/wyde-wells

- Page: <https://dataexplorer.wogcc.wyo.gov/> (title "WOGCC Data Explorer"), linked as "WYDE (Data Explorer)" from <https://wogcc.wyo.gov/public-resources/oil-gas-resources>.
  - Layer names in /api/GISConfig: "Oil Wells", "Gas Wells", "CBM Wells", "Injection Wells", "Disposal Wells", "Orphan Wells", "APDs - Active", "Oil and gas fields", "Gas Plants".
  - Map layers served through `/geoserver/wfs` and `/geoserver/gwc/service/wms` (from the page script).
- Licence: none stated. Only notice: "No Warranty is made by the Wyoming Oil and Gas Conservation Commission for the use of this data. Any use of this information to any specific application should be based on independent examination and verification. Those making use of, or relying on, this information assume all risks and liability arising from such use or reliance." Site footer: "Copyright © 2019 State of Wyoming. All Rights Reserved".
- Extent: State of Wyoming, approximate. Period: none stated.
- Listing: none (map application; GeoServer WFS is not a listing shape the verifier reads).

## staatsolie/open-door-data-offering

- Page: <https://geoportal-staatsolie.hub.arcgis.com/pages/open-door-offering> (Hub page "Staatsolie GeoPortal_Open-Door Offering", item 262b5d99691a48c983b1de427bee60e1, updatedAt 2026-06-23T19:26:31Z)
  - "Special Open-Door Data Offering As part of our Offshore Open-Door Offering Campaign, Staatsolie is pleased to offer the following options to interested companies. This special offer will remain available for a period of two (2) years, starting on November 24, 2025."
  - "1. 50% Discount Policy The discount applies when an entire data type is leased (example: All Wells and/or All Seismic 2D, etc.)."
  - "All Wells USD 127,500 ... All 2D Seismic USD 504,500 ... All 3D Seismic USD 273,000 ... All Gravity & Magnetic USD 7,500 ... All Technical Reports USD 75,000 ... Total USD 987,500"
  - "2. Access to all data via Virtual Data Room Included tools: SLB Petrel, Techlog and more. Cost: USD 110,000 per user per quarter, available for up to two (2) quarters."
- Downloads page <https://geoportal-staatsolie.hub.arcgis.com/pages/downloadables>: "Wells Well locations available for lease in shapefile format Shapefile 7 KB"; "Seismic 2D 2D seismic line data available for lease in shapefile format Shapefile 1,611 KB"; "Seismic 3D 3D seismic survey available for lease in shapefile format".
- Licence: no licence or reuse terms on the Open-Door, Downloads, LeaseStore or Multiclient pages; the Hub item `license` field is "none". Purchase terms quoted in `licence.terms.stated`.
- Extent: Suriname and offshore (Guyana-Suriname Basin), approximate. Period: none stated for the data (offer dates only).
- Listing: none proposed. The Downloads page is script-rendered; its links sit in Hub markdown, which the verifier's readers do not pick up. Hub robots.txt: `Crawl-delay: 60`; `/pages/` not disallowed.

## sk-mer/vertical-wells

- Page: <https://gisappl.saskatchewan.ca/WebDocs/Geo_Atlas/MetaData/Vertical_well.html> (title "PETROLEUM.vertical_well__")
  - "This feature class shows the location of vertical wells for mapping purposes, and surface and subsurface analysis. The well location information was taken from survey plans and entered in to the Ministry's IRIS system and is the best representation of the information that has been submitted."
  - "... licenced under The Oil and Gas Conservation Act and Regulations and The Oil and The Gas Conservation Regulations 2012 across Saskatchewan for the purpose drilling, operating, producing/injecting or exploring an upstream oil and gas well, mineral exploration potash wells, in Saskatchewan."
  - "Credits Government of Saskatchewan, Ministry of Energy and Resources"
- Service: <https://gis.saskatchewan.ca/arcgis/rest/services/Economy/Petroleum/MapServer?f=json>: "All feature classes from the PETROLEUM schema in the Production Data Warehouse."; copyrightText "Ministry of Energy and Resources, Government of Saskatchewan"; capabilities "Map,Query,Data". Layer 0 "Vertical Wells", Feature Layer, maxRecordCount 2000, count 119,595.
- Licence: metadata "This product contains information licensed under the Government of Saskatchewan Standard Unrestricted Use Data License (Version 2.0)." Licence PDF: "You are free to: Copy, modify, publish, translate, adapt, distribute or otherwise use the Information in any medium, mode or format for any lawful purpose." "you must use the following attribution statement: 'Contains information licensed under the Government of Saskatchewan Standard Unrestricted Use Data Licence (Version 2.0).'"
- Extent: metadata "Extent West -111.088192 East -100.550859 North 57.740033 South 48.895534". Period: none stated.
- robots.txt: https://gis.saskatchewan.ca/robots.txt answers 404 (no rules), so the layer and query paths are allowed.
- Listing shape: arcgis-layer (layer `?f=json`); one geojson export of 2000 features, 4,232,645 bytes (GET at 15:18 UTC, `exceededTransferLimit: true`).

## ns-energy/onshore-petroleum-well-log-database

- Page: <https://novascotia.ca/onshore-atlas/> (title "Onshore petroleum atlas, geoscience and maps - Government of Nova Scotia, Canada")
  - "The Government of Nova Scotia openly provides science, data, maps and other information to give geoscientists and technical professionals the opportunity to reproduce and verify findings"
  - "Preliminary petroleum well log database (NSDOE OFR 2017-09) Part 1 - Cape Breton region.zip (LAS files) Part 2 - Cumberland region.zip (LAS files) Part 3 - Windsor region.zip (LAS files)"
  - "Provincial data is now available on the Nova Scotia Onshore Petroleum Data Viewer, an interactive application that allows users to explore and download provincial petroleum well, 2D and 3D seismic and geologic model datasets"
- Licence: <https://novascotia.ca/onshore-atlas/docs/Disclaimer(15).txt>: "Information contained with this electronic publication is considered public information and may be distributed or copied, but may not copyrighted. We request that Public re-use of these materials bear a Nova Scotia Department of Energy byline/photo/image credit line." Suggested citation: "Bianco, E., 2017, Preliminary petroleum well log database, onshore Nova Scotia. Nova Scotia Department of Energy Open File Report 2017-09."
- Extent: onshore Nova Scotia (Cape Breton, Cumberland, Windsor regions), approximate. Period: 2017 (report year).
- robots.txt: https://novascotia.ca/robots.txt, `User-agent: *` disallows only named paths (none under /onshore-atlas/).
- Listing shape: html (the page links the zips). HEAD: Part 1 Cape Breton 4,837,104 bytes (application/x-zip-compressed, Last-Modified 2026-06-08).

## ns-energy/onshore-2d-seismic-navigation

- Page: <https://novascotia.ca/onshore-atlas/> (as above)
  - "Navigation data for 2D Seismic lines (NSDOE OFR 2017-11) Part 1 - Cape Breton region.zip (shapefile) Part 2 - Cumberland region.zip (shapefile) Part 3 - Windsor region.zip (shapefile)"
  - "Schedule of 2D Seismic Data, Onshore Nova Scotia (NSDOE OFR 2017-07) Part 1: Cape Breton region (PDF) ... Appendix 1 - List of seismic lines (PDF) Appendix 2 - List of seismic surveys (PDF)"
- Licence: <https://novascotia.ca/onshore-atlas/docs/Disclaimer(16).txt> ("NSDOE Open File Report 2017-11: Navigation data for 2D seismic lines, onshore Nova Scotia"), same public-information wording as above; suggested citation "... Nova Scotia Department of Energy Open File Report 2017-10." (sic).
- Extent and period: as above.
- Listing shape: html. HEAD: Part 2 Cumberland region 1,954,295 bytes.

## Proposed samples.yaml lines

```
sk-mer/vertical-wells: ["*"]   # ArcGIS layer 0: one geojson export of at most 2000 of 119,595 features, 4,232,645 bytes
ns-energy/onshore-petroleum-well-log-database: ["*2017-09*Cape*Breton*region.zip"]   # html: NSDOE OFR 2017-09 Part 1 Cape Breton LAS zip, 4,837,104 bytes
ns-energy/onshore-2d-seismic-navigation: ["*2017-11*Cumberland*region.zip"]   # html: NSDOE OFR 2017-11 Part 2 Cumberland shapefile zip, 1,954,295 bytes
```
