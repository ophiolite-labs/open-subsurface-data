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
