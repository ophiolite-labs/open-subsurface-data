"""E52 acceptance 1, one-off: no record field other than region.national, region.country and notes
changed against a base commit. Usage: uv run python docs/program/evidence/e52/check_diff.py [base]"""
import copy
import subprocess
import sys

import yaml

ALLOWED = (("region", "national"), ("region", "country"), ("notes",))


def strip(doc: dict) -> dict:
    d = copy.deepcopy(doc)
    for path in ALLOWED:
        node = d
        for key in path[:-1]:
            node = node.get(key) or {}
        node.pop(path[-1], None)
    return d


def main(base: str = "main") -> int:
    changed = subprocess.run(["git", "diff", "--name-only", base, "--", "records/"],
                             capture_output=True, text=True, check=True).stdout.split()
    bad, national = [], 0
    for path in changed:
        old = subprocess.run(["git", "show", f"{base}:{path}"], capture_output=True, text=True)
        if old.returncode:
            bad.append(f"{path}: new file")
            continue
        try:
            new_doc = yaml.safe_load(open(path))
        except FileNotFoundError:
            bad.append(f"{path}: deleted")
            continue
        old_doc = yaml.safe_load(old.stdout)
        if strip(old_doc) != strip(new_doc):
            bad.append(f"{path}: a field outside region.national, region.country, notes changed")
        if (new_doc.get("region") or {}).get("national"):
            national += 1
        if old_doc.get("licence") != new_doc.get("licence"):
            bad.append(f"{path}: licence changed")
    print(f"records changed: {len(changed)}; national: true in changed records: {national}")
    print(f"fields changed outside region.national, region.country, notes: {len(bad)}")
    for line in bad:
        print("  " + line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
