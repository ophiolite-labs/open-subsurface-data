"""The site test's Python half (E06 slice 2): a manifest the page downloaded, read by the CLI's reader.

    python tests/site/manifest_roundtrip.py <page manifest> <assets.json> <dest>

1. `osd.manifest.read` accepts the page's file (schema/manifest.schema.json, sha256 decoded).
2. Its entries equal what `osd manifest` writes for the same ids from the same catalogue, with the
   Collection assets the test served to the page (`assets.json`: collection id -> assets).
3. `osd get <manifest> --dest <dest>` runs on it; its output is the round-trip transcript.
Exit 0 and a last line of JSON (the typed entries) when all three hold.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

from osd import cli
from osd import manifest as mf

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "site" / "data"


def main(page_file: str, assets_file: str, dest: str) -> int:
    m = mf.read(page_file)
    page = json.loads(Path(page_file).read_text())
    assets = json.loads(Path(assets_file).read_text())
    with tempfile.TemporaryDirectory() as tmp:
        cat = Path(tmp)
        shutil.copy(DATA / "records.json", cat / "records.json")
        for e in m.entries:
            col = json.loads((DATA / "stac" / e.collection_id / "collection.json").read_text())
            if e.collection_id in assets:
                col["assets"] = assets[e.collection_id]
            (cat / "stac" / e.collection_id).mkdir(parents=True)
            (cat / "stac" / e.collection_id / "collection.json").write_text(json.dumps(col))
        want = mf.from_catalog([e.record_id for e in m.entries], catalog_dir=cat)
    if page["entries"] != want["entries"] or page["selection"] != want["selection"]:
        print("page manifest differs from osd manifest:", json.dumps(page["entries"]), json.dumps(want["entries"]),
              sep="\n", file=sys.stderr)
        return 1
    print(f"$ osd get {Path(page_file).name} --dest {Path(dest).name}", flush=True)
    code = cli.main(["get", page_file, "--dest", dest])
    print(f"exit {code}", flush=True)
    if code:
        return code
    print(json.dumps([{"record_id": e.record_id, "coverage": e.coverage, "unresolved": e.unresolved,
                       "share_alike": e.licence.share_alike, "statement": e.licence.statement,
                       "sha256": {a.key: a.sha256 for a in e.assets}} for e in m.entries]))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
