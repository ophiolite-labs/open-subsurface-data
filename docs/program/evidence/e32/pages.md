# E32 design 5: the staged site against the 500 MB bound

`make build` on the branch (all records, nine registers with outlines, tippecanoe 2.79.0, no
`build/verification`, as CI's `make build` and the Pages job stage it), 23 Oct. Bytes are file
sizes summed over `site/` (`os.walk`), what `actions/upload-pages-artifact` packs.

| Part | Files | Bytes | MB |
|---|---:|---:|---:|
| STAC tree `site/data/stac/` | 178,161 | 196,184,664 | 196.2 |
| of which Items (`*/items/*.json`) | 177,891 | 181,824,312 | 181.8 |
| of which shard Catalogs (`*/shards/*/catalog.json`, 93) | 93 | 13,875,310 | 13.9 |
| of which root catalog and Collections | 177 | 485,042 | 0.5 |
| `outlines.pmtiles` | 1 | 149,894,767 | 149.9 |
| `outlines.geojson` | 1 | 138,278,044 | 138.3 |
| `collections.json` (repeats every Collection's links) | 1 | 724,748 | 0.7 |
| `records.json` | 1 | 445,105 | 0.4 |
| the rest (HTML, JS, CSS, `files.txt`, `mirror.json`, `robots.txt`) | 8 | 51,641 | 0.05 |
| **complete staged site** | **178,173** | **485,578,969** | **485.6** |

Bound: 500 MB (half of GitHub Pages' 1 GB site limit). Met, with 14.4 MB to spare. The Pages
artifact is a tar of these files: 597,678,080 bytes uncompressed here (178,173 headers of 512 bytes
and 512-byte padding per file add 112 MB), 161 MB with gzip -1. Pages' 1 GB limit is on the site;
the artifact's own limit is 10 GB.

Before sharding (E29's tree, nine registers, indented JSON): the largest Collection, North Dakota,
carried 44,018 item links in one `collection.json` and `collections.json` repeated them all; after
it the largest `collection.json` is 96 KB, every Collection holds at most 2,000 links, and
`collections.json` is 0.7 MB.

What grows next: the STAC Items (one ~1 KB file per feature) and `outlines.geojson` (~0.8 KB per
feature) are proportional to features; `outlines.pmtiles` to features and zooms. At ~2.7 KB per
feature in all, the 14.4 MB left is about 5,000 more features; the three registers above 50,000
features (out of scope here) do not fit under this bound as staged today. Four of the five new
outlines are also above OSD-D16's 8 MB per-register allowance in `outlines/` (North Dakota 17.5 MB,
Utah 13.6, BCER 13.3, SGC 9.0; `outlines.md`). Both go to the owner (inbox e32.md).

## Client walk

`uv run --no-project --with pystac python docs/program/evidence/e32/pystac_walk.py` on the staged North Dakota Collection:

```
pystac 1.15.2: nd-dmr--wells: 23 child Catalogs, 44018 Items (44018 distinct), every Item's collection_id ['nd-dmr--wells'], 20.7 s
```

44,018 equals the committed outline's feature count (`outlines/nd-dmr__wells.geojson`, and the day's
`returnCountOnly`, `outlines.md`). The walk is `col.get_items(recursive=True)` from
`site/data/stac/nd-dmr--wells/collection.json`: pystac follows the `child` links to the shards and
their `item` links, with no OSD code.

## Screenshots (phone width, 390 x 844, live basemap)

`node docs/program/evidence/e32/shots.mjs docs/program/evidence/e32` after `make build`:

- `nd-wells-phone.png`: Watford City, ND at zoom 12; North Dakota's wells drawn from the tiles at
  their own positions (well pads along the section lines; 80 rendered in the viewport). The bottom
  sheet is hidden for this shot (`visibility: hidden`) so the whole viewport is map. The page opens
  with the record selected (`#sel=nd-dmr/wells&map=12/47.765/-103.28`): headless Chromium at
  phone width leaves the basemap unpainted while the sheet shows the dataset list (on load, and
  again after the panel is closed), the body colour showing through the canvas; desktop width
  paints it either way, and every earlier phone shot (E15, E21, E27) selects a record. Not checked
  on a real phone; `site/**` is not this lane's (inbox e32.md note 7).
- `nd-dataset-panel-phone.png`: after clicking well `nd-dmr/wells#23634` (HEGG 11-29SH), the
  dataset panel as it is today: the record's title, level, description, why this level and
  publisher; hash `#sel=nd-dmr/wells&map=12.00/47.7650/-103.2800`; no console errors. The level
  reads L0 "never verified" because a local build has no `build/verification`; the published site
  shows the level of the last verify run.
