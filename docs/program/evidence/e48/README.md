# E48 evidence: outlines, names and the globe on /shop.html

Screenshots by `node tools/shot.mjs docs/program/evidence/e48 e48`, over the local build of the
real catalogue (237 records; 68 countries, 141 provinces, 145 basins hold a dataset) with the live
basemap (OpenFreeMap liberty) and its fonts. Every level reads L0: the build here has no
verification results.

| File | What it shows |
|---|---|
| `country-europe-names.png`, `province-europe-names.png`, `basin-europe-names.png` | Europe, one kind each, Names on: one name per drawn area, the dataset dots' names |
| `country-north-america-names.png`, `province-north-america-names.png`, `basin-north-america-names.png` | The same over North America |
| `north-sea-basin-clicked.png` | Basins, North Sea Graben clicked: "13 datasets in North Sea Graben", the chip, the basin outlined stronger, the USGS credit |
| `globe-first-view.png` | `#p=globe`, the first view on the globe |
| `phone-switch.png` | 390 × 844: the kind switch, Names and Flat · Globe on the map, reachable (credits folded under their (i)) |

Bytes from the site (journey test "budget", E36's method, this host):

- First load with Countries on: 1,043,874 bytes in 22 requests (records.json 649,296; areas.json
  131,952; outlines.pmtiles 113,651; areas.pmtiles 70,659; shop.js 56,988). **Over the 1 MB line**:
  see the PR and inbox note e48 #2 (both JSON files are written pretty-printed; compact they are
  513,518 and 79,634 bytes).
- Switching to Provinces: 46,423 bytes in 6 requests (area tiles of the same file, read again for
  the new source); to Basins: 46,423 bytes in 6 requests.
