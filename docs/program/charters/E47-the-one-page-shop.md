## E47 The one-page shop: a search bar, a list that follows the map, Filters behind one button, the plus and the bag — CHARTERED 25 Nov 2026 (Surface; no strategy, no Codex round; the acceptance list is the brief)

Authority: family `MAP-AS-A-SHOP-family.md` (journey J1–J7, J11, J14, J15; R-S1, R-S2, R-S6–R-S9);
OSD-D26, OSD-D30, OSD-D31; boards Shop 01, 02 and 04 (`b6.py`), the prototype `index.html` (design
evidence only). Builds on E05, E06, E21, E27, E36, E43.

**Outcome.** At `/shop.html` a person sees one page: a top bar with the name, a search bar, one
Filters button and the bag; on the left a list of exactly the datasets in the map window; the map.
Each row has a round green plus that becomes a tick, and a small icon for how the dataset is
obtained. The bag opens on the right and gives the files. The live front page is untouched.

**Context today (verified on `origin/main` `fd69de4`).** `site/index.html` + `site/app.js`
(36 kB) + `site/style.css`: a filter panel that is always open, a detail panel with four cards, a
select mode with a basket that writes manifest/4 (E06), hash state (`q`, `map`, kinds, `t`, `pick`,
`starter`). MapLibre 4.7.1 and pmtiles 4.5.0 from unpkg, pinned in `package.json` for the tests.
`records.json` gives 236 records with `origin.access` (anonymous, registration, api, request,
purchase), `level`, `kinds`, `period`, `region`, `starters`; `collections.json` gives assets;
`mirror.json` gives what the mirror holds.

**The design the charter fixes.**

1. *A second page, its own files.* `site/shop.html`, `site/shop.js`, `site/shop.css`. Nothing is
   imported from `app.js`; what is needed is rewritten small. MapLibre 5.x (exact version pinned in
   the page and in `package.json` as a second, aliased dev dependency so the live page's tests keep
   4.7.1). No link from the live pages (R-S1).
2. *Layout.* Top bar: site name (Merriweather), search input, `Filters` button with a count of set
   filters, bag button with its count. Left column: "N datasets in this view" and the rows. Right:
   the map, full height. Phone width: the map on top, the list as a sheet that can be pulled up,
   the top bar kept to name, search and bag, Filters inside the sheet's head.
3. *The list follows the map (R-S7).* On `moveend` the rows are the records whose place meets the
   map window, filtered from the page's own `records.json` array: a record with a bbox by box
   overlap; a record without one, by its country's box when it has a country, else listed only at
   the world view under a quiet "no place stated" group. Never `queryRenderedFeatures`. Each
   dataset appears once. The order is stable: datasets wholly inside the window first, then by
   title. Rendering is windowed or capped so 236 rows cost nothing while panning.
4. *A row.* Green round plus (tick when in the bag; keyboard reachable; `aria-pressed`), title,
   publisher, one line of kinds and years, the level badge as today, and the access icon with a
   text alternative: download, sign-in, API, on request, purchase. A click on the row (not the
   plus) opens the detail in place of the list, with a back arrow: the content of today's detail
   panel (when, why, licence, origin link, starter project, Open in QGIS, Read in Python) laid out
   as plain sections, not as a row of cards (R-S2).
5. *Filters, one button.* A panel over the list with kinds (chips from the data), level, years and
   "dated only", access, "with a starter project", and Clear. Closing it leaves the count on the
   button. Same meaning as today's filters; same hash keys where they exist (`q`, `t`, `dated`,
   `starter`, kinds), so an old shared link opened on the shop means the same.
6. *The map, first form.* Familiar colours: OpenFreeMap "liberty" style or the same palette
   (blue sea, green and sand land), no key needed. Datasets with outlines draw as today (tiles,
   well grids from E36 reused as they are: counted circles when zoomed out); a dataset with only a
   box draws as one dot with its name at the middle of the box, not a rectangle. No legend. A row
   hovered or opened highlights its features by feature state. A click on a feature opens its row.
   The outline switch, names and globe are E48: this lane leaves the three controls out, not
   disabled.
