# E32 design 4: the five register outlines

Derived on the branch (base dd06ac9 + designs 1-3) on the VPS, 23 Oct 2026 19:00-19:06 UTC:

    uv run osd verify --outlines va-energy/gas-oil-wells bcer/well-surface-holes-permitted \
        sgc/banco-informacion-petrolera-pozos ut-dogm/oil-gas-wells nd-dmr/wells     # 5 min 51 s

Review: every layer's `returnCountOnly` (`<layer>/query?where=1%3D1&returnCountOnly=true&f=json`, asked
19:43-19:44 UTC the same day) equals the committed feature count; `osd validate`: 176 records, 0
problems; the verifier's own checks on the derivation run below.

| record | layer | `returnCountOnly` | features | bytes | outline-present | outline-derived | level (local) |
|---|---|---|---|---|---|---|---|
| va-energy/gas-oil-wells | energy.virginia.gov DGO/DGO_wells/MapServer/0 | 8,605 | 8,605 | 2,717,681 | pass | pass | L1 |
| bcer/well-surface-holes-permitted | geoweb-ags.bc-er.ca PASR/PASR_WELL_SURFACE_STATE_PT/MapServer/0 | 34,431 | 34,431 | 13,258,649 | pass | pass | L1 |
| sgc/banco-informacion-petrolera-pozos | services1.arcgis.com Banco_de_Información_Petrolera_Pozos/FeatureServer/0 | 25,013 | 25,013 | 9,010,741 | pass | pass | L1 |
| ut-dogm/oil-gas-wells | services.arcgis.com viewAGRC_WellData_Surf/FeatureServer/0 | 40,422 | 40,422 | 13,628,901 | pass | pass | L1 |
| nd-dmr/wells | gis.dmr.nd.gov Wells/FeatureServer/0 | 44,018 | 44,018 | 17,452,415 | pass | pass | L1 |

The counts are E29's of the same morning (PR #43 table). Each record stays at L1 because
`files-checksummed` skips: the verifier's ArcGIS listing export stops at 2,000 features
(`exceededTransferLimit`, kept as a partial export), so L2, and L3 above it, are not reached; the
listing reader is out of this charter's scope (inbox note e32 #1). No record carried a `known_issues`
line about a deferred outline, so `records/**` is unchanged.

Four files exceed OSD-D16's 8 MB for register outlines (written "until a tiling lane produces
PMTiles"; E15 did): North Dakota 17.5 MB, Utah 13.6 MB, BCER 13.3 MB, SGC 9.0 MB. Named in the PR.
