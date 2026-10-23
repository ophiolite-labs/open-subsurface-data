# E24 new records: group "europe" (read 2026-10-23, 15:15 to 15:26 UTC)

Every page below was opened from the lane host on 2026-10-23 with curl (browser user agent), at the
UTC times given. Status codes are the final answer after redirects. Records state publisher facts
only; no level, checksum or verification word is written into a record. Budget for
`redistribution: unknown` was 2; none of the four records uses it.

## Hosts tried

| Host | Address opened | Answer | Result |
|---|---|---|---|
| Croatian Hydrocarbon Agency | https://www.azu.hr/, /robots.txt, /hr-hr/data-room, /en-us/data-room | 200, 15:15 to 15:18 UTC | record `azu/data-room` (purchase) |
| Narodne novine (Croatian official gazette) | https://narodne-novine.nn.hr/clanci/sluzbeni/full/2023_05_52_872.html | 200, 15:18 UTC | the Data Room ordinance (fees, terms) |
| HEREMA (Greece) | https://www.herema.gr/, http://www.herema.gr/, https://herema.gr/, https://www.herema.gr/en/ | timeout (curl exit 28) at 15:15, 15:16, 15:16 and 15:22 UTC | refused; no record |
| NAMR (Romania) | https://www.namr.ro/, http://www.namr.ro/ | 503 "Verifying your browser..." (script challenge), 15:15 and 15:22 UTC | refused (blocked); no record |
| MBFSZ (Hungary, old hosts) | https://map.mbfsz.gov.hu/ (TLS name mismatch, curl exit 60); https://mbfsz.gov.hu/, https://www.mbfsz.gov.hu/ (timeout) | 15:15 to 15:17 UTC | gone; successor SZTFH answers |
| SZTFH / HuGeo (Hungary) | https://sztfh.hu/ (+robots.txt, /tevekenysegek/foldtani-tevekenyseg/); https://hugeo.hu/hu (+robots.txt and four Adatbank pages, one PDF); https://map.hugeo.hu/robots.txt, /szeizmika/ | 200, 15:17 to 15:21 UTC | record `sztfh/seismic-and-well-log-databases` (purchase); map.hugeo.hu robots disallows /arcgis/ |
| Czech Geological Survey, www.geology.cz | https://www.geology.cz/, /robots.txt (timeout 25 s); http://www.geology.cz/ | timeout 15:15 to 15:16 UTC; http answers 200 with a refresh to https://cgs.gov.cz, 15:18 UTC | moved to cgs.gov.cz |
| Czech Geological Survey, cgs.gov.cz | /robots.txt, /, /mapy-a-data/data, /mapy-a-data/poskytovani-dat, /copyright, /statni-geologicka-sluzba/vytezena-loziska-ropy-a-zemniho-plynu, /statni-geologicka-sluzba/vrtna-prozkoumanost | 200, 15:18 to 15:25 UTC (Crawl-delay 10 kept) | record `cgs/vrtna-prozkoumanost` |
| ČGS ArcGIS, mapy.geology.cz | /arcgis/rest/services?f=json, /Prozkoumanost, /Geofyzika, Vrtna_prozkoumanost and seismicke_profily MapServer, layer 1 json, count and one export | 200, 15:18 to 15:26 UTC; /robots.txt 404 | listing for `cgs/vrtna-prozkoumanost` |
| ČGS open data / ATOM | https://od.geology.cz/ (403 directory listing forbidden; robots.txt 415); https://app.geology.cz/atom/atom.php?request=getfile&file=8... and /atom/datalist8.xml | 401 "Authentication required!", 15:20 UTC | the CC BY 4.0 INSPIRE seismic-profile download needs a login; no record from it |
| Bulgaria, Ministry of Energy | https://www.me.government.bg/ (+robots.txt, /pages/about-ubgur-105.html, /themes-c329.html, /themes-c305.html) | 200, 15:22 UTC | concession decisions and PDF maps only, no geofund data page; no record |
| Bulgaria, geofond.bg | https://geofond.bg/, https://www.geofond.bg/ | DNS: could not resolve, 15:22 UTC | no host; no record |
| ŠGÚDŠ (Slovakia), www.geology.sk | /, /robots.txt, /licencie-a-citacie-2/, /geoinfoportal/mapovy-portal/registre-geofondu/, .../vrty/ | 200, 15:23 to 15:24 UTC | record `sgudds/register-geotermalnych-vrtov` |
| ŠGÚDŠ ArcGIS, ags.geology.sk | /arcgis/rest/services?f=json, /Geofond, Vrty_all MapServer, layers 0 and 2 json, counts, one export | 200, 15:23 to 15:26 UTC; /robots.txt 404 | listing for `sgudds/register-geotermalnych-vrtov` |
| GeoZS (Slovenia) | https://www.geo-zs.si/ (+robots.txt, /egeologija/); https://egeologija.si/robots.txt (404) and GeoNetwork search API (404) | 200 / 404, 15:23 to 15:25 UTC | eGeologija is a script-rendered GeoNetwork catalogue; no data page found; no record |

