## H1 Origins that recover, and origins that hide from robots — QUEUED · Kernel (hardening) · one Codex round

Authority: E02 (verifier levels), E08 (curation that runs itself), OSD-D9 (blocked awards no
level); the E22 and E23 findings in `docs/program/HANDOFF.md`.

**Outcome.** An origin-dead issue closes by itself when the origin answers again, with the run
that saw it; and a publisher that answers a browser but hides from the verifier is called
`blocked`, not dead, so no false issue is opened and the map says "blocked" as OSD-D9 means it.

**Context today (verified 23 Oct, main 3ece7a2).** `osd report` (`src/osd/report.py`) compares the
previous and current verification results and emits one issue per record that fell from L1+ to
dead, skipping titles already open; `verify.yml` creates those issues on a dispatch on main. Nothing
closes them: #20 (EUG) and #28/#29 (SPE) stayed open after the origins answered, and the supervisor
closed them by hand on 23 Oct. The verifier (`src/osd/verify.py`) probes the origin with its own
user agent and classifies 403 and challenge pages as `blocked` (OSD-D9) and 404/5xx/timeouts as
dead. New Mexico OCD and Pennsylvania DEP (ArcGIS Hub) and ohiodnr.gov answer 404 to the verifier's
agent and 200 to a browser agent; from the runner they count as dead and E08 would open issues for
them on the next fall. Seven origin-dead issues are open for the CO2 DataShare outage (real, HTTP
500) and GEUS (404 on every page).

**The design the lane must map to.**
1. Recovery: `osd report` also emits a `recovered` list: open `origin dead: <id>` titles whose
   record is at L1 or above in the current results (the before/after comparison already has
   both). `verify.yml` closes each with a comment naming the run id, the level and `checked_at`.
   Output stays in one JSON document (`{"open": [...], "recovered": [...]}`); the workflow's
   `jq length` reads `.open`. Dry run prints what it would close.
2. Hiding publishers: when the first probe answers 404, 410 or 5xx, the verifier sends one more
   probe of the same URL with a browser-like user agent (constant in `verify.py`, named for
   what it is); if that answers 2xx or 3xx-to-2xx, the outcome is `blocked` with detail "answers a
   browser, not the verifier (HTTP <first> to osd-verifier, HTTP <second> to a browser agent)"
   and no origin-dead issue is opened (blocked is not dead, OSD-D9). The verifier never uses the
   browser agent to fetch content, listings or licence text; the probe reads headers only
   (`Range: bytes=0-0`). Record this as OSD-D20 in `DECISIONS.md`.
3. Tests: recovered list derived from fixtures (open titles, before/after results), closing is
   idempotent (a closed title is not in the next run's open titles, so nothing happens), dry run
   emits no close; the second probe happens only after 404/410/5xx (opener records every request
   and its agent), never after 403 or 2xx, never fetches a body; mutation list in the PR.
4. The seven open issues are left to the workflow: the first dispatched run on main after the
   merge closes the ones whose origin answers.

**Acceptance.**
- `osd report --dry-run` on a fixture pair prints the open and recovered lines; the PR shows
  the dispatched run on main closing at least one issue (or states that none recovered today).
- NM OCD, PA DEP and ODNR show `blocked` in the PR's verify comment, with the two status codes.
- `make check` green; `verification/4` unchanged (the detail is a string).

**Claim.** `src/osd/report.py`, `src/osd/verify.py` (probe classification only), `src/osd/cli.py` (report output only), `.github/workflows/verify.yml` (the report step), `tests/test_report.py`, `tests/test_verify.py` (additions only), `docs/program/DECISIONS.md` (OSD-D20), `docs/program/charters/H1-*STRATEGY.md`, `docs/program/evidence/h1/**`.
