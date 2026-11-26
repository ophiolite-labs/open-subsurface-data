# E48 evidence: outlines, names and the globe on /shop.html

Screenshots by `node tools/shot.mjs docs/program/evidence/e48 e48`, over the local build of the
real catalogue (main of 26 Nov; with E51's Licences the switch has a fourth part) with the live
basemap (OpenFreeMap liberty) and its fonts. Every level reads L0: the build here has no
verification results.

| File | What it shows |
|---|---|
| `country-europe-names.png`, `province-europe-names.png`, `basin-europe-names.png` | Europe, one kind each, Names on: one name per drawn area, the dataset dots' names |
| `country-north-america-names.png`, `province-north-america-names.png`, `basin-north-america-names.png` | The same over North America |
| `north-sea-basin-clicked.png` | Basins, North Sea Graben clicked: "13 datasets in North Sea Graben", the chip, the basin outlined stronger, the USGS credit |
| `globe-first-view.png` | `#p=globe`, the first view on the globe |
| `phone-switch.png` | 390 × 844: the kind switch, Names and Flat · Globe on the map, reachable (credits folded under their (i)) |

Bytes from the site (journey test "budget", E36's method, this host, after OSD-D41 made the build
write records.json and areas.json compact; areas.json now also holds E51's licences):

- First load with Countries on: 991,831 bytes in 22 requests at the first view (records.json
  523,930; areas.json 181,052; outlines.pmtiles 113,697; areas.pmtiles 93,675; shop.js 58,404),
  988,092 bytes over the North Sea. Under 1 MB, by 8 KB.
- Switching to Provinces: 69,436 bytes in 6 requests at the first view, 57,534 bytes in 9 over the
  North Sea (area tiles of the same file, read again for the new source); to Basins the same.
