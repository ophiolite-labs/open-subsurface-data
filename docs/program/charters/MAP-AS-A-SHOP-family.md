# The map as a shop (E46–E53): one page where a person finds, picks and takes open subsurface data

Authority: owner, 25 Nov 2026. The design was drawn in rounds on Paper (file "OpenSubsurfaceData",
page "Where we want to be: the map as a shop", boards Shop 01–06; page "Open questions", boards
Open 01 and 02, both decided) and accepted with "go with your recommendations" / "go with all your
recommendations" / "go with your advice". The owner's rulings are OSD-D26 to OSD-D31. The working
prototype and the three studies are at `~/.local/share/osd-program/prototype-2026-11-25/` on the
controller (`index.html`, `build_areas.py`, `speed-practices.md`, `global-layers.md`,
`block-layers.md`; `b6.py` holds the text of every board). The prototype is evidence of the design,
not source: every lane rebuilds in this repository's structure and copies nothing in.

Builds on E05 (map, hash state, Playwright site test), E06 (select, manifest/4, `osd get`), E15 and
E36 (tiles, well grids, first load under 1 MB), E21 and E27 (when, why), E32 (build shape), E43
(starter cards), E07 (mirror).

**Review.** Kernel charters E46, E49 and E51 each get one Codex round (OSD-D8); dispositions are
recorded under each charter. E47, E48, E50, E53 (Surface) and E52 (Records) get none.

**Why this family exists.** Today the site is a map with a filter panel, a detail panel and three
side pages (How, Status, Starter projects). A person who arrives cannot see at a glance what exists
where they are looking, the map draws a rectangle for a dataset that covers a country, and taking
data means a manifest and a command line. The agreed design turns the one page into a shop: look at
a place, see the list for that place, add to a bag, leave with the files, a Python file, or (later)
an Ophiolite project.

**The page.**

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Open Subsurface Data   [ search …………………………… ]  [Filters]            [Bag · 3] │
├───────────────────────────┬──────────────────────────────────────────────────┤
│ 101 datasets in this view │                                                  │
│ ⊕ NLOG            ⤓       │                     the map                      │
│ ✓ Volve           ⤓       │   blue sea, green and sand land; no legend       │
│ ⊕ UKCS wells      ✉       │   an area is drawn only when a dataset sits in it│
│ …  (follows the map)      │                                                  │
│                           │  [Countries|Provinces|Basins]  [Names]  [Flat|Globe] │
└───────────────────────────┴──────────────────────────────────────────────────┘
 ⊕ round green plus, ✓ when in the bag; the small icon says how the dataset is obtained
 Bag (right): Download the files · Get a Python file · (Open in Ophiolite: not shipped, R-S6)
