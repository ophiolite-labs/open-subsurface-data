"""Apply one mutation at a time, run the named tests, record red/green, restore."""
import subprocess, sys, pathlib
M = [
 ("shard by list position", "src/osd/shards.py",
  "    return [rid for rid, rec in recs.items() if shard_of(origin_host(rec), n) == i]",
  "    return [rid for k, rid in enumerate(recs) if k % n + 1 == i]",
  "tests/test_shards.py::test_a_record_that_sorts_first_moves_no_other_record"),
 ("CLI ignores --shard", "src/osd/cli.py",
  "        ids = shards_mod.select(load_records(), i, n)\n", "",
  "tests/test_shards.py::test_shard_calls_the_verifier_with_exactly_its_ids"),
 ("empty shard calls the verifier (verifies everything)", "src/osd/cli.py",
  " if ids != [] else []", "",
  "tests/test_shards.py::test_an_empty_shard_calls_nothing"),
 ("--shard '' read as no shard", "src/osd/cli.py",
  "    if a.shard is not None:", "    if a.shard:",
  "tests/test_shards.py::test_malformed_shards_and_ids_with_a_shard_are_refused"),
 ("destination deleted before overlay", "src/osd/shards.py",
  "    accepted, discarded = {}, {}\n",
  "    shutil.rmtree(out); out.mkdir()\n    accepted, discarded = {}, {}\n",
  "tests/test_shards.py::test_a_failed_shards_records_keep_their_earlier_files"),
 ("overwrite suppressed", "src/osd/shards.py",
  "            shutil.copyfile(shards_dir", "            (out / _file(rid)).exists() or shutil.copyfile(shards_dir",
  "tests/test_shards.py::test_a_fresh_file_replaces_the_earlier_one"),
 ("foreign id accepted", "src/osd/shards.py",
  "        if shard_of(origin_host(recs[rid]), n) != i:", "        if False:",
  "tests/test_shards.py::test_a_shard_artifact_outside_its_shard_is_discarded"),
 ("--verified all restored in the finishing step", ".github/workflows/verify.yml",
  '--verified "$fresh"', "--verified all",
  "tests/test_shards.py::test_the_finishing_report_passes_only_fresh_ids"),
 ("zero fresh ids guard removed", ".github/workflows/verify.yml",
  'if [ -z "${fresh// /}" ]; then', "if false; then",
  "tests/test_shards.py::test_no_fresh_ids_opens_and_closes_no_issue"),
]
rows = []
for name, path, old, new, test in M:
    p = pathlib.Path(path); src = p.read_text()
    assert src.count(old) == 1, (name, old)
    p.write_text(src.replace(old, new))
    try:
        r = subprocess.run(["uv", "run", "pytest", "-q", "-x", test], capture_output=True, text=True)
    finally:
        p.write_text(src)
    last = r.stdout.strip().splitlines()[-1]
    rows.append(f"| {name} | `{path}` | `{test.split('::')[1]}` | {'RED' if r.returncode else 'green (survived)'}: {last} |")
    print(rows[-1], flush=True)
pathlib.Path(sys.argv[1]).write_text("\n".join(rows) + "\n")
