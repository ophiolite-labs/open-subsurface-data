## E18 Items carry their own dates — QUEUED · Kernel · strategy at lane open · one Codex round

Authority: OSD-D14 (Items need a period), OSD-D11 (record versus tool boundary), OSD-D16 (outline
rules name their inputs); E16 finding in `docs/program/HANDOFF.md` (23 Oct: register Items carry the
collection's period, Sodir survey/10003 shows 1966 to today).

**Outcome.** A STAC client filtering the catalogue by time gets the wellbores drilled and the
surveys shot in that window, not every feature of a register: each Item of a register collection
carries the feature's own start and end dates as the publisher's service states them, and falls
back to the collection's period only when the feature states none.

**Context today (verified 23 Oct, main after PR #14).** `src/osd/stac.py` writes `start_datetime`
and `end_datetime` on every Item from the record's `period` (lines 63–108); outline features carry
the publisher's properties selected by `src/osd/outlines/rules.yaml`, which today names geometry
sources and drop rules, not date fields; Sodir's WFS exposes `wlbEntryDate`/`wlbCompletionDate`
on wellbores and `seaStartDate`/`seaCompletionDate` (names to verify at lane open) on surveys, NLOG
exposes `START_DATE_DRILLING`/`END_DATE_DRILLING` (E16 evidence shows five 1800-01-01 placeholders).
18,432 Items exist; the gate validates a sample (OSD-D18) and `make check-full` the tree.

**The design the lane must map to.**
1. Rules, not records: `rules.yaml` gains per-source `period_fields: {start: <prop>, end: <prop>}`;
   the outline writer copies those two values into each feature's properties as ISO dates
   (`osd:period_start`, `osd:period_end`), verbatim from the service, and names the fields in the
   outline's `inputs` (OSD-D16). Records stay untouched (OSD-D11).
2. Items: `start_datetime`/`end_datetime` come from the feature's two properties when both parse
   as dates and start ≤ end; an open end (no completion date) uses the collection period's end;
   otherwise the collection's period is used and the Item carries `osd:period_source:
   collection`. A placeholder rule per source (`period_placeholders: ["1800-01-01"]`) treats listed
   values as absent.
3. The Collection's temporal extent stays the record's `period` (publisher-stated, E16); the lane
   reports in the PR how many Items took their own dates, how many fell back, and the min and max
   feature dates per register against the collection period.
4. No new network: the dates come from the same WFS reads the outline run already does
   (`osd verify --outline-inputs`).

**Acceptance.**
- Fixture WFS responses for Sodir and NLOG (offline) with dated, undated, placeholder and
  reversed-date features: Items take their own dates, fall back, drop the placeholder, and refuse
  the reversed pair with the collection period and `osd:period_source: collection` (each a test).
- Every Item still validates offline; the sample gate and `make check-full` stay green; the gate
  stays under two minutes.
- Mutations against the unchanged suite: placeholder rule dropped → red; fallback dropped → red;
  reversed dates accepted → red; period fields copied from the record instead of the feature → red.
- On main after merge: the published Sodir collection has Items whose `start_datetime` differ from
  1966-01-01 (count in the PR from a local full build), and the collection extent is unchanged.

**Out of scope.** Collection periods (E16, records); Items for records without outlines; any
record edit.

**Stop rules.** If a register's service does not expose per-feature dates, that register keeps the
collection period and the lane says so; it does not scrape pages.

**Ownership and dependencies.** Coding lane; paths `src/osd/outlines/rules.yaml`, `src/osd/outlines/
*.py` (date copy and inputs), `src/osd/stac.py` (Item dates), `tests/test_outlines.py`,
`tests/test_stac.py`, `tests/fixtures/outlines/**`, `docs/program/evidence/e18/**`. Depends on E03,
E04, E16 (merged). Touches no file of E07 slice 2 or E17.

**Evidence to inspect.** The per-register counts and date ranges in the PR; one Sodir wellbore Item
before and after; the mutation list.
