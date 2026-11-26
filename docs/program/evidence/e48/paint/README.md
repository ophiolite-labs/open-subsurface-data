# E48 follow-up: the drawn areas read, the surveys step back, area names win

Before (main 5875fa3) and after (this branch) at the same views, over the same local build, live
basemap: `node tools/shot.mjs <dir> e48` (desktop, phone-switch) and two phone views with Names on
(`o=country&n=1&map=3.60/55.0000/6.0000`, `o=basin&n=1&map=5.00/57.0000/3.0000`).

| View | Before | After |
|---|---|---|
| Countries over Europe, Names on | lilac at 8 % on green land: no country reads as drawn; orange survey grids over the North Sea | one slate tint at 14 % and a 1.4 px line: the drawn countries read; surveys a faint grey ink |
| Basins over Europe, Names on | the same | the same change |
| North Sea Graben clicked | lilac selection under orange grids | slate at 30 %, 3 px line; the grids grey below zoom 7 |
| Provinces over North America | thin lilac | slate, firm |
| Phone (390 × 844): switch, Countries and Basins with Names on | areas hardly visible; dataset names as dark as area names | areas read; area names bold and on top |

What changed, paint and layout only (`site/shop.js`):
- Areas: one neutral slate `#34465f` for every area and kind, fill 0.14 (0.30 when clicked), line
  1.4 px (3 px when clicked). No data-driven colour, no legend.
- Survey outlines below zoom 7: a neutral ink `#7b8592`, line opacity 0.3 at zoom 4 rising to 0.75 at
  7, no fill at zoom 4; from zoom 7 their orange as before. A lit survey is night blue at every zoom.
- Names: area names 13 px bold, the top symbol layer, so they are placed first and win collisions;
  dataset names 10.5 px, a softer ink, 6 px padding, so they give way.
