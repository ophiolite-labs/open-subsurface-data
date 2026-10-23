## E13 Twenty records from the national registers — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026 ("combine the SEG open data list and the national
registers"); E01 follow-ups recorded in `docs/program/PROGRAM.md` (ten of twelve E01 records came
from one aggregator; origins opened by an agent); OSD-D7, OSD-D9.

**Outcome.** The map lists at least forty datasets, and the second twenty come from the
publishers themselves: national registers and surveys, universities and consortia, with at most
three new records from any one aggregator. A reader filtering by country sees a government source
for at least eight countries.

**Context today (verified 23 Oct, main 37476eb).** Twenty-one records exist in `records/`;
twelve of them point at TerraNubis. Government publishers present: Sodir (NO), NLOG (NL), NSTA
NDR (UK), NZP&M (NZ), NOPIMS (AU, blocked for automated requests). `osd validate` passes. Record
schema is record/1 (`schema/record.schema.json`, `additionalProperties: false`); the kinds
vocabulary is its enum. Three records are held by lane E02 and are out of this lane's reach:
`records/sodir/factpages.yaml`, `records/opm/norne.yaml`, `records/nopims/poseidon.yaml`.

**The design the lane must map to.**
1. One record per dataset or per register (E01 design 1 stands). A register is one record with
   `source-list` among its kinds; a named dataset the register carries that has its own landing
   page and licence statement gets its own record.
2. Candidates, in this order until twenty, each opened on the day: GEUS (Denmark, Frisbee and the
   Danish subsurface archive), Geoscience Australia (data.gov.au and the GA eCat entries for
   open 3D surveys, the AWS open-data registry entries), USGS NAMSS (US marine seismic archive),
   USGS National Geologic Map Database boreholes, BGS OpenGeoscience and the UK Onshore Geophysical
   Library, Ireland PAD/Geological Survey Ireland petroleum data, Natural Resources Canada GDR and
   the Canada-Nova Scotia and Canada-Newfoundland offshore boards, Germany (LBEG NIBIS, BGR GeoPortal),
   Kansas Geological Survey well data, Alaska DGGS/AOGCC, Equinor and partners' CO2 DataShare
   (Sleipner 4D, Smeaheia, Northern Lights), SEAM, Marmousi and other synthetics (flagged
   `notes: synthetic`), Stratton 3D (BEG Texas), Mobil AVO Viking Graben, OpendTect/dGB sets not
   yet listed. TerraNubis entries only when no publisher page exists (cap: three).
3. Every origin is opened by the author in a browser-like fetch or an ordinary browser on the day
   of the record; a 403 to automated requests is recorded in `known_issues` as "blocked for
   automated requests since <date>" (OSD-D9), not as dead.
4. Licence fields as E01 design 4: `unknown` only when the publisher states nothing; never inferred
   from a country; `share_alike: true` for BY-SA families; `licence.url` always present.
5. `region.bbox` on every record whose publisher states an extent; `region.country` always.
6. No schema change. A field the lane wants but the schema lacks goes to `notes` and a line in the
   PR for the planner.

**Acceptance.**
- `uv run osd validate` reports `>= 41 records, 0 problems`.
- Publisher spread, hand counted in the PR: at least eight distinct `region.country` values among
  the new records with a government or survey publisher; at most three new records with
  `terranubis` in the id.
- `licence.redistribution` is `unknown` on at most six of the twenty new records.
- At least fourteen new records carry `region.bbox`.
- The `verify` workflow comment on the PR lists every new record with a level or `blocked`.
- Existing tests pass unchanged; the lane adds no tests.

**Out of scope.** Outlines (E03), checksums and `manifest_url` curation (E02 holds three records;
other records may carry `manifest_url` when the publisher offers a listing), mirrors (E07), any
schema change.

**Stop rules.** A publisher forbids redistribution: record it, continue. A licence page needs a
login: `unknown`, note it, continue. A register's terms forbid automated access: record the
register at the level the verifier observes, note the terms, continue.

**Ownership and dependencies.** Records lane; paths `records/**` except the three E02 files.
Depends on nothing; runs in parallel with E02 and E05 (disjoint paths).

**Evidence to inspect.** `uv run osd status` in the PR body; the verify comment; the hand counts;
a screenshot of the map list with the new count.
