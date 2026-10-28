## E43 Ready for your tools on the site: a person sees which datasets come with a starter project and picks their application — QUEUED (after E40, on fixture packs; real-data acceptance after E42; Surface; no strategy, no Codex round)

Authority: owner direction 28 Oct 2026 ("incorporate … into the opensubsurfacedata.org, maybe think of
a different tab or consider from an end user journey what would make sense to be able to see what
example datasets would be available"); family rules R-T1, R-T3, R-T4, R-T6; E05 (map, hash state,
Playwright site test), E06 (select mode and manifest download), E27 (reasons on the map and the
status page), E40 (`starters.json`, `records.json` `starters`); AGENTS.md (site is one HTML, one
JS, one CSS per page, no build step; a screenshot is its proof).

**Outcome.** On the map, a dataset that comes with a starter project shows a fourth card in its
detail panel: "Starter project", with one button per application (OpendTect, ResInsight, Python),
the licence line and a link to the decision log. A "Starter projects" page lists every pack: the
dataset, where it is, what is inside, which applications, the licence, and how to open it in three
steps (download the manifest, `osd get`, run the import script). A filter "with a starter project"
narrows the map. The journey a new user follows: land on the map → "Starter projects" in the header
→ pick F3 → pick OpendTect → download → open. Until a real pack exists, none of this is visible.

**Context today (verified in code on `origin/main` `4293cc8`, 28 Oct).**

- `site/index.html`: the header links How, Status, Contribute (line 17); the filters section has
  kind chips, a level select and two checkboxes (lines 22–30). `site/app.js` renders the detail
  panel with three cards (Open in QGIS, Read in Python, Get the data; lines 318–346) and the select
  basket with the manifest download (lines 419–448). `site/how.html` explains the levels and the
  three cards; `site/status.html` is a sortable table from `records.json`.
- `tests/site/site.test.mjs`: Playwright journeys offline against a local build (E05, E21, E27).
- No `starters.json` exists until E40 merges; the page and cards read it and render nothing when
  it is absent or empty.

**The design the charter fixes (surface, the acceptance list is the brief).**

1. *Data only from the build.* `starters.json` (every published pack whole: contents, decisions,
   targets with artefact sizes, licence, oracle; E40 design 5) and the `starters` key on records are
   the only inputs; the site holds no pack text of its own and invents no second data contract.
2. *The fourth card.* In the detail panel, after "Get the data", when the record has `starters`:
   title "Starter project", one button per target in the pack's order with the application name
   and the version it was built against, the licence line (spdx, "attribution required",
   "share-alike" when true), a link "what we decided" to the page's decision-log section for that
   pack, and the three steps in one line. A button copies or downloads the pack manifest the same
   way the basket does (E06), so `osd get` is the one fetch route.
3. *The page.* `site/starters.html`, same style as How and Status: one section per pack with the
   dataset title and level badge, region, what is inside (kinds and counts from the pack), targets
   with version and artefact sizes, licence and attribution, the decision log as a table (topic,
   value, source, note; `chosen` lines marked), the oracle sentence ("100 traces compared, 0
   differences"), and the three steps. Header link "Starter projects" appears on index, how and
   status only when `starters.json` has at least one pack.
4. *The filter.* A checkbox "with a starter project" in Show; hash parameter `starter=1`; the list
   and the map narrow to records with `starters`.
5. *Asking for one.* The page ends with "Want a starter project for another dataset?" linking to a
   GitHub issue template `starter-request.yml` (dataset, applications, what you would do with it),
   so E44's choice has evidence.
6. *Phone.* The page reads at 360 px; the card's buttons wrap; no horizontal scroll.

**Acceptance.**

1. Playwright, fixture build with E40's two fixture packs: opening the F3-shaped record shows the
   fourth card with two buttons in the pack's order, the licence line "CC-BY-SA-3.0 · attribution
   required · share-alike", and the "what we decided" link lands on that pack's section of
   `starters.html` (anchor present).
2. Fixture build with `starters.json` empty: no fourth card, no header link, no filter checkbox,
   and `starters.html` says "No starter projects yet" (screenshot).
3. `#starter=1` lists exactly the two fixture records; unticking restores the count.
4. The "Download the pack manifest" button produces a manifest/4 whose entries equal the fixture
   pack's artefacts by sha256 (the E06 basket test extended, offline).
5. `starters.html` at 360 px: no horizontal scroll, buttons wrapped (screenshot).
6. After E42 merges: the real F3 card and page section with the OpendTect, ResInsight and Python
   buttons, the oracle sentence and the decision log (screenshot in the E42 handoff, this charter's
   DONE condition).

**Out of scope.** Counting downloads (no server, R-T6); any account or payment; packs for other
datasets (E44); STAC exposure of packs (E40 follow-on).

**Stop rules.** None before E40 merges; the lane does not open without `starters.json` in the build.

**Ownership and dependencies.** Coding lane; paths `site/index.html` (header link and filter only),
`site/app.js` (fourth card, filter, starter manifest), `site/starters.html` (new), `site/style.css`
(card and table rules only), `site/how.html` (one paragraph on the fourth card),
`.github/ISSUE_TEMPLATE/starter-request.yml` (new; announced in the PR title), `tests/site/site.test.mjs`
(new tests at the end), `docs/program/evidence/e43/**`. Depends on E40 (merged); DONE after E42.

**Evidence to inspect.** The two screenshots; the Playwright run in the check; the manifest the button
writes.
