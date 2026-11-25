# Area sources (E46)

The committed area files and where each was taken from. `osd areas prepare <kind> <file>` writes
each file from the publisher's file by its rule in `prepare.yaml`; the publisher's files are not
committed. A source without read terms is not drawn (R-S5). Digests are SHA-256 of the publisher's
file as retrieved, the same as `source.sha256` in each area file.

| File | Source | Edition | Retrieved | SHA-256 of the publisher's file | Areas |
|---|---|---|---|---|---|
| `country.geojson` | Natural Earth 1:50m Cultural Vectors, Admin 0 – Countries, <https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip> | 5.1.1 | 2026-11-25 | `5fed433373581fa648920435f937d95f2d3c0200e067409c6478dcdf1b853139` | 237 |
| `province.geojson` | Natural Earth 1:10m Cultural Vectors, Admin 1 – States, Provinces, <https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip> | 5.1.1 | 2026-11-25 | `efc59726337323058f9446210adc96673179cd344e053666ee3d28cb58ba2b05` | 4,546 |
| `basin.geojson` | U.S. Geological Survey, Geologic Provinces of the World, 2000 World Petroleum Assessment, all defined provinces (WEP_PRVG), <https://doi.org/10.5066/P9RMSU2R> | World Petroleum Assessment 2000 (DDS-60) | 2026-11-25 | `8cf1f1ba98b5065a3f18d31fa832ed62ddfa3265516d1f77c06ad13e588f4ff6` | 938 |

## Terms, quoted

**Natural Earth** (countries, provinces). Read at <https://www.naturalearthdata.com/about/terms-of-use/>
on 25 Nov 2026 (HTTP 200): "All versions of Natural Earth raster + vector map data found on this
website are in the public domain." "No permission is needed to use Natural Earth." "Crediting the
authors is unnecessary." The map credits "Natural Earth" all the same (`source.credit`).

**U.S. Geological Survey** (basins). Read in the publisher's metadata inside the file
(`WEP_PRVG/WEP_PRVG.xml`, FGDC): Use_Constraints "None."; Access_Constraints "None". Credit
"U.S. Geological Survey" (family rule R-S5). The copy prepared is the archive copy named
`WEP_PRVG-archive-2025-02-02.zip` (ScienceBase refused automated reads on 25 Nov: Cloudflare);
its metadata names the publisher's addresses <https://doi.org/10.5066/P9RMSU2R> and
<https://pubs.usgs.gov/dds/dds-060/>.

## What preparation leaves out

- Countries: Natural Earth rows without an ISO 3166-1 code (`ISO_A2_EH` = -99): Somaliland, N. Cyprus,
  Siachen Glacier. Australia's three rows (Australia, Indian Ocean Ter., Ashmore and Cartier Is.)
  are one area, named by its largest part.
- Provinces: 50 rows, each without a usable code (`iso_3166_2` ending in `~` and `adm1_code` with `+`,
  such as Gaza, Western Sahara, Vatican) or whose country is not a country area (UM, GI, TK, -1).
  Province ids are `iso_3166_2` when it is unique in the file, else Natural Earth's `adm1_code`.
- Basins: the row coded 0 ("Ocean"). The 1,023 rows hold 938 province codes; rows of one code are
  one area. Ids are `usgs-<CODE>`.

Geometry: Douglas-Peucker at 300 m, positions rounded to 4 decimals (11 m), rings below 300 m x 300 m
dropped, an edge left longer than 180 degrees of longitude halved (Antarctica along -90). Neighbouring
areas are simplified apart, so a point within a few hundred metres of a border can count on either side.
