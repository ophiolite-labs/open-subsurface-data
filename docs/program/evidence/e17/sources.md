# E17 sources: what each publisher states (read 2026-10-23)

One section per new record: the pages opened on the day, the verbatim excerpts that carry the
licence, extent and period, and what did not answer. All pages were read on 2026-10-23 from the
lane host with curl (browser user agent where noted). Where a bbox is the publisher's stated
jurisdiction rather than a coordinate box, the record says "approximate" in `known_issues`, as in
E13 and E14.

## aer/st37-list-of-wells

- Page: <https://www.aer.ca/data-and-performance-reports/statistical-reports/st37>
  - "ST37: List of Wells in Alberta reflect the life cycle of wells within Alberta as reported to the AER and is available in Excel, Shapefile and Geodatabase format."
  - "All format zip packages have been upgraded to include bottom holes, surface holes, production strings and geometry information."
  - "Geodatabase [ZIP, 1. 23 GB] Excel [ZIP, 170 MB] Shapefile [ZIP, 532 MB]"
- Licence: <https://www.aer.ca/copyright-and-disclaimer>
  - "Information on this site has been posted with the intent that it be readily available for personal and public non-commercial (educational) use. ... the AER be identified as the source of the materials ..."
  - "Reproduction of multiple copies of materials on this site, in whole or in part, for the purposes of commercial redistribution is prohibited except with prior written permission of the AER."
- Extent: Province of Alberta (approximate). Period: none stated.

## bcer/well-surface-holes-permitted

- Page: <https://data-bc-er.opendata.arcgis.com/datasets/657b609ee3314adf91da5ab86d42cda7_0> (item metadata via <https://www.arcgis.com/sharing/rest/content/items/657b609ee3314adf91da5ab86d42cda7?f=json>, owner BC_Energy_Regulator)
  - "Provides non-confidential information about the surface location of a well. The status view provides information on the current status of the surface hole. Data is updated nightly."
  - item "extent": [[-134.1905, 47.9913], [-110.8406, 60.1147]]
- Licence: <https://www.bc-er.ca/files/gis/BCER-Open-Data-Licence.pdf>
  - "You are free to copy, modify, publish, translate, adapt, distribute or otherwise use the Information in any medium, mode or format for any lawful purpose. You must ... Acknowledge the source of the Information using an attribution statement such as “Contains information licenced under the BC Energy Regulator Open Data Licence”"
- Other channels: BC Data Catalogue copy is Access Only ("It may not be reproduced or redistributed without the prior written permission of the Province of British Columbia."); <https://www.bc-er.ca/terms/> carries the same for Data Centre downloads.
- Period: none stated.

## cnsoer/directory-of-offshore-wells

- Page: <https://cnsopbdigitaldata.ca/geoviewer/dmc/public/query/0>; files dow-2025.xlsx (42,654 bytes) and dow-2025.pdf ("CNSOER Directory of Wells, Nova Scotia Offshore Area", "Last Revised January 2025")
  - "This listing contains information about the well, i.e. Well Name, Company, Drilling Unit, Location, Spud Date, Well Termination Date, RT Elevation, Water Depth, Total Depth, Well Type, Classification, & Status."
- Licence: none stated for the data. DMC page: "Content © CNSOER 2025". Website terms <https://cnsoer.ca/website-terms-of-use>: "Unauthorized use or reproduction of these materials, either in whole or in part, is strictly prohibited." Recorded `unknown`.
- Earlier unreachable (E13): cnsopb.ns.ca now redirects to cnsoer.ca.
- Extent: Canada-Nova Scotia offshore area (approximate). Period: none stated.

## gsq/qped

- Page: <https://geoscience.data.qld.gov.au/dataset/ds000005>: 403 (blocked).
- Publisher's catalogue entry: <https://www.data.qld.gov.au/api/3/action/package_show?id=ds000005> (organisation "Geological Survey of Queensland")
  - "2017 Database extract containing geological, geophysical, and geochemical data relating to Queensland’s sedimentary basins derived from the drilling of petroleum wells, coal seam gas wells 'CSG', and stratigraphic bores."
  - "license_id": "CC-BY-4.0", "license_title": "Creative Commons Attribution 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/"
