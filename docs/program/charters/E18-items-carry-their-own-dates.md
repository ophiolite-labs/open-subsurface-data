## E18 Items carry their own dates — QUEUED · Kernel · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round) · follow-on of E03 and E04

Authority: OSD-D14 (Items need a period), OSD-D11 (record versus tool boundary), OSD-D12 and
OSD-D16 (derived outlines are committed and name their inputs); E16 charter line assigning
per-feature dates to the outline side; E16 finding in `docs/program/HANDOFF.md` (register Items carry
the collection's period).

**Outcome.** A STAC client filtering the catalogue by time gets the wellbores drilled and the
surveys shot in that window, not every feature of a register: each Item of a register collection
carries the feature's own start and end as the publisher's service states them, normalised to
RFC 3339, with the raw value kept and the provenance of each bound marked; an Item falls back to
the collection's period only when the feature states nothing usable, and every Item interval lies
inside its Collection's extent.

**Context today (verified 23 Oct, main after PR #16).** `src/osd/stac.py` passes the record's
period to every Item (`_item`, both timestamps). The outline extractor emits identifiers, name,
kind and geometry only (`src/osd/outlines/extractors.py`); `rules.yaml` `propertyName` lists select
exactly those fields, so no date reaches an outline today. Outlines are committed files regenerated
by `osd verify --outlines` (`--outline-inputs` derives without writing); the build reads the
committed files. `schema/stac-osd.json` forbids unknown `osd:` members; `schema/outline.schema.json`
closes `inputs`. The gate validates a sample of Items (OSD-D18), `make check-full` the whole tree.
External prerequisites, to verify at lane open against the live services, not facts: Sodir
wellbore and survey date fields (E16 evidence names `Entry_year` and `Entered_date`; completion and
survey start/end field names unknown), NLOG `START_DATE_DRILLING` (five `1800-01-01` values that
E16 called "likely a placeholder") and an end-date field if one exists.

**The design the lane must map to.**
1. Rules select dates: for each register source `rules.yaml` gains `period_fields: {start, end}`
   naming service properties, and those names are added to that source's `propertyName` request
   list; an injected-transport test asserts the request carries them. `period_placeholders` per
   source lists values treated as absent (NLOG `1800-01-01` only if the lane confirms it on the
   live service; otherwise none).
2. Outlines carry them: the extractor writes `osd:period_start_raw` and `osd:period_end_raw`
   (the service's strings, verbatim) and the normalised `osd:period_start` / `osd:period_end`
   (RFC 3339 UTC instants: a date becomes `T00:00:00Z` for a start and `T23:59:59Z` for an end; a
   timestamp without zone is read as UTC; anything else is invalid and the normalised member is
   omitted). outline/3 (`$id` bumped; outline/2 files still validate under their own schema in the
   compatibility test) admits these four members and names the date fields in `inputs`. The two
   register outline files are regenerated with `--outlines`, their diffs reviewed and committed
   (OSD-D12).
3. Items: both bounds from the feature when both normalise and start ≤ end
   (`osd:period_source: feature`); feature start with the collection's end when the end is absent
   and start ≤ collection end (`osd:period_source: feature-start,collection-end`); otherwise the
   collection's period (`osd:period_source: collection`). `schema/stac-osd.json` gains the member
   with that closed enum (`$id` bumped, old files still validate).
4. Containment guard: an offline test asserts every Item interval lies within its Collection's
   extent for the fixture and, in `make check-full`, for the whole tree. If a real register fails
   it, that register keeps the collection period in this lane and the finding goes to a records
   lane (the Collection period is E16's, records-owned); the PR says which.
5. Collection extents stay the record's `period`; the PR reports per register: Items with own
   dates, mixed, fallback; min and max feature dates against the collection period; named Item
   examples before and after.

**Acceptance.**
- Injected-transport test: the WFS request for each register includes the date fields; removing
  them from `propertyName` fails it.
- Fixture features (distinct fixture collection period, 1990–2000): dated → own bounds, exact
  RFC 3339 strings asserted per named feature id; undated → collection bounds and `collection`;
  placeholder → treated as undated; reversed → collection and `collection`; open end → feature
  start plus collection end and the mixed provenance; start after the collection end with no end
  → collection; malformed string → raw kept, normalised omitted, collection used; timestamp without
  zone → read as UTC.
- Containment test green on the fixture; `make check-full` containment on the tree.
- Compatibility: outline/2 fixture files and STAC files without `osd:period_source` validate under
  their own schemas; the schema map carries both versions.
- Mutations against the unchanged suite: placeholder rule dropped; fallback dropped; reversed
  accepted; dates read from the record instead of the feature; raw not kept; mixed provenance
  mislabelled `feature`; containment guard dropped → each red.
- After merge: the published Sodir and NLOG trees have the named example Items with the asserted
  bounds (post-publication check in HANDOFF).

**Out of scope.** Collection periods (E16, records); Items for records without outlines; records.

**Stop rules.** A register whose service exposes no per-feature dates keeps the collection period;
the lane says so and does not scrape pages.

**Ownership and dependencies.** Coding lane; paths `src/osd/outlines/rules.yaml`,
`src/osd/outlines/extractors.py`, `src/osd/outlines/*.py`, `src/osd/stac.py`, `src/osd/verify.py`
(only if the outline writer needs the date fields passed), `schema/outline.schema.json` (outline/3),
`schema/stac-osd.json` (`osd:period_source`; shared with E19's access enum: second to merge
rebases), `schema/stac/schema-map.json`, `records/outlines/sodir--factpages.geojson` and
`records/outlines/nlog--nlog.geojson` (or wherever the committed register outlines live; name at
lane open), `tests/test_outlines.py`, `tests/test_stac.py`, `tests/fixtures/outlines/**`,
`docs/program/evidence/e18/**`. Depends on E03, E04, E16 (merged).

**Evidence to inspect.** The per-register counts; two named Items before and after; the
containment result; the mutation list; the outline diff summary.

**Dispositions of the Codex round (23 Oct).** Accepted: context corrected (call path, extractor
emits fixed fields, propertyName lists, field names and the 1800 placeholder are prerequisites not
facts, no generated tree in the checkout); schemas claimed and versioned (outline/3, stac-osd
`$id`), schema map and compatibility tests; the committed register outlines claimed and regenerated
with `--outlines`; date fields added to the requests with an injected-transport test; normalisation
and invalid handling defined, raw kept; open-end and mixed provenance defined with a validity rule;
containment guard added with deferral to a records lane; acceptance rewritten with exact instants
on named ids, distinct fixture period, post-publication check, and mutations for each guard; E18
named a follow-on of E03/E04. Refuted: none.
