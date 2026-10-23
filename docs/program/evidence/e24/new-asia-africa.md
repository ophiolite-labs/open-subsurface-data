# E24 new records: Asia and Africa group (read 2026-10-23, 15:15 to 15:28 UTC)

Every page below was opened from the lane host on 2026-10-23 with curl (browser user agent), a few
requests per host. Status codes are the final answer after redirects. Records state publisher facts
only; no level, checksum or verification word is written into a record. `osd verify` was not run.

## Hosts tried

| Host | Address opened | Answer | Result |
|---|---|---|---|
| Angola ANPG | https://www.anpg.co.ao/ (SPA), /robots.txt, /api/content-blocks?page_key=iona, data-packages, data, production-history, terms; /api/production-historical | 200, 15:15 to 15:17 UTC | answered: `anpg/historico-de-producao` (data packages "Sob consulta" not recorded: no terms beyond the site's) |
| ANPG legacy PDF | https://dev.anpg.co.ao/uploads/legacy-imports/5edfd21aee5747e79d68c1b3b06167a46ae12241.pdf | 403, 15:16 UTC | refused; noted in the record |
| Côte d'Ivoire PETROCI VDR | https://www.petrocivirtualdataroom.ci/, /resquest-form.html, /abidjan-margin.html, /diagram.html, process PDF | 200, 15:18 to 15:19 UTC; /robots.txt 302 to /404.html | answered: `petroci/virtual-data-room` |
| PETROCI block PDFs | https://www.petroci.ci/virtual_data_room/fichiers_uploades/files/abidjan%20margin/abidjan-margin-block_500.pdf | 302 to /page_erreur_404.php, 15:19 UTC; www.petroci.ci/robots.txt 302 | dead links; no listing |
| Malaysia MPM / myPROdata | https://www.petronas.com/mpm/data-centre, /myprodata/, /myprodata/subscriptions, /myprodata/faq | 200, 15:18 to 15:20 UTC | answered: `petronas/myprodata` |
| mpm.petronas.com | https://mpm.petronas.com/ | DNS: could not resolve host (curl exit 6), 15:18 UTC | refused; used www.petronas.com/mpm |
| Thailand DMF | https://dmf.go.th/, /public/, /public/createpetroleum/data/index/menu/1114, /robots.txt | 200, 15:18 to 15:20 UTC | robots.txt `User-Agent: *` `Disallow: /` (and `User-agent: ClaudeBot` `Disallow: /`); treated as refused; no record. The monthly production page links xlsx reports per month from 2546 to 2569 BE, "© สงวนลิขสิทธิ์ 2566 กรมเชื้อเพลิงธรรมชาติ" |
| Thailand data.go.th | https://data.go.th/, /robots.txt, /api/3/action/package_search | 403 "Access Denied", 15:18 to 15:20 UTC | refused; no record |
| Philippines DOE | https://doe.gov.ph/ (from www), /energy-resources-development-programs, /data-and-prices/energy-statistics, /pecr | 200 (/pecr "Page Not Found"), 15:18 to 15:21 UTC | answered; no petroleum data page (energy statistics are electric power only; PECR notice links only DC2017-12-0017); no record |
| pecr.doe.gov.ph, legacy.doe.gov.ph | https://pecr.doe.gov.ph/, https://legacy.doe.gov.ph/ | DNS: could not resolve host, 15:18 and 15:27 UTC | refused; no record |
| Vietnam PVN | https://www.pvn.vn/ | 200, 15:18 UTC | answered; corporate news site, no data page; no record |
| Uganda PAU | https://www.pau.go.ug/ (SPA), /robots.txt (serves the app shell), /about-us/petroleum-data-management, /api/petroleum-data-mgt?, /api/faqs | 200, 15:18 to 15:26 UTC | answered: `pau/petroleum-data` |
| Tanzania PURA | https://www.pura.go.tz/, /robots.txt, /licencing-rounds | 200; /licencing-rounds 404, 15:18 and 15:27 UTC | answered; no data page (as in E22); no record |
| Kenya NOCK | https://www.nationaloil.co.ke/ (to nationaloil.co.ke/website_11ab3dee/), /robots.txt, /wells-drilled/, /pdf/Wells__Drilled.pdf | 200, 15:18 to 15:25 UTC | answered: `nock/wells-drilled` |
| Senegal PETROSEN | https://www.petrosen.sn/ | 200 with "PETROSEN - Maintenance" / "Site temporairement en maintenance", 15:18 UTC | refused (maintenance page, as at 14:02 UTC); no record |
| Morocco ONHYM | https://www.onhym.com/ (to /fr), https://hydrocarbons.onhym.com/en, /en/exploration-acreage-map, robots.txt (Drupal default) | 200 with `-k` (TLS chain incomplete, as in E22), 15:18 to 15:27 UTC | answered; the only map is an ArcGIS Instant App over a FeatureServer of petroleum agreements, open acreage, cities and a structural map; no subsurface dataset; footer "2026 All rights reserved"; no record |
| ONHYM ArcGIS | onhym.maps.arcgis.com item 0355fea6... and webmap 1bb744d9...; services8.arcgis.com .../PETROLEUMAGREEMENTS_RECONNAISSANCE_CONTRACTS_WFL1/FeatureServer/3 | 200, 15:27 to 15:28 UTC; services8 robots.txt 403 "Invalid URL" | layers are licence areas and a structural (geological units) map; not recorded |

