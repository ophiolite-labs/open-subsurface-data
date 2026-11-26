# E51 J13: Licences on /shop.html, and the licences out of the first load

## First load, bytes

The build of 26 Nov (main 08ea48d, the real catalogue with Norway's and the United States' licences)
writes these index files:

| File | Bytes | First load before | First load after |
|---|---:|:-:|:-:|
| `areas.json` (area/1 index, unchanged) | 181,038 | read | not read |
| `areas-country.json` | 17,413 | — | read |
| `areas-province.json` | 30,311 | — | read when Provinces is chosen |
| `areas-basin.json` | 31,836 | — | read when Basins is chosen |
| `areas-licence.json` | 101,554 | — | read when Licences is chosen |

- **Before:** 991,831 bytes from the site at the first view with Countries on. This is E48's
  measurement (journey test "budget", `docs/program/evidence/e48/README.md`), with `areas.json` at
  181,052 bytes of it.
- **After, computed:** 991,831 − 181,052 + 17,413 = **828,192 bytes**, 164 KB under the earlier figure
  and 172 KB under the 1 MB line. Everything else on the page is unchanged.
- **After, measured:** not yet. The local browser run that measures it is held under the supervisor's
  host-emergency stop of 26 Nov. CI skips "budget" because it needs the real catalogue's tiles. The
  number will be added here when browsers are allowed again.

The budget test asserts that the first load asks for `areas-country.json` and `areas.pmtiles`, and that
it asks for neither `areas.json` nor `areas-licence.json`.

## What the page shows

The switch gets a fourth part, Licences, when `areas-licence.json` is in `files.txt`. A click on a licence
filters the list to its datasets. While Licences are drawn, each row names its blocks ("blocks 7/9, 7/12",
at most four and then "+N"). The attribution reads "Licences: Sodir, as of <date>; BOEM, as of <date>."
followed by the credit lines.

Screenshots are held under the same stop.
