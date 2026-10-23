# E22 sources: records, fifth twenty (read 2026-10-23)

Every page below was opened from the lane host on 2026-10-23 with curl (browser user agent), at
the UTC times given per group. Status codes are the final answer after redirects. Records state
publisher facts only; no level, checksum or verification word is written into a record. Each
group lists the hosts it tried, including those that refused (blocked is not dead, OSD-D9), and
then one section per record with the page, verbatim excerpts, licence, extent and period.

## Group D: geothermal and CO2 sites (read 2026-10-23, 13:54 to 13:58 UTC, curl with browser user agent)

### Hosts tried for group D

| Host | Address opened | Answer | Result |
|---|---|---|---|
| DOE Geothermal Data Repository | https://gdr.openei.org/forge, /search?q=FORGE+16A, /submissions/1006, 1015, 1141, 1144, 1531 | 200, 13:54 to 13:55 UTC | answered: three Utah FORGE records (publisher cap 3) |
| CDGP Soultz-sous-Forêts (EOST) | https://cdgp.u-strasbg.fr/ (also http://, /geonetwork/srv/eng/catalog.search) | timeout after 30 s (curl exit 28), 13:55 and 13:57 UTC | refused; no record |
| CIUDEN (Hontomín) | https://www.ciuden.es/ (200); https://www.ciuden.es/es/almacenamiento-de-co2 (404) | 13:55 and 13:57 UTC | no data page; Zenodo search "Hontomín" lists only publications; no record |
| CO2CRC Otway | https://co2crc.com.au/otway-international-test-centre/ | 200, 13:57 UTC | page names "Datasets shared internationally" but lists no dataset or terms; GA lists no Otway stage beyond Brumbys found; no record |
| Alberta Open Government (Quest CCS) | https://open.alberta.ca/api/3/action/package_search?q=Quest%20carbon%20capture | 403 "Just a moment..." (challenge), 13:58 UTC | refused (blocked); no record |
| BedrettoLab (ETH Zurich) | https://bedrettolab.ethz.ch/en/research/Data-access/ | 200, 13:58 UTC | links datasets in the ETH Research Collection (search page, script-rendered); record taken from a Zenodo deposit instead |
| GFZ (Ketzin, Groß Schönebeck) | not opened | — | GFZ already has 4 records (over the cap of 3); no new record |

### doe-gdr/utah-forge-well-58-32-logs

- Page: <https://gdr.openei.org/submissions/1006> (title "GDR: Utah FORGE: Logs and Data from Deep Well 58-32 (MU-ESW1)")
  - "Data, logs, and graphics associated with the drilling and testing of Utah FORGE deep test well 58-32 (MU-ESW1) near Roosevelt Hot Springs."
  - "Download All Resources 2.24 GB — 11 files"
  - "Zipped archive containing the Pason drilling logs from well 58-32 in CSV format from 7/31/2017 to 9/13/2017."
  - "Zipped dataset consisting of Schlumberger logs and derived graphics for well 58-32 (MU-ESW1) including Dipole Shear Sonic Imaging, FullBore Micro Imager, Array Induction, Porosity, Triple Combo, Caliper Cement Volume, Cement Evaluation Gamma Ray, Cement Bond, and VDL Wide logs."
  - Citation: "Nash, Greg, and Joe Moore. Utah FORGE: Logs and Data from Deep Well 58-32 (MU-ESW1) . Energy and Geoscience Institute at the University of Utah, 11 April, 2018, Geothermal Data Repository. https://doi.org/10.15121/1452735."
  - "Organization Energy and Geoscience Institute at the University of Utah"; "Project Number EE0007080"
- Licence: the "License" link beside the CC BY badge points to https://creativecommons.org/licenses/by/4.0/; JSON-LD `"license": "https://creativecommons.org/licenses/by/4.0/"`; footer "Content is available under Creative Commons Attribution 4.0 unless otherwise noted."
- Extent: JSON-LD `spatialCoverage` box "38.483935 -112.916367 38.5148 -112.879748" on every file. Period: Pason logs 2017-07-31 to 2017-09-13 (drilling), as quoted.

### doe-gdr/utah-forge-seismic-reflection

- Page: <https://gdr.openei.org/submissions/1141> (title "GDR: Utah FORGE: Seismic Reflection Data")
  - "This is 2D and 3D seismic reflection data from Utah FORGE reprocessed during Phase 2c. ... For all 3D and 2D data the following datasets were created and output in SEG-Y format: Unmigrated Time; Prestack Time Migration (PSTM), Unenhanced (UnEnh) and Enhanced (Enh); Prestack Depth Migration (PSDM), Unenhanced (UnEnh) and Enhanced (Enh); Velocity Model used for Migration"
  - Resource: Paper titled "2018-2019 reprocessing of the 2D and 3D multichannel seismic surveys at the FORGE Utah EGS Laboratory"
  - "Download All Resources 849.51 MB — 3 files"; "Data from Jun 19, 2019"; "Submitted Jun 21, 2019"; author John Miller, Geophysical Consultant
