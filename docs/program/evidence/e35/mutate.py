import hashlib, shutil, subprocess, sys
M = [
 ("sort removed", "src/osd/verifier/layers.py",
  '"features": sorted(features, key=lambda f: f["attributes"][oid])}', '"features": features}',
  "test_shuffled_pages_and_features_give_identical_bytes"),
 ("count guard removed", "src/osd/outlines/extractors.py",
  '    if len(seen) != count:\n        raise Refused(f"{name}: the layer counts', '    if False:\n        raise Refused(f"{name}: the layer counts',
  "test_count_guard_alone_catches_an_oversized_final_page"),
 ("feature cap removed", "src/osd/verifier/layers.py",
  'n["count"] > ARCGIS_MAX_FEATURES:', 'n["count"] > 10**9:',
  "test_a_layer_above_the_feature_cap_stays_a_partial_export"),
 ("duplicate check removed", "src/osd/outlines/extractors.py",
  '            if a[oid] in seen:\n                raise Refused(f"{name}: object id', '            if False:\n                raise Refused(f"{name}: object id',
  "test_duplicate_id_fails"),
 ("page-error check removed (error JSON)", "src/osd/outlines/extractors.py",
  '        _arcgis_error(page, what)\n        if check_page:', '        if check_page:',
  "test_error_json_page_fails"),
 ("page-error check removed (HTTP)", "src/osd/verify.py",
  '            raise layers.Incomplete(f"page error: {e}") from None', '            return b"{}"',
  "test_http_page_error_fails"),
 ("robots check bypassed", "src/osd/verify.py",
  '        if not robots.allowed(url):\n            raise layers.Incomplete(robots.refusal(url, f"the layer query {url}"), "skip")',
  '        if False:\n            raise layers.Incomplete(robots.refusal(url, f"the layer query {url}"), "skip")',
  "test_robots_disallow_skips_the_layer"),
 ("pacing removed (injected clock)", "src/osd/verify.py",
  '        def __iter__(self):\n            pacer.wait(self.url)', '        def __iter__(self):\n            pass',
  "test_every_layer_request_is_paced_per_host"),
 ("budget bound removed", "src/osd/verify.py",
  '                if len(chunk) > budget.remaining:\n                    budget.exhaust()\n                    raise layers.Incomplete(',
  '                if False:\n                    budget.exhaust()\n                    raise layers.Incomplete(',
  "test_a_page_over_the_budget_share_is_abandoned_and_counted"),
 ("a layer export written into files", "src/osd/verify.py",
  '                exports.append(x)\n', '                exports.append(x)\n                files.append({"path": "layer", "url": x["layer"], "bytes": x["bytes"], "sha256": x["sha256"]})\n',
  "test_a_layer_export_never_becomes_an_asset"),
 ("id-set equality removed", "src/osd/verifier/layers.py",
  '        if got != set(ids) or len(ids) != len(set(ids)):', '        if False:',
  "test_ids_differing_from_return_ids_only_fail"),
]
out = ["| # | mutation | file | test | mutated | restored |", "|---|---|---|---|---|---|"]
for i, (name, path, old, new, test) in enumerate(M, 1):
    orig = open(path, "rb").read(); sha = hashlib.sha256(orig).hexdigest()
    s = orig.decode(); assert s.count(old) == 1, (name, s.count(old))
    open(path, "w").write(s.replace(old, new))
    assert open(path).read() == s.replace(old, new) != s  # re-read from disk
    r = subprocess.run(["uv", "run", "pytest", "-q", "tests/test_whole_layers.py", "-k", test], capture_output=True, text=True)
    red = r.returncode != 0
    open(path, "wb").write(orig); assert hashlib.sha256(open(path, "rb").read()).hexdigest() == sha
    r2 = subprocess.run(["uv", "run", "pytest", "-q", "tests/test_whole_layers.py", "-k", test], capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if l.startswith(("FAILED", "E "))][:1]
    out.append(f"| {i} | {name} | `{path}` | `{test}` | {'RED' if red else 'GREEN (!)'}: {last[0][:140].replace('|','/') if last else ''} | {'pass' if r2.returncode == 0 else 'FAIL'} |")
    print(out[-1], flush=True)
open(sys.argv[1], "w").write("\n".join(out) + "\n")
