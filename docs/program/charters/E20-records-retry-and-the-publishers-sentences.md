## E20 Records: the retry, and the publishers' own sentences — QUEUED · Records · no strategy, no Codex round

Authority: owner direction 23 Oct 2026 (open lists plus national registers); E17 and E19 findings
in `docs/program/HANDOFF.md`; OSD-D7, OSD-D9, OSD-D15.

**Outcome.** The publishers that were unreachable on 23 Oct are listed when they answer; the
purchase records state the publisher's own licence sentence, not ours; a potential-fields
publisher that the vocabulary now admits (E19) is in the catalogue; two "origin dead" issues are
either closed by a run that reaches the origin or carry the publisher's current state in the
record.

**Context today (verified 23 Oct, main ad9e624).** 92 records from 18 + 9 countries. record/3
admits `potential-fields`, `origin.access: purchase` and `licence.terms` (E19). Unreached on
23 Oct: SEG-hosted sets (SEAM Phase I, Stratton 3D, Viking Graben line 12; 403 from the runner and
this host), Kochi Core Center (503), GSJ gbank (maintenance), JAMSTEC J-CORES (reset), AOGCC (403),
BRGM (refused), NRCan GDR (TLS), CNSOER, LBEG. No data page found at NUPRC, Ghana PC, Oman MEM.
Open issues: #17 geus/deep-subsurface-data (502), #20 eug/national-data-repository (origin dead).
PASA `licence.terms.stated` carries our notes wording (E19 ruling), the publisher's sentence is on
its obtain-our-technical-data page. Unquoted YAML `expires` under `licence.terms` is refused by
the schema because `src/osd/records.py` coerces dates only for `added` and `period`.

**The design the lane must map to.**
1. E01 design 1, E13 designs 3 to 6, E14 design 1, E17 designs 1 to 3 stand (one record per
   dataset or register; origin opened on the day; blocked is not dead; licence never inferred;
   bbox and period when stated; wants go to `notes` and the PR). Every record an open lane holds
   is out of reach: E21 holds none (check `CLAIMS.md`).
2. Retry, in this order, each opened on the day: NRCan GDR (as `potential-fields` where that is
   what the publisher offers), BRGM, AOGCC, CNSOER, LBEG, Kochi Core Center, GSJ gbank, JAMSTEC
   J-CORES, the SEG-hosted sets. A host that still refuses from here gets no new record and one
   line in the PR (host, status, date). A host that answers gets a record; blocked stays
   `blocked` (OSD-D9), never dead.
3. PASA: replace `licence.terms.stated` with the publisher's sentence, verbatim, and name the page
   and date in `notes`; the same for any other purchase record whose `stated` is not the
   publisher's wording (check NAMCOR, BEG Stratton, DGH).
4. Issues #17 and #20: open each origin on the day; if it answers, write nothing (the next verify
   run closes the issue); if it does not, add one sentence to the record's `notes` with the date
   and the publisher's status page or notice when there is one. Never close an issue by hand.
5. Granted kernel edit (one place): in `src/osd/records.py`, coerce `licence.terms.expires`
   the way `period.start`/`end` are coerced (a date to its ISO string, an int to its string), with
   one test case beside the existing period coercion test. No schema change.
6. Aggregator cap: three records per publisher.

**Acceptance.**
- `uv run osd validate` reports `>= 96 records, 0 problems` (at least four new records; fewer
  only if fewer than four of the retry hosts answer, each refusal named in the PR).
- The PR lists every retry host with answered or refused, status and date.
- Every purchase record's `licence.terms.stated` is a sentence from the publisher's page, with the
  page named in `notes`; the PR quotes each.
- `make check` green; the one records.py case covered by a test; an unquoted `expires` in a
  fixture record validates.
- The `verify` workflow comment on the PR lists every new record with a level or `blocked`.

**Claim.** `records/**` (new files and edits to records no open lane holds), `docs/program/evidence/e20/**`, `src/osd/records.py` (design 5 only), one test case in the module that covers record loading.