- Linked raw data: <https://gdr.openei.org/submissions/1015> ("Utah FORGE: 2D and 3D Seismic Data"): "This set of data contains raw and Initially-processed 2D and 3D seismic data from the Utah FORGE study area near Roosevelt Hot Springs. ... The zipped archives numbered from 1-100 to 1001-1122 contain 3D seismic uncorrelated shot gatherers SEG-Y files." Also CC BY 4.0; file boxes "38.2867158822 -113.052795604 38.6867158822 -112.652795604" and the site box.
- Licence: as for 1006 (CC BY 4.0 link and JSON-LD license).
- Extent: box "38.483935 -112.916367 38.5148 -112.879748". Period: 2018 to 2019 (reprocessing), from the paper title.

### doe-gdr/utah-forge-3d-gravity

- Page: <https://gdr.openei.org/submissions/1144> (title "GDR: Utah FORGE: 3D Gravity Data")
  - "These resources describe the 3D geophysical inversion modeling of gravity data at the FORGE site near Milford, Utah. ... 3D modelling of gravity data at the FORGE site is to help characterize the subsurface geologic framework."
  - "This report provides details regarding the model parameters, data used, and geologic constraints applied to the 3D gravity modelling effort. Two different 3D density models constitute the output of the gravity modelling effort"
  - "Download All Resources 11.24 MB — 2 files"; "Data from Jun 24, 2019"; "Submitted Jun 24, 2019"; authors Christian Hardwick (Utah Geological Survey), Jeff Witter (Innovate Geothermal Ltd.)
- Licence: as for 1006 (CC BY 4.0).
- Extent: box "38.483935 -112.916367 38.5148 -112.879748". Period: 2019-06-24 (release).

### ustc/bedrettolab-atv-logs-stress

- Page: <https://zenodo.org/records/15725567> (title "ATV logs, ellipticity data, and stress inversion results from boreholes in the BedrettoLab | Zenodo"); API <https://zenodo.org/api/records/15725567>
  - "This dataset contain ATV logs, ellipticity data, and stress inversion results from borehole CB1(MB1), CB2(MB2), CB3(MB3), MB4, MB5, MB8, ST1, and ST2 in the Bedretto Underground Laboratory (BedrettoLab)."
  - "The ATV.zip file contain the acoustic amplitudes, traveltimes, traveltime-derived borehole radii, and binary masks of the borehole damage areas (breakouts, keyseats, and pre-existing fractures)."
  - Creator "Wang, Guangyu", "University of Science and Technology of China"; publication_date "2025-06-24"; DOI 10.5281/zenodo.15725567; files ATV.zip 2,405,568,281 bytes, ellipticity.zip 36,485,435, stress_inversion.zip 5,491,891
- Licence: `"license": {"id": "cc-by-4.0"}` (Creative Commons Attribution 4.0 International).
- Lab page: <https://bedrettolab.ethz.ch/en/research/Data-access/>: "The BedrettoLab addresses data management challenges in adherence to the FAIR principles ..."; "Available datasets" links https://www.research-collection.ethz.ch/search?query=leitzahlCode:02334. Home page: "Deep under the Swiss Alps, the BedrettoLab ... Its extraordinary overburden of up to 1.5 km of rock".
- Extent: none stated (no bbox). Period: 2025-06-24 (release).

## US state regulators (group A)

Every page below was opened from the lane host on 2026-10-23 between 13:52 and 14:00 UTC with curl
(browser user agent); ArcGIS item metadata read from `https://www.arcgis.com/sharing/rest/content/items/<id>?f=json`,
Socrata metadata from `https://<domain>/api/views/<id>.json`, CKAN from `https://data.ca.gov/api/3/action/package_show`.

### Hosts that refused or offer no open record