Redistribution budget for `unknown`: one used (`nock/wells-drilled`). Following existing records
(`gy-mnr/well-activities` "All Rights Reserved" is forbidden; `cnsoer/directory-of-offshore-wells`
bare "©" is unknown), pages whose terms or footer say "all rights reserved" are recorded as forbidden.

## anpg/historico-de-producao

- Page: <https://www.anpg.co.ao/producao/historico> (script-rendered; route `/producao/historico` in the site bundle; content from `/api/content-blocks?page_key=production-history`)
  - "Evolução Histórica (1978-2025)", "Produção de petróleo bruto em milhares de barris por dia"
  - "Produção Mensal (2024-2025)", "Dados mensais detalhados de petróleo e gás associado"
  - Stats: "Pico Histórico" "1.875" "Mil bbl/dia (2008)"; "Actual (Jun 2025)" "1.003"
  - Reports block: "Histórico de Produção 1956-2020", "Relatório consolidado da produção petrolífera nacional desde 1956." (URL malformed: "https://webgis.anpg.co.aohttps://dev.anpg.co.ao/uploads/legacy-imports/...pdf"; the dev host answered 403)
- Data: <https://www.anpg.co.ao/api/production-historical?limit=100>: `"total":71`, first `{"year":1955,"oil_bopd":"5.00","source":"ANPG - Direcção de Produção","status":"published","published_at":"2026-08-04 10:26:15"}`, last `{"year":2025,"oil_bopd":"1036763.00"}`.
- Licence: `/api/content-blocks?page_key=terms` ("Janeiro 2025"): "Este website destina-se exclusivamente a fins informativos sobre as actividades da ANPG e oportunidades de investimento no sector petrolífero angolano."; "Todos os conteúdos deste website, incluindo textos, imagens, logótipos, gráficos e software, são propriedade da ANPG ou dos seus licenciadores." Footer string in the bundle: "© 2025 ANPG. Todos os direitos reservados." → forbidden.
- robots.txt: `User-agent: *` `Allow: /`. No file listing (JSON API only): no manifest_url.
- Extent: Angola with offshore (approximate). Period: 1955 to 2025 from the API rows.

## petroci/virtual-data-room

- Page: <https://www.petrocivirtualdataroom.ci/> (title "Petroleum Geology | Petroci Virtual Data Room")
  - "Access Virtual Data Room using given credentials to get full insights into blocks you are entitled to"
  - Request form: "To request for data review, please complete the following form. One of our representatives will contact you shortly for scheduling the data review." "Data review request type * Browse and preview data Download Data"
  - Abidjan Margin page: "AREA BLOCKS SIZE SEISMIC DATA GEOLOGY DATA 2D (km) 3D (Sq.km) WELLS LEADS/PLAYS"; e.g. "CI-526 download 2979 1409 2979"; "CI-710 ... Ivoire-1X: oil sampled"
  - Contact: "+225 27 20 202 500 infosVDRr@petroci.ci"
- Terms: process chart <https://www.petrocivirtualdataroom.ci/fichiers_uploades/files/access%20procedure/Processus_Commercial_VDR_PETROCI_CLIENT.pdf> (27,063 bytes): "Send confidentiality agreement", "Sign agreement, execute payment and send receipt", "Visualize limited images files", "Request data for download", "Send licence agreement and data pricing", "Sign licence agreement and execute payment", "Download data and analyse it". Footer: "© Copyright 2023 (Petroci Virtual Data Room) All rights reserved" → forbidden; access purchase.
- Listing: block PDFs on www.petroci.ci redirect to a 404 page; robots.txt on both hosts redirects to an error page. No manifest_url.
- Extent: Ivorian basin and offshore (approximate). Period: none stated.

