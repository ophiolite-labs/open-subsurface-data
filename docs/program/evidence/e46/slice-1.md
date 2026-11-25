# E46 slice 1: numbers, times, mutations

Real build of 237 records against the committed area files (25 Nov 2026, this branch).

| Kind | Areas in the file | Areas holding a dataset | Datasets placed | Prototype (25 Nov) |
|---|---|---|---|---|
| country | 237 | 68 | 223 | (counted none: national registers left out) |
| province | 4,546 | 159 | 137 | 4,590 provinces drawn |
| basin | 938 | 158 | 190 | 933 named basins drawn |
| any | | | 223 of 237 | 121 datasets with a place (one box-middle point each) |

The prototype drew every named area; this build draws only areas that hold a dataset (R-S3). The 14
records with no country have neither outline nor box nor a country that is an area (SEG, SPE, Egg,
UNISIM and other synthetic or worldwide sets).

Area files: country 1.8 MB, province 13.2 MB, basin 6.6 MB = 21.6 MB (< 25 MB). Published:
`areas.json` 0.14 MB, `areas-*.geojson` 4.7 MB, `areas.pmtiles` 7.7 MB (z0-8, tippecanoe 2.49.0 here).

Times on this host (16 cores, load about 7 from other lanes): the count of all 237 records, cold,
5.8 s; from the cache, 0 s; `osd validate` of the area files 1.3 s (memoised per file within a
process); area tiles cold 9.2 s, cached a copy. `make check` 1 min 48 s, the only red the known
tippecanoe 2.49.0 test.

Notes on the real result: `sodir/factpages` NO only, 14 basins; `nlog/nlog` NL, BE, DE (wells within
a few hundred metres of the simplified border, or drilled across it); `sodir/faults-and-boundaries`
has no outline and is not yet `national`, so its box middle places it in FI until E52 marks it.

## Mutations (each applied alone, the named tests run, the file restored)

| Mutation | File | Result |
|---|---|---|
| cache key ignores the outline | `src/osd/areas.py` | RED: 1 failed, 39 deselected in 4.79s |
| cache key ignores the area files' content | `src/osd/areas.py` | RED: 1 failed, 39 deselected in 0.09s |
| shapefile holes made polygons of their own | `src/osd/areas.py` | RED: 1 failed, 39 deselected in 0.04s |
| projection check removed | `src/osd/areas.py` | RED: 1 failed, 39 deselected in 0.05s |
| edges over 180 degrees left as simplified | `src/osd/areas.py` | RED: 1 failed, 39 deselected in 0.04s |
| excluded rows kept | `src/osd/areas.py` | RED: 1 failed, 39 deselected in 0.04s |

The offshore fallback is guarded by the slice 0 fixture (`test_box_middle_in_the_sea_falls_back_to_its_country`, evidence slice-0-mutations.md): on the real catalogue Sodir also has onshore wells, so the Sodir test does not bite on it.