| Host | Address opened | Answer | Result |
|---|---|---|---|
| North Dakota DMR | https://www.dmr.nd.gov/oilgas/ , /oilgas/subscriptionservice.asp , /oilgas/disclaimer.asp | 200, 13:52–13:58 UTC | answered; well files, logs, scout tickets and production sit behind "Premium Subscription Services" (sign-up form); disclaimer states no terms of use. No record (E14 finding stands: the data are paid) |
| Wyoming WOGCC | https://wogcc.wyo.gov/ , /public-resources | 200, 13:52 and 13:59 UTC; /public-resources/data-site 404 | answered; data in "WYDE (Data Explorer)", no terms stated; held back (unknown-licence budget) |
| Louisiana SONRIS | https://www.sonris.com/ ; https://www.dnr.louisiana.gov/page/sonris | 200 with an empty body (3 characters), 13:52 UTC; 403, 13:59 UTC | blocked; no record |
| California CalGEM | https://www.conservation.ca.gov/calgem/Pages/Oil-and-Gas-Data.aspx | timeout (curl exit 28), 13:53 and 13:54 UTC | refused; the Data.CA.gov entry answers: `calgem/wellstar-oil-and-gas-wells` |
| Michigan EGLE | https://www.michigan.gov/egle/maps-data/oil-gas ; /egle/about/organization/geologic-resources-management/oil-and-gas | 403 "Access Denied", 13:53 and 13:54 UTC | blocked; no record |
| Illinois ISGS | https://isgs.illinois.edu/ilwater-ilgas , /ilgas , /ilogas , /oil-and-gas-resources | 404, 13:53–13:59 UTC | no data page found; ILOIL is an ArcGIS web app (item af7f150b9ec348d3860b1d225bffb035, no licence or description); no record |
| Pennsylvania DEP open data | https://gis.dep.pa.gov/opendata | timeout (curl exit 28), 13:56 UTC | the hub at newdata-padep-1.opendata.arcgis.com answers: `pa-dep/oil-and-gas-well-locations` |
| Kentucky KGS | https://www.uky.edu/KGS/oilgas/ | TLS failure (curl exit 60), 13:59 UTC | refused; no record |
| Montana BOGC | https://bogfiles.dnrc.mt.gov/ ; https://dnrc.mt.gov/Oil-and-Gas/ | 403; 404, 13:59 UTC | no record |
| Arkansas AOGC | https://www.aogc.state.ar.us/ | 403 Cloudflare challenge, 13:59 UTC | blocked; no record |
| Mississippi OGB | https://www.ogb.state.ms.us/ | 500, 13:59 UTC | no record |
| Indiana IGWS | https://igws.indiana.edu/PDMS | 404, 13:59 UTC | no record |

### calgem/wellstar-oil-and-gas-wells

- Page: <https://data.ca.gov/dataset/wellstar-oil-and-gas-wells> (200, redirects to /@california-department-of-conservation/wellstar-oil-and-gas-wells, 13:55 UTC; title "WellSTAR: Oil and Gas Wells – Data.CA.gov")
  - "License Creative Commons Attribution"; CKAN `license_id: cc-by`, `license_url: http://www.opendefinition.org/licenses/cc-by`; organization "California Department of Conservation"; `dcat_publisher_name: California Department of Conservation`.
  - "This online map represents oil and gas wells in the CalGEM Well Statewide Tracking and Reporting System, or WellSTAR. Wells are displayed by well type and well status."
  - Resources: CSV, shapefile ZIP, GeoJSON, KML from gis-cnra.hub.arcgis.com; service https://gis.conservation.ca.gov/server/rest/services/WellSTAR/Wells/MapServer/0.
- ArcGIS item ef53080fdf894761858dd1728610b9a0 `licenseInfo`: "The Department of Conservation, Geologic Energy Management Division (CalGEM) provides the data contained in this website for informational purposes. ... Before using the services provided in this database, review the Department of Conservation “Conditions of Use” policy, which is incorporated by reference into this Data Disclaimer." (discrepancy recorded in `known_issues`)
- Licence: CC BY without version (spdx null), redistribution allowed, attribution required. Extent: California (approximate). Period: none stated.

### ecmc/oil-and-gas-active-and-plugged-wells

- Page: <https://data.colorado.gov/Environment/Oil-and-Gas-Active-and-Plugged-Wells/hvzn-ur6t> (200, 14:00 UTC)
  - Metadata: name "Oil and Gas Active and Plugged Wells"; attribution "DNR - Colorado Oil & Gas Conservation Commission"; "Oil and Gas Active and Plugged Wells as reported by the Colorado Oil & Gas Conservation Commission."
  - License: "Creative Commons 1.0 Universal (Public Domain Dedication)", termsLink http://creativecommons.org/publicdomain/zero/1.0/legalcode
  - "Update Schedule": "Daily"; "Citation": "DNR - Colorado Oil & Gas Conservation Commission"; access point "download zip file": http://cogcc.state.co.us/documents/data/downloads/gis/WELLS_SHP.ZIP
- Download (HEAD only): redirects to https://ecmc.state.co.us/documents/data/downloads/gis/WELLS_SHP.ZIP, 200, 15,763,674 bytes, last-modified 22 Oct 2026 13:33:48 GMT (13:56 UTC).
- https://ecmc.state.co.us/ and /data.html, /data2.html: 200, an Angular application with no terms in its text (13:52–13:55 UTC).
- Licence: CC0-1.0 as stated on the state portal entry. Extent: Colorado (approximate). Period: none stated.

### pa-dep/oil-and-gas-well-locations

