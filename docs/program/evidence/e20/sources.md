# E20 sources: the retry, and what the publishers state (read 2026-10-23)

Every page below was opened from the lane host on 2026-10-23 between 13:25 and 13:40 UTC with
curl (browser user agent). Status codes are the final answer after redirects. Records state
publisher facts only; no level, checksum or verification word is written into a record.

## Retry hosts (charter design 2, in order)

| Host | Address opened | Answer | Result |
|---|---|---|---|
| NRCan GDR | https://gdr.agg.nrcan.gc.ca/gdrdap/dap/search-eng.php | TLS failure (curl exit 60), 13:25 UTC | old host refused; successor answers |
| NRCan Geophysical Data (successor) | https://geophysical-data.canada.ca/Portal/Search | 200, 13:25 UTC | answered: `nrcan/canadian-airborne-geophysical-data-base` |
| BRGM InfoTerre | https://infoterre.brgm.fr/ (also /rechercher/default.htm, ficheinfoterre.brgm.fr) | connection refused (curl exit 7), 13:25 and 13:34 UTC | refused; no record (www.brgm.fr answers 200) |
| AOGCC | https://www.commerce.alaska.gov/web/aogcc/data | 403, 13:25 and 13:34 UTC | refused (blocked); no record |
| CNSOER DMC | https://cnsopbdigitaldata.ca/geoviewer/dmc | 200, 13:25 UTC | answered: `cnsoer/data-management-centre` |
| LBEG | https://www.lbeg.niedersachsen.de/ | 200, 13:25 UTC | answered: `lbeg/tunb3d-ni`, `lbeg/tunb-velo-2-0-ni` |
| Kochi Core Center | https://www.kochi-core.jp/en/ | 503, 13:25 UTC; http://www.kochi-core.jp/ redirects to a maintenance page | refused; no record |
| GSJ gbank | https://gbank.gsj.jp/ (also /gravdb/, /aeromag/, /geonavi/) | 200 with the page "メンテナンス中" (under maintenance), 13:25 UTC | refused (maintenance page, no data); no record |
| JAMSTEC J-CORES | https://sio7.jamstec.go.jp/j-cores.data/ | connection reset (curl exit 35), 13:28 UTC; https://www.jamstec.go.jp/j-cores/ answers 404 | refused; no record |
| SEG-hosted sets (SEAM, Stratton 3D, Viking Graben) | https://wiki.seg.org/wiki/Open_data, /wiki/SEAM, /wiki/Stratton_3D_survey | 403, 13:25 and 13:30 UTC | refused (blocked); no record |

