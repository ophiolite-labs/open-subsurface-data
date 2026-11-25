# E51 slice 1: Norway read from Sodir, 25 Nov 2026

`uv run osd areas read no` (client name `areas-reader/1`; robots.txt of factmaps.sodir.no answered 302 to
/map/robots.txt and allows the reads), 46 s: `NO: written, licences 0 -> 536 (+536 -0)`. A second read the
same day: `NO: unchanged, licences 536 -> 536 (+0 -0)` (the file is byte-identical).

| What | Number |
|---|---|
| Layer 616 rows / current (`prlStatus` ACTIVE) / relinquished (INACTIVE) | 1,813 / 536 / 1,277 |
| Layer 615 rows (licence by block) / licences named / block ids all in 802 with the same name | 1,113 / 536 / yes |
| Blocks per licence, most | 21 |
| Licences written to `areas/licence/no.geojson` (100 m simplification, 4 decimals) | 536; 215,862 bytes in git |
| Licences holding a dataset (`areas.json`, kind licence) | 536 (Sodir's own register, 9,805 wellbores and 1,405 survey outlines, sits in every one) |
| Datasets placed in a licence | 4: sodir/factpages (536 licences: no block list, the count), equinor/volve (4 licences), co2datashare/sleipner-4d-seismic and sleipner-2019-benchmark-model (1 each) |
| Datasets that gained `blocks` | 3: Volve 15/6, 15/8, 15/9, 16/1, 16/4, 16/7 …; both Sleipner sets 15/8, 15/9 |
| `areas-licence.geojson` (drawn) / `areas.pmtiles` before and after | 207,363 bytes / 7,715,664 -> 7,968,600 bytes (+252,936; tippecanoe 2.49 here) |
| The count over 237 records, uncached, without and with licences | 5.65 s -> 6.35 s |

Mutations (each guard removed in turn; `tests/test_areas_read.py`):

```
FAILS (caught): shrink guard removed: ['1 failed, 27 deselected in 0.05s']
FAILS (caught): a fifth refused (> to >=): ['1 failed, 28 deselected in 0.08s']
FAILS (caught): failed layer read taken as empty: ['1 failed, 27 deselected in 0.05s']
FAILS (caught): repeated id: ['1 failed, 28 deselected in 0.05s']
FAILS (caught): no id or name: ['1 failed, 27 deselected in 0.06s']
FAILS (caught): filter field absent: ['1 failed, 28 deselected in 0.11s']
FAILS (caught): current filter ignored: ['1 failed, 28 deselected in 0.06s']
FAILS (caught): licence without blocks: ['1 failed, 1 passed, 27 deselected in 0.07s']
FAILS (caught): block row of no current licence: ['1 failed, 28 deselected in 0.12s']
FAILS (caught): block not in block layer: ['1 failed, 28 deselected in 0.09s']
FAILS (caught): block named twice: ['1 failed, 27 deselected in 0.05s']
FAILS (caught): not WGS84: ['1 failed, 27 deselected in 0.05s']
FAILS (caught): invalid geometry: ['1 failed, 28 deselected in 0.05s']
FAILS (caught): terms binding (SOURCES.md): ['1 failed, 28 deselected in 0.18s']
FAILS (caught): unchanged read rewritten: ['1 failed, 28 deselected in 0.05s']
FAILS (caught): blocks for 26 licences: ['1 failed, 28 deselected in 0.03s']
```
