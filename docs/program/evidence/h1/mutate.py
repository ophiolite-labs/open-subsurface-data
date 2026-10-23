"""Apply each mutation, run the named test against the unchanged suite, expect red, restore."""
import subprocess, sys
from pathlib import Path

R, V = "tests/test_report.py::", "tests/test_verify.py::"
REP, CLI, VER, LST, WF = "src/osd/report.py", "src/osd/cli.py", "src/osd/verify.py", "src/osd/verifier/listings.py", ".github/workflows/verify.yml"
M = [
 ("M1", "recovery without the L1+ test", REP, 'if v.get("level", "L0") == "L0":\n            continue', 'if False:\n            continue', R+"test_dead_or_blocked_is_not_recovered"),
 ("M2", "title and label match dropped", REP, 'if not _labelled(i) or not i["title"].startswith(prefix):', 'if False:', R+"test_recovered_needs_an_open_issue_with_the_exact_title_and_label"),
 ("M3", "verified ids ignored", REP, 'if verified != "all" and rid not in verified:', 'if False:', R+"test_retained_result_not_verified_this_run_is_not_recovered"),
 ("M4", "absent result treated as reachable", REP, 'if v is None:\n            continue', 'if v is None:\n            v = {"level": "L1", "checked_at": "x", "origin": {}}', R+"test_record_absent_is_not_recovered"),
 ("M5", "recovery behind the fell-from-L1+ skip", REP, '"recovered": recovered(after_dir, issues, verified, run_url),', '"recovered": [x for x in recovered(after_dir, issues, verified, run_url) if _results(before_dir).get(x["record_id"], {}).get("level", "L0") != "L0"],', R+"test_previous_L0_now_L1_counts_as_recovered"),
 ("M6", "unreadable issue list read as none open", REP, '    except (OSError, ValueError):\n        return None', '    except (OSError, ValueError):\n        return []', R+"test_issue_enumeration_failure_mutates_nothing " + R+"test_failed_issue_listing_in_the_workflow_mutates_nothing"),
 ("M7", "workflow reads the old array", WF, "jq -c '.open[]' report.json", "jq -c '.[]' report.json", R+"test_workflow_consumes_open_and_recovered"),
 ("M8", "workflow skips .recovered[]", WF, "jq -c '.recovered[]' report.json", "jq -c '.recovered[]' /dev/null", R+"test_workflow_consumes_open_and_recovered"),
 ("M9", "dry guard removed from the step", WF, 'if [ -z "$dry" ]; then', 'if true; then', R+"test_dry_run_mutates_nothing"),
 ("M10", "close by title, not number", WF, 'gh issue close "$(jq -r .number <<<"$issue")"', 'gh issue close "$(jq -r .title <<<"$issue")"', R+"test_workflow_consumes_open_and_recovered"),
 ("M11", "run left out of the closing comment", REP, 'return (f"The origin of `{rid}` answers again: {run} of', 'return (f"The origin of `{rid}` answers again: a run of', R+"test_recovered_closes_by_number_with_the_run_named"),
 ("M12", "open dedupe by listed issues removed", REP, 'r = dead_reports(before_dir, after_dir, {i["title"] for i in issues})', 'r = dead_reports(before_dir, after_dir)', R+"test_two_runs_against_one_issue_state_mutate_once"),
 ("M13", "browser asked before the retry", VER, '    f = probe(url, fetch)\n    reach, detail', '    if browser_probe and fetch(url).status >= 500:\n        browser_probe(url)\n    f = probe(url, fetch)\n    reach, detail', V+"test_503_then_200_is_L1_without_browser_probe"),
 ("M14", "browser answer not consulted", VER, 'if reach == "dead" and (browser := hides(f, url, browser_probe)):', 'if False and (browser := hides(f, url, browser_probe)):', V+"test_terminal_dead_answering_a_browser_is_blocked"),
 ("M15", "browser asked after every dead answer", VER, 'if browser_probe is None or not (f.status in BROWSER_RETRY or f.status >= 500):', 'if browser_probe is None:', V+"test_browser_probe_only_after_404_410_5xx"),
 ("M16", "any browser answer below 400 accepted", VER, 'if not 200 <= status < 300:', 'if not 200 <= status < 400:', V+"test_browser_failure_leaves_dead"),
 ("M17", "browser's final URL held to the origin host", VER, '    status, _ = browser_probe(url)\n', '    status, final = browser_probe(url)\n    if urlsplit(final).hostname != urlsplit(url).hostname:\n        return None\n', V+"test_browser_redirect_to_2xx_counts"),
 ("M18", "browser asked on a challenge too", VER, 'if reach == "dead" and (browser := hides(f, url, browser_probe)):', 'if reach in ("dead", "blocked") and (browser := hides(f, url, browser_probe)):', V+"test_challenge_after_404_is_blocked_without_browser_probe"),
 ("M19", "browser probe reads its response", VER, '            return resp.status, resp.geturl()\n    except urllib.error.HTTPError as e:\n        e.close()', '            resp.read()\n            return resp.status, resp.geturl()\n    except urllib.error.HTTPError as e:\n        e.close()', V+"test_browser_probe_never_reads_a_body"),
 ("M20", "opener sends the browser agent", VER, '        req = urllib.request.Request(self.url, headers={"User-Agent": USER_AGENT})', '        req = urllib.request.Request(self.url, headers={"User-Agent": BROWSER_USER_AGENT})', V+"test_browser_agent_only_on_the_origin_request"),
 ("M21", "browser probe unpaced", VER, '    def b(url: str) -> tuple[int, str]:\n        pacer.wait(url)', '    def b(url: str) -> tuple[int, str]:\n        pass', V+"test_browser_probe_is_paced"),
 ("M22", "origin detail dropped from osd verify", CLI, '(origin {o.get(\'reachability\')} HTTP {o.get(\'http_status\')}: {l1}; "', '(origin {o.get(\'reachability\')} HTTP {o.get(\'http_status\')}; "', V+"test_cli_verify_prints_the_origin_detail"),
 ("M23", "blocked reason dropped from osd status", CLI, 'if v.get("origin", {}).get("reachability") == "blocked":', 'if False:', V+"test_status_reason_names_why_blocked"),
 ("M24", "content-type rule removed", LST, 'return bool(t) and t not in LISTING_TYPES and not t.endswith(("+json", "+xml"))', 'return False', V+"test_file_manifest_is_the_one_entry[content-type]"),
 ("M25", "attachment rule removed", LST, '.strip().lower() == "attachment":', '.strip().lower() == "inline":', V+"test_file_manifest_is_the_one_entry[attachment]"),
 ("M26", "file: true ignored", VER, 'is_file, sample = sample.get("file") is True, sample.get("sample", ["*"])', 'is_file, sample = False, sample.get("sample", ["*"])', V+"test_file_manifest_is_the_one_entry[file-flag]"),
 ("M27", "CSV rows read as URLs", LST, '"application/xml", "text/xml", "text/plain"})', '"application/xml", "text/xml", "text/plain", "text/csv"})', V+"test_csv_manifest_is_a_file_not_a_url_list"),
 ("M28", "file manifest opened again to hash it", VER, '_digest(opened.pop(e.url, None) or opener(e.url), budget,', '_digest(opener(e.url), budget,', V+"test_file_manifest_is_fetched_once"),
 ("M29", "Content-Length ignored", VER, 'listing = file_listing(manifest, getattr(stream, "content_length", None))', 'listing = file_listing(manifest)', V+"test_file_manifest_over_budget_is_not_hashed"),
 ("M30", "5xx robots.txt allowed", VER, '                if 400 <= e.status < 500:\n                    rp.allow_all = True', '                if 400 <= e.status < 600:\n                    rp.allow_all = True', V+"test_robots_5xx_is_unreadable_and_treated_as_disallow"),
 ("M31", "unreadable robots called a disallow", VER, '        if why := self.unread.get(f"{u.scheme}://{u.netloc}"):\n            return f"robots.txt unreadable', '        if False:\n            return f"robots.txt unreadable', V+"test_robots_5xx_is_unreadable_and_treated_as_disallow"),
 ("M32", "404 robots.txt treated as unreadable", VER, '                if 400 <= e.status < 500:\n                    rp.allow_all = True', '                if False:\n                    rp.allow_all = True', V+"test_robots_404_allows"),
]
rows = []
for mid, name, path, old, new, tests in M:
    p = Path(path); src = p.read_text()
    assert src.count(old) == 1, (mid, src.count(old))
    p.write_text(src.replace(old, new))
    try:
        r = subprocess.run(["uv", "run", "pytest", "-q", "-p", "no:cacheprovider", *tests.split()], capture_output=True, text=True)
        tail = [l for l in r.stdout.splitlines() if " failed" in l or " passed" in l][-1:]
    finally:
        p.write_text(src)
    red = r.returncode != 0
    rows.append((mid, name, path, tests.replace("tests/", "").replace(" ", ", "), "red" if red else "GREEN (survived)", tail[0] if tail else r.stdout[-200:]))
    print(mid, "red" if red else "SURVIVED", tail, flush=True)
assert subprocess.run(["git", "diff", "--quiet", "--", "src", ".github"]).returncode == 0, "not restored"
out = ["# H1 mutations", "", "Each mutation applied alone to the code at the lane's head, the named tests run against the",
       "unchanged suite, the code restored (`git diff` empty afterwards). Script: `uv run python docs/program/evidence/h1/mutate.py` from the repository root.", "",
       "| # | Mutation | File | Test(s) | Result |", "|---|---|---|---|---|"]
out += [f"| {m} | {n} | `{p}` | `{t}` | {res}: {tail} |" for m, n, p, t, res, tail in rows]
Path("docs/program/evidence/h1/mutations.md").write_text("\n".join(out) + "\n")
sys.exit(any("SURVIVED" in r[4] for r in rows))