Kochi Core Center maintenance notice (http://www.kochi-core.jp/, Shift_JIS):
"当ホームページで使用しているソフトウェアにおけるPHPの脆弱性の対応のため、緊急メンテナンスを実施しております。 ... 再開の見込みにつきましては、現在、未定となっております。"
(emergency maintenance for a PHP vulnerability; no date for reopening).

## nrcan/canadian-airborne-geophysical-data-base

- Page: <https://geophysical-data.canada.ca/Portal/Search> (title "Natural Resources Canada - Geological Survey of Canada - Geophysical Data")
- Terms (same page, terms-and-conditions dialog):
  - "The data on this site have been posted with the intent that they be readily available for commercial, personal and public use and may be reproduced, in part or in whole and by any means, without charge or further permission from Natural Resources Canada. However, please ensure the following: These terms and conditions remain with the data at all times. The citation appropriate to the data type appears on any publication of the data (see below). Notification of any publication of the data is provided to the appropriate contact (see below). See the Open Government Licence - Canada for more information."
  - "Aeromagnetic, Airborne Electromagnetic, Gravity and Radiometric Survey / Compilation Data 2024, Canadian Airborne Geophysical Data Base, Airborne Geophysics Section, Geological Survey of Canada, Lands and Minerals Sector, Natural Resources Canada Contact: infogdc-infocdg@nrcan-rncan.gc.ca"
  - "Gravity Data (Geodetic Survey): 2024, Canadian Geodetic Survey, Surveyor General Branch, Lands and Minerals Sector, Natural Resources Canada"
- Extent: search by Canada, province, NTS sheet or drawn area; bbox is Canada (approximate). Period: none stated.

## cnsoer/data-management-centre

- Page: <https://cnsopbdigitaldata.ca/geoviewer/dmc> ("Login Here or Apply for an Account"; "Content © CNSOER 2025")
- Application: <https://cnsopbdigitaldata.ca/ixplor-admin/dmc/apply>
  - "Complete this application form to request access to the Canada-Nova Scotia Offshore Energy Regulator (CNSOER) Data Management Centre (DMC), to access non-confidential digital well and geological data and exclusive seismic data."
  - "The user named above ("DMC User") agrees to comply with the terms of the Exclusive Seismic Data - Data Access & Confidentiality Agreement (the "Agreement") as it pertains to the disclosure of digital exclusive seismic data."
  - "The CNSOER will monitor the data accessed by each DMC user. This information will be made available to the data owners"
  - "Your application will be reviewed, and you will be notified by email"
- Public data summary: <https://cnsopbdigitaldata.ca/geoviewer/dmc/public/query/0>: "The IMC contains physical files (Well and G & G) as well as physical samples." Listings of conventional core, sidewall core, micropaleontology, nannofossil and palynology slides, thin sections, cuttings and fluids.
- Licence: none stated for the data; recorded `unknown`. Period: none stated.

## lbeg/tunb3d-ni

- Page: <https://www.lbeg.niedersachsen.de/startseite/geologie/neu_3d_modelle_des_untergrundes/geologische_ubersichtsmodelle/tieferer_untergrund_norddeutsches_becken_tunb3d_ni/tieferer-untergrund-norddeutsches-becken-fur-niedersachsen-und-bremen-tunb3d-ni-2022-206774.html>
  - "Das Übersichtsmodell TUNB3D-NI ... wurde durch das LBEG von 2014 bis 2020 im Rahmen eines Verbundprojektes mit der BGR ... erstellt. Nach Abschluss des Projektes wurden am LBEG weitere Überarbeitungen durchgeführt, die in der aktuellen Modellversion vom März 2022 münden."
  - "Als Ergebnis wurden nahezu flächendeckend für ganz Niedersachsen 13 Basisflächen lithostratigraphischer Einheiten von Zechstein bis Tertiär modelliert. ... 1592 horizontübergreifende Störungen ..., 2091 senkrechte Störungsversätze an der Basis Zechstein sowie 130 Salzstrukturen"
  - "Zugänglich ist das Modell TUNB3D-NI über den NIBIS® KARTENSERVER als 3D PDF. ... Auf Anfrage wird das Modell auch im GOCAD-ts-Format oder als Esri Multipatch bereitgestellt." "Vertrieb der Modelldaten (unentgeltlich)"
- Citation: <https://www.lbeg.niedersachsen.de/download/183313/Zitierweise_Modell_und_Abschlussbericht.pdf> ("3D-Modell: LBEG (2022): Geologisches 3D-Modell Tieferer Untergrund Norddeutsches Becken für Niedersachsen und Bremen (TUNB3D-NI), ggf. Kachel ... – NIBIS® Kartenserver, Landesamt für Bergbau, Energie und Geologie (LBEG), Hannover"); report DOI 10.48476/tunb3d-ni.
- Licence: <https://nibis.lbeg.de/cardomap3/content.aspx?method=CopyRight,UsageConstraints,ApplicationContent>
  - "Die im NIBIS-Kartenserver bereitgestellten Daten (offene Daten) können unter den Bedingungen der Lizenz „Creative Commons“ (CC-BY 4.0)“ genutzt werden."
  - "Das Urheberrecht für die angezeigten, zum Download bereitgestellten oder druckbaren Daten verbleibt bei den jeweils (nach Thema unterschiedlich) im Copyright oder in den Metadaten benannten Rechteinhabern."
- Extent: Lower Saxony and Bremen (approximate). Period: 2014 to March 2022 (construction and release), as quoted.

## lbeg/tunb-velo-2-0-ni

- Page: <https://www.lbeg.niedersachsen.de/startseite/geologie/3d_modelle_des_untergrundes/geologische_ubersichtsmodelle/geschwindigkeitsmodell_tunb_velo_2_0_ni_2026/geschwindigkeitsmodell-des-norddeutschen-beckens-fur-niedersachsen-und-bremen-tunb-velo-2-0-ni-2026-250388.html>
  - "Am LBEG wurden für Niedersachsen und Bremen regionale Intervallgeschwindigkeiten von der Basis Zechstein bis zur Geländeoberkante modelliert. In das Modell flossen 14 lithostratigraphische Horizonte sowie Salzstrukturen und Störungen ein, die überwiegend aus dem Modell TUNB3D-NI ... stammen."
  - "für Südniedersachsen und den Raum Osnabrück aufgrund unzureichender Datengrundlagen kein Modell erstellt werden konnte"
  - "eine wichtige Grundlage für ... die Zeit-Tiefen-Umwandlung seismischer Daten"
  - "Auf Anfrage wird das Modell auch im Aspen SKUA®-vo-Format (Intervall- und Durchschnittgeschwindigkeiten) und im txt-Format bereitgestellt." "Vertrieb der Modelldaten (unentgeltlich)"
- Licence: the NIBIS Kartenserver terms above (CC BY 4.0). Report DOI 10.48476/geober_56_2026.
- Extent: Lower Saxony and Bremen without the south and Osnabrück (approximate). Period: none beyond "2026" in the title; none written.

## Purchase records: the publishers' sentences (charter design 3)

- **pasa/national-petroleum-exploration-database**: <https://www.petroleumagencysa.com/obtain-our-technical-data/> (200)
  - "The purchase of data constitutes a license to use the data for a maximum period of 10 years. The actual term of the agreement will depend on the amount of data and the extent of the area under review."
  - "All data purchased under the DCDUA plus any Reprocessed Data needs to be returned at termination of the contract."
  - "The supply of draft publications to the Agency for comments and review prior to publication."
  - "Foreign institutions will be charged 10% of the commercial value/catalogue prices. Foreign institutions will be charged 5% of the commercial value/catalogue price if a South African institution/student/academic or student is involved in the study project."
  - Replaces the E19 wording in `licence.terms.stated`; `duration` now the publisher's "a maximum period of 10 years".
- **dgh/national-data-repository**: <https://www.ndrdgh.gov.in/NDR/pdf/data_policy.pdf> (200, 1,719,185 bytes, "Published on 17.05.2017")
  - 5.2.5: "No resale of data is permitted by the entity with whom the data has been shared under the policy. Copy of the report generated as a result of value addition by the entity after getting data from NDR shall be submitted to NDR as per the defined timelines."
  - 5.3.4: "The institute must share the study reports with DGH free of cost within three months of completion of project."
  - No licence duration and no review before publication stated; `terms` carries `stated` only.
- **namcor/exploration-production-data**: <https://www.namcor.com.na/technical-data/> and <https://www.namcor.com.na/data-sales/> (200). No terms of use, licence or duration stated ("we are offering in-house Exploration & Production data to potential investors and operators in Namibia at discounted prices"). No `terms` written; the record's licence stays "Not stated".
- **beg/stratton-3d**: <https://store.beg.utexas.edu/publications/seminars-and-workshops/sw0003> (200). The store page states only "(Digital Version) ... $40.00" and the publication details; no terms or licence link. No `terms` written.

## Origin-dead issues (charter design 4) and DGH

- **#20 eug/national-data-repository**: <https://eug.petroleum.gov.eg/> answered 200 (redirect to `/dp/jsp/new_live/PleaseLogin.jsp?redirected=true`), 13:25 UTC. Nothing written; the next verify run closes the issue.
- **dgh/national-data-repository** (L0 after the E19 verify run, supervisor note): <https://www.ndrdgh.gov.in/NDR/> answered 200, 13:28 UTC. Nothing written for design 4.
- **#17 geus/deep-subsurface-data**: <https://eng.geus.dk/products-services-facilities/data-and-maps/subsurface-data-denmark> answered 404 (IIS "HTTP Error 404. The requested resource is not found."), twice at 13:26 UTC; <https://eng.geus.dk/> and <https://www.geus.dk/> answer 404 too. <https://data.geus.dk/geusmap/?mapname=oil_and_gas&lang=en> and the terms PDF answer 200. No status notice found. One `notes` sentence written; issue left open.
