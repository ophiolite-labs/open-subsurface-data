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
