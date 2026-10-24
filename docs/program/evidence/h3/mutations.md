# H3 mutations (24 Oct 2026, branch h3-robots-rfc-9309 at 4e758e8)

Each mutation is one literal edit applied by `mutate.py` (this directory): the file is copied aside,
the edit applied and re-read from disk, the named test in `tests/test_robots.py` run (RED expected),
the original bytes written back and their SHA-256 compared, the test run again (pass). Bytecode is
off and `src/**/__pycache__` removed first: a same-length edit restored within the same second
otherwise runs a stale `.pyc` (a first run showed row 6 green and row 19's restore failing for that
reason alone). Rerun with `uv run python docs/program/evidence/h3/mutate.py /tmp/table.md` from the
repository root.

Rows 1-20 are the matcher's guards (`src/osd/verifier/robots.py`); rows 21-22 the status handling
`_Robots` keeps (the H1 tests in `tests/test_verify.py` guard the same lines with their wording).
Row 10's test first put the product token after the other agent, where a group per line still
reads the rule; the test now puts the token first, so the rule only reaches it through the shared group.

| # | mutation | file | test | mutated | restored |
|---|---|---|---|---|---|
| 1 | a blank line ends the group | `src/osd/verifier/robots.py` | `test_blank_lines_inside_a_group_do_not_end_it` | RED: E       AssertionError: assert not True | pass |
| 2 | `*` matched literally | `src/osd/verifier/robots.py` | `test_star_matches_any_run_of_characters` | RED: E       AssertionError: assert not True | pass |
| 3 | `$` anchor dropped | `src/osd/verifier/robots.py` | `test_dollar_ends_the_pattern` | RED: E       AssertionError: assert False | pass |
| 4 | first matching rule wins | `src/osd/verifier/robots.py` | `test_the_longest_match_wins_whatever_the_order` | RED: E       AssertionError: assert not True | pass |
| 5 | a tie keeps the first rule | `src/osd/verifier/robots.py` | `test_allow_wins_a_tie` | RED: E       AssertionError: assert False | pass |
| 6 | `*` tried before the token | `src/osd/verifier/robots.py` | `test_the_product_token_group_is_chosen_over_star` | RED: E       AssertionError: assert False | pass |
| 7 | token matched case-sensitively | `src/osd/verifier/robots.py` | `test_the_product_token_is_matched_case_insensitively` | RED: E       AssertionError: assert not True | pass |
| 8 | an empty token group falls through to `*` | `src/osd/verifier/robots.py` | `test_a_token_group_without_rules_allows_everything` | RED: E       AssertionError: assert False | pass |
| 9 | only the first matching group read | `src/osd/verifier/robots.py` | `test_groups_for_the_token_are_combined` | RED: E       AssertionError: assert (not False and not False and not True) | pass |
| 10 | each user-agent line opens a group | `src/osd/verifier/robots.py` | `test_consecutive_user_agent_lines_share_one_group` | RED: E       AssertionError: assert not True | pass |
| 11 | rules never close the group | `src/osd/verifier/robots.py` | `test_a_user_agent_line_after_rules_starts_a_new_group` | RED: E       AssertionError: assert False | pass |
| 12 | an empty disallow read as `/` | `src/osd/verifier/robots.py` | `test_an_empty_disallow_allows` | RED: E       AssertionError: assert False | pass |
| 13 | rules outside a group applied as `*` | `src/osd/verifier/robots.py` | `test_rules_before_any_user_agent_are_ignored` | RED: E       AssertionError: assert False | pass |
| 14 | no applicable group read as disallow-all | `src/osd/verifier/robots.py` | `test_no_group_for_us_means_no_rules` | RED: E       AssertionError: assert False | pass |
| 15 | /robots.txt matched like any path | `src/osd/verifier/robots.py` | `test_robots_txt_itself_is_always_allowed` | RED: E       AssertionError: assert False | pass |
| 16 | the byte order mark kept | `src/osd/verifier/robots.py` | `test_a_byte_order_mark_does_not_hide_the_first_line` | RED: E       AssertionError: assert not True | pass |
| 17 | escaped unreserved octets kept | `src/osd/verifier/robots.py` | `test_percent_encoding_is_normalised` | RED: E       AssertionError: assert not True | pass |
| 18 | escapes compared as written | `src/osd/verifier/robots.py` | `test_percent_encoding_is_normalised` | RED: E       AssertionError: assert not True | pass |
| 19 | non-ASCII octets left raw | `src/osd/verifier/robots.py` | `test_percent_encoding_is_normalised` | RED: E       AssertionError: assert not True | pass |
| 20 | literal `*`/`$` in the URL left raw | `src/osd/verifier/robots.py` | `test_literal_star_and_dollar_match_only_their_escapes` | RED: E       AssertionError: assert not True | pass |
| 21 | _Robots: a 4xx treated as unreadable | `src/osd/verify.py` | `test_robots_4xx_allows_everything` | RED: E       AssertionError: assert (False) | pass |
| 22 | _Robots: unreachable read as allow-all | `src/osd/verify.py` | `test_robots_5xx_or_no_answer_disallows_and_says_why` | RED: E       AssertionError: assert (not True) | pass |
