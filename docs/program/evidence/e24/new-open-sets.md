# E24 new records: open sets (read 2026-10-23)

Pages opened from the lane host on 2026-10-23, 15:16 to 15:25 UTC, with curl. Zenodo answers a
browser user agent with 403 and ePrints Soton answers it with an Anubis proof-of-work challenge
(401); both answer the verifier's own agent
`open-subsurface-data-verifier/0.1 (+https://github.com/ophiolite-labs/open-subsurface-data)`
with 200, so those pages were read with that agent. Records state publisher facts only.

## Hosts tried

| Host | Address opened | Answer (UTC) | Result |
|---|---|---|---|
| Zenodo | https://zenodo.org/records/4351156 | 403 with browser UA, 200 with verifier UA, 15:16 | record force/ml-competition-2020-well-logs |
| Zenodo | https://zenodo.org/records/1471548 | 200, 15:17 | record ibm-research/netherlands-f3-interpretation |
| Zenodo | https://zenodo.org/records/13381669 (Hikurangi 3D Vp model, CC BY 4.0) | 200, 15:19 | one file of 1,180,507,176 bytes, no sample under 200 MB; no record |
| Zenodo | https://zenodo.org/records/15857064 (crop of USGS B-32c-93-LA, eastern Gulf of Mexico) | 200, 15:21 | one SEG-Y of 8,741,141,824 bytes, derived from USGS NAMSS (already listed); no record |
| GitHub API | https://api.github.com/repos/OPM/opm-data/contents/spe9 | 200, 15:17 | record opm/spe9 (OPM now 2 records) |
| GitHub API | https://api.github.com/repos/equinor/fmu-drogon, /contents/eclipse/model, /releases | 200, 15:22 | record equinor/drogon (Equinor now 2 records) |
| GitHub API | https://api.github.com/repos/bolgebrygg/Force-2020-Machine-Learning-competition | 200, 15:16 | README states no licence; it points to the Zenodo deposit, which is used instead |
| GitHub API | equinor/xtgeo-testdata (LGPL-3.0 test data), equinor/webviz-subsurface-testdata (no licence), OPM/opm-tests (no licence) | 200, 15:22 | not used |
| ePrints Soton | https://eprints.soton.ac.uk/503057 | 401 Anubis with browser UA, 200 with verifier UA, 15:23 | record soton/scanner-pockmark-velocity-models |
| 4TU.ResearchData | https://data.4tu.nl/robots.txt, https://data.4tu.nl/ (TU Delft geothermal doublet logs, Scheemda 2D seismic) | timeout after 30 s (curl exit 28), 15:17 and 15:20 | refused; no record |
| UCD Fault Analysis Group | https://www.fault-analysis-group.ucd.ie/Publications/206_Fault_recognition_Dataset.html (Thebe) | no answer within 40 s, 15:21 | refused; no record |

Robots: zenodo.org/robots.txt `User-agent: *` disallows `/search`, `/api`, `/records/*/preview` and
not `/records/<id>` or `/records/<id>/files/...`; api.github.com/robots.txt and
raw.githubusercontent.com/robots.txt answer 404 (no rules); eprints.soton.ac.uk/robots.txt
`User-agent: *` / `Disallow: /cgi/` only.

## force/ml-competition-2020-well-logs

- Page: <https://zenodo.org/records/4351156> ("FORCE 2020 Well well log and lithofacies dataset for machine learning competition | Zenodo")
  - "This well log dataset from 118 wells in the Norwegian Sea that has been used in the FORCE 2020 machine learning competition with seismic and wells to predict the lithofacies using machine learning models."
  - "The well logs have been slightly cleaned up and partially despiked. The lithofacies and lithology interpretation has been hand crafted using skilled geoscientists"
  - "The original well log data comes form the Norwegian government and is provided by a NOLD 2.0 license"
  - Creators Bormann, Aursand, Dilib, Manral, Dischington; `"publication_date": "2020-12-18"`; files LAS_files_Force_2020_all_wells_train_test_blind_hidden_final.zip 169,785,172; NPD_Casing_depth_most_wells.xlsx 27,080; NPD_Lithostratigraphy_groups_all_wells.xlsx 80,797; NPD_Lithostratigraphy_member_formations_all_wells.xlsx 168,501; lithology scoring matrix cost function.xlsx 14,558
- Licence: `"id": "cc-by-4.0"`, "Creative Commons Attribution 4.0 International", url https://creativecommons.org/licenses/by/4.0/legalcode.
- Extent: no coordinates stated. Period: publication_date 2020-12-18; GitHub CITATION.cff `date-released: 2020-11-18`.
- Listing: Zenodo record page links five `/records/4351156/files/<name>?download=1`. Sample: the LAS zip, HEAD 200, content-length 169,785,172.

## ibm-research/netherlands-f3-interpretation

- Page: <https://zenodo.org/records/1471548> ("Netherlands F3 Interpretation Dataset | Zenodo")
  - "The Netherlands F3 dataset was acquired in the North Sea, offshore Netherlands. The data is publicly available and comprises pos-stack data, eight horizons and well logs of 4 wells."
  - "we had to reinterpret the seismic, generating nine horizons separating different seismic facies intervals. The interpreted horizons were used to create 651 labeled masks for inlines and 951 for crosslines."
  - "Crosslines: Classes: 10 Number of slices: 651 ... Inlines: Classes: 10 Number of slices: 951"
  - Creators Baroni, Silva, Ferreira, Chevitarese, Szwarcman, Vital Brazil (affiliation "IBM Research"); version 2.0.0; `"publication_date": "2018-09-20"`
