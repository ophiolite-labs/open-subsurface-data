# E32 design 3: tiles of nine registers, compared in full

## The cause and the releases tried

Before 2.55.0 tippecanoe's string pool compared two strings by `(int)(ahash - bhash)` of their
64-bit FNV-1a hashes (`swizzlecmp`), so two different strings whose hashes share their low 32 bits
compare equal and the second is written as the first (felt/tippecanoe#239, fixed in 2.55.0). With
nine registers' well names, UWIs and `feature_id`s in one pool, such pairs occur; this is the E18
known red.

`tests/fixtures/tiles/crossing.geojson` carries one such pair per register (README there: the
hashes and the brute-force search). `tests/test_build.py::test_crossing_strings_keep_their_own_features`
on each release (`crossing-runs`, the deb's `usr/bin` first on `PATH`):

```
== tippecanoe v2.49.0   (Ubuntu 24.04 2.49.0-1build1, the old pin)
E             {'feature_id': 'A-001377 WELL'} != {'feature_id': 'crossing/register-b#900540'}
1 failed
== tippecanoe v2.53.0   (Ubuntu 2.53.0-1build1)
E             {'feature_id': 'A-001377 WELL'} != {'feature_id': 'crossing/register-b#900540'}
1 failed
== tippecanoe v2.79.0   (Ubuntu 2.79.0-1, the newest packaged release)
1 passed
```

Pinned: 2.79.0, the Ubuntu `.deb` by sha256
`78261946e0ee8f6cb10c00c4aaf5e66858f0bfb9d870c530d6704fbcc67fb727` in `ci.yml` and `pages.yml`
(it needs libc6 >= 2.38 and libstdc++6 >= 13.1, both on ubuntu-24.04), `TIPPECANOE_PIN = "2.79.0"`;
`test_both_workflows_install_the_pinned_tippecanoe` keeps the two workflows and the constant equal.

## The real tile, every feature both ways

`compare_tiles.py` decodes every z12 tile of the built `outlines.pmtiles` (all nine registers,
177,895 outline features, 724,097 tile pieces) and compares it with `outlines.geojson` in both
directions: every GeoJSON feature in a tile and every tile feature a GeoJSON feature; `feature_id`,
`kind`, `title` and every other property equal; geometry type equal; a point exactly on the
position tippecanoe's z12 grid gives the GeoJSON position; a line or polygon's extent within one
grid unit.

| | 2.49.0 (`compare-2.49.0.txt`) | 2.79.0 (`compare-2.79.0.txt`) |
|---|---:|---:|
| GeoJSON features found in z12 tiles | 177,893 of 177,895 | 177,895 of 177,895 |
| tile features that are no GeoJSON feature | 2 | 0 |
| properties crossed (`name`, `uwi`, `publisher_id`) | 26 | 0 |
| `feature_id`, `kind`, `title` differ | 0 | 0 |
| points off their grid position | 0 | 0 |
| polygon extents off by more than one grid unit | 76 (Sodir surveys) | 76 (the same) |
| **differences** | **106** | **76** |

On 2.49 a BCER well name is the identity of a Utah feature and a BCER-style name that of a North Dakota one, two features vanish under another's
identity (nd-dmr/wells#18505, ut-dogm/oil-gas-wells#11965), and names and UWIs cross between
North Dakota, Utah, SGC, BCER, Virginia and New Zealand. On 2.79 none.

**Points and 1e-6 degrees.** MVT stores integer tile coordinates: at z12 with extent 4096 one unit
is 2.15e-5 degrees of longitude, so a tile cannot hold a position to 1e-6 degrees on any release.
The check that can be exact is the one made: every one of the 175,012 points sits exactly where
tippecanoe's grid puts its GeoJSON position (rounded at the 2^32 world, then to the tile grid);
the largest offset from the unrounded position is 0.502 grid units, 1.08e-5 degrees. The charter's
"point coordinates to 1e-6" is met in the outline files and STAC Items, which keep the
publisher's coordinates; in tiles it is the grid (inbox e32.md).

**76 Sodir survey polygons.** Their extents in the tiles are smaller than in the GeoJSON (median
1,137 square grid units of the polygon outside the tile extent, largest 5.2 % of a polygon's area,
`sodir/factpages#survey/9052`). The same 76, byte for byte the same lines, on 2.49 and 2.79, and on
a single-feature tile of one of them, so they come from tippecanoe's polygon clipping and cleaning
of these large, partly self-intersecting outlines (3 of the 76 are invalid polygons), not from the
string pool and not from E32's registers: with `--no-clipping` survey 7659's extent is exact,
7062's is off by 5 units. Sodir's polygons were tiled this way since E15; a later tiles lane can
take them (inbox e32.md).
