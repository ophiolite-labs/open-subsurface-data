## E48 Outlines, names and the globe: one switch for the kind of area, every area clickable, Flat and Globe — CHARTERED 25 Nov 2026 (Surface; no strategy, no Codex round) — QUEUED after E46 slice 1 and E47

Authority: family `MAP-AS-A-SHOP-family.md` (journey J8–J10, J14; R-S2–R-S5, R-S7); OSD-D26,
OSD-D27, OSD-D28; boards Shop 02 and 03, Open 01 (`b6.py`); the prototype (design evidence only).

**Outcome.** On the shop a person picks Countries, Provinces or Basins with one switch. Only areas
that hold a dataset are drawn; a click on one narrows the list to the datasets that sit in it and
shows its name as a chip that clears it. Names can be turned on and off, one per area. Flat or
Globe is one switch at the bottom right; the globe has the same data, colours and clicks.

**Context at charter time.** E46 will give `areas.json` (per kind: `area_id`, `name`, `label`,
`bbox`, `n`, `ids`), `areas.pmtiles` with layers `areas_country`, `areas_province`, `areas_basin`
and a GeoJSON fallback per kind; records carry `areas`. E47 will give `shop.html`, `shop.js`,
`shop.css` on MapLibre 5 and the journey file with J8–J10 as todo. The lane verifies both on main
at open and corrects this paragraph in its PR if they differ.

*Verified at lane open (25 Nov 2026, main b09078f).* As stated, with these differences: each kind
in `areas.json` also carries `sources` (file, name, url, licence, `credit`, edition), and a
province carries its `country`; the file is pretty-printed (132 KB on the real build, 80 KB
compact). `areas.pmtiles` is one file whose every tile holds all three layers (z0–8), so on the
tile path a kind is a source layer, not a file; the per-kind GeoJSON is written beside it and is the
path when tiles are absent (the fixture build). Drawn features carry `area_id`, `name`, `n` and an
integer id. E47 already uses `a=` in the hash for access, so the area is `area=<area_id>`.

**The design the charter fixes.**

1. *The switch (R-S4).* A three-part control on the map, bottom left: Countries, Provinces,
   Basins; exactly one is on; Countries is the default. Only the chosen kind's layer is loaded and
   drawn; switching fetches the other on demand and keeps what was fetched. A fourth part,
   Licences, appears when `areas.json` has that kind (E51) and not before.
2. *Drawing (R-S2, R-S3).* A drawn area has a quiet fill (lilac, low opacity) and a thin line,
   the same for every area: no colour scale, no legend. `areas.json` is the authority for which
   areas exist; nothing is drawn for an area not in it.
3. *Click.* A click on an area sets the area filter: the list shows that area's `ids` (met with
   the other filters and search, not with the map window, so a dataset of the area that is out of
   view is still listed); the map eases to the area's `bbox`; a chip with the area's name and a
   cross sits above the list; the area is outlined stronger by feature state. A click on a dataset
   feature inside an area still opens the dataset (dataset features win). The hash carries
   `o=country|province|basin` and `a=<area_id>`.
4. *Names.* A `Names` toggle: on, each drawn area shows its name once at `label` (a symbol layer
   from `areas.json` points, not from tile polygons, so no name repeats across tiles), and dataset
   dots show theirs; off, none. `fadeDuration` 0. Hash `n=0|1`.
5. *Globe.* `Flat | Globe` bottom right, MapLibre 5 `setProjection`; hash `p=globe`. Every
   interaction of J2, J5, J8 works on the globe. The list rule on the globe uses the map's bounds
   as on the flat map; when the whole earth is in view the list is all datasets.
6. *Credits.* The attribution line shows the chosen kind's `source.credit` from `areas.json`
   ("U.S. Geological Survey" for basins) beside the base map's.

**Acceptance.** Playwright, offline, fixture build with E46's fixture areas unless said.

1. J8: for each kind the set of drawn area ids equals `areas.json`'s for that kind; no other
   kind's layer is present in the style; only the chosen kind's file was requested.
2. J8: a click on a fixture basin gives exactly its `ids` in the list, the chip with its name, and
   `a=` in the hash; the cross restores the window's list. Nothing with `n = 0` can be clicked
   because nothing with `n = 0` exists (asserted from the files).
3. J9: Names on shows one label per drawn area (count equals areas); off shows none.
4. J10: after Globe, `map.getProjection()` is globe; J2, J5 and the click of (2) pass again.
5. J14: a hash with `o=`, `a=`, `n=`, `p=`, a filter and a bag renders the same in a second
   context.
6. The style has no legend element and the paint of area layers has no data-driven colour.
7. Real catalogue: screenshots in `docs/program/evidence/e48/` of Countries, Provinces and Basins
   over Europe and over North America, Names on, the North Sea with a basin clicked, the globe
   first view, and phone width with the switch reachable.
8. Budget: first load of `/shop.html` is still under 1 MB from the site with Countries on; the
   size requested when switching to Provinces and to Basins is stated in the PR.
9. J8–J10 and the E48 half of J14 are lit in `shop.test.mjs`; the live page's tests pass unchanged.

**Out of scope.** Licences data (E51); speed measurements (E50); the front page (E53).

**Stop rules.** If the globe cannot draw the well grids and area fills without visible seams or
below a usable frame rate on the controller's headless run, ship Flat with the globe behind
`p=globe` only (no switch), and say so; E50 measures and decides.

**Ownership and dependencies.** Coding lane (surface). Paths: `site/shop.html`, `site/shop.js`,
`site/shop.css`, `tests/site/shop.test.mjs`, `tools/shot.mjs`, `docs/program/evidence/e48/**`.
Depends on E46 slice 1 and E47 merged.