- Page: <https://newdata-padep-1.opendata.arcgis.com/datasets/4300a4d66be4497f8c228bbbeb2401c2> (200, 13:57 UTC, "PA Department of Environmental Protection"); item 4300a4d66be4497f8c228bbbeb2401c2, owner ra_epgeospatialdatacenter.
  - "An Oil and Gas Location is a DEP primary facility type related to the Oil & Gas Program. This layer represents wells."
  - "Some sub facility types are not included in this layer due to security policies."
  - `licenseInfo`: "Not for commercial use or resale. The User shall save the Commonwealth harmless from any suits, claims or actions arising out of the use of the data files or accompanying documentation ... These data files and documentation are provided AS IS"
  - Extent [[-80.9559, 39.2552], [-74.9242, 42.9725]]; service https://gis.dep.pa.gov/depgisprd/rest/services/emappa/eMapPA_External/MapServer/89
- data.pa.gov entry qzfm-e4nk "Department of Environmental Protection(DEP) GIS Open Data Portal": license "Public Domain" (discrepancy recorded).
- Oil and Gas Reports page: <https://www.pa.gov/agencies/dep/data-and-tools/reports/oil-and-gas-reports> (200, 13:53 UTC): "The report links on this page provide oil and gas production information, permits issued, drilling commence date (SPUD date), county data, operator specific data, as well as inspections, violations and enforcement actions."
- Licence: restricted (not for commercial use or resale), attribution not stated. Extent: item extent. Period: none stated.

### nysdec/oil-gas-and-other-regulated-wells

- Page: <https://data.ny.gov/Energy-Environment/Oil-Gas-Other-Regulated-Wells-Beginning-1860/szye-wmt3> (200, 13:57 UTC)
  - "Information on oil, gas, storage, solution salt, stratigraphic, and geothermal wells in New York State"
  - "Posting Frequency": "Quarterly"; "Time Period": "Beginning 1860"; "Coverage": "Statewide"; "Dataset Owner": "New York State Department of Environmental Conservation"; rows updated 2026-10-23 09:10 UTC; licence field empty.
- DEC wells layer, ArcGIS item b7a08a1be2c141dd9d432b737da608ed (owner NYSDEC_PUB), read 13:59 UTC:
  - "The Division of Mineral Resources maintains information and data on more than 40,000 wells, categorized under New York State Article 23 Regulated wells. Service layer is updated daily."
  - `licenseInfo`: "1.The NYS DEC asks to be credited in derived products. 2.Secondary Distribution of the data is not allowed. 3.Any documentation provided is an integral part of the data set. Failure to use the documentation in conjunction with the digital data constitutes misuse of the data."
  - Extent [[-79.968, 40.548], [-70.149, 44.720]]; service FeatureServer answered 200 (14:00 UTC).
- OPEN-NY Terms of Use (see next section) say otherwise; the record carries DEC's own terms (restricted, attribution required) and names the conflict.
- Period: 1860 to date read (register updated quarterly; precedent tx-rrc, sodir).

### nysdec/oil-and-gas-annual-production

- Page: <https://data.ny.gov/Energy-Environment/Oil-and-Gas-Annual-Production-Beginning-2001/mxea-iw3u> (200, 14:00 UTC)
  - "This dataset contains annual production information of oil and gas wells in New York State from 2001 to present."
  - "Posting Frequency": "Annually"; "Time Period": "Beginning 2001"; licence field empty.
- OPEN-NY Terms of Use: <https://data.ny.gov/d/77gx-ii52> (PDF "OPEN-NY Terms of Use", 200, 13:58 UTC; "LAST MODIFIED: March 8, 2013")
  - "The OPEN NY Terms of Service do not contain restrictions requiring members of the public to use attribution, to re-post the license terms with any re-uses of the data, to impose share-alike or technical restrictions, nor require the public to obtain pre-approval before re-use of the data."
  - "So long as you are not doing anything malicious with NYS data, you may use it as you wish, subject to no other requirements."
  - "The State grants you a non-exclusive, revocable license to use the Content contained on this website in a manner consistent with the Terms of Use."
- Licence: OPEN-NY, redistribution allowed, attribution not required. Extent: New York (approximate). Period: 2001 to date read.

### nm-ocd/oil-and-gas-wells

- Page: <https://ocd-hub-nm-emnrd.hub.arcgis.com/datasets/387f397ebf164c7aa6a752aac7d22b17> (200, 14:00 UTC, "OCD Hub"); item 387f397ebf164c7aa6a752aac7d22b17 (owner jlivengood_EMNRD)
  - "*Wells are updated daily* Point features representing the surface drilling location of energy production wells (oil, gas, CO2), including injection and salt water disposal wells in New Mexico. A well point is added to this database when an Application Permit to Drill (APD) is submitted and approved."
  - "Well locations are based on information contained on Form C-102 ... and should be considered approximate."
  - `licenseInfo`: "OCD geospatial data is intended for general reference use by the public, and should not be construed as the definitive record for legal purposes, locations, etc."
  - Service https://gis.emnrd.nm.gov/arcgis/rest/services/OCDView/Wells_Public/FeatureServer answered 200 (14:00 UTC).
