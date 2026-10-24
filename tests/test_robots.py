"""H3: robots.txt read as RFC 9309 reads it (osd.verifier.robots) and judged by osd.verify._Robots.
Each test names the mutation it catches; docs/program/evidence/h3/mutations.md records them red."""

import pytest

from osd.verifier.robots import Rules, parse
from osd.verify import USER_AGENT, FetchError, _Robots

TOKEN = "open-subsurface-data-verifier"
SITE = "https://fixture.test"

# data.qld.gov.au/robots.txt as read on 24 Oct 2026, cut short: blank lines inside the `*` group
QLD = "\nUser-agent: *\n\n\nDisallow: /dataset/rate/\nDisallow: /dataset/*/history\nDisallow: /api/\n"


def ok(text: str, path: str) -> bool:
    return parse(text, TOKEN).allowed(SITE + path)


def test_blank_lines_inside_a_group_do_not_end_it():
    # mutation: a blank line ends the group -> the qld rules belong to no user-agent, all allowed
    assert not ok(QLD, "/api/3/action/package_search?q=petroleum%20wells")
    assert not ok(QLD, "/dataset/rate/x")
    assert ok(QLD, "/dataset/petroleum-wells")


def test_star_matches_any_run_of_characters():
    # mutation: `*` matched literally -> neither rule below matches
    assert not ok(QLD, "/dataset/petroleum-wells/history")
    wallonie = "User-agent: *\nDisallow: /tmp\nDisallow: /*.metadataExport.do*\n"
    assert not ok(wallonie, "/catalogue/srv/fre/x.metadataExport.do?id=1")
    assert ok(wallonie, "/catalogue/351ee778-bbbe-422d-82fd-e7f5d5b0cfbc.html")
    assert not ok("User-agent: *\nDisallow: *private\n", "/a/private/b")


def test_dollar_ends_the_pattern():
    # mutation: `$` ignored (or matched literally) -> /a.pdf?x disallowed, or /a.pdf allowed
    text = "User-agent: *\nDisallow: /*.pdf$\n"
    assert not ok(text, "/docs/a.pdf")
    assert ok(text, "/docs/a.pdf?download=1")
    assert ok(text, "/docs/a.pdfx")


def test_the_longest_match_wins_whatever_the_order():
    # mutation: the first matching rule wins (urllib.robotparser's reading)
    text = "User-agent: *\nAllow: /\nDisallow: /data\nAllow: /data/public\n"
    assert not ok(text, "/data/secret.zip")
    assert ok(text, "/data/public/wells.zip")
    assert ok(text, "/index.html")
    assert not ok("User-agent: *\nAllow: /d\nDisallow: /*.zip\n", "/d/x.zip")  # length of the pattern


@pytest.mark.parametrize("text", ["User-agent: *\nDisallow: /page\nAllow: /page\n",
                                  "User-agent: *\nAllow: /page\nDisallow: /page\n",
                                  "User-agent: *\nDisallow: /pag*\nAllow: /page\n"])
def test_allow_wins_a_tie(text):
    # mutation: a tie keeps the first (or the disallow) -> /page refused
    assert ok(text, "/page")


def test_the_product_token_group_is_chosen_over_star():
    # mutation: `*` tried before the token -> everything refused
    text = ("User-agent: *\nDisallow: /\n\nUser-agent: Open-Subsurface-Data-Verifier\nDisallow: /private\n"
            "\nUser-agent: OtherBot\nDisallow: /\n")
    assert ok(text, "/data.zip")
    assert not ok(text, "/private/x")


def test_the_product_token_is_matched_case_insensitively():
    # mutation: case-sensitive token -> the `*` group (allow all) applies
    assert not ok("User-agent: OPEN-SUBSURFACE-DATA-VERIFIER/0.1\nDisallow: /\n", "/x")


def test_a_token_group_without_rules_allows_everything():
    # mutation: an empty token group falls through to `*` -> refused
    assert ok("User-agent: *\nDisallow: /\n\nUser-agent: open-subsurface-data-verifier\n", "/x")


def test_groups_for_the_token_are_combined():
    # mutation: only the first matching group read -> /baz allowed (RFC 9309 figure 2)
    text = (f"User-agent: {TOKEN}\nDisallow: /foo\nDisallow: /bar\n\n"
            f"User-agent: {TOKEN}\nDisallow: /baz\n")
    assert not ok(text, "/foo") and not ok(text, "/bar") and not ok(text, "/baz")
    assert ok(text, "/qux")


def test_consecutive_user_agent_lines_share_one_group():
    # mutation: each user-agent line opens its own group -> our line has no rules, all allowed
    text = f"User-agent: {TOKEN}\n# both\n\nUser-agent: OtherBot\nDisallow: /x\n"
    assert not ok(text, "/x")
    assert ok(text, "/y")


def test_a_user_agent_line_after_rules_starts_a_new_group():
    # mutation: rules never close the group -> OtherBot's /b joins the `*` group
    text = "User-agent: *\nDisallow: /a\nUser-agent: OtherBot\nDisallow: /b\n"
    assert not ok(text, "/a")
    assert ok(text, "/b")


def test_other_records_neither_end_a_group_nor_count_as_rules():
    text = "User-agent: *\nCrawl-delay: 5\nSitemap: https://fixture.test/s.xml\nUser-agent: x\nDisallow: /x\n"
    assert not ok(text, "/x")