- Extent: State of Queensland (approximate). Period: 2017 (the extract).

## Not recorded (Canada and leftovers)

- NRCan GDR: gdr.agg.nrcan.gc.ca fails TLS (curl exit 60). Its successor <https://geophysical-data.canada.ca/Portal/Search> answers, under the Open Government Licence – Canada with citation and notification conditions, but holds aeromagnetic, gravity, radiometric and EM data: no kind in the vocabulary (E14's `potential-fields` want). Held back.
- AOGCC: 403 (blocked) at <https://www.commerce.alaska.gov/web/aogcc/data>.
- BRGM InfoTerre: connection refused.
- CNSOER Data Management Centre (<https://cnsopbdigitaldata.ca/geoviewer/dmc>, account by application, no licence stated): held back to stay within six `unknown` records.

## pasa/national-petroleum-exploration-database

- Page: <https://www.petroleumagencysa.com/introduction/>
  - "Petroleum Agency SA is responsible for the archive and management of the national hydrocarbon exploration database on behalf of the State. It has digitised, indexed and archived all of the data and reports resulting from the drilling of more than 300 offshore and some 200 onshore boreholes."
  - "more than 300 000 line km’s of 2D and 40 000 km² of 3D seismic data"
- Licence: <https://www.petroleumagencysa.com/obtain-our-technical-data/>
  - "All interested parties, who requires access to data, needs to sign a Confidentiality Agreement (CA) ... Data belongs to the State and ownership of the data is not transferred when purchased. Data purchased from the Agency may not be sold. ... Data is not permitted to be supplied to any third party without written authorization from the Agency."
- Kinds: <https://www.petroleumagencysa.com/dataset-standard-format/> ("Well completion report ... Cores Samples ... Geophysical well logs-T-Lis, D-Lis, Las ... Seismic 2D/3D data Field/Raw Data-SEGD Processed Data-SEGY ... Geochemical Data Source Rock Information").
- Extent: South Africa with offshore (approximate). Period: none stated for the database.

## namcor/exploration-production-data

- Page: <https://www.namcor.com.na/technical-data/>
  - "NAMCOR is the custodian of all the Namibian Exploration and Production data; therefore, it is NAMCOR’s responsibility to provide this data to potential investors."
  - "a core and drill cuttings storage facility in which the rock samples retrieved during petroleum exploration in this country from 1960 to date are stored for use by those carrying out exploration activities. This data includes all seismic data, well data, engineering well reports, other exploration reports, and aeromagnetic as well as gravity data"
- Sales: <https://www.namcor.com.na/data-sales/> ("we are offering in-house Exploration & Production data to potential investors and operators in Namibia at discounted prices.")
- Licence: none published. Recorded `unknown`.
- Extent: Namibia with offshore (approximate). Period: 1960 to date (the sample archive).

## eug/national-data-repository

- Page: <https://eug.petroleum.gov.eg/> (redirects to the login page; about page <https://eug.petroleum.gov.eg/dp/jsp/new_live/pre_about_us.jsp>)
  - "Egypt Upstream Gateway (EUG) is the country's first digital platform for the upstream sector, launched by the Egyptian Ministry of Petroleum in collaboration with SLB in February 2021."
  - Home counters: "National Data Repository - NDR ... 16981 Wells ... 465 Seismic 3D ... 658 Seismic 2D ... 106 Gravity/Magnetic"
- Tiers: <https://eug.petroleum.gov.eg/dp/jsp/new_live/pre_tiers.jsp> ("BRONZE $ 35K SILVER $ 100K GOLD $ 150K PLATINUM $ 250K ... Discount on data and derivatives licensing")
- Licence: none published. Recorded `unknown`.
- Extent: Egypt with offshore (approximate). Period: none stated.

## prime/national-oil-gas-database

- Page: <https://prime.energy.gov.il/en/prime.html> (Angular application; text from its static assets)
  - "Here you can find data and information on E&P activity for oil and gas onshore and offshore Israel." "Materials related to active petroleum rights are subject to confidentiality restrictions."
  - GIS: "A map showing various data layers including well, seismic, gravity and magnetic data and active licensese and leases"
- Licence: <https://prime.energy.gov.il/assets/static/pages/termsofuse/termsofuse_en.html> (browser user agent; a plain one gets an error page)
  - "copyrights for government offices' publications, including those published on this site, are the property of The State of Israel. ... The user is permitted to make "fair use" of the protected material, according to law. Fair use includes reasonable quotation of the protected material. In making a quotation, the user must state the source of quoted material"
- www.gov.il Ministry of Energy pages: 403 (blocked).
- Extent: Israel with offshore (approximate). Period: none stated.

## Not recorded (Africa and Middle East)

- Nigeria NUPRC: names a National Data Repository but has no data page or terms; the NDR Regulations PDF is 404 and ndr.nuprc.gov.ng does not resolve.
- Ghana Petroleum Commission: 406 to a plain user agent; no data page found with a browser one.
- Oman MEM: JavaScript-only site, no data page found.
- Namibia MME / Geological Survey of Namibia, Tanzania TPDC and PURA, Morocco ONHYM: unreachable. Kenya National Oil: "Account Suspended". Senegal PETROSEN: maintenance page. Uganda PAU, Mozambique INP: no data page.
- Held back: Council for Geoscience coal and core borehole headers (ZA, licence not stated, no new country); Saudi Geological Survey National Geological Database (licence not stated, minerals); Israel Water Authority borehole depths (CC BY, groundwater).

## dgh/national-data-repository

- Page: <https://www.ndrdgh.gov.in/NDR/> (the bare host redirects here)
  - "National Data Repository (NDR) is an integrated data repository of Exploration and Production (E&P) data of Indian sedimentary basins."
  - "Online portal (Team Work Space-TWS) showcasing E&P data of 26 Indian Sedimentary Basins along with capability for online data viewing, selecting and ordering"
  - <https://www.ndrdgh.gov.in/NDR/?page_id=1153>: "data storage capacity of 200 TB to store processed data & 720TB robotic tape library to store raw data"
- Licence: <https://www.ndrdgh.gov.in/NDR/pdf/data_policy.pdf>
  - "5.2.5 No resale of data is permitted by the entity with whom the data has been shared under the policy."
  - <https://www.ndrdgh.gov.in/NDR/?page_id=11708>: "Confidentiality agreement is required to be filled out, signed and a soft copy is to be sent ... for data purchase only"
- Extent: India with offshore (approximate). Period: none stated (the service "was launched for public on 28th July 2017").

## esdm/migas-data-repository

- Page: <https://datamigas.esdm.go.id/home>
  - "Digital Well Log 169.875 records", "2D Seismic Processed Digital Data 386.597 records", "3D Seismic Processed Digital Data 49.253 records", "Well Sample and Well Core Sample 60.610 box"; "Diperbarui pada: 30 September 2026"
- Licence: <https://datamigas.esdm.go.id/docsviewer/DocumentView.aspx?filename=termandco> (Edaran Nomor 2.E/03/SJD.2/2020)
  - "Anggota dan Non Anggota wajib bertanggungjawab dan menjamin bahwa dalam pemanfaatan “Data dan Informasi” akan menjaga kerahasiaannya dan tidak akan mengungkapkan atau membocorkannya kepada siapapun yang tidak berhak."
  - "“Data dan Informasi” dan produk turunannya adalah milik Negara Republik Indonesia dan digunakan hanya untuk kepentingan internal Anggota dan Non Anggota dan tidak boleh dikomersialisasikan kepada siapapun tanpa persetujuan dari Pusdatin ESDM."
- Extent: Indonesia with offshore (approximate). Period: none stated.
- migas.esdm.go.id timed out; geologi.esdm.go.id did not resolve.

## jamstec/seismic-survey-database

- Page: <https://www.jamstec.go.jp/obsmcs_db/e/>
  - "Categories of accessible data are Multi-Channel Seismic reflection data (MCS), refraction and wide-angle seismic reflection data by Ocean Bottom Seismograph." "All the MCS and OBS data are available for academic use via the data request form."
- Licence: <https://www.jamstec.go.jp/obsmcs_db/e/policy.html>
  - "You can freely view the information on JAMSTEC Seismic Survey DB Site, but cannot provide them for any other people. ... You can use the requested data for academic and educational purposes. You cannot use the data for commercial purposes basically."
  - DataCite 10.17596/0002069: rights "Site policy and data policy"; issued 2004; no geoLocations.
- Period: <https://www.jamstec.go.jp/obsmcs_db/e/survey/db/list_cruise.json>: first "KR97-02_Leg4" "period": {"sdate": "1997/05/02", "edate": "1997/05/09"}; latest edate "2025/10/21" (KM25-10C).
- Extent: none stated (named survey areas only).

## kigam/marine-geological-map-korea-strait

- Page: <https://data.kigam.re.kr/data/a7dd595f-4d9b-49a4-845e-289dc1416f52>
  - "데이터명 수치해저지질도_25만 축척_한국해협 주제분류 석유해저 지도자료 해저지질도 ... 축척 1:250,000 발간일 1990-12-31 발행기관 한국동력자원연구소"
  - "Location POLYGON ((130.000000 34.500000, 129.000000 34.500000, 129.000000 35.500000, 130.000000 35.500000, 130.000000 34.500000))"
  - License link `http://creativecommons.org/licenses/by-nc/4.0/`; "이 데이터의 저작권은한국지질자원연구원에게 있습니다."
  - Request form: "Application for use is available after logging in. If you are not a member, please sign up."
- Period: 1990-12-31 (publication). Extent: the stated polygon.
- Not used: the agent's first find (수치연안해저지질도 1집, Gangneung–Samcheok, CC BY-NC-ND) states no location; the SEG-Y item PA-108 answered HTTP 500.

## Not recorded (Asia)

- Kochi Core Center: 503 (emergency maintenance). JAMSTEC J-CORES / SIO7: connection reset. GSJ gbank: every page "メンテナンス中"; GSJ's terms are CC BY 4.0 compatible, a strong retry. JOGMEC data, PETRONAS MPM: no DNS. data.gov.in: no connection. Philippines DOE PECR: soft 404.

## gsmma/hydrogeological-drilling-database, gsmma/sw-offshore-seismic-lines-2008-2011, gsmma/sw-offshore-core-stations-2008-2011, cpc/onshore-well-locations

- Pages: <https://data.gov.tw/dataset/16799>, <https://data.gov.tw/dataset/32556>, <https://data.gov.tw/dataset/32564>, <https://data.gov.tw/dataset/62919>; metadata <https://data.gov.tw/api/v2/rest/dataset/{id}>
  - 16799: "地質鑽井基本資料、鑽探岩心紀錄、井測紀錄 1.地質鑽井基本資料(包括TWD97_X坐標、TWD97_Y坐標、井址) 2.地質鑽井岩心紀錄(包括井名、井號、深度、岩性判釋紀錄) 3.地質鑽井地物井測紀錄(包括自然電位、16吋電阻、64吋電阻、自然伽瑪)"; "授權方式 政府資料開放授權條款-第1版 計費方式 免費"
  - 32556: "天然氣水合物資源潛能調查2D、3D反射震測測線"; "coverageStartedDate": "2008-01-01", "coverageEndedDate": "2011-12-31"
  - 32564: "天然氣水合物資源潛能調查岩心採樣站"; "coverageStartedDate": "2008-01-01", "coverageEndedDate": "2011-12-31"
  - 62919: "提供探採研究所收集相關台灣陸域鑽井位置資訊，以WGS84為標準的座標系統，度為單位"; "notes": "授權說明網址:https://data.gov.tw/license"
  - spatialCoverage is empty on all four.
- Licence: <https://data.gov.tw/en/license>: "The Data Providing Organization grants User a perpetual, worldwide, non-exclusive, irrevocable, royalty-free copyright license to reproduce, distribute ... for any purpose" and "The License is compatible with the Creative Commons Attribution License 4.0 International."
- Downloads: www.gsmma.gov.tw answered a Cloudflare challenge (403); www3.cpc.com.tw timed out. Metadata hosts answered.
- Extent: Taiwan (approximate) for the island-wide sets; none for the offshore surveys.
