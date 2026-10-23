"""E32 client walk: pystac reads one staged Collection and counts its Items, shards included.

    uv run --no-project --with pystac python docs/program/evidence/e32/pystac_walk.py site/data/stac/nd-dmr--wells/collection.json
"""
import sys
import time

import pystac

t = time.time()
col = pystac.read_file(sys.argv[1])
assert isinstance(col, pystac.Collection), type(col)
children = list(col.get_children())
items = list(col.get_items(recursive=True))
ids = {i.id for i in items}
print(f"pystac {pystac.__version__}: {col.id}: {len(children)} child Catalogs, {len(items)} Items ({len(ids)} distinct), "
      f"every Item's collection_id {sorted({i.collection_id for i in items})}, {time.time() - t:.1f} s")