7. *The bag.* A panel on the right: the datasets added, each with its licence line and access
   sentence, remove buttons, and one amber button "Download the files", which gives (a) the
   manifest/4 the E06 basket writes (same object, tested equal) with the one line to run, and
   (b) direct links for every file the catalogue holds for those datasets (mirror copies and
   anonymous assets from `collections.json`), each with size and sha256. A dataset behind a
   sign-in is listed with where to sign in, not dropped silently. "Get a Python file" is added by
   E49's last slice; "Open in Ophiolite" is absent (R-S6). The bag is in the address (`pick=`, as
   E06) and survives a reload.
8. *Look (R-S9).* Merriweather for titles, Roboto for text, night blue `#101824`, amber `#e0912f`
   for the one bag action, green for the plus. Fonts with `font-display: swap`; no layout jump of
   the list when they arrive.
9. *The journey file.* `tests/site/shop.test.mjs` is created by this lane with all fifteen steps
   of the family journey by name; J8–J10, J12, J13 are `test.todo('J8 … (E48)')` and so on. It is
   added to the `site-test` script.

**Acceptance.** Playwright, offline, over the fixture build unless said.

1. J1: `/shop.html` shows the search bar, a list with a count and the map with no console error;
   there is no legend element and no link to how, status or starters in the top bar.
2. J2: at a window over the North Sea the list ids equal the set computed in the test from
   `records.json` by the rule in design 3; after a pan to Australia they change to that window's
   set; no id twice. A test shows the list is filled with all map sources removed (it does not
   come from tiles).
3. J3: typing `volve` leaves one row; clearing restores the window's count.
4. J4: Filters opens and closes with one button; setting a kind and a level shows "2" on it; the
   list narrows; `#…` carries the same keys as the live page and a live-page hash (`q=`, `t=`,
   `starter=1`, a kind) opened on `/shop.html` gives the same ids as the live page gives.
5. J5: the plus becomes a tick, the bag count is 1, and the map's layers and paint are equal
   before and after (no bag colour: the style is compared).
6. J6: five fixture records, one per access value, show five different icons, each with its text
   alternative.
7. J7: an opened dated, blocked and starter-carrying fixture record shows the When sentence, the
   verifier's reason with its date, and the starter section with the pack's buttons.
8. J11: with two datasets in the bag, "Download the files" writes a manifest/4 equal to the one
   `osd manifest` writes for the same ids (E06 test reused), and lists the direct links with size
   and sha256 for the mirrored fixture dataset; a registration dataset is listed with its sign-in
   sentence.
9. J14: the address copied into a second context gives the same window, filters, opened row and
   bag.
10. J15: at 390 × 844: J1, J2, J5, J11 pass; no horizontal scroll; the plus is at least 44 px.
11. Budget: first load of `/shop.html` on the real catalogue stays under 1 MB from the site
    (the E36 test's method), fonts and libraries reported separately.
12. The live page's tests (`site.test.mjs`, `status.test.mjs`) pass unchanged; `git diff` of
    `site/index.html`, `site/app.js`, `site/style.css` is empty.
13. Screenshots in `docs/program/evidence/e47/`: desktop first view (Europe), Filters open, a row
    opened, the bag with three datasets, phone list and phone bag. No screenshot shows three
    decorative cards in a row.

**Out of scope.** Outline kinds, names, globe (E48); the Python file (E49); the speed practices
beyond design 3 and 6 and all measurements (E50); replacing the front page (E53); any change to
`osd build`.

**Stop rules.** If MapLibre 5 cannot read the existing `outlines.pmtiles` and well grids
unchanged, stop with the error: the tiles are not rebuilt in this lane.

**Ownership and dependencies.** Coding lane (surface). Paths: `site/shop.html`, `site/shop.js`,
`site/shop.css` (new), `tests/site/shop.test.mjs` (new), `tests/site/` helpers it adds,
`package.json`, `package-lock.json`, `tools/shot.mjs` (shop shots), `Makefile` (`site-test`, `shot`
lines only), `docs/program/evidence/e47/**`. No dependency; E46's files are not read by this lane.

**Evidence to inspect.** The screenshots; the journey run in the check; the first-load number.
