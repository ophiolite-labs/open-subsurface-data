# E51 slice 0: licence terms of NSTA, Sodir, BOEM and BLM, read 25 Nov 2026

Authority: `docs/program/charters/E51-licences-per-country.md` design 1 and acceptance 1;
`MAP-AS-A-SHOP-family.md` R-S5. Input: `block-layers.md` beside the 25 Nov 2026 prototype.

**What is asked of each text.** We will (a) publish simplified licence outlines as vector tiles on
a public site, and (b) commit them to this public repository, whose records and outlines are CC0
1.0 (`README.md`, "Licences"). Per source: does the text allow (a), does it allow (b) under CC0,
and if not, what notice must travel with the file.

**Method.** All reads on 25 Nov 2026 from the controller, `curl -L` with a generic client name
(`Mozilla/5.0 (X11; Linux x86_64) generic-client`), into an empty directory outside the worktree;
HTML and PDF reduced to text with `python3 -I` and `pdftotext`; nothing executed. Where curl met a
bot check, WebFetch was tried, then the Internet Archive copy (capture date given). Quotes below
are verbatim from the text opened; nothing is stated from memory or from a catalogue tag unless it
says "catalogue tag". The human-check line is for a person: open the address, find the quoted
sentence, sign.

## Summary

| Source | (a) tiles on a public site | (b) commit under CC0 | Credit line (word for word where the publisher gives one) |
|---|---|---|---|
| NSTA (UK) | **Only non-commercially** | **No**: the grant is non-commercial; CC0 would hand on commercial use | "Contains information provided by the North Sea Transition Authority and/or other third parties." |
| Sodir (NO) | Yes, any purpose, with attribution and a change notice | **No** (no sub-licensing); the file may be committed under NLOD 2.0 with its notice | NLOD 2.0 default (Sodir names none): "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Norwegian Offshore Directorate" |
| BOEM (US offshore) | Yes | Yes: federal public information, "may be distributed or copied" | None prescribed; "Use of appropriate byline/photo/image credit is requested." Layer credit field: "MarineCadastre.gov"; service: "BOEM, BSEE" |
| BLM (US onshore) | Yes, citing BLM and describing changes | Yes: "None, these data are considered public domain." | "The BLM should be cited as the data source"; source field: "U.S. Department of Interior, Bureau of Land Management (BLM)" |

Consequence for the charter's order (UK, Norway, US): the United Kingdom is held (stop rule
"a source whose terms forbid redistribution of derived data"; here, the grant forbids commercial
exploitation and so forbids the CC0 commit). Inbox `e51s0.md` note 1 carries the default and the
owner action. Norway is drawable but its file is not CC0 (note 2). The United States is clear.

## United Kingdom: NSTA (North Sea Transition Authority)

- **Layer**: `https://services-eu1.arcgis.com/OZMfUznmLTnWccBc/arcgis/rest/services/UKCS%20offshore%20petroleum%20licence%20blocks%20WGS84/FeatureServer/0`
  (item `d01ebe9fe5da45b1a0bb285a7c5b7434`, owner `NSTA_GIS`); England onshore: same host,
  `England%20onshore%20petroleum%20licence%20blocks%20WGS84/FeatureServer/0`.
- **Where the layer points for its terms**: item `licenseInfo` = "NSTA Open User Licence", linked to
  `https://www.nstauthority.co.uk/footer/access-to-information/` (HTTP 200, opened 25 Nov 2026).
  That page: "The NSTA regularly makes data available in accordance with the terms of the NSTA's
  User Agreement." and "Should you wish to use the information other than in accordance with the
  User Agreement, please contact the NSTA at: correspondence@nstauthority.co.uk." Its link is the
  licence text below. The NSTA terms-and-conditions page
  (`https://www.nstauthority.co.uk/footer/terms-and-conditions/`, HTTP 200) links the words "NSTA
  Open User Licence" to the same PDF.
- **Licence text opened**: `https://www.nstauthority.co.uk/media/u51lhvio/nsta-user-agreeement-june-2023.pdf`
  (HTTP 200, 122,115 bytes, "North Sea Transition Authority User Agreement", June 2023), opened
  25 Nov 2026. Quotes:
  - "The NSTA grants you a worldwide, royalty-free, perpetual, non-exclusive right to use the
    Information subject to the conditions below."
  - "You are free to: copy, publish, distribute and transmit the Information; adapt the
    Information; exploit the Information non-commercially."
  - "You must (where you do any of the above): acknowledge the source of the Information by
    including the following attribution statement: Contains information provided by the North Sea
    Transition Authority and/or other third parties."
  - "This is an important condition of this User Agreement and if you fail to comply the rights
    granted to you under this User Agreement will end automatically."
  - "This User Agreement does not grant you any right to use the Information in a way that suggests
    any official status or that the NSTA and/or any Third Party Information Provider endorse you or
    your use of the Information."
  - Exemption: "use of the NSTA logo or any Third Party Information Provider logo".
