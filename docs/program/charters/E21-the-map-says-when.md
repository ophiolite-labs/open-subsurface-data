## E21 The map says when — QUEUED · Surface · no strategy, no Codex round

Authority: owner thesis (surfaces change through user testing; one surface lane, journey tests);
E16 and E18 outcomes; `docs/ENGINEERING.md` proof bar for surface.

**Outcome.** A person asks the map "what was acquired between 1990 and 2000" and sees only those
datasets; the detail panel says when a dataset was acquired and where the publisher said so; the
link they share carries the window.

**Context today (verified 23 Oct, main ad9e624).** 66 of 92 published records carry `period`
(`start`, `end`, `stated`; years, months or dates as strings; E16), STAC Items carry their own
dates (E18), and the site uses none of it: `site/app.js` filters on search, kinds and level, keeps
state in the hash (`q`, `k`, `l`, `pick`, selection, viewport; E05), lists records with a level
badge and shows a detail panel with three cards. The map layer (tiles) carries no dates and this
lane does not add any (E18 ruling; the tippecanoe known red in HANDOFF).

**The design the lane must map to.**
1. Filter: a "from" and "to" year pair under the level select; a record matches when its period
   overlaps the window (a period with only `start` runs to today; only `end` runs from its
   start of record); records without a period are shown by default and hidden by a checkbox
   "only dated datasets". Hash keys `t=<from>-<to>` and `dated=1`; load restores them (E05 rule).
2. Detail panel: a "When" row with the period as the publisher stated it (`start` to `end`,
   "to today" when open) and the `stated` sentence in the same plain style as the licence row;
   "not stated by the publisher" when there is none.
3. List: the period years after the publisher name, small, when present.
4. The manifest the Select flow writes is unchanged byte for byte (E06 test stays green).
5. `how.html`: one short paragraph on what the dates mean (the publisher's stated period of the
   dataset, not the dates of single wells or surveys; those are in the STAC Items) under the
   existing levels section.
6. Phone width: the two year inputs fit the sheet; nothing overflows.

**Acceptance (journey tests in `tests/site/site.test.mjs`, same harness).**
- `#t=1990-2000` lists only records whose period overlaps 1990–2000 plus undated ones; with
  `dated=1` only the dated ones; a record with `start: 2004` is out, one with `end: 1995` is in.
- A hash with `t=`, a kind and a selection renders the same list and detail in a second context.
- The detail of a dated record shows the "When" row with the stated sentence; an undated record
  shows "not stated by the publisher".
- The E05 performance test and the E06 select tests stay green; `make check` green.
- Screenshots of the filter and of a detail "When" row in `docs/program/evidence/e21/`.

**Claim.** `site/app.js`, `site/index.html`, `site/style.css`, `site/how.html`, `tests/site/**`, `docs/program/evidence/e21/**`.
