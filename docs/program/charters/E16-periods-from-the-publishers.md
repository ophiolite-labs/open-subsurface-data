## E16 Periods from the publishers — QUEUED · Records · no strategy, no Codex round

Authority: OSD-D14 (STAC Items need a datetime or a bounded interval; Items only where a record
declares a `period`); E04 as merged (record/2 optional `period`).

**Outcome.** A STAC client lists Items, not only Collections: every record whose publisher states
an acquisition, drilling or release period carries it, quoted as the publisher states it, and the
published catalogue has Items for every outlined feature of those records.

**Context today (after E04 merges).** 68 records, none with `period`; the STAC tree has 68
Collections and 0 Items. `period` is `{start, end}` strings (ISO dates or years as the publisher
states them; `records.py` coerces unquoted YAML dates and ints). Outlined records: Sodir, NLOG,
Poseidon, Parihaka, Kerry 3D (derived); F3, Teapot Dome (placeholders).

**The design the lane must map to.**
1. One `period` per record, from the publisher's own page or register (survey year, drilling
   years, release date), with `stated` text in `notes` or the record's existing field where short;
   never inferred from a file name or from another aggregator.
2. Registers (Sodir, NLOG) get the register's own coverage period as the publisher states it
   (first wellbore year to today, or the register's stated range); per-feature dates are E03's
   business, not this lane's.
3. Target: every record whose publisher states a period, expected at least forty of 68; the PR
   lists the records without a stated period and why.

**Acceptance.**
- `uv run osd validate`: 68 records, 0 problems; every `period` has `start <= end` (existing test).
- `make build` then a count: Items emitted for every outlined record with a period; the PR shows
  the Item count per collection for the five derived-outline records.
- The verify comment on the PR shows no level change (periods do not touch levels).
- Hand count in the PR: records with a period, records without, by reason.

**Out of scope.** Schema changes, outlines, levels.

**Ownership and dependencies.** Records lane; paths `records/**`, `docs/program/evidence/e16/**`.
Depends on E04 (merged).

**Evidence to inspect.** The Item counts; the verify comment; a QGIS Item screenshot (owner, with
action 102).