- **The superseded text** (for the record, not the operative terms): the address in
  `block-layers.md`, `https://www.nstauthority.co.uk/media/9096/oga-open-user-licence_v3.pdf`,
  returns HTTP 404 today; the Internet Archive copy of 21 Feb 2024 ("Oil and Gas Authority Licence
  (OGA Licence)") allowed to "exploit the Information commercially and non-commercially" with the
  statement "Contains information provided by the OGA." Both NSTA pages now link the June 2023
  User Agreement, which drops commercial use.
- **Verdict**. (a) Publishing simplified outlines as tiles is copying, adapting and publishing:
  allowed, with the attribution statement, **only if our exploitation is non-commercial**. (b) A
  commit under CC0 is **not allowed**: CC0 lets anyone exploit commercially, a right NSTA does not
  grant. If committed at all, the file must travel with the attribution statement and a pointer to
  the User Agreement, and must be excluded from the repository's CC0 grant. Whether the shop and
  Ophiolite's use count as non-commercial is not ours to decide: inbox note 1.
- **Credit line, word for word**: "Contains information provided by the North Sea Transition
  Authority and/or other third parties."
- **Update frequency**: no frequency on the item or its metadata (`maintFreq` absent). NSTA's data
  FAQ (`https://www.nstauthority.co.uk/data-and-insights/about-nsta-data/faqs/`): "Many of our
  datasets update daily". Layer `lastEditDate` 2026-11-25 05:44 UTC; item modified 2026-11-25
  05:42 UTC.
- **Human check**: open the User Agreement PDF above; confirm "exploit the Information
  non-commercially" and the attribution statement. Checked by: ______ on ______.

## Norway: Sodir (Norwegian Offshore Directorate)

- **Layer**: `https://factmaps.sodir.no/api/rest/services/Factmaps/FactMapsWGS84/FeatureServer`
  layers 616 (production licences, current with geometry) and 802 (blocks). Service
  `copyrightText`: "Norwegian Offshore Directorate".
- **Sodir's statement of the licence**: `https://www.sodir.no/en/about-us/open-data/`.
  **Live page not opened**: curl HTTP 403 with a bot check ("Just a moment... Enable JavaScript
  and cookies to continue"); WebFetch HTTP 403. Read instead from the Internet Archive copy
  `http://web.archive.org/web/20250623085346/https://www.sodir.no/en/about-us/open-data/`
  (capture 23 Jun 2025; the page says "Updated: 2/17/2025"):
  - "This page gives an overview of avaliable services. Data is published under the Norwegian
    Licence for Open Government Data (NLOD). See infobox for details on licence and update
    routines."
  - Infobox: "Norwegian Licence for Open Government Data (NLOD) 2.0".
  - "Disclaimer: Positional data accuracy is, unless otherwise stated, within approx. +- 0-300m.
    NOD is not responsible for accuracy on data reported by third parties. Content shall not be
    used for navigational purposes."
  - No attribution wording of Sodir's own is on the page.
  A person confirms the live page: inbox note 3 (owner action "open this address in a browser").
- **Licence text opened**: NLOD 2.0, `https://data.norge.no/nlod/en/2.0` (HTTP 200, Norwegian
  Digitalisation Agency), opened 25 Nov 2026. Quotes:
  - §2: "The licensee, subject to the limitations that follow from this licence, may use the
    information for any purpose and in all contexts, by: copying the information and distributing
    the information to others, modifying the information and/or combining the information with
    other information, and copying and distributing such changed or combined information."
  - §2: "This is a non-exclusive, free, perpetual and worldwide licence. The information may be
    used in any medium and format known today and/or which will become known in the future. The
    Licensee shall not sub-license or transfer this licence."
  - §2 comment: "The licensee does not have permission to change the terms and conditions for use
    of the information."
  - §5: "The licensee shall attribute the licensor as specified by the licensor and include a
    reference to this licence. To the extent practically possible, the licensee shall provide a
    link to both this licence and the source of the information. If the licensor has not specified
    how attributions shall be made, the licensee shall normally state the following: «Contains
    data under the Norwegian licence for Open Government data (NLOD) distributed by [name of
    licensor]»." and "If the information has been changed, the licensee must clearly indicate that
    changes have been made by the licensee."
  - §5 comment: "the attribution statement need not be placed on the same page as the information,
    as it is sufficient that the reference to the source be placed on an «About» page, etc." and
    "The sources may instead be stated below the map, on an «About» page, etc. However, the
    reference to the source must not be hidden or difficult to find."
  - §9: an adapted or combined work "may be based on an appropriate licence compatible by
    contract", listed for all information as "Open Government Licence (version 1.0, 2.0 and 3.0),
    Creative Commons Attribution Licence (international version 4.0 and norwegian version 4.0)".
- **Verdict**. (a) Allowed for any purpose, commercial included: tiles on a public site, with the
  attribution, a link to NLOD 2.0 and to FactMaps, and a statement that we simplified the outlines.
  (b) A commit **under CC0 is not allowed** (no sub-licensing, no change of terms; CC0 is not in
  the §9 list). The file **may** be committed carrying NLOD 2.0: the notice that must travel with
  it is the attribution line, the NLOD 2.0 link, the source address and "simplified by Open
  Subsurface Data". Inbox note 2 (how a non-CC0 file sits in a CC0 repository).
- **Credit line**: Sodir specifies none (archive copy); NLOD §5 default, filled in: "Contains data
  under the Norwegian licence for Open Government data (NLOD) distributed by Norwegian Offshore
  Directorate".
- **Update frequency**: service description: "The information is synchronised with the Norwegian
  Offshore Directorate databases on a daily basis." Layer 616: "Layer source data is updated with
  service update."
- **Human check**: in a browser, open `https://www.sodir.no/en/about-us/open-data/`; confirm "Data
  is published under the Norwegian Licence for Open Government Data (NLOD)" and look for any
  attribution wording; open `https://data.norge.no/nlod/en/2.0` §2 and §5. Checked by: ______ on
  ______.

## United States offshore: BOEM (Bureau of Ocean Energy Management)

- **Layer**: `https://gis.boem.gov/arcgis/rest/services/BOEM_BSEE/MMC_Layers/MapServer/15`
  ("BOEM Oil and Gas Leases"; layer 11 is the block grid). Service `copyrightText` "BOEM, BSEE";
  layer 15 `copyrightText` and metadata `idCredit` "MarineCadastre.gov". No licence or use
  constraint on the service or the layer metadata (`/MapServer/15/metadata`, 885 bytes: title,
  abstract, credit only).
- **Service description** (opened 25 Nov 2026): "These data layers are being made available as REST
  mapping services for the purpose of web viewing and map overlay viewing in GIS systems." and
  "these data layers should not be used for official or legal purposes." and "These and other
  cadastre information the BOEM and BSEE produces are generated in accordance with 30 Code of
  Federal Regulations (CFR) 256.8".
- **Terms opened**: `https://www.boem.gov/about-boem/disclaimer-liability-and-endorsement`
  (HTTP 200; `https://www.boem.gov/disclaimer` redirects there), opened 25 Nov 2026:
  - "Information presented on this website is considered public information and may be distributed
    or copied. Use of appropriate byline/photo/image credit is requested. We strongly recommend that
    the Bureau data be acquired directly from a Bureau server and not through other sources that
    may change the data in some way."
  - "Reference in this site to any specific commercial product ... does not constitute endorsement".
  And `https://www.boem.gov/about-boem/copyright-restrictions-and-permissions` (HTTP 200):
  - "Generally, materials produced by federal agencies are in the public domain and may be
    reproduced without permission. However, not all materials appearing on this web site are in the
    public domain. Some materials have been donated or obtained from individuals or organizations
    and may be subject to restrictions on use."
  - Trademarks: no right to use BOEM or Department of the Interior marks "without the express
    written permission of the Department of the Interior".
- **Verdict**. (a) Allowed. (b) Allowed under CC0: the lease outlines are BOEM's own cadastre
  (30 CFR 256.8), public information that "may be distributed or copied"; no third-party material
  is named on the layer. Notice to travel (requested, not a condition): the credit below, the
  retrieval date, and that our outlines are simplified and not official (the service's own
  warning). No BOEM logo.
- **Credit line**: BOEM prescribes none. Recorded fields, word for word: "MarineCadastre.gov"
  (layer), "BOEM, BSEE" (service). Proposed: "Leases: Bureau of Ocean Energy Management (BOEM),
  MarineCadastre.gov; simplified, not official".
- **Update frequency**: **not stated** on the service, the layer metadata or the mapping pages read
  (`https://www.boem.gov/oil-gas-energy/mapping-and-data`; the Gulf GIS page's active-leases map
  says "updated February 2025", which is a map product, not this service).
- **Human check**: open the disclaimer page above; confirm "may be distributed or copied" and
  "credit is requested". Checked by: ______ on ______.

## United States onshore: BLM (Bureau of Land Management)

- **Layer**: `https://nlsdbpubgis.blm.gov/arcgishub/rest/services/HUB/BLM_Natl_MLRS_Oil_and_Gas_Leases/FeatureServer/0`
  (ArcGIS item `ce26353f9cf74439b3619b5b410505e2`, owner `blm_arcgis_hub_natl`; service
  `copyrightText` and item `accessInformation`: "U.S. Department of Interior, Bureau of Land
  Management (BLM)").
- **Terms opened**: item `licenseInfo` (`https://www.arcgis.com/sharing/rest/content/items/ce26353f9cf74439b3619b5b410505e2?f=json`)
  and its metadata (`.../info/metadata/metadata.xml`, 72,883 bytes, `useLimit` and `othConsts`),
  opened 25 Nov 2026:
  - "These data are provided by Bureau of Land Management (BLM) “as is” and may contain errors or
    omissions."
  - "The BLM should be cited as the data source in any products derived from these data. Any Users
    wishing to modify the data should describe the types of modifications they have performed. The
    User should not misrepresent the data, nor imply that changes made were approved or endorsed
    by BLM. These data may be updated by the BLM without notification."
  - "These data are neither legal documents nor land surveys, and must not be used as such."
  - `othConsts` (twice): "None, these data are considered public domain."
- **Verdict**. (a) Allowed. (b) Allowed under CC0 (public domain). Notice to travel: BLM cited as
  the source, the modification described ("simplified outlines; filtered to current cases"), and
  no implied endorsement.
- **Credit line, word for word from the source field**: "U.S. Department of Interior, Bureau of Land
  Management (BLM)". Proposed with the required change note: "Leases: U.S. Department of Interior,
  Bureau of Land Management (BLM); outlines simplified and filtered by Open Subsurface Data, not
  endorsed by BLM".
- **Update frequency**: metadata `resMaint/maintFreq/MaintFreqCd value="002"`, which is "daily" in
  the ISO 19115 maintenance-frequency code list; metadata record itself `012` (unknown), "Last
  metadata review date: 20230615". Item modified 2026-10-19 19:47 UTC.
- **Human check**: open the item page `https://www.arcgis.com/home/item.html?id=ce26353f9cf74439b3619b5b410505e2`
  ("Terms of Use"); confirm "should be cited as the data source" and the public-domain line.
  Checked by: ______ on ______.

## Feature counts re-run (25 Nov 2026, about 15:35 UTC; `returnCountOnly` / WFS `resultType=hits`)

| Layer | `block-layers.md` | Today | Moved |
|---|---|---|---|
| NSTA UKCS offshore licence blocks WGS84 /0 | 698 | 698 | no |
| NSTA England onshore licence blocks WGS84 /0 | 193 | 193 | no |
| Sodir 802 Blocks | 1,827 | 1,827 | no |
| Sodir 803 Quadrants | 192 | 192 | no |
| Sodir 616 Production licence, current with geometry | 1,813 | 1,813 | no |
| Sodir 615 licence by block and operator | 1,113 | 1,113 | no |
| BOEM 11 OCS Lease Blocks | 278,438 | 278,438 | no |
| BOEM 15 Oil and Gas Leases | 1,875 | 1,875 | no |
| BLM MLRS Oil and Gas Leases /0 | 466,838 | 466,838 | no |
| EMODnet `emodnet:activelicenses` | 1,303 | 1,303 | no |
| NOPTA Titles and Permits Current /0 | 242 | 242 | no |
| NOPTA Titles history /0 | 432 | 432 | no |
| BC Oil and Gas Tenure Areas (bcgwpub 24) | 266 | 266 | no |

None moved (same day as the prototype read).

## The next countries (shorter): Canada and Australia

| Source | Opened | What the text says (verbatim) | Verdict | Needs a person |
|---|---|---|---|---|
| C-NLOER (Newfoundland and Labrador) | `https://www.cnloer.ca/disclaimer/` HTTP 200 (old `cnlopb.ca/information/shapefiles` and `/terms-of-use/` are 404; maps page says the data "can now be found on the Data and Information Hub" `home-cnlopb.hub.arcgis.com`) | "Unless otherwise stated, the Board is the owner of all information maintained on the Website including Board WebPages, maps and publications. ... Unauthorized use or reproduction of these materials, either in whole or in part, is strictly prohibited." "To seek permission to reproduce any Board materials for commercial purposes, please contact the Information and Privacy Coordinator" | **No** without written permission; no current-licence layer found (25 Nov) | Yes: hub item terms for a current-licence layer, or a permission (note 4) |
| CNSOER (Nova Scotia) | `https://cnsoer.ca/website-terms-of-use` HTTP 200 (`cnsopb.ns.ca` redirects to `cnsoer.ca`) | "Unauthorized use or reproduction of these materials, either in whole or in part, is strictly prohibited." "You may only use the material for your personal and non-commercial use." | **No** without permission; no licence layer found | Yes: permission (note 4) |
| British Columbia | OGL-BC `https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/open-government-licence-bc` HTTP 200; catalogue record `d7b059df-f978-4687-842c-01c4afe2033d` "Oil and Gas Tenure Areas" names this licence (publisher's own catalogue; record modified 2026-11-25) | "The Information Provider grants you a worldwide, royalty-free, perpetual, non-exclusive licence to use the Information, including for commercial purposes" "Copy, modify, publish, translate, adapt, distribute or otherwise use the Information in any medium, mode or format for any lawful purpose" default credit "Contains information licensed under the Open Government Licence – British Columbia." | (a) yes; (b) not CC0 (licence terms travel, as for NLOD); but the layer read is administrative tenure areas (266), not leases; the grid layers are "Access Only" (catalogue) | Which BC layer holds current leases |
| Alberta | `https://open.alberta.ca/licence`: **not opened live** (curl 403 bot check, WebFetch 403); Internet Archive copy of 28 Oct 2026 read | "including for commercial purposes" ... default credit "Contains information licensed under the Open Government Licence – Alberta." | Licence text read (archive); **no Alberta licence/agreement layer identified**, so which terms apply is unknown | Yes: browser for open.alberta.ca and the agreements layer (note 3) |
| NOPTA (Australia offshore) | `https://www.nopta.gov.au/copyright.html` HTTP 200; service `TitlesCompany_NOPTA` has no licence or copyright text | "All material on this website is licensed under a Creative Commons Attribution 4.0 International Licence, save for content supplied by third parties ..." "Content contained herein should be attributed as © Commonwealth of Australia (Department of Industry) [year], NOPTA [name of document or page containing the content]." | Website terms, not stated for the spatial service: **not verified** for the layer | Yes: NOPTA to confirm the service licence (note 4) |
| Western Australia (DEMIRS) | `https://dasc.dmirs.wa.gov.au/home?productAlias=WAPetroleumTitles` HTTP 200 | "All data and other material produced by Department of Mines, Petroleum and Exploration constitute Crown copyright." "... is licensed under a Creative Commons Attribution 4.0 International licence." "Please give attribution to: © State of Western Australia (Department of Mines, Petroleum and Exploration) 2026"; for derived material: "Attribution: Based on Department of Mines, Petroleum and Exploration material." | (a) yes with attribution; (b) not CC0 (CC BY 4.0 travels). Catalogue tags disagree: data.wa.gov.au says CC BY 4.0, daily; data.gov.au says CC BY-SA 4.0 for the same "WA Petroleum Titles (DMIRS-011)" | The page is DASC's generic home; a person confirms the licence on the product page itself |
| Northern Territory | Metadata `http://www.ntlis.nt.gov.au/metadata/export_data?type=html&metadata_id=FB244D05EFB6203BE040CD9B21446E40` ("Northern Territory Petroleum Tenure") HTTP 200 | "The data or product is copyright of the Northern Territory Government. The data and other information may be reproduced or used to develop other products but any such copies or works must acknowledge the Northern Territory Geological Survey, on behalf of the Northern Territory of Australia as the source of the original data or information." Maintenance: "daily" | (a) yes with that acknowledgement; (b) CC0 not stated either way: **not verified** | Confirm whether the CC BY catalogue tag (data.nt.gov.au) is the operative licence |
| Queensland | Catalogue only: data.qld.gov.au "Queensland mining and exploration tenure series", tag CC BY 4.0, `update_frequency` daily | catalogue tag only | **not verified** | Open the dataset's own licence text |
| South Australia | `https://data.sa.gov.au/...`: **not opened** (curl 403, WebFetch 403) | none | **not verified** | Yes: browser (note 3) |
