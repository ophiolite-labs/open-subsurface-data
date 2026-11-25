# E51 slice 3: the United States offshore read from BOEM, 25 Nov 2026

`uv run osd areas read us` (client name `areas-reader/1`; gis.boem.gov robots.txt 404, allows), about 50 s:
`US: written, licences 0 -> 1841 (+1841 -0)`. `osd areas read no` the same hour: unchanged (the id trimming
leaves Norway byte-identical).

| What | Number |
|---|---|
| Layer 15 rows / current (oil and gas statuses) / renewable (RENACV, left out) | 1,875 / 1,841 / 34 |
| Lease numbers served with a leading blank (trimmed: " 00016" -> US:00016) | 80 |
| Blocks per lease (`ACLABS` on the row) | 1 |
| `areas/licence/us.geojson` (100 m, 4 decimals) | 468,399 bytes in git; with Norway 684,261 (< 10 MB) |
| Leases holding a dataset | **0**: the six US Gulf records (BOEM well data, OGOR-A production, paleontologic data; Alabama, Florida, BEG) have no committed outline, and their box middles fall in no lease |
| Datasets that gained `blocks` | 0 |
| Added to the tiles and `areas-licence.geojson` | nothing (no lease is drawn until a dataset lies in one) |

BLM (onshore, MLRS FeatureServer/0): 466,838 cases, of which 32,406 are `Authorized` (also Closed 433,583,
Pending 497, Interim 352). A sample page of 2,000 Authorized cases (38,487,174 bytes served; 91 without
geometry) simplified at 100 m: 1,439,931 bytes, 754 bytes a lease, about 24.4 MB for all. That is over the
5 MB stop rule, so BLM is not drawn. The fetched page was deleted after measurement.

Mutations (slice 3 guards):

```
FAILS (caught): projected wkid allowed: ['1 failed, 35 deselected in 0.14s']
FAILS (caught): served SR not the configured one: ['1 failed, 35 deselected in 0.05s']
FAILS (caught): blank block on the lease row taken: ['1 failed, 35 deselected in 0.05s']
FAILS (caught): leading blank kept in the id: ['1 failed, 35 deselected in 0.06s']
FAILS (caught): status list ignored (op in): ['1 failed, 35 deselected in 0.05s']
```
