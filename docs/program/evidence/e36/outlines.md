# E36 design 3: the register outlines

Derived on the branch (base 70a9de0) on the VPS, 24 Oct 2026 01:05-01:10 UTC (5 min 0 s):

    uv run osd verify --outlines va-energy/gas-oil-wells bcer/well-surface-holes-permitted \
        sgc/banco-informacion-petrolera-pozos ut-dogm/oil-gas-wells nd-dmr/wells

Review: each layer's `returnCountOnly` (`<layer>/query?where=1%3D1&returnCountOnly=true&f=json`)
against the committed feature count; `osd validate`: 196 records, 0 problems.

| record | layer | `returnCountOnly` (UTC) | features | bytes | sha256 (first 12) |
|---|---|---|---:|---:|---|
| bcer/well-surface-holes-permitted | geoweb-ags.bc-er.ca PASR/PASR_WELL_SURFACE_STATE_PT/MapServer/0 | 34,431 (01:29) | 34,431 | 13,258,649 | aca0d9595e06 |
| sgc/banco-informacion-petrolera-pozos | services1.arcgis.com Banco_de_Información_Petrolera_Pozos/FeatureServer/0 | 25,013 (01:11) | 25,013 | 9,010,741 | 6f33b0242021 |
| ut-dogm/oil-gas-wells | services.arcgis.com viewAGRC_WellData_Surf/FeatureServer/0 | 40,422 (01:11) | 40,422 | 13,628,901 | ab9f1ba194fa |
| nd-dmr/wells | gis.dmr.nd.gov Wells/FeatureServer/0 | 44,018 (01:11) | 44,018 | 17,452,415 | d639c14a8779 |
| va-energy/gas-oil-wells | energy.virginia.gov DGO/DGO_wells/MapServer/0 | not asked: TLS certificate expired | not derived | | |

Counts and sizes equal E32's of 23 Oct (`docs/program/evidence/e32/outlines.md`).

**BCER mid-reload.** At 01:11 BCER's `returnCountOnly` answered 18,000, then 26,000, 27,000 and
28,000 `objectIds` over a minute: the layer was being reloaded. At 01:29 it answered 34,431 again,
the derived count; the derived file is byte-size equal to E32's.

**Virginia.** energy.virginia.gov's certificate (DigiCert Global G2, CN www.energy.virginia.gov)
has `notAfter=Oct 23 23:59:59 2026 GMT`; the verifier's run an hour later read the origin as a
connection failure and robots.txt as unreadable, so the derivation was refused ("derivation
refused: robots.txt disallows ..."). The verifier does not skip TLS. Virginia keeps no outline in
this lane (inbox e36 note 1, accepted by the supervisor 24 Oct).

**`known_issues`.** None of the five records carries an "outline deferred" line (inbox e36 note 2,
accepted), so `records/**` is unchanged.

Each record stays at L1 locally (`files-checksummed` skips: the ArcGIS export stops at 2,000
features, as in E32 note 1).
