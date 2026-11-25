# E46 fixture areas

Three countries, four provinces, three basins and six records, in degrees on an invented coast
(ISO user-assigned codes XA, XB, XC). `areas.json` is the golden index the build writes for them
(tests/test_areas.py); regenerate it only when the charter's rule changes, and say so in the PR.

```
lat 10 +-------------------+-------------------+
       | XA-N  +--1001--+  | XB-W    |   XB-E  |      1001, 1002: basins (usgs-)
       |       |  boxed |  |         |         |      1003 (-5..-1, -5..-1): in the sea, holds nothing
 lat 5 +-------+--------+--+         |         |
       | XA-S  +--+      survey+---+1002-------+      XC: the enclave (2..4, 2..4), a hole in XA and XA-S
       |       |XC|   [7..12 x 1..3]           |
 lat 0 +-------+--+--------+-------------------+
      lon 0             lon 10    lon 15     lon 20
```

| Record | Positions | Areas |
|---|---|---|
| register | wells (5,7) (14,2) (3,3) (-3,5); box middle (17,7) unused | XA XB XC; XA-N XB-W; 1001 1002 |
| survey | polygon 7..12 x 1..3; line (12,0.5)-(13.5,5) crosses 1002 with no vertex in it | XA XB; XA-S XB-W; 1002 |
| boxed | box middle (6,7) | XA; XA-N; 1001 |
| national | `national`, no outline: box unused | XB |
| nothing | none | none |
| offshore | box middle (-3,5) in the sea: falls back to `region.country` | XA |
