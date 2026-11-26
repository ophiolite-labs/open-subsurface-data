## E54 The site says what changed: a foot line with the build date and commit, a page of dated changes, one daily note to the owner — CHARTERED 26 Nov 2026 (Surface with a small build piece; no strategy, no Codex round)

Authority: the owner's question of 26 Nov 2026 ("when are we releasing an updated version", and
how to verify progress, as Ophiolite has nightly builds); OSD-D42 (publish on merge stays, no
nightly); AGENTS.md (the site is surface, one HTML, one JS, one CSS per page, no build step).

**Outcome.** A person who opens any page of opensubsurfacedata.org can read at its foot when the
site was built and from which commit, and one click further reads, in plain words and newest
first, what changed and where to click to see it. The owner gets one short note a day naming at
most three things worth opening. Nobody has to read the repository to know whether the site moved.

**Context today (main `e1b2399`).** The Pages workflow builds and publishes on every merge to
main. Nothing on the site says when or from what. Pages: `index.html` (with `app.js`,
`style.css`), `shop.html`, `how.html`, `status.html`, `starters.html`. `osd build` writes
`site/data/` (ignored by git). The shop's first load is about 8 KB under its 1 MB line (E50).
E53 will rename the shop's files onto the front page and is alone on `site/**` while open.

**The design the charter fixes.**

1. *The stamp.* `osd build` writes `site/data/build.json`: `{"commit": "<7 hex>", "date":
   "<YYYY-MM-DD>", "time": "<HH:MM> UTC"}`, taken from the environment variable the Pages
   workflow already has (`GITHUB_SHA`) or else from `git` in the checkout, with the commit's own
   date (not the clock: the same commit builds the same file). No git and no variable: the file
   is not written and the foot line is absent. No network.
2. *The foot line.* A new `site/foot.js` (under 1 KB, loaded `defer`, after everything else,
   failing silently) appends one line to the end of the page: "Built 26 Nov 2026 from 9d223f7 ·
   What changed". The commit links to that commit on GitHub; "What changed" links to
   `/changes.html`. One `<script>` line in each of the five pages is the lane's only edit of
   them. On the shop the line sits where the page's own foot or attribution allows without
   covering the map or the list; it must not be requested before the map is usable and must not
   move E50's first-load count over the line (the speed test's budget stays green unchanged).
3. *The entries: one file each, so lanes never share a path.* `changes/<YYYY-MM-DD>-<slug>.yaml`
   with exactly `date`, `title` (one plain sentence saying what a person can now do: no epic
   numbers, no file names), `link` (an address on the site, beginning with `/`, that shows it),
   `pr` (the pull request number). `osd build` reads the folder into `site/data/changes.json`,
   newest first, and refuses an entry with a missing or extra key, a `link` not beginning with
   `/`, or a title over 140 characters. A lane adds its own entry file in its pull request;
   `changes/**` is append-only and a new file there needs no row in CLAIMS (one sentence added
   to AGENTS.md says so, announced in the PR title).
4. *The page.* `site/changes.html` (its own small inline script, the house look, no menu):
   entries grouped by day, each a sentence and a link "Open it"; the PR number as a quiet link.
   The lane back-fills one entry per merged outcome of the family E46–E52 from PROGRAM.md
   (about ten), each with a link that really shows the thing.
5. *The daily note.* `osd changes --since <date> [--top 3]` prints, from the committed entries
   only, a plain-text note: the date, up to three sentences with their full addresses, and the
   build the live site should show. No timer and no sending in the repository (R6): the
   supervisor runs it once a day when something merged and places the text in the owner's file
   under "Open Subsurface Data: worth opening today". Which three: the newest, one per pull
   request.

**Acceptance.** Offline.

1. Fixture build with `GITHUB_SHA` set writes the golden `build.json`; with neither git nor the
   variable no file is written and the build succeeds.
2. Site test: each of the five pages shows the foot line with the fixture's date and commit and
   a link to `/changes.html`; with `build.json` absent no line and no console error.
3. A bad entry (missing key, extra key, link without `/`, long title) refuses the build with the
   file name (four tests; mutation: the guard removed lets it through).
4. `changes.html` on the fixture lists three entries newest first under their days; every `link`
   of the committed real entries answers in the built site (test walks them against the build
   tree).
5. `osd changes --since 2026-11-25 --top 3` on the fixture equals a golden text.
6. E50's speed test passes unchanged: first load of the shop not above its line, `foot.js` and
   `build.json` requested after the usable mark.
7. Screenshots, desktop and phone, of the foot line on the front page and the shop, and of
   `changes.html`, in `docs/program/evidence/e54/`.
8. After merge and publish (supervisor): the live foot line names the merge commit.

**Out of scope.** A nightly build, version numbers, release notes by email, an RSS feed, any
edit of the shop's layout beyond the one line.

**Stop rule.** If the foot line cannot sit on the shop without covering the map, the list or the
attribution on a 393 px screen, ship it on the other four pages and `changes.html`, and write the
shop's placement to the inbox for E53.

**Ownership and dependencies.** Coding lane (surface). Paths: `site/foot.js`, `site/changes.html`
(new), one `<script>` line each in `site/index.html`, `site/shop.html`, `site/how.html`,
`site/status.html`, `site/starters.html`, `src/osd/changes.py` (new), one call line in
`src/osd/build.py`, the `changes` subcommand in `src/osd/cli.py`, `changes/**` (new),
`tests/test_changes.py`, `tests/site/foot.test.mjs` (new), `tests/fixtures/changes/**`,
`AGENTS.md` (one sentence), `docs/program/evidence/e54/**`. Must merge before E53 opens or
rebase on it after: E53 is alone on `site/**` while open, and then carries the five script lines
through its renames.