```

**The journey (the contract every slice lights a part of).** `tests/site/shop.test.mjs` holds these
steps under these names from E47 on; a step no merged slice lights yet is a `test.todo` naming its
epic. E53 may replace the front page only when none is left.

| Step | A person… | Lit by |
|---|---|---|
| J1 | opens the page and within the budget sees the search bar, a list and the map; no legend, no side pages needed | E47 |
| J2 | pans or zooms and the list is exactly the datasets of the map window, each once, with its count | E47 |
| J3 | types in the search bar and the list and the map narrow | E47 |
| J4 | opens Filters (one button), sets kind, level, years, access, starter; closes it; the button shows how many are set | E47 |
| J5 | presses the green plus on a row: it becomes a tick, the bag count goes up; nothing on the map changes colour | E47 |
| J6 | reads from the row's small icon how the dataset is obtained (download, sign-in, API, on request, purchase) | E47 |
| J7 | opens a row and reads what E21, E27 and E43 said: when, why at this level, starter project | E47 |
| J8 | switches Countries / Provinces / Basins: only areas holding a dataset are drawn; a click on one filters the list to it; a second click or the chip's cross clears it | E48 (data E46) |
| J9 | turns Names on and off: one name per drawn area | E48 |
| J10 | switches Flat / Globe: same data, same clicks | E48 |
| J11 | opens the bag and downloads: a manifest/4 for `osd get`, and direct links for files the catalogue holds | E47 |
| J12 | takes "Get a Python file": a `.py` that runs as written against the catalogue | E49 |
| J13 | switches to Licences where a regulator is read: licences holding a dataset are drawn, the row names the block | E51 |
| J14 | shares the address: a second browser shows the same window, filters, outline kind, area and bag | E47, E48 |
| J15 | does J1, J2, J5 and J11 on a phone-width screen | E47 |

**Family rules.**

- **R-S1 The live site stays usable at every merge.** The shop lives at `site/shop.html` (with
  `site/shop.js`, `site/shop.css`) until E53. `site/index.html` and `site/app.js` are not edited
  by this family before E53 except for a defect. No link to the shop from the live pages before E53.
- **R-S2 Show the thing itself.** No legend on the map. No colour on the map for what is in the
  bag. No row of three decorative cards anywhere (owner, 24 Nov). Credits required by a source go
  in the map's attribution line, nowhere else.
- **R-S3 An area is drawn only when a dataset sits in it, and the build decides.** "Sits in it" is
  counted by `osd build` from real well positions and survey outlines (the committed outlines);
  a dataset without positions uses the middle of its box; a country-wide dataset counts for its
  country only. The browser never computes containment. Every drawn area is clickable and filters
  the list. One name per area.
- **R-S4 One exclusive switch.** Countries / Provinces / Basins, later Licences. Never two kinds at
  once.
- **R-S5 Sources are named with their terms.** Countries and provinces: Natural Earth (public
  domain). Basins: USGS "Geologic Provinces of the World" (WEP_PRVG; use constraints none; credit
  "U.S. Geological Survey"). Licences: per country from the regulator, each licence text read and
  its credit line recorded before the first byte is committed (E51). A source without read terms
  is not drawn.
- **R-S6 No "Open in Ophiolite" button** until the whole path works: Ophiolite has no public
  sign-up; its supervisor sends the landing address shape. Not a hidden button, not a disabled
  one: absent. The row mark for a built sample project waits with it.
- **R-S7 Speed is an acceptance line, not a hope.** Target (owner): map usable within 2 s of
  opening, 60 pictures a second while dragging and zooming, no download for an area visited in the
  same visit, no download of our files for a return visit. The list is filtered from the page's own
  records by the map window, never from tile queries. First-load budget stays under 1 MB from the
  site (E36). The four owed measurements are E50's acceptance with numbers in the PR.
- **R-S8 The house rules hold.** One HTML, one JS, one CSS per page, no build step, no framework.
  Schemas are contracts. Records state publisher facts. `make check` stays offline and under two
  minutes; no station is added to it.
- **R-S9 Look.** Ophiolite house look: Merriweather titles, Roboto text, night blue `#101824`,
  amber `#e0912f` for the one action in the bag. Base map in familiar colours (blue sea, green and
  sand land). Fonts are loaded so that text is readable before they arrive.

**Epics and order.**

```text
E46 s0 contract ──▶ E46 s1 countries, provinces, basins ──▶ E48 outlines, names, globe ──▶ E53 front page
        │                                                        ▲
        ├──▶ E52 country-wide datasets (records)                 │
        └──▶ E51 s1.. licences (UK, NO, US)  ◀── E51 s0 terms    │
E47 the one-page shop ───────────────────────────────────────────┤
E49 the Python file (kernel) ──▶ its button in the bag (after E47)│
E50 speed and the four measurements (after E47, again after E48) ─┘
```

Open at once, files disjoint: E46, E47, E49, E51 slice 0. After E46 slice 0: E52. After E46 slice 1
and E47: E48. After E47: E50. After E48 and E46: E51 slices 1–3. Last: E53.

| Epic | Class | Outcome |
|---|---|---|
| E46 Areas that hold data | Kernel | The build says which country, province and basin each dataset sits in, and writes only the areas that hold one |
| E47 The one-page shop | Surface | Search, a list that follows the map, Filters behind one button, the plus, the bag |
| E48 Outlines, names and the globe | Surface | One switch for the outline kind, clickable areas, names, Flat and Globe |
| E49 The Python file | Kernel | `import osd; osd.get("opm/norne")` and the file the bag writes |
| E50 Speed, measured | Surface (with build) | The Shop 06 practices in place and the four measurements with numbers |
| E51 Licences per country | Kernel + Records | Licences from the UK, Norway and the United States as a fourth outline kind, as fresh as the regulator |
| E52 Country-wide datasets say so | Records | Every national register carries the publisher's statement that it covers the country |
| E53 The shop becomes the front page | Surface | opensubsurfacedata.org opens on the shop; How, Status and Starter projects are folded in |

**Not in this family.** Mirror growth for small allowed datasets (inbox item of 25 Nov, a later
charter); the Ophiolite landing and the sample-project tree (Ophiolite E211); Canada and Australia
licences (after their terms are read, a follow-on to E51); any account, payment or server.