## azu/data-room

- Page: <https://www.azu.hr/en-us/data-room> (title "Data Room | Croatian Hydrocarbon Agency"); Croatian twin /hr-hr/data-room
  - "It is a centralized and modern reference database for the assessment of hydrocarbon resources, geothermal water for energy purposes and geological structures for the storage of natural gas and the permanent disposal of carbon dioxide."
  - "The overview of the available geological, geophysical, and well data is organised in the specialist software Kingdom, in which three projects have been created: the Adriatic Sea, the Pannonian Basin and the Dinarides. All seismic (2D and 3D) and basic well data are loaded into the projects."
  - "Other well data, consisting of reports, well logs, velocity measurements, etc. are available via the Web browser in .pdf and .tif format."
  - "Interested parties are required to complete the access form indicating the objective and area of their interest. Before visiting the data room, it is necessary to sign the Data Confidentiality Agreement."
  - "All data contained in the data room are the property of the Republic of Croatia and may not be used without permission."
- Licence/terms: the page links "ORDINANCE ON ACCESS TO THE DATA ROOM AND THE USE OF DATA" to <https://narodne-novine.nn.hr/clanci/sluzbeni/full/2023_05_52_872.html> ("PRAVILNIK O PRISTUPU SOBI S PODACIMA I KORIŠTENJU PODATAKA", Zagreb, 2. svibnja 2023):
  - Art. 4(1): "Naknada za pristup sobi s podacima i pregled podataka za naftno-rudarske gospodarske subjekte i investitore [...] ugljikovodika iznosi 2.000,00 eura."
  - Art. 7: "2D seizmički izvorni podaci – naknada iznosi 10,00 eura po km 2. 2D seizmički obrađeni podaci (stck/mig) – naknada iznosi 50,00 eura po km 3. 3D seizmički izvorni podaci – naknada iznosi 500,00 eura po km 2 4. 3D seizmički obrađeni podaci – naknada iznosi 1.000,00 eura po km 2 5. Podaci o bušotinama – naknada iznosi 500,00 eura po bušotini."
  - Art. 5(6): "Primatelj odobrenja za korištenje podataka se slaže da će podatke i njihove kopije koristiti za internu upotrebu i da ih ne smije prodavati, trgovati njima, otkriti bilo kojoj trećoj strani ili na bilo koji način učiniti dostupnima." Hence `redistribution: forbidden`; no attribution rule stated.
- Extent: the three named areas (Adriatic Sea, Pannonian Basin, Dinarides); bbox is Croatia with its offshore, approximate. Period: none stated.
- Robots: azu.hr robots.txt lists only sitemaps (no Disallow). Listing: none (no files on the page); no sample.

## sztfh/seismic-and-well-log-databases

- Page: <https://hugeo.hu/hu/adatbank/geofizikai-adatbazisok/geofizikai-adatbazisok> (title "Geofizikai adatbázisok", HuGeo, "A Földtani Szolgálat és az Országos Bányakapitányság földtudományi portálja", © 2026 SZTFH)
  - "Szeizmikus adatbázis Az adatbázis Magyarország területén végzett szeizmikus 2D és 3D mérések terepi, illetve feldolgozott adatait tartalmazza kivitelezőtől, a mérés céljától függetlenül."
  - "Objektumok száma: 3D tömb, feldolgozott: 103 db 3D tömb, terepi mérés: 109 db 2D vonal: 6757 db 2D feldolgozott vonal, SEGY formátumban: 4810 db [...] Adatformátum: SEGY, SEGD, az adatbázis feltöltöttsége közel 85%-os. Fedettség: országos"
  - "Mélyfúrás-geofizikai adatbázis [...] A szénhidrogén-kutatás szempontjából informatív objektumok száma: kb. 7200, ebből 1700 digitális. [...] Adatformátum: las file. Fedettség: országos."
