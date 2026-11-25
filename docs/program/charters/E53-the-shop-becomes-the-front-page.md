## E53 The shop becomes the front page: opensubsurfacedata.org opens on the shop; How, Status and Starter projects are folded in — CHARTERED 25 Nov 2026 (Surface; no strategy, no Codex round) — QUEUED last: after E47, E48, E49 slice 4, E50 first pass

Authority: family `MAP-AS-A-SHOP-family.md` (R-S1: "the redesign replaces the current page only
when the journey test passes whole"); OSD-D26, OSD-D33; board Shop 01 ("one page").

**Gate to open the lane.** `tests/site/shop.test.mjs` has no `test.todo` left except J13 where no
licence country has merged (J13 is then lit by E51 on the front page itself), and E50's first
three measurements are in. The supervisor checks this on main, not the lane.

**Outcome.** The address everyone already has opens the shop. Every link shared before still
means the same. What How, Status and Starter projects told a person is reachable from the one
page without a row of menu links: how the levels work from the level badge of any row, the status
table from the count line (for example "236 datasets, 141 checked this week"), starter projects through the
filter and the row.

**The design the charter fixes.**

1. `site/index.html`, `site/app.js`, `site/style.css` become the shop's files (the shop files are
   renamed onto them, one HTML, one JS, one CSS); `/shop.html` stays as a redirect to `/` with the
   hash kept.
2. Old hashes keep their meaning (E47 acceptance 4 already holds the keys); a test opens ten
   recorded old links (in `tests/fixtures/site/old-links.txt`, taken from the E05–E43 tests) and
   compares the listed ids with what the old page gave (recorded once from the old page before the
   switch, committed as the expectation).
3. `how.html`, `status.html`, `starters.html` remain as pages (links to them exist in the world
   and in issues), restyled to the house look, reached from the places named in the outcome; no
   top-bar menu. Their own tests keep passing.
4. The old page's code is deleted in the same PR (deletable modules, never migrations); the old
   tests whose subject no longer exists are removed with a line each in the PR saying which shop
   journey step covers the behaviour, or that the behaviour was dropped by which decision (the
   legend, the always-open filter panel, select mode).
5. README and CONTRIBUTING screenshots and sentences that describe the old page are updated.

**Acceptance.**

1. The whole journey J1–J15 passes at `/`.
2. The ten old links give the recorded ids.
3. `/shop.html#x` lands on `/#x`.
4. First load under 1 MB from the site; E50's measuring mode works at `/?measure=1` and the
   usable-in-seconds number on the controller is not worse than at `/shop.html` before the switch.
5. Screenshots, desktop and phone, of the front page, a row opened with the level explanation
   reached, the status table reached from the count line, in `docs/program/evidence/e53/`.
6. After the merge and the Pages publish: https://opensubsurfacedata.org answers 200 with the
   shop, checked by the supervisor; if not, the merge is reverted within the hour (loop step 7).

**Out of scope.** The "Open in Ophiolite" button (R-S6); new features.

**Ownership and dependencies.** Coding lane (surface), alone on `site/**` and `tests/site/**`
while open. Paths: `site/**` (not `site/data/`), `tests/site/**`, `tests/fixtures/site/**`,
`tools/shot.mjs`, `README.md`, `CONTRIBUTING.md`, `docs/program/evidence/e53/**`.
