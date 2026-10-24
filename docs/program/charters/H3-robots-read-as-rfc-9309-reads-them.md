## H3 Robots read as RFC 9309 reads them — OPEN · Hardening (kernel, small) · no strategy, no Codex round

Authority: supervisor 24 Oct 2026 on E37's finding (inbox e37, `docs/program/evidence/e37/sources.md`
on branch e37-records-tenth-twenty): data.qld.gov.au's robots.txt puts blank lines between
`User-agent: *` and its `Disallow` lines; `urllib.robotparser` ends the group at the blank line and
reads the file as allow-all. RFC 9309 groups end only at the next `user-agent` line after rules.
`urllib.robotparser` also ignores the `*` and `$` path patterns of RFC 9309 section 2.2.3 and takes
the first matching rule, not the most specific one (section 2.2.2). The verifier, `osd mirror` and
the outline derivation all judge robots through `osd.verify._Robots`, so all three may fetch what a
publisher disallowed.

**Outcome.** Every place that fetches from a publisher obeys robots.txt as RFC 9309 defines it, so
no publisher's disallow is read as an allow because of blank lines, wildcards or rule order.

**The design the lane must map to.**
1. A small RFC 9309 matcher in `src/osd/verifier/robots.py` (new): groups by `user-agent` lines
   (consecutive ones share a group; blank lines and comments ignored), the most specific group for
   the verifier's product token else `*`, rules `allow`/`disallow` with `*` and `$`, the longest
   match wins and `allow` wins a tie, percent-encoding normalised as section 2.2.2 says, an empty
   `disallow` allows. `/robots.txt` itself is always allowed. No new dependency.
2. `_Robots` keeps its status handling (2xx obeyed, 4xx allow-all, 5xx or no answer disallow,
   `unread`, `refusal`) and replaces `urllib.robotparser` with the matcher. Its interface does not
   change, so `mirror.py` and `outlines/__init__.py` are untouched.
3. Tests in `tests/test_robots.py` (new): the data.qld.gov.au shape (blank lines inside a group) is
   a disallow; `*` and `$` patterns; longest match; allow wins a tie; product-token group chosen over
   `*`; consecutive user-agent lines; empty disallow; 4xx/5xx handling unchanged. Each guard in the
   matcher gets a mutation recorded red in `docs/program/evidence/h3/mutations.md`.
4. A dispatch of verify on the branch over all records: list every record whose level changes
   against main's stored results, with the robots line that explains it, in
   `docs/program/evidence/h3/results.md`. A record that loses a level because its publisher
   disallows us is the correct outcome, not a regression.

**Acceptance.** `make check` green inside main's spread; the tests above; the branch run's change
list in the PR.

**Claim.** `src/osd/verify.py` (`_Robots` only), `src/osd/verifier/robots.py` (new),
`tests/test_robots.py` (new), `docs/program/evidence/h3/**`.