- Access page: <https://hugeo.hu/hu/adatbank/adattar/adattari-adatok-hozzaferhetosege/adattari-adatok-hozzaferhetosege>: "Az adatokról térítési díj ellenében papír- és digitális másolatok kérhetők [...] az adatközléssel kapcsolatos, felszámítható költségtérítés mértékét az SZTFH 11/2025. (VII. 17.) elnöki utasításának 2. melléklete szabályozza."
- Licence/terms: the linked PDF (2. melléklet a 11/2025. (VII. 17.) elnöki utasításhoz), point 7.3 (copies for a fee; 50% or full fee waiver for non-business requests), point 9 ("csak az SZTFH-val történt előzetes egyeztetés, és az SZTFH hozzájárulása esetén [...] adhatja tovább harmadik személynek") hence `redistribution: restricted`. Fee table 1. függelék: SZEIZMIKA, "Feldolgozott 2D szeizmikus vonal [...] < 1000 CDP 14 000 [...] ≥ 3000 CDP 47 000"; "Feldolgozott 3D szeizmikus mérés [...] < 1 GB 254 000 [...] ≥ 10 GB 977 000"; KAROTÁZS "LAS formátumú fájlok [...] alapdíj fúrásonként 31 000".
- Digital Data Room page (<https://hugeo.hu/hu/adatbank/adattar/digitalis-adatszoba/digitalis-adatszoba>): "Az adatszoba használata díjmentes. A kívánt adatokat a Magyar Állami Földtani, Geofizikai és Bányászati Adattáron keresztül lehet megrendelni".
- Extent: "Fedettség: országos" (national); bbox is Hungary, approximate. Period: none stated for the seismic set.
- Robots: hugeo.hu (Drupal default, `User-agent: *` disallows only /core/, /profiles/, admin paths); map.hugeo.hu `Disallow: /arcgis/`. Listing: none; no sample.

## cgs/vrtna-prozkoumanost

- Page: <https://cgs.gov.cz/statni-geologicka-sluzba/vrtna-prozkoumanost> (title "Vrtná prozkoumanost | Česká geologická služba")
  - "Česká geologická služba (ČGS) vede a spravuje databáze údajů o objektech (zásazích do zemské kůry – vrtech, studnách, kopaných sondách, pramenech atd.), které vybírá ze zpráv a posudků povinně předávaných do archivu Geofondu ČGS"
  - "Informace z databází jsou všem zájemcům poskytovány buď jako placené datové výstupy (viz. Poskytování dat) nebo si lze základní údaje o objektech prohlédnout zdarma v mapové aplikaci Vrtná prozkoumanost."
  - "Databáze pokrývá celé území ČR a obsahuje informace cca o 720 tis. objektech [...] včetně cca 620 tis. geologických vrtných profilů"
- Data directory <https://cgs.gov.cz/mapy-a-data/data> lists "Vrtná prozkoumanost ArcGIS Server služba [...] https://mapy.geology.cz/arcgis/rest/services/Prozkoumanost/Vrtna_prozkoumanost/MapServer". Service description: "Služba zpřístupňuje základní informace o vrtech a dalších dílech evidovaných v databázi geologicky dokumentovaných objektů."; copyrightText "© ČGS".
- Licence: <https://cgs.gov.cz/copyright>: "Všechny materiály pocházející z produkce České geologické služby uveřejněné na tomto webu jsou předmětem autorské ochrany. Jejich využívání nebo reprodukce je možná pouze s písemným souhlasem České geologické služby." plus a citation form for map services ("Pokud využíváte mapovou službu jako rozšiřující obsah jiné mapové aplikace, uveďte prosím citaci ve tvaru ..."); "Licence datové sady INSPIRE: Všechny datové sady jsou k dispozici ke stažení pod licencí Creative Commons BY 4.0" applies to the INSPIRE downloads, which need a login (401). Poskytování dat: "Česká geologická služba zpřístupňuje informace volně a bezplatně prostřednictvím aplikací a webových služeb. Tyto informace lze citovat ve smyslu §31 zákona [...] autorského zákona." Hence `redistribution: restricted`, `attribution: required`.
- Extent: whole Czech Republic ("celé území ČR"); service fullExtent in S-JTSK; bbox approximate. Period: none stated.
- Robots: mapy.geology.cz/robots.txt answers 404 (no rules), so the layer and its query are allowed; cgs.gov.cz robots allows the record page (Crawl-delay 10).
- Listing: ArcGIS layer <https://mapy.geology.cz/arcgis/rest/services/Prozkoumanost/Vrtna_prozkoumanost/MapServer/1?f=json>: "type": "Feature Layer", maxRecordCount 3000, count 746,789; `osd.verifier.listings.read_listing` reads it as `arcgis-layer` with one export. The export (3000 features) answered 200 with 2,669,877 bytes at 15:19 UTC.

## sgudds/register-geotermalnych-vrtov

- Page: <https://www.geology.sk/geoinfoportal/mapovy-portal/registre-geofondu/vrty/> (title "Vrty – Štátny geologický ústav Dionýza Štúra")
  - "Aplikácia „Vrty“ slúži na prehliadanie a analýzu geologických vrtov na území Slovenskej republiky. Integruje v sebe dáta z troch samostatných registrov"
  - "3. Register geotermálnych vrtov Tento register vznikol vyčlenením z registra hydrogeologických vrtov s cieľom zabezpečiť lepšiu prehľadnosť údajov a reflektovať rastúci záujem o geotermálnu energiu."
  - "Vrtné pasporty: K vybraným objektom sú priamo v mape pripojené naskenované vrtné pasporty vo formáte PDF."
  - "Spustenie aplikácie: 06/2016 Aktualizácia dát: Údaje sú aktualizované priebežne podľa potreby."
- Licence: <https://www.geology.sk/licencie-a-citacie-2/>: "Všetky údaje, ktoré sú na portáli k dispozícii na stiahnutie, podliehajú medzinárodnej licencii Creative Commons BY 4.0. [...] Pri každom použití a rozširovaní údajov ste povinní jasne uviesť pôvod: © Štátny geologický ústav Dionýza Štúra." and "Všetky poskytované dáta a informácie majú výhradne informatívny charakter." The page links https://creativecommons.org/licenses/by/4.0/.
- Extent: "na území Slovenskej republiky"; bbox approximate. Period: none stated.
- Robots: ags.geology.sk/robots.txt answers 404 (no rules); www.geology.sk robots disallows only /wp-admin/ and one plugin file.
- Listing: ArcGIS layer <https://ags.geology.sk/arcgis/rest/services/Geofond/Vrty_all/MapServer/2?f=json> ("Register geotermálnych vrtov", "type": "Feature Layer", maxRecordCount 1000, count 307); read as `arcgis-layer`. The export (all 307 features) answered 200 with 392,511 bytes at 15:24 UTC.

## Not recorded, for a later lane

- ČGS "Vytěžená ložiska ropy a zemního plynu" (<https://cgs.gov.cz/statni-geologicka-sluzba/vytezena-loziska-ropy-a-zemniho-plynu>): NZIA table of depleted Czech oil and gas fields (production totals, depths, years); an HTML table, no files.
- ČGS seismic profiles MapServer (Geofyzika/seismicke_profily, "seismických reflexních profilech [...] odměřených v letech 1971-1994"); not written: the brief asks one record per publisher.

## Proposed samples.yaml lines

```
cgs/vrtna-prozkoumanost: ["*"]   # ArcGIS layer 1: one geojson export of at most 3000 of 746,789 features (kept as partial), 2,669,877 bytes
sgudds/register-geotermalnych-vrtov: ["*"]   # ArcGIS layer 2: one geojson export, all 307 features (maxRecordCount 1000), 392,511 bytes
```
