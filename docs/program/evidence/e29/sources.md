# E29 lane-open evidence: the nine ArcGIS layers (read from the VPS, 23 Oct 2026)

Layer description `?f=json` and `query?where=1=1&returnCountOnly=true&f=json`, user agent
`osd-verifier`, 23 Oct 2026 between 16:50 and 17:05 UTC. Every request answered HTTP 200.

| record | layer | geometry | object id field | pagination | maxRecordCount | spatialReference (wkid / latestWkid) | count |
|---|---|---|---|---|---|---|---|
| sgudds/register-geotermalnych-vrtov | Geofond/Vrty_all/MapServer/2 | point | OBJECTID (field type OID) | true | 1000 | 102067 / 5514 | 307 |
| nzpam/petroleum-wells | GeodataCatalogue_Layers/MapServer/4 | point | OBJECTID (field type OID) | true | 2000 | 2193 / 2193 | 1,302 |
| nzpam/seismic-surveys-2d | GeodataCatalogue_Layers/MapServer/6 | polyline | OBJECTID (field type OID) | true | 2000 | 2193 / 2193 | 990 |
| wa-demirs/petroleum-wells | Industry_and_Mining/MapServer/13 | point | objectid (field type OID) | true | 10000 | 7844 / 7844 | 4,371 |
| va-energy/gas-oil-wells | DGO/DGO_wells/MapServer/0 | point | OBJECTID (field type OID) | true | 2000 | 102747 / 2284 | 8,605 |
| bcer/well-surface-holes-permitted | PASR_WELL_SURFACE_STATE_PT/MapServer/0 | point | OBJECTID (field type OID) | true | 2000 | 102190 / 3005 | 34,431 |
| sgc/banco-informacion-petrolera-pozos | Banco_de_Información_Petrolera_Pozos/FeatureServer/0 | point | FID (`objectIdField`) | true | 2000 | 102100 / 3857 | 25,013 |
| ut-dogm/oil-gas-wells | viewAGRC_WellData_Surf/FeatureServer/0 | point | OBJECTID (`objectIdField`) | true | 2000 | 102100 / 3857 | 40,422 |
| nd-dmr/wells | Wells/FeatureServer/0 | point | OBJECTID (`objectIdField`) | true | 2000 | 102100 / 3857 | 44,018 |

All nine are under the 50,000 cap. `supportedQueryFormats` lists geoJSON on all nine, but a
`f=geojson` query answers WGS84 coordinates with no `spatialReference` (Virginia OBJECTID 4211047:
geojson `[-77.509195, 38.788625]`, json `{x: 11765413.29, y: 4176392.52}` in 102747), so the adapter
reads `f=json` only (strategy, dispositions).

NZP&M 2D lines: 959 of 990 features have more than one path (219,146 vertices in all).

## Date fields (esriFieldTypeDate) and what the rules use

| record | date fields | period_fields |
|---|---|---|
| nzpam/petroleum-wells | Start_Date, End_Date, Rig_Release_Date | start Start_Date, end End_Date |
| nzpam/seismic-surveys-2d | Start_Date, End_Date | start Start_Date, end End_Date |
| wa-demirs/petroleum-wells | spud_date, rig_release_date, extract_date | start spud_date, end rig_release_date |
| nd-dmr/wells | spud_date | start spud_date |
| va-energy/gas-oil-wells | FiStatDt (status), FiDrComp, FiWellComp (max 2027-02-20, future) | none: no start date |
| bcer/well-surface-holes-permitted | name, status and authorization grant dates | none: administrative dates |
| ut-dogm/oil-gas-wells | ConfRelDate, AbandonDate, OrigComplDate | none: no start date |
| sgudds, sgc | none (SGUDDS states a year, `rokrealizacie`) | none |

## Origin and L2 as stored on `verification-results` (main, 23 Oct)

wa-demirs L2; bcer, sgc, ut-dogm L1 (`files-checksummed` skip: the listing export is truncated at
2,000 features, kept as a partial export); sgudds L0 (origin page HTTP 403 to the runner, blocked
since 2026-10-23; HTTP 200 from the VPS); nzpam x2, va-energy, nd-dmr not yet verified on main.