- OCD Data page <https://www.emnrd.nm.gov/ocd/ocd-data/> (200, 13:52 UTC): "Browse, view, and download OCD publicly available data and documents."; FTP page (200, 13:54 UTC): "anonymous connection, no other username / password needed".
- Licence: none stated → unknown. Extent: New Mexico (approximate). Period: none stated.

### odnr/oil-and-gas-well-database

- Page: <https://ohiodnr.gov/discover-and-learn/safety-conservation/about-ODNR/oil-gas/oil-gas-resources/featured-content-3> (200, 13:53 UTC, "Oil & Gas Well Database")
  - "This online search is linked directly to the Risk Based Data Management System (RBDMS) database. Access Ohio oil and gas well records including completion, permit and production information."
  - "Please Note: The Oil and Gas Well Database is not accessible to locations outside the United States."
  - "The RBDMS contains comprehensive well data for over 100,000 wells permitted since 1980. Historical well card information from the Division of Geological Survey for wells permitted before 1980 has also been added to the database. ... It can be downloaded from the below link or is available free on CD"
- Download (HEAD only): https://dam.assets.ohio.gov/raw/upload/ohiodnr.gov/documents/oil-gas/rbdms/Rbdmsd97Weekly.zip, 200, 304,095,782 bytes, last-modified 22 Oct 2026 (14:00 UTC).
- Wells service item e03ec46046af49c49d879ab9be07f980 (owner ODNR_GISAPPDEV): `licenseInfo` "Liability Statement: The Ohio Department of Natural Resources (DNR) provides this geographic data 'as is.' ..."; extent [[-84.90, 38.38], [-80.32, 41.98]].
- Licence: none stated → unknown. Period: not written (wells "since 1980" plus earlier well cards; no bounded start).

### wvges/pipeline-oil-and-gas-well-data

- Page: <https://www.wvgs.wvnet.edu/www/datastat/datastat.htm> (200, 13:52 UTC, "WVGES Oil and Gas Summary Data"): "Search individual well records on 'pipeline.'", "File Repositories: Scanned Well Logs, Digitized Logs, and Scanned Well Records", "Searchable Oil and Gas Production Data (1979 through latest available)", "Downloadable Log ASCII Standard (.LAS) Files".
- Pipeline: <https://www.wvgs.wvnet.edu/oginfo/pipeline/pipeline2_intro.asp> (200, 13:59 UTC)
  - "'Pipeline' provides public access to oil and gas well data for over 154,000 wells. ... Data contained within tables include: locations; completions; farm name and operator; pays and shows of hydrocarbons; water; formation tops and thicknesses; monthly and annual production of gas and/or oil, generally since 1979; plugging; data about mechanical logs ..."
  - "DISCLAIMER REGARDING THE RELEASE OF DATA AND USER REQUIREMENTS: The West Virginia Geological and Economic Survey (WVGES) makes basic data available to the public from its computerized databases on mineral resources under the following conditions: ... 3. These data are provided as a service to the State of West Virginia through the WVGES for the purpose of research and development efforts. Final use of these data is the sole responsibility of the user."
- Licence: none stated → unknown. Extent: West Virginia (approximate). Period: not written (production only from 1979).

## Group B: Iberia, the Alps, Canada and the North Atlantic (read 2026-10-23, 13:54 to 14:02 UTC)


### Hosts tried for group B
Pages opened with curl (browser user agent); status is the final answer after redirects.