## petronas/myprodata

- Page: <https://www.petronas.com/myprodata/> (title "PETRONAS myPROdata | Home | PETRONAS myPROdata"), linked from <https://www.petronas.com/mpm/data-centre>
  - "PETRONAS myPROdata is a web-based platform that provides greater access and transparency to Malaysia's E&P data."
  - "Over 1,100 TB Data to explore Subsurface Data 700,000 sqkm 3D Seismic 292,000 sqkm Full Tensor Gradiometry 495,000 line-km 2D seismic 6,000 Wells and well logs 83,000 Technical reports"
  - Subscriptions: "Standard Full Access of Malaysia E&P Technical Data in Open Areas RM68,000*"; "Premium Full Access of Malaysia E&P Technical Data RM89,000*"; "Basic ... Available for a period of 3 months - free access."
- Terms (FAQ <https://www.petronas.com/myprodata/faq>): "users must agree with the terms and conditions outlined in the End User Agreement." "It stipulates the terms and conditions in relation to data access policy, subscription model, subscription fees, data confidentiality and acknowledgement of PETRONAS as the data and/or product owner." "Basic – three months only Standard: Minimum – one year Maximum – five years Premium: Minimum – one year Maximum – five years". "Additional data over 5TB, subscribers will be charged with an additional fee of approximately USD 0.12 per gigabyte". Footer "All rights reserved." → forbidden; access purchase.
- No listing (data behind login). Extent: Malaysia with offshore (approximate). Period: none stated.

## pau/petroleum-data

- Page: <https://www.pau.go.ug/about-us/petroleum-data-management> (title "PETROLEUM DATA MANAGEMENT - Petroleum Authority of Uganda"); text from <https://www.pau.go.ug/api/petroleum-data-mgt?> (WordPress post 495, modified 2026-06-01)
  - "The PAU manages all the data generated from oil and gas activities in Uganda and assesses and responds to requests for data."
  - "The data is of various categories including Geological and Geophysical (G&G) subsurface data essentially wells and seismic data, facilities data, Health, Safety, and Environment (HSE) data, Costs data, National Content data, Geospatial data (GIS) data"
  - "A Tier Three Data Center A Modern Core Store Seismic Data Tape storage and Transcription and facility"
  - "Enhanced capacity to currently manage over sixty (60) Terabytes of electronic oil and gas digital data and thousands of physical data (geo samples)."
  - "The development of the National Petroleum Data Repository."
- Licence: none for the data; footer "Copyright ©2025 Petroleum Authority of Uganda. All rights reserved." → forbidden; access request. FAQs (/api/faqs) say nothing on data access.
- No listing. Extent: Uganda (approximate), Albertine Graben. Period: none stated.

## nock/wells-drilled

- Page: <https://nationaloil.co.ke/website_11ab3dee/wells-drilled/> (title "Wells Drilled – National Oil Corporation of Kenya")
  - "Wells Drilled Click here to have a clearer view of Wells drilled in Kenya Document"; link `../pdf/Wells__Drilled.pdf`
- File: <https://nationaloil.co.ke/website_11ab3dee/pdf/Wells__Drilled.pdf>: 200, application/pdf, 266,101 bytes, last-modified Thu, 09 Dec 2021; 2 pages, Creator "Microsoft® Excel® 2013", CreationDate 30 Jun 2017
  - Header: "WELL YEAR OPERATOR WELL TYPE BLOCK BASIN MDRT (M) ENCOUNTERED STATRIGRAPHIC LEVEL AT TOTAL DEPTH WELL STATUS"
  - "Meri-1 1961 BP/Shell Exploration 3B Anza 1937.6 Dry hole Early Tert., Miocene P&A"; "Ngamia 1/1A 2012 Tullow Kenya Exploration 10BB Tert. Rift 2232 Oil discovery"
- Licence: none stated; footer "© 2026 National Oil Corporation of Kenya, Energizing Kenya" → unknown (budget 1 of 2).
- robots.txt (hestiacp): `User-agent: *` `Crawl-delay: 10` (no Disallow), so the page and /pdf/ are allowed.
- Listing shape: HTML page linking one PDF; sample below.
- Extent: Kenya (approximate). Period: 1960 to 2017 from the YEAR column.

## Proposed samples.yaml lines

```
nock/wells-drilled: ["*/pdf/Wells__Drilled.pdf"]   # page links one PDF table: Wells__Drilled.pdf, 266101 bytes
```