def test_an_empty_disallow_allows():
    # mutation: an empty disallow read as `/` -> everything refused
    assert ok("User-agent: *\nDisallow:\n", "/anything")
    assert ok("User-agent: *\nDisallow: # nothing\n", "/anything")
    assert not ok("User-agent: *\nDisallow:\nDisallow: /x\n", "/x")


def test_rules_before_any_user_agent_are_ignored():
    # mutation: rules outside a group applied as `*` -> refused
    assert ok("Disallow: /\nUser-agent: OtherBot\nDisallow: /\n", "/x")


def test_no_group_for_us_means_no_rules():
    # mutation: no applicable group read as disallow-all -> refused
    assert ok("User-agent: OtherBot\nDisallow: /\n", "/x")
    assert ok("", "/x")


def test_robots_txt_itself_is_always_allowed():
    # mutation: /robots.txt matched like any path -> refused
    assert ok("User-agent: *\nDisallow: /\n", "/robots.txt")
    assert not ok("User-agent: *\nDisallow: /\n", "/robots.txt.bak")


def test_a_byte_order_mark_does_not_hide_the_first_line():
    # mutation: the BOM kept -> the first key reads "﻿user-agent", no group, all allowed
    assert not ok("﻿User-agent: *\nDisallow: /\n", "/x")


@pytest.mark.parametrize("rule, path", [
    ("/foo/bar?baz=quz", "/foo/bar?baz=quz"),             # RFC 9309 figure 4, row 1
    ("/foo/bar/ツ", "/foo/bar/%E3%83%84"),           # row 3: non-ASCII in the rule is encoded
    ("/foo/bar/%E3%83%84", "/foo/bar/ツ"),           # row 4: and in the URL
    ("/foo/bar/%62%61%7A", "/foo/bar/baz"),              # row 5: escaped unreserved octets decoded
    ("/foo/bar", "/foo/%62ar"),                           # ... in the URL too
    ("/foo/%e3%83%84", "/foo/%E3%83%84"),                 # escapes compared in upper case
])
def test_percent_encoding_is_normalised(rule, path):
    # mutations: unreserved escapes kept, escapes compared as written, non-ASCII left raw
    assert not ok(f"User-agent: *\nDisallow: {rule}\n", path)


def test_reserved_escapes_stay_escaped():
    # %2F is not `/`: the escape is reserved, so it is never decoded
    assert ok("User-agent: *\nDisallow: /a/b\n", "/a%2Fb")


def test_literal_star_and_dollar_match_only_their_escapes():
    # mutation: a literal `*` or `$` in the URL left raw -> the escaped patterns of figure 6 miss
    assert not ok("User-agent: *\nDisallow: /path/file-with-a-%2A.html\n", "/path/file-with-a-*.html")
    assert not ok("User-agent: *\nDisallow: /path/foo-%24\n", "/path/foo-$")
    assert ok("User-agent: *\nDisallow: /path/file-with-a-%2A.html\n", "/path/file-with-a-x.html")


def test_disallow_all_and_allow_all():
    assert not Rules.disallow_all().allowed(SITE + "/") and not Rules.disallow_all().allowed(SITE)
    assert Rules().allowed(SITE + "/x")


# --- osd.verify._Robots: status handling unchanged, the body read by the matcher ---------------

def opener_for(answers: dict, calls: list):
    def open_(url):
        calls.append(url)
        a = answers[url]
        if isinstance(a, Exception):
            raise a
        return iter([a.encode()[i:i + 5] for i in range(0, len(a), 5)])
    return open_


def test_the_verifier_names_its_product_token():
    assert _Robots.TOKEN == TOKEN and TOKEN in USER_AGENT


def test_a_2xx_body_is_read_by_the_matcher_once_per_host():
    calls = []
    r = _Robots(opener_for({SITE + "/robots.txt": QLD}, calls))
    assert not r.allowed(SITE + "/api/3/action/package_search?q=x")
    assert r.allowed(SITE + "/dataset/x")
    assert calls == [SITE + "/robots.txt"] and r.unread == {}
    assert r.refusal(SITE + "/api/", "the listing") == "robots.txt disallows the listing"


@pytest.mark.parametrize("status", [401, 403, 404, 410])
def test_robots_4xx_allows_everything(status):
    # mutation: a 4xx treated as unreadable -> refused
    r = _Robots(opener_for({SITE + "/robots.txt": FetchError(SITE + "/robots.txt", status)}, []))
    assert r.allowed(SITE + "/anything") and r.unread == {}


@pytest.mark.parametrize("error, why", [(FetchError(SITE + "/robots.txt", 503), "HTTP 503"),
                                        (FetchError(SITE + "/robots.txt", 0, "timeout"), "timeout"),
                                        (FetchError(SITE + "/robots.txt"), "no answer")])
def test_robots_5xx_or_no_answer_disallows_and_says_why(error, why):
    # mutation: unreachable read as allow-all -> fetched
    r = _Robots(opener_for({SITE + "/robots.txt": error}, []))
    assert not r.allowed(SITE + "/x") and r.unread == {SITE: why}
    assert r.refusal(SITE + "/x", "the listing").startswith(f"robots.txt unreadable ({why}), treated as disallow")
