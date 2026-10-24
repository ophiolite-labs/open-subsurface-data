"""E38 mutations: each guard removed alone turns its test red (rerun from the repository root:
uv run python docs/program/evidence/e38/mutate.py /tmp/table.md)."""
import hashlib, subprocess, sys
L, V = "src/osd/verifier/layers.py", "src/osd/verify.py"
M = [
 ("sort removed from the canonical bytes", L,
  '"features": sorted(features, key=_fid)}', '"features": features}',
  "test_shuffled_pages_and_features_within_pages_give_identical_bytes"),
 ("count guard removed (WFS hits)", L,
  "    if count is not None and len(pages.features) != count:", "    if False:",
  "test_hits_mismatch_fails_with_unique_ids_and_valid_pages"),
 ("count guard removed (OGC numberMatched)", L,
  "    if count is not None and len(pages.features) != count:", "    if False:",
  "test_number_matched_mismatch_fails_with_unique_ids_and_valid_pages"),
 ("duplicate id check removed", L,
  "            if k in self.seen:\n", "            if False:\n",
  "test_a_duplicate_id_fails"),
 ("paging loop check removed", L,
  "            if url in seen:\n", "            if False:\n",
  "test_a_paging_loop_fails"),
 ("empty page with a next link allowed", L,
  "            if url and not got:\n", "            if False:\n",
  "test_an_empty_page_that_links_a_next_page_fails"),
 ("short WFS page allowed", L,
  "            if not last and got != size:\n", "            if False:\n",
  "test_a_short_wfs_page_before_the_end_fails"),
 ("crs check removed", L,
  '        if self.pages and page.get("crs") != self.crs:', "        if False:",
  "test_a_crs_differing_between_pages_fails"),
 ("missing count read as complete", L,
  "    if count is None:\n        return Outcome(\"unconfirmed\"", "    if False:\n        return Outcome(\"unconfirmed\"",
  "test_a_missing_count_is_unconfirmed_and_earns_no_l2"),
 ("WFS feature cap removed", L,
  "        if count is not None and count > ARCGIS_MAX_FEATURES:\n            reason",
  "        if count is not None and count > 10**9:\n            reason",
  "test_above_the_cap_a_wfs_layer_is_partial_with_the_manifests_export_as_evidence"),
 ("OGC feature cap removed", L,
  "                if count is not None and count > ARCGIS_MAX_FEATURES:", "                if count is not None and count > 10**9:",
  "test_above_the_cap_an_ogc_collection_keeps_its_first_page_as_evidence"),
 ("partial evidence written into files", V,
  'return (check("skip", f"not read whole: {out.reason}{kept}"), [],',
  'return (check("skip", f"not read whole: {out.reason}{kept}"), [out.evidence] if out.evidence else [],',
  "test_above_the_cap_a_wfs_layer_is_partial_with_the_manifests_export_as_evidence"),
 ("ImplementsSorting not read", L,
  '        if caps.constraints.get("ImplementsSorting", "").upper() != "TRUE":', "        if False:",
  "test_a_wfs_that_cannot_be_read_whole_is_partial_and_not_hashed and sorting-false"),
 ("sort property not required", L,
  "        if not sort:\n", "        if False:\n",
  "test_a_wfs_that_cannot_be_read_whole_is_partial_and_not_hashed and no-sort-property"),
 ("robots check bypassed (a later page)", V,
  "        if not robots.allowed(url):\n            raise layers.Incomplete(robots.refusal(url, f\"the layer query {url}\"), \"skip\")",
  "        if False:\n            raise layers.Incomplete(robots.refusal(url, f\"the layer query {url}\"), \"skip\")",
  "test_robots_refusal_on_a_later_page_declines_the_layer"),
 ("budget bound removed", V,
  "                if len(chunk) > budget.remaining:\n                    budget.exhaust()\n                    raise layers.Incomplete(",
  "                if False:\n                    budget.exhaust()\n                    raise layers.Incomplete(",
  "test_a_page_over_the_budget_share_is_abandoned_and_counted"),
 ("OWS exception report not named", L,
  '    if text.startswith("<"):\n        if "ExceptionReport" in text[:2000]:', '    if text.startswith("<"):\n        if False:',
  "test_exception_responses_fail_with_the_publishers_message"),
 ("OGC API exception not named", L,
  '    if isinstance(d, dict) and "code" in d and "description" in d and "features" not in d:', "    if False:",
  "test_exception_responses_fail_with_the_publishers_message"),
 ("dispatch precedence removed (file: true, attachment)", V,
  "    if (service := ogc_service(manifest)) is not None:", "    if False and (service := ogc_service(manifest)) is not None:",
  "test_the_wfs_reader_takes_the_manifest_over_file_true_and_an_attachment_header"),
 ("a complete export written into files (end to end)", V,
  'f"file; {out.reason}"), [], {"layer_exports": [out.entry]}',
  'f"file; {out.reason}"), [{"path": "layer", "url": out.entry["layer"], "bytes": out.entry["bytes"], "sha256": out.entry["sha256"]}], {"layer_exports": [out.entry]}',
  "test_a_complete_layer_passes_l2_as_evidence_never_a_file_or_asset"),
 ("pacing removed (injected clock)", V,
  "        def __iter__(self):\n            pacer.wait(self.url)", "        def __iter__(self):\n            pass",
  "test_every_layer_request_is_paced_per_host"),
]
T = "tests/test_ogc_layers.py"
out = ["| # | mutation | file | test | mutated | restored |", "|---|---|---|---|---|---|"]
for i, (name, path, old, new, test) in enumerate(M, 1):
    orig = open(path, "rb").read(); sha = hashlib.sha256(orig).hexdigest()
    s = orig.decode(); assert s.count(old) == 1, (name, s.count(old))
    open(path, "w").write(s.replace(old, new))
    assert open(path).read() == s.replace(old, new) != s  # re-read from disk
    r = subprocess.run(["uv", "run", "pytest", "-q", T, "-k", test], capture_output=True, text=True)
    red = r.returncode != 0
    open(path, "wb").write(orig); assert hashlib.sha256(open(path, "rb").read()).hexdigest() == sha
    r2 = subprocess.run(["uv", "run", "pytest", "-q", T, "-k", test], capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if l.startswith(("FAILED", "E "))][:1]
    out.append(f"| {i} | {name} | `{path}` | `{test}` | {'RED' if red else 'GREEN (!)'}: {last[0][:140].replace('|','/') if last else ''} | {'pass' if r2.returncode == 0 else 'FAIL'} |")
    print(out[-1], flush=True)
open(sys.argv[1], "w").write("\n".join(out) + "\n")
