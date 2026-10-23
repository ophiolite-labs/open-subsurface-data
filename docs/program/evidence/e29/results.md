# E29 results: the all-record dispatch on the branch (23 Oct 2026)

`verify.yml` dispatched on `e29-outlines-from-the-map-services`, `ids` empty (all 160 records):
run 39998588144, 17:52:02 to 18:34:31 UTC, **42 min 29 s** (the verify step 42 min 14 s), success.
`make check-full` on its downloaded `verification` artifact: **25,563 STAC objects valid** (4m14 here).

| record | layer | count on the day | level (dispatch) | first failing check | STAC Items |
|---|---|---|---|---|---|
| sgudds/register-geotermalnych-vrtov | Geofond/Vrty_all/MapServer/2 | 307 | L0 | origin-reachable: HTTP 403 to the runner (outline-derived pass) | 307 |
| nzpam/petroleum-wells | GeodataCatalogue_Layers/MapServer/4 | 1,302 | L0 | origin-reachable: HTTP 403 to the runner (outline-derived pass) | 1,302 |
| nzpam/seismic-surveys-2d | GeodataCatalogue_Layers/MapServer/6 | 990 | L0 | origin-reachable: HTTP 403 to the runner (outline-derived pass) | 990 |
| wa-demirs/petroleum-wells | Industry_and_Mining/MapServer/13 | 4,371 | L2, then **L3** (run 40005843929) | outline-derived on the first run (see below); none on the second | 4,371 |
| va-energy/gas-oil-wells | DGO/DGO_wells/MapServer/0 | 8,605 | L1 | files-checksummed skip (export truncated at 2,000); outline-present: no outlines file (gate budget) | 0 |
| bcer/well-surface-holes-permitted | PASR_WELL_SURFACE_STATE_PT/MapServer/0 | 34,431 | L1 | as Virginia | 0 |
| sgc/banco-informacion-petrolera-pozos | Banco_de_Información_Petrolera_Pozos/FeatureServer/0 | 25,013 | L1 | as Virginia | 0 |
| ut-dogm/oil-gas-wells | viewAGRC_WellData_Surf/FeatureServer/0 | 40,422 | L1 | as Virginia | 0 |
| nd-dmr/wells | Wells/FeatureServer/0 | 44,018 | L1 | as Virginia | 0 |

WA DEMIRS: `outline-derived` failed on the runner with the same 4,371 features: a second dispatch
(run 40005235199, `ids=wa-demirs/petroleum-wells`, after re-deriving) failed the same way while
fetches here stayed stable. Twelve fetches of the layer description from the VPS answered two
byte sets (5 and 7) that differ only in `drawingInfo` (renderer colours): the SLIP service's
load-balanced nodes. The adapter now stores the description's facts the derivation reads
(canonical JSON), not its bytes; the four outlines were re-derived (only `inputs.*.sha256`
changed) and the four records re-dispatched: run 40005843929 (18:44:57 to 18:46:38 UTC), WA DEMIRS
L3, `outline-derived` pass for all four; SGUDDS and NZP&M x2 stay L0 on origin-reachable (403).
