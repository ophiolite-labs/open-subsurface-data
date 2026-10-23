import subprocess, pathlib, sys
M = [
 ("schema: licence not required", "schema/manifest.schema.json", '"required": ["collection_id", "record_id", "title", "origin_url", "access", "licence", "assets"]', '"required": ["collection_id", "record_id", "title", "origin_url", "access", "assets"]', "drop_licence"),
 ("schema: href without the credential guard", "schema/manifest.schema.json", '"not": {"pattern": "(?i)', '"x-not": {"pattern": "(?i)', "signed_query"),
 ("schema: href allows userinfo", "schema/manifest.schema.json", '"pattern": "^https?://[^/?#@]+(/|$)"', '"pattern": "^https?://"', "userinfo"),
 ("schema: empty assets without unresolved", "schema/manifest.schema.json", '"then": {"required": ["unresolved"]}', '"then": {}', "no_unresolved"),
 ("schema: asset keys may climb", "schema/manifest.schema.json", '"not": {"pattern": "(^|/)', '"x-not": {"pattern": "(^|/)', "escaping_key"),
 ("reader: any multihash accepted", "src/osd/manifest.py", "if not checksum.startswith(SHA256_MULTIHASH) or len(checksum) != len(SHA256_MULTIHASH) + 64:", "if False:", "test_read_refuses"),
 ("manifest: Item entries copy Collection assets", "src/osd/manifest.py", "e.update(item_id=fid if has_item else None, feature_id=fid, assets={})", "e.update(item_id=fid if has_item else None, feature_id=fid, assets=_assets(col))", "test_item_selection"),
 ("manifest: mixed selection allowed", "src/osd/manifest.py", "if features and len(features) != len(ids):", "if False:", "test_mixed"),
 ("manifest: share_alike defaults to false", "src/osd/manifest.py", '"licence": {k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]}}', '"licence": {"share_alike": False, **{k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]}}}', "test_licence_copied_whole"),
 ("manifest: known_issues dropped", "src/osd/manifest.py", 'e["known_issues"] = list(rec["known_issues"])', 'pass', "test_known_issues"),
 ("get: rename before comparing", "src/osd/get.py", "        if a.size is not None and n != a.size:", "        os.replace(tmp, p)\n        if a.size is not None and n != a.size:", "test_get_corrupt_byte"),
 ("get: run continues after a mismatch", "src/osd/get.py", 'stopped = f"{r.collection_id}/{r.key}"', 'pass', "test_get_corrupt_byte"),
 ("get: checksum-free reported verified", "src/osd/get.py", 'return o("verified" if a.sha256 else "fetched", f"{n} bytes")', 'return o("verified", f"{n} bytes")', "test_get_without_checksum"),
 ("get: size not compared", "src/osd/get.py", "if a.size is not None and n != a.size:", "if False:", "test_get_size_mismatch"),
 ("get: existing file skipped without rehash", "src/osd/get.py", "    if p.is_file():\n", "    if p.is_file():\n        return o(\"verified\", \"already on disk\", False)\n", "test_rerun_repairs"),
 ("get: no containment check", "src/osd/get.py", "if key.startswith((\"/\", \"\\\\\")) or not p.is_relative_to(base) or p == base:", "if False:", "test_get_refuses_escaping"),
 ("get: duplicate targets allowed", "src/osd/get.py", "if p in seen:", "if False:", "test_get_refuses_duplicate"),
 ("get: 401/403 as origin-dead", "src/osd/get.py", "if err.status in (401, 403):", "if False:", "test_get_401"),
 ("get: record title written as the statement", "src/osd/get.py", 'lines.append("- Statement: none stated by the publisher in the record")', 'lines += ["- Statement, verbatim:", "", f"  > {e.title}"]', "test_attribution_missing_statement"),
 ("get: share-alike summary dropped", "src/osd/get.py", 'sa = Counter(_licence_label(e) for e in m.entries if e.licence.share_alike is True)', 'sa = Counter()', "test_cli_get_summary"),
]
for name, f, old, new, k in M:
    p = pathlib.Path(f); s = p.read_text()
    assert s.count(old) == 1, (name, s.count(old))
    p.write_text(s.replace(old, new))
    try:
        r = subprocess.run(["uv", "run", "pytest", "-q", "-x", "tests/test_manifest.py", "-k", k], capture_output=True, text=True)
        last = r.stdout.strip().splitlines()[-1]
        print(f"{'FAILS' if r.returncode else 'PASSES(!)'} | {name} | -k {k} | {last}")
    finally:
        p.write_text(s)
