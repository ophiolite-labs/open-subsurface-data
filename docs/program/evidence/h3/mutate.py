import hashlib, os, pathlib, shutil, subprocess, sys
# no bytecode: a mutation of the same length restored in the same second would run a stale .pyc
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
for d in pathlib.Path("src").rglob("__pycache__"):
    shutil.rmtree(d)
R, V = "src/osd/verifier/robots.py", "src/osd/verify.py"
M = [
 ("a blank line ends the group", R,
  "        if not sep:\n            continue",
  "        if not sep:\n            if groups and not line.strip():\n                groups.append((set(), []))\n            continue",
  "test_blank_lines_inside_a_group_do_not_end_it"),
 ("`*` matched literally", R,
  'body = ".*".join(re.escape(part) for part in (path[:-1] if end else path).split("*"))',
  "body = re.escape(path[:-1] if end else path)",
  "test_star_matches_any_run_of_characters"),
 ("`$` anchor dropped", R, '(r"\\Z" if end else "")', '""', "test_dollar_ends_the_pattern"),
 ("first matching rule wins", R, "(best is None or (len(path), allow) > best)", "best is None",
  "test_the_longest_match_wins_whatever_the_order"),
 ("a tie keeps the first rule", R, "(best is None or (len(path), allow) > best)",
  "(best is None or len(path) > best[0])", "test_allow_wins_a_tie"),
 ("`*` tried before the token", R, 'for name in (token.lower(), "*"):', 'for name in ("*", token.lower()):',
  "test_the_product_token_group_is_chosen_over_star"),
 ("token matched case-sensitively", R, ".group().lower()", ".group()",
  "test_the_product_token_is_matched_case_insensitively"),
 ("an empty token group falls through to `*`", R,
  "if matched := [rules for agents, rules in groups if name in agents]:",
  "if matched := [rules for agents, rules in groups if name in agents and rules]:",
  "test_a_token_group_without_rules_allows_everything"),
 ("only the first matching group read", R, "return Rules(tuple(r for rules in matched for r in rules))",
  "return Rules(tuple(matched[0]))", "test_groups_for_the_token_are_combined"),
 ("each user-agent line opens a group", R, "            if not open_:\n", "            if True:\n",
  "test_consecutive_user_agent_lines_share_one_group"),
 ("rules never close the group", R, "            open_ = False\n            if value:", "            if value:",
  "test_a_user_agent_line_after_rules_starts_a_new_group"),
 ("an empty disallow read as `/`", R, "            if value:\n", '            value = value or "/"\n            if value:\n',
  "test_an_empty_disallow_allows"),
 ("rules outside a group applied as `*`", R, 'elif key in ("allow", "disallow") and groups:',
  'elif key in ("allow", "disallow") and (groups or groups.append(({"*"}, [])) or True):',
  "test_rules_before_any_user_agent_are_ignored"),
 ("no applicable group read as disallow-all", R, "            return Rules(tuple(r for rules in matched for r in rules))\n    return Rules()",
  "            return Rules(tuple(r for rules in matched for r in rules))\n    return Rules.disallow_all()",
  "test_no_group_for_us_means_no_rules"),
 ("/robots.txt matched like any path", R, 'if u.path == "/robots.txt":', "if False:",
  "test_robots_txt_itself_is_always_allowed"),
 ("the byte order mark kept", R, 'text.removeprefix("\\ufeff").splitlines()', "text.splitlines()",
  "test_a_byte_order_mark_does_not_hide_the_first_line"),
 ("escaped unreserved octets kept", R, "bytes([o]) if o in UNRESERVED else", "bytes([o]) if False else",
  "test_percent_encoding_is_normalised"),
 ("escapes compared as written", R, 'b"%" + m.group(1).upper()', 'b"%" + m.group(1)',
  "test_percent_encoding_is_normalised"),
 ("non-ASCII octets left raw", R, "o > 0x7E or", "o > 0xFF or", "test_percent_encoding_is_normalised"),
 ("literal `*`/`$` in the URL left raw", R, 'special = b"*$" if url else b""', 'special = b""',
  "test_literal_star_and_dollar_match_only_their_escapes"),
 ("_Robots: a 4xx treated as unreadable", V, "                if 400 <= e.status < 500:", "                if False:",
  "test_robots_4xx_allows_everything"),
 ("_Robots: unreachable read as allow-all", V, "self.hosts[key] = robots_txt.Rules.disallow_all()",
  "self.hosts[key] = robots_txt.Rules()", "test_robots_5xx_or_no_answer_disallows_and_says_why"),
]
out = ["| # | mutation | file | test | mutated | restored |", "|---|---|---|---|---|---|"]
for i, (name, path, old, new, test) in enumerate(M, 1):
    orig = open(path, "rb").read(); sha = hashlib.sha256(orig).hexdigest()
    s = orig.decode(); assert s.count(old) == 1, (name, s.count(old))
    open(path, "w").write(s.replace(old, new))
    assert open(path).read() == s.replace(old, new) != s  # re-read from disk
    r = subprocess.run(["uv", "run", "pytest", "-q", "tests/test_robots.py", "-k", test], capture_output=True, text=True, env=ENV)
    red = r.returncode != 0
    open(path, "wb").write(orig); assert hashlib.sha256(open(path, "rb").read()).hexdigest() == sha
    r2 = subprocess.run(["uv", "run", "pytest", "-q", "tests/test_robots.py", "-k", test], capture_output=True, text=True, env=ENV)
    last = [l for l in r.stdout.splitlines() if l.startswith(("FAILED", "E "))][:1]
    out.append(f"| {i} | {name} | `{path}` | `{test}` | {'RED' if red else 'GREEN (!)'}: {last[0][:140].replace('|','/') if last else ''} | {'pass' if r2.returncode == 0 else 'FAIL'} |")
    print(out[-1], flush=True)
open(sys.argv[1], "w").write("\n".join(out) + "\n")
