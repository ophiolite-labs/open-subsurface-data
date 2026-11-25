# E47 evidence: the one-page shop at /shop.html

Screenshots by `node tools/shot.mjs docs/program/evidence/e47 shop` (also `make shot`), over the
local build of c3baa16 with the live basemap (OpenFreeMap liberty) and fonts. The build here has no
verification results, so every level reads L0 and the bag's direct links say "No file address yet";
the journey test serves fixture files for those lines.

| File | What it shows |
|---|---|
| `desktop-first-view.png` | First view (Europe): top bar, "85 datasets in this view", the map with no legend |
| `desktop-filters-open.png` | Filters open over the list, one kind set, the count "1" on the button |
| `desktop-row-opened.png` | NLOG opened in place of the list (plain sections), its outlines lit by feature state |
| `desktop-bag-three.png` | The bag with NLOG, Norne and Volve: licence line, access sentence, the amber button |
| `phone-list.png` | 390 × 844: the map on top, the list as a sheet, Filters in the sheet's head |
| `phone-bag.png` | 390 × 844: the bag after "Download the files": the line to run and the direct links |

First load of `/shop.html` on the real catalogue (journey test "budget", E36's method):
site 786,558 bytes (Europe) and 794,721 bytes (North Sea) in under 1 MB; MapLibre 5.24.0 and pmtiles
4.5.0 from unpkg 1,147,072 bytes uncompressed, reported apart; fonts from Google Fonts, reported apart.
