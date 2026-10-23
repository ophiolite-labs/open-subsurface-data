## E27 The map says why — QUEUED · Surface · no strategy, no Codex round · journey tests

Authority: owner direction 23 Oct 2026 (levels on the map are real); E23 (a reason per record
below L2, `osd status` prints it: `src/osd/cli.py` `l2_reason`); H1 (OSD-D20 `blocked` with its
reason "answers a browser, not the verifier (HTTP a to osd-verifier, HTTP b to a browser agent)";
`osd status` prints the reason for blocked); E08 (status page); OSD-D9 (blocked awards no level).

**Outcome.** A person who opens a dataset on the map, or a row on the status page, reads in the
verifier's own words why it is at its level and when that was established: "no file address is
published to us", "listing names no file", "robots.txt disallows the listing", "answers a browser,
not the verifier", "origin dead since …", or "sampled 3 files, sha256 matched" for L2.

**Context today (verified 23 Oct, main 4dcdc56).** `src/osd/build.py` writes `site/data/records.json`
with title, publisher, kinds, licence, redistribution, level and the verification date; it does
not carry the reason. `site/app.js` shows a sentence from `noAssetsReason(r)` that depends on
`origin.access` only, so a dead origin and a listing without files read the same. The reason
sentence exists once, in `src/osd/cli.py` `l2_reason` (E23, extended by H1), and nowhere else.
`site/status.html` lists level, dataset and last-checked date (phone: those three columns only).
`how.html` explains the levels. Site journey tests run in `tests/site/site.test.mjs` (Playwright,
fixture catalogue, CI `check`). Known red: tippecanoe attribute corruption (tiles carry no dates).

**The design the lane must map to.**
1. One source: move `l2_reason` into `src/osd/reasons.py` (or equivalent) and have `osd status`
   and `build.py` call the same function; a test asserts, for each level and for `blocked`, that
   the status line and the `records.json` field are the same string.
2. `records.json` gains `reason` (that sentence) and keeps the verification date; the site's data
   contract (`site/data/` is regenerated, never committed) gets the field documented in
   `build.py`'s docstring. Records never verified read "never verified" as `osd status` does.
3. Detail panel: a "Why this level" row with the sentence and the date ("checked 23 Oct 2026");
   `noAssetsReason` is replaced by the record's `reason`, so the access-based sentence survives
   only where the verifier's reason is the access itself. Status page: a "Why" column on wide
   screens (hidden on the phone layout like the other columns are), sortable as the others.
4. `how.html` gains one paragraph that lists the reason sentences and what a publisher can do
   about each (publish a file listing; allow the verifier in robots.txt; answer robots the same
   as browsers).
5. Journey tests on a fixture catalogue with one record per reason class: the detail panel and
   the status row show the sentence and date; a `blocked` record shows the OSD-D20 sentence and
   no level badge; the share hash and filters are unchanged.

**Acceptance.**
- `make check` green; the reason-equality test red when `build.py` formats its own sentence
  (mutation: duplicate the sentence in build.py → red).
- Screenshot of the detail panel for a `blocked` record and for an L2 record at phone width.
- `site/status.html` shows the Why column on a desktop screenshot and hides it at phone width.
- Playwright journey tests listed by name in the PR; no record file touched.

**Out of scope.** New reason classes; issue automation; map tiles; any schema change.

**Claim.** `src/osd/build.py`, `src/osd/cli.py` (the `l2_reason` move only), `src/osd/reasons.py`
(new), `site/app.js`, `site/index.html`, `site/status.html`, `site/how.html`, `site/style.css`,
`tests/test_build.py` (or where build tests live), `tests/test_cli.py` additions,
`tests/site/site.test.mjs` (shared with E26, second to merge rebases), `tests/fixtures/site/**`,
`docs/program/evidence/e27/**`.