- Licence: `"id": "cc-by-4.0"`, Creative Commons Attribution 4.0 International.
- Extent: none stated; bbox copied from the F3 block extent in terranubis/f3-demo-2020 (approximate). Period: publication date only.
- Listing: record page links eight files. Sample: horizons.tar.gz, HEAD 200, content-length 95,320,034.

## opm/spe9

- Page: <https://github.com/OPM/opm-data/tree/master/spe9>; listing <https://api.github.com/repos/OPM/opm-data/contents/spe9>
  - SPE9.DATA header: "This reservoir simulation deck is made available under the Open Database License: http://opendatacommons.org/licenses/odbl/1.0/. Any rights in individual contents of the database are licensed under the Database Contents License"
  - "Copyright (C) 2015 Statoil"; "This simulation is based on the data given in 'Ninth SPE Comparative Solution Project: A Reexamination of Black-Oil Simulation', by J.E. Killough, Journal of Petroleum Technology, 1995"
  - "NOTE: This data set is currently not supported by the OPM simulator flow due to a bug in how Cartesian grids are handled."
  - README: "CPG_SPE9.DATA: is the data file for SPE9 with a Corner Point Geometry"; `DIMENS 24 25 15`
- Licence: repository README "decks are now provided under the open database license ... data contained in or pointed to by the decks is licensed under the open database content license".
- Extent: synthetic. Period: none stated for the deck (copyright 2015 only).
- Listing: GitHub contents, nine files. Sample: SPE9.DATA, HEAD 200, content-length 15,927.

## equinor/drogon

- Page: <https://github.com/equinor/fmu-drogon>; listing <https://api.github.com/repos/equinor/fmu-drogon/contents/eclipse/model>
  - "Drogon is a synthetic reservoir model developed and maintained by Equinor. It includes a complete FMU (Fast Model Update) set-up."
  - "This GitHub version is a minimized version that requires a restoring workflow to be run after a git clone (Equinor). As an alternative for externals, one can use a bundle that includes a restored state of Drogon, located in share/external folder."
  - "Git LFS is used for storing the large binary files"
  - DROGON_HIST.DATA: "Synthetic reservoir simulation model Drogon (2020)", "The Drogon model - the successor of the Reek model"
- Licence: "This work is dual-licensed under CC-BY-SA-4.0 and GPL-3.0 (or any later version) ... Data and text files in this work are licensed under the Creative Commons Attribution-ShareAlike 4.0 International License"; GitHub licence field CC-BY-SA-4.0.
- Extent: synthetic. Period: releases 24.4.0 (2024-12-20), 25.0.0 (2025-05-20), 26.0.0 (2026-03-23), from the releases API.
- Listing: GitHub contents of eclipse/model, three decks (DROGON_DST_55_33-1.DATA, DROGON_HIST.DATA, DROGON_PRED.DATA). Sample: DROGON_HIST.DATA, HEAD 200, content-length 6,010.

## soton/scanner-pockmark-velocity-models

- Page: <https://eprints.soton.ac.uk/id/eprint/503057/> ("Scanner-Pockmark Subsurface Velocity Models - ePrints Soton")
  - "P-wave velocity models derived from seismic data acquired over the Scanner Pockmark complex. The models were generated as part of PhD thesis using full waveform inversion (FWI) approaches using the in-house software tools provided by Shell and Imperial Collegeand a Tomographic model (Tomo) using the open-source FAST tomography code."
  - "The FWI velocity models are in both binary and SEG-Y, while the Tomo velocity model is only in binary format."
  - "Jedari Eyvazi, Farid (2025) Scanner-Pockmark Subsurface Velocity Models. University of Southampton doi:10.5258/SOTON/D3589 [Dataset]"; "Published date: 18 July 2025"
  - README.txt: "This dataset supports the thesis entitled "Imaging the Internal Structure of an Active Fluid Escape Structure in the North Sea: 3-D Full Waveform Inversion of the Scanner Pockmark OBS Seismic Dataset""; "Related projects/Funders: - CHIMNEY"
- Licence: each file "Available under License Creative Commons Attribution", linking http://creativecommons.org/licenses/by/4.0/.
- Extent: none stated (no bbox). Period: "Published date: 18 July 2025".
- Listing: the page links six files at `/id/eprint/503057/<n>/<name>`. Sample: FAST_Final_Tomo_Vp_GI_geo_SP, HEAD 200, content-length 146,169,210.

## Proposed samples.yaml lines

```
force/ml-competition-2020-well-logs: ["*/files/LAS_files_Force_2020_all_wells_train_test_blind_hidden_final.zip?download=1"]   # Zenodo record page: the LAS zip, 169,785,172 bytes
ibm-research/netherlands-f3-interpretation: ["*/files/horizons.tar.gz?download=1"]   # Zenodo record page: the horizons archive, 95,320,034 bytes
opm/spe9: ["SPE9.DATA"]   # GitHub contents: the SPE9 deck, 15,927 bytes
equinor/drogon: ["DROGON_HIST.DATA"]   # GitHub contents of eclipse/model: the history deck, 6,010 bytes
soton/scanner-pockmark-velocity-models: ["*/1/FAST_Final_Tomo_Vp_GI_geo_SP"]   # html: page links six files; the tomographic model, 146,169,210 bytes
```
