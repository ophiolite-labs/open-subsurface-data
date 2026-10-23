## E19 Vocabulary from the records lanes: potential fields, purchase, licence terms — QUEUED · Kernel (small) · strategy at lane open · one Codex round

Authority: E13, E14 and E17 findings for the planner in `docs/program/HANDOFF.md` (23 Oct); OSD-D7
(records say what the publisher says), OSD-D11 (record versus tool boundary); Ophiolite E55 kind
registry (kinds overlap where they can).

**Outcome.** A records lane can describe what the three batches could not: gravity and magnetic
data (`potential-fields`), data sold rather than given (`access: purchase`), and licences that end
or require the publisher's review before publication (`licence.terms`), each as the publisher
states it; the site filters and the STAC extension know the new values; nothing existing changes
meaning.

**Context today (verified 23 Oct, main after PR #15).** `schema/record.schema.json`: `origin.access`
enum `anonymous | registration | api | request`; `kinds` enum of 18 values ending in `source-list`;
`licence` object closed (`additionalProperties: false`) with `name, spdx, url, redistribution,
attribution, statement, share_alike`; record/2 additions so far (`inputs`, `period`) stayed at
record/2 because they were additive. The STAC `osd` extension schema (`schema/stac-osd.json`) and
the site's filter chips (`site/app.js`) carry the kind and access vocabularies. 92 records; E17
named four publishers with gravity and magnetics (NRCan, NAMCOR, EUG, PRIME), four that sell data
(BEG Stratton, NAMCOR, DGH, PASA) and one with time-limited terms and pre-publication review (PASA).

**The design the lane must map to.**
1. Additive, record/2 stays: `kinds` gains `potential-fields` (gravity, magnetic, gravity-gradient
   grids and lines); `origin.access` gains `purchase` (a price list or a sales desk stands between
   the person and the files; a free registration is still `registration`); `licence` gains an
   optional closed object `terms: {expires: date|null, review_before_publication: bool|null,
   stated: string}` where `stated` is the publisher's words (same convention as `period.stated`).
2. One vocabulary, three consumers: the record schema is the source; `schema/stac-osd.json`, the
   site's filter chips and labels, and `osd new` prompts read the same lists (a test asserts the
   three agree, so a later addition cannot drift).
3. Verifier: `purchase` origins are reachability-checked like `request` (the page, not the files);
   no level change rules. `terms.expires` in the past makes `osd status` print `terms expired` beside
   the level and E08 opens an issue once (same path as origin dead), never edits the record.
4. Records are not edited in this lane except to use the new values where E17 wrote the want into
   `notes` (NRCan, NAMCOR, EUG, PRIME, BEG, DGH, PASA): the lane moves those facts from `notes`
   into the fields and removes the want sentence, nothing else.

**Acceptance.**
- Schema: a record with each new value validates; `terms` without `stated` is refused; an unknown
  kind or access is still refused (negatives as tests).
- Agreement test across record schema, STAC extension and site vocabulary; mutation: add a kind to
  the record schema only → red.
- Site: the kind chip for `potential-fields` and the access label for `purchase` render in the
  offline site test; filtering by the new kind lists the NRCan record.
- `osd status` shows `terms expired` on a fixture with a past date and nothing on a null; E08's
  issue text for it exists as a fixture; mutation: expiry check dropped → red.
- The seven records read with the new fields; `uv run osd validate` 92 records, 0 problems; the
  verify comment on the PR shows no level change.

**Out of scope.** New kinds beyond `potential-fields`; a price field; licence texts; any record
beyond the seven.

**Stop rules.** None.

**Ownership and dependencies.** Coding lane; paths `schema/record.schema.json`, `schema/stac-osd.json`,
`src/osd/cli.py` (`osd new` prompts, status line), `src/osd/verify.py` (purchase reachability, terms
expiry), `src/osd/curation.py` or wherever E08 composes issues (name at lane open), `site/app.js`
and `site/index.html` (chips and labels), `tests/test_schema.py`, `tests/test_site/**` additions,
`tests/site/site.test.mjs`, the seven records named above, `docs/program/evidence/e19/**`. Depends on
E17 (merged). Touches no E18 file (`stac.py`, `outlines/**`) and none of E07 slice 2.

**Evidence to inspect.** The agreement test; the seven record diffs; the site screenshot with the
new chip; the verify comment.
