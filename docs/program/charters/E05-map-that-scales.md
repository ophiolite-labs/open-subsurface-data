## E05 Map that scales — QUEUED · Surface · no strategy

Authority: owner direction 23 Oct (the offentligdata.com example: toggles, key, search, detail);
`docs/ENGINEERING.md` proof bar for surface.

**Outcome.** A person can filter the map, share the link and the receiver sees the same view;
thousands of wellbores pan without lag; a visitor understands in one page what the levels mean
and how to open a layer in QGIS or Python.

**Context today (verified 23 Oct).** `site/` is one HTML, one JS, one CSS on MapLibre 4.7 over
OpenFreeMap Positron; chips per kind, a level select, extents and placeholder toggles, search,
a list, a detail panel with three cards, a key. State is in memory only. GeoJSON source only.
Headless screenshot works with Playwright and swiftshader; the basemap did not render in the
headless run (overlays did).

**The design the lane must map to.**
1. URL state: filters, selection and viewport in the hash; load restores it.
2. Sources: PMTiles via `pmtiles` protocol when `data/outlines.pmtiles` exists, else GeoJSON;
   wellbores clustered below zoom 7.
3. Stale levels: `checked_at` older than 30 days shows "stale" next to the level.
4. A `how.html` page: the ladder, the three cards, the licence rule ("the publisher's page is the
   authority"), the contribution path. Plain words, no marketing.
5. Theme: dark basemap when OSD-D3 names one; until then Positron.
6. Mobile: the panel is a bottom sheet under 640 px (exists; keep it working).
7. `tools/shot.mjs` (exists) gets Playwright as a devDependency instead of borrowing the Ophiolite
   web tree.

**Acceptance.**
- Open `#q=volve`, the list shows one dataset (screenshot).
- A hash with a kind filter and a selection, pasted in a second browser context, renders the
  same list count and panel title (Playwright test, `tests/site/`).
- 10,000 synthetic wellbore points (generated in the test) render at zoom 5 with clusters; the
  frame after `moveend` arrives under 100 ms in the Playwright trace.
- `how.html` exists and the three cards' snippets run as written (the Python one executed in CI
  against the local server).
- No console error on load (Playwright asserts).

**Out of scope.** Accounts, state beyond the URL, a server, analytics.

**Stop rules.** A basemap needs a key: do not add one; keep Positron and note it under OSD-D3.

**Ownership and dependencies.** Coding lane; paths `site/**`, `tools/shot.mjs`, `tests/site/**`,
`Makefile` (site targets only). No dependency; runs in parallel with E02 on disjoint paths.

**Evidence to inspect.** Two screenshots (desktop, phone width) and the Playwright run in the PR.