| Host | Address opened | Answer | Result |
|---|---|---|---|
| IGME-CSIC | https://www.igme.es/datos-y-mapas/bases-de-datos/ ; http://info.igme.es/sigeof/ | 200, 13:57 and 14:02 UTC | answered: `igme/sigeof` |
| IGME Hidrocarburos | https://info.igme.es/Hidrocarburos | 200, but a Blazor application ("An unhandled error has occurred") with no readable content, 13:57 UTC | no record (SIGEOF carries the hydrocarbon seismic sections and well logs) |
| IGME ATH (guessed address) | https://info.igme.es/ATH/ | 404, 13:54 UTC | no record |
| IGME data catalogue | https://www.igme.es/datos-y-mapas/catalogo-de-datos/ | timeout (curl exit 28), 13:59 UTC | no record |
| swisstopo (opendata.swiss) | https://opendata.swiss/en/dataset/tiefe-bohrungen ; /2d-und-3d-reflexionsseismik-in-der-schweiz | 200, 13:54 UTC | answered: `swisstopo/deep-wells`, `swisstopo/reflection-seismic` |
| opendata.swiss CKAN API | https://opendata.swiss/api/3/action/package_show?id=tiefe-bohrungen | 403 (nginx), 13:54 UTC | not used; the HTML dataset pages carry the terms symbol |
| swisstopo (guessed page) | https://www.swisstopo.admin.ch/en/geological-data-deep-boreholes | 404 | not used |
| GeoSphere Austria | https://www.geosphere.at/de/daten ; https://www.tethys.at/oai (ListRecords, GetRecord 184/191/212) ; https://tethys.at/dataset/191 and /212 | 200, 13:55 to 13:57 UTC | answered: `geosphere-at/molasse-basin-subsurface-model`, `geosphere-at/aerogeophysics-northern-lower-austria` |
| GeoSphere Data Hub / data.gv.at | https://data.hub.geosphere.at/dataset/?q=… ; data.gv.at CKAN API | 200 script shell / HTML instead of JSON | not used |
| Portugal ENMC | https://www.enmc.pt/ | connection refused (curl exit 7), 13:54 UTC | refused; DGEG used |
| Portugal DGEG | https://www.dgeg.gov.pt/pt/areas-setoriais/geologia/petroleo-armazenamento-de-co2/ and subpages | 200, 13:59 UTC | answered: `dgeg/petroleum-technical-data` |
| Manitoba | https://www.manitoba.ca/iem/petroleum/index.html, /gis/technical.html, /pubcat/digital.html | 200, 13:54 and 14:00 UTC | answered: `manitoba-petroleum/technical-well-files` |
| Saskatchewan | .../oil-and-gas/oil-and-gas-news-and-bulletins/geoscience-data (404); .../saskatchewan-geoscience-data-system (200) | 14:01 UTC | no record: the Geoscience Data System is mineral assessment data; well data are via Petrinex (not opened) |
| Newfoundland C-NLOER | not opened | | already present as `cnloer/data-information-hub` |
| Faroe Jarðfeingi | https://jf.fo/ ; /datur/boridatur/ ; /datur/data-package/ ; /datur/seismikk-datur/ | 200, 13:54 and 14:01 UTC | answered: `jardfeingi/well-data` |
| Greenland via GEUS | not opened | | GEUS already at the publisher cap (3) |

### igme/sigeof

- Listing: <https://www.igme.es/datos-y-mapas/bases-de-datos/>: "SIGEOF Sistema de Información Geofísica Aplicación dirigida a la búsqueda y localización de datos de distintas metodologías de Geofísica: Eléctrica – Corriente Continua; Electromagnético; Resonancia Magnética; Testificación; Gravimetría; Petrofísica; Magnetometría y/o Radiometría Aeroportada y Sísmica."
- Page: <http://info.igme.es/sigeof/> (200, 14:02 UTC; https redirects to http)
  - "Confirma haber leido y aceptar las condiciones de la licencia de uso de los datos facilitados por esta aplicación."
  - "LICENCIA DE USO: Condiciones de uso público y difusión de la información para la reutilización de los datos del IGME" … "Son de aplicación las siguientes condiciones generales para la reutilización de los datos procedentes de SIGEOF: 1. Está prohibido desnaturalizar el sentido de la información. 2. Debe citarse la fuente de los datos objeto de la reutilización. Esta cita podrá realizarse de la siguiente manera: Sistema de Información Geofísica del IGME: SIGEOF. Editor: Área de Geofísica y Teledetección. [Fecha de consulta DD/MM/AAAA]. Disponible en: http://info.igme.es/sigeof/ 3. No se podrá indicar, insinuar o sugerir que el Instituto Geológico y Minero de España (IGME) … participa, patrocina o apoya la reutilización"
- Format report <http://info.igme.es/sigeof/doc/SIGEOF_INFO.pdf> (200): sections "SÍSMICA – LÍNEAS (SEG-P1) Y SECCIONES SÍSMICAS (TIF)", "SÍSMICA – SECCIONES SÍSMICAS (SEG-Y)", "MAGNETOMETRÍA Y/O RADIOMETRÍA – VUELOS/MALLAS", "DATOS GRAVIMÉTRICOS", "TESTIFICACIÓN – EXXONMOBIL"; "la mayoría de las secciones sísmicas obtenidas a partir del Archivo Técnico de Hidrocarburos (Ministerio de Industria, Energía y Turismo). También se encuentra la información de Sondeos de Hidrocarburos proporcionada por la compañía ExxonMobil International Limited."
- Generic licence <https://info.igme.es/media/Pdfs/LicUsoIGME_GENERICA_EN_2022.pdf> (linked from https://www.igme.es/condiciones-de-uso/): "the re-use and dissemination of the NC IGME information and data is granted and supported by way of this free licence for commercial and non-commercial use, for any purpose"; "Certain databases or data sets may be subject to special conditions of use".
- Extent: by map, province or sheet; bbox is Spain (approximate). Period: none stated.

