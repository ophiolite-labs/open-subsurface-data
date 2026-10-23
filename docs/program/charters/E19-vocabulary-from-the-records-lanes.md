## E19 Vocabulary from the records lanes: potential fields, purchase, licence terms — QUEUED · Kernel (small) · strategy at lane open · Codex round done 23 Oct (REWORK, dispositions below; no second round)

Authority: E13, E14 and E17 findings for the planner in `docs/program/HANDOFF.md` (23 Oct); OSD-D7,
OSD-D11; AGENTS.md schema-change rule (bump the `$id`, keep old files validating, name the change in
the PR title); E06 and E09 dispositions (licence fields travel whole through the manifest).

**Outcome.** A record can say that a dataset holds gravity or magnetic data (`potential-fields`),
that the files are sold (`origin.access: purchase`), and what the publisher's terms say about
duration and pre-publication review (`licence.terms`), each as the publisher states it; the manifest,
`osd get`, the STAC output and the site carry the new values through unchanged; existing records
and manifests keep validating.

**Context today (verified 23 Oct, main after PR #16).** `schema/record.schema.json` (record/2):
`origin.access` enum `anonymous | registration | api | request`; 18 kinds; closed seven-field
`licence`. record/1 → record/2 was a `$id` bump for `inputs`; `period` was the only addition kept at
/2. `schema/manifest.schema.json` (manifest/3) repeats the access enum and the licence allowlist;
`src/osd/manifest.py` and `site/app.js` carry licence allowlists. The STAC extension
(`schema/stac-osd.json`) defines access, not kinds; kinds are STAC `keywords`. Site chips derive
from the records present. `src/osd/new.py` carries the access choices as scaffold comments. 92
records; PRIME's summary names gravity and magnetics, BEG's want is in `known_issues`, PASA states
"at most 10 years" per purchase and a pre-publication review; NRCan has no record (unreachable,
E17), so nothing here concerns NRCan.

**The design the lane must map to.**
1. record/3: `kinds` gains `potential-fields`; `origin.access` gains `purchase` (a price list or
   sales desk between the person and the files; a free account is `registration`); `licence` gains
   an optional closed `terms: {duration: string|null, review_before_publication: bool|null,
   expires: date|null, stated: string}` where `stated` is the publisher's words, `duration` the
   publisher's conditional wording ("at most 10 years from purchase"), `expires` only an absolute
   publisher-stated calendar date (UTC day boundary), never computed. record/2 files validate under
   their own schema in the compatibility test.
2. manifest/4: the access enum and the licence allowlist admit the new values; manifest/1–3 still
   read; `src/osd/manifest.py` and `site/app.js` preserve `terms` field by field (absence kept);
   `osd get` writes the `stated` terms into ATTRIBUTION.md under the licence lines.
3. STAC: `schema/stac-osd.json` access enum gains `purchase` (`$id` bumped, old files validate;
   shared with E18: second to merge rebases); `potential-fields` appears as a keyword; no new
   vocabulary copies anywhere; `src/osd/new.py` scaffold comments list the schema's values and a
   test reads them from the schema.
4. `osd status` prints `terms expire <date>` beside the level for an absolute `expires`, with an
   injected clock for tests; no issue automation in this lane (E08's report path is untouched).
5. Records, exact edits and nothing else: `prime/national-oil-gas-database` kinds +
   `potential-fields`; `eug/national-data-repository` kinds + `potential-fields` (only if its own
   text names gravity or magnetics; else no edit, said in the PR); `namcor/exploration-production-data`
   kinds + `potential-fields` on the same condition and `access: purchase`; `beg/stratton-3d`
   `access: purchase` and the want sentence removed from `known_issues`; `dgh/national-data-repository`
   `access: purchase`; `pasa/national-petroleum-exploration-database` `access: purchase` and
   `terms: {duration: "at most 10 years from purchase" (publisher's words), review_before_publication:
   true, expires: null, stated: <verbatim>}`. Every edit cites the record's own existing text or
   evidence; nothing is re-fetched.

**Acceptance.**
- record/3 fixtures: each new value validates; `terms` without `stated` refused; `expires` not a
  date refused; unknown kind or access refused; record/2 fixtures validate under record/2.
- Manifest: a record with `purchase` and full `terms` round-trips build → `osd manifest` →
  `osd.manifest.read` with exact values and exact absence; manifest/1–3 fixtures still read;
  the browser path (site select mode test) emits the same `terms` object; mutation: Python
  allowlist unchanged → red; browser allowlist unchanged → red.
- STAC: the emitted Collection for the fixture carries `osd:access: purchase` and the keyword;
  validates offline; a stac-osd/1 file still validates.
- Status: injected clock; past, today, future, null, absent, malformed each asserted; mutation:
  comparison dropped → red.
- Site: with a fixture catalogue holding one `potential-fields` record and one without, the chip
  appears and filtering includes the one and excludes the other.
- Verification unchanged: identical injected responses for a record before and after `request →
  purchase` give identical checks and level.
- The six record diffs show exactly the named fields; `uv run osd validate` 92 records, 0 problems.

**Out of scope.** Issue automation for expiry (E08 later); NRCan (records lane); prices; licence
texts; new kinds beyond `potential-fields`.

**Stop rules.** None.

**Ownership and dependencies.** Coding lane; paths `schema/record.schema.json` (record/3),
`schema/manifest.schema.json` (manifest/4), `schema/stac-osd.json` (access enum; shared with E18),
`schema/stac/schema-map.json`, `src/osd/manifest.py`, `src/osd/get.py` (terms in ATTRIBUTION.md),
`src/osd/stac.py` (access value pass-through only; shared with E18, second to merge rebases),
`src/osd/cli.py` (status line), `src/osd/new.py` (scaffold comments), `site/app.js`,
`tests/test_schema.py`, `tests/test_manifest.py`, `tests/site/site.test.mjs`, `tests/fixtures/**`
additions, the six records named in design 5, `docs/program/evidence/e19/**`. Depends on E17, E09
slice 1 (merged).

**Evidence to inspect.** The six record diffs; the manifest round-trip transcript; the site
screenshot with the chip; the status lines; the mutation list.

**Dispositions of the Codex round (23 Oct).** Accepted: versioning per AGENTS.md (record/3,
manifest/4, stac-osd `$id`) with compatibility tests; manifest and browser allowlists extended and
tested for exact preservation (E06/E09 integration claimed); expiry model corrected (duration in the
publisher's words, absolute `expires` only when stated, never computed, UTC day boundary); vocabulary
copies dropped in favour of tests on emitted STAC, data-derived chips and schema-read scaffold
comments; issue automation deferred to keep E08's paths untouched; NRCan removed, Laurentian not
touched, the six records named with field-exact edits sourced from their own text; acceptance
rewritten with exact values, negative records, injected clock, identical-response verification
comparison and per-guard mutations. Refuted: none.