### swisstopo/deep-wells

- Page: <https://opendata.swiss/en/dataset/tiefe-bohrungen> (200, 13:54 UTC), "Deep wells", organisation Federal Office of Topography swisstopo; terms symbol links `/en/terms-of-use#terms_by`.
  - "This map shows the deep wells in Switzerland. The data come from the Federal Office of Topography swisstopo, from universities, cantons and private companies. Metadata are publicly accessible and the associated documents, when they are free for publication, are accessible through the Federal Geoportal (map.geo.admin.ch). For any information concerning the documentation, please contact the rights holder directly. The map is revised regularly and does not purport to be complete. MD = Measured depth, TVD = True vertical depth, TD = Total depth"
  - Resources: WMS / WMTS ch.swisstopo.geologie-bohrungen_tiefer_500, API "RESTful API von geo.admin.ch", map preview, download. "Issued date July 14, 2017", "Modified date July 28, 2026", "Temporal coverage -", "Spatial coverage Schweiz (mit grenznahem Ausland)", "Update interval Quarterly".
- Terms: <https://opendata.swiss/en/terms-of-use> (200, 13:55 UTC): "Open use. Must provide the source. You may use this dataset for non-commercial purposes. You may use this dataset for commercial purposes. You must provide the source (author, title and link to the dataset)."; "the datasets on opendata.swiss are generally accompanied by terms of use, rather than licences."
- Extent: Switzerland (approximate bbox). Period: catalogue issued to modified (release), as quoted.

### swisstopo/reflection-seismic

- Page: <https://opendata.swiss/en/dataset/2d-und-3d-reflexionsseismik-in-der-schweiz> (200, 13:54 UTC); terms symbol `#terms_by` (same terms as above).
  - "This map shows the location of seismic reflection data acquired in Switzerland for the exploration of the geological subsurface. The majority of these are two-dimensional measurements (2D) along the profile traces shown. Three-dimensional measurements (3D) cover the areas within the shown perimeters. … Downloading is possible for many of the processed seismic datasets that are publicly available. For more detailed information on other seismic data (raw, non-public etc.), please contact the rights holder directly. This map is continuously updated and does not claim to be complete."
  - "Issued date September 8, 2023", "Modified date November 24, 2025", "Spatial coverage Schweiz (mit grenznahem Ausland)", "Update interval Semiannual".
- Not recorded (cap and spread): "Gravimetric Atlas of Switzerland 1:100000" (terms `#terms_open`, issued 1994).

### geosphere-at/molasse-basin-subsurface-model

- Page: <https://tethys.at/dataset/191> (200, 13:57 UTC; script application). Metadata from <https://www.tethys.at/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:tethys.at:191> (200, 13:56 UTC):
  - title "Geological subsurface model of the Austrian Molasse Basin"; "Increasing usage requirements in the Molasse Basin regarding mining, geothermal energy and storage of CO2 and natural gas have been the main driving force for creating a geological subsurface model"; "The modelled geological layers were exported as .DXF files from SKUA-GOCAD™."
  - coverage "SOUTH-BOUND LATITUDE: 47.79 * WEST-BOUND LONGITUDE: 12.75 * NORTH-BOUND LATITUDE: 48.78 * EAST-BOUND LONGITUDE: 16.59 * ELEVATION ABSOLUT: 783 * DEPTH ABSOLUT: -7412"
  - rights "Creative Commons Attribution 4.0 International (CC BY 4.0)", "info:eu-repo/semantics/openAccess"; date 2022-12-02; DOI 10.24341/tethys.191
  - source "Porpaczy, C.,Bottig, M. (2022): Geological subsurface model of the Austrian Molasse Basin.Tethys RDR, Geologische Bundesanstalt (GBA), Wien"
- Period: 2022-12-02 (publication, release).

### geosphere-at/aerogeophysics-northern-lower-austria

- Page: <https://tethys.at/dataset/212> (200, 13:57 UTC). OAI record oai:tethys.at:212 (200, 13:56 UTC):
  - "The aerogeophysical dataset contains geomagnetic, electromagnetic and radiometric (Th, U, K) data from five airborne surveys carried out between 1983 and 1997 in the northern part of Lower Austria: Geras (1996, 1997), Pulkau North (1995), Pulkau (1994), Kamptal-Ziersdorf (1983), Krems (1983). … In 1998, the geomagnetic datasets were combined and reprocessed."
  - coverage "SOUTH-BOUND LATITUDE: 48.331274 * WEST-BOUND LONGITUDE: 15.449582 * NORTH-BOUND LATITUDE: 48.886203 * EAST-BOUND LONGITUDE: 16.096122"
  - rights "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"; date 2023-08-17; DOI 10.24341/tethys.212
  - source "Schattauer, I.,Hintersberger, E. (2023): Aerogeophysical data - Northern Lower Austria.Tethys RDR, GeoSphere Austria, Wien"
- Period: 1983 to 1997 (acquisition).

### dgeg/petroleum-technical-data

- Page: <https://www.dgeg.gov.pt/pt/areas-setoriais/geologia/petroleo-armazenamento-de-co2/dados-informacao-tecnico-cientifica/dados-consulta/> (200, 13:59 UTC):
  - "Os dados e informação técnica no âmbito das atividades de prospeção e pesquisa de petróleo … estão disponíveis nas instalações da DGEG ou do Laboratório Nacional de Energia e Geologia (LNEG)"
  - "Sísmica 2D - No âmbito das concessões atribuídas, foram adquiridos cerca de 72600 km de sísmica (Dados de campo, processados e reprocessados): 5.865 Km onshore 67.009 Km offshore"; "Sísmica 3D - Desde 2010, foram adquiridos cerca de 10.372 km² de sísmica 3D"; "Sondagens - Desde 1938, foram efetuadas 175 sondagens. … Relatórios finais; Diagrafias elétricas; Dados de Velocidade; Relatórios de geoquímica; Relatórios de biostratigrafia; Testemunhos e detritos de sondagens; Lâminas delgadas …; Amostras de óleo e de testes de formação."
- Price page <…/precario-aplicavel/> (200, 13:59 UTC): "Para consultar o respetivo preçário … bem como resumo das respetivas condições, ver Tabela de Preços 2018/2019" → <https://www.dgeg.gov.pt/media/5nvewoac/doc-7.pdf> (200):
  - "A venda de documentação deve obedecer aos seguintes termos e condições: … 2. As companhias não licenciadas/não concessionárias deverão pagar … pela consulta de informação técnica, uma taxa fixa de 1250,0 Euros. … 3. A taxa fixa … terá a validade de 12 meses … 5. Os organismos públicos e as instituições académicas poderão beneficiar dum desconto de 50%, a ser analisado caso a caso. 6. A informação só será vendida, ao setor petrolífero, a companhias idóneas. 7. A informação não poderá ser reproduzida ou vendida a terceiros."
- Extent: none stated (bbox mainland Portugal and offshore, approximate). Period: 1938 to date (wells), as quoted.

### manitoba-petroleum/technical-well-files

- Page: <https://www.manitoba.ca/iem/petroleum/gis/technical.html> (200, 14:00 UTC):
  - "Technical Well files can be accessed by entering the well licence number below."; "The Regulatory Services Branch has technical records of all non-confidential wells drilled in the Province. Files may include the original well licence, survey plan, drilling prognosis, core analyses, drill stem test reports, reservoir pressure measurements, logs, drilling and service rig tour reports, and well completion reports."
  - sample file http://content.gov.mb.ca/iem/petroleum/documents/technical/008001.pdf (200, application/pdf, 34 MB); UWI key list …/reports/uwi_weekly.xlsx (200).
- Digital data page <https://www.manitoba.ca/iem/petroleum/pubcat/digital.html>: "Digital Well data is available from the Regulatory Services Branch by contacting …"
- Licence: <https://www.gov.mb.ca/legal/copyright.html> (200, 14:00 UTC; footer link of the page): "The OpenMB License makes clear that most material covered by Crown copyright can be copied, modified, published, translated, adapted, distributed or otherwise used, without seeking additional permissions"; "Information that belongs to a third-party is governed by that third-party and can't be licensed by the government."; attribution example "Contains information from the Manitoba government, licensed under the OpenMB Information and Data Use Licence ( Manitoba.ca/OpenMB )". Licence PDF <https://www.gov.mb.ca/asset_library/en/legal/OpenMB-Information-Data-Use-Licence.pdf> (200): exemptions include "third party rights the Information Provider is not authorized to license".
- Extent: none stated (bbox southern Manitoba, approximate). Period: none stated.

### jardfeingi/well-data

- Page: <https://jf.fo/datur/boridatur/> (200, 14:01 UTC): "Below are all the data releases for the wells on the map. Press on the data below each well to download a pdf file. (9 offshore wells and 3 onshore wells)." Zip files 2015.08.24_FO_Offshore_Wells.zip and Onshore_wells_NOV2017.zip. Sample PDFs: 6004-12-1_well_fakta.pdf ("Well information … Spud date 23/7-2001 … Operator BP Amoco Exploration (Faroes) Ltd"), 6004-12-1_digital-logs.pdf ("Digital Logs (LAS)" list).
- Data-package <https://jf.fo/datur/data-package/> (200, 14:01 UTC): "It includes released 3D-, 2D-seismic and well data."; "There is an administration fee of £400 for sending the data on a harddrive"; "Press here to see the Terms and Conditions (pdf)" (no link in the page).
- Licence: none stated; recorded `unknown`. Extent: none stated (bbox the Faroese area, approximate). Period: none stated.
