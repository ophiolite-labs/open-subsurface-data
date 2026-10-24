# E36: the gate, the first load and the staged site

Branch e36-wells-on-a-phone, 166,407 wellbore points committed (BCER, SGC, Utah and North Dakota
added; Virginia waits on its certificate, `outlines.md`), tippecanoe 2.79.0.

## `make check` on CI

| run | what | `make check` step |
|---|---|---:|
| main 40048721236, 40049649921, 40048254203 | main's spread on 24 Oct | 91 s, 117 s, 119 s |
| PR #52, 40050937307 | designs 1-4, two tile runs and tile-join, stations in sequence | 209 s (pytest 90, validate 16, build STAC 22, tiles 72 cold, copy 8) |
| PR #52, **40052861934** | one tile run z0-12, `test`, `validate` and `build` side by side (`make -j3 --output-sync=target`) | **114 s** (pytest 113 s on the critical path, 563 passed, 1 deselected) |

With the real-catalogue tile comparison out of pytest (design 4), the cold tiling of the whole
catalogue lands in `make build`; on CI that was 72 s. Two changes put the step back inside main's
spread: one tippecanoe run (z0-12, `--no-line-simplification`) in place of E15's two runs and
`tile-join` (locally 40 s against 39 s + 22 s; the archive is 75 kB larger), and the Makefile running
lint, then test, validate and build in parallel. No station was added.

## `make check-full` on the branch

`make check-full` (local, 24 Oct): `pytest -m full` 1 passed (the real-catalogue tile comparison:
every one of 169,290 features at z12 with every property; wellbore 166,407, survey-2d 1,759,
survey-3d 1,123, field 1); `stac.validate` 169,571 STAC objects valid. Rerun of `pytest -m full` after
the one-run tiling: 1 passed in 51.6 s.

## First load at the world view (site test, PR run 40052861934)

| load | site bytes | of which pmtiles | ranges |
|---|---:|---:|---:|
| `#` (world view) | 655,533 | 109,371 | 6 |
| `#q=sodir` | 655,533 | 109,371 | 6 |
| `#map=5/59/5` | 663,710 | 104,523 | 8 |

E32's nine registers with wells in every tile: 1,780,594 (pmtiles 1,239,898). Budget 1 MB, unchanged.

The well grids (`site/data/wells-z<z>.json`), each summing to 166,407 wells:

| z | rows | bytes |
|---:|---:|---:|
| 0 | 14 | 715 |
| 1 | 24 | 1,021 |
| 2 | 51 | 1,879 |
| 3 | 101 | 3,464 |
| 4 | 224 | 7,399 |
| 5 | 500 | 16,488 |
| 6 | 1,133 | 37,673 |
| all | | 68,639 |

## The staged site (`make build`, `site/`, file sizes summed)

| Part | Files | Bytes | MB |
|---|---:|---:|---:|
| STAC tree `site/data/stac/` | 169,571 | 187,221,589 | 187.2 |
| of which Items | 169,286 | 173,508,635 | 173.5 |
| of which shard Catalogs | 88 | 13,193,521 | 13.2 |
| of which root catalog and Collections | 197 | 519,433 | 0.5 |
| `outlines.geojson` | 1 | 132,626,345 | 132.6 |
| `outlines.pmtiles` | 1 | 117,693,359 | 117.7 |
| `collections.json` | 1 | 769,108 | 0.8 |
| `records.json` | 1 | 500,810 | 0.5 |
| `wells-z0..z6.json` | 7 | 68,639 | 0.1 |
| the rest (HTML, JS, CSS, `files.txt`, `mirror.json`, `robots.txt`) | 8 | 53,631 | 0.1 |
| **complete staged site** | **169,590** | **438,933,481** | **438.9** |

Bound 500 MB: met with 61 MB to spare (E32 measured 485.6 MB with Virginia and wells at every zoom
in the tiles; the tiles are 32 MB smaller without wellbore points at z0-6).

## Screenshots (phone width 390 x 844, live basemap; `node docs/program/evidence/e36/shots.mjs docs/program/evidence/e36`)

- `world-phone.png`: `#sel=nd-dmr/wells&map=1.2/38/-60`, sheet hidden; the clusters come from
  `wells-z1.json`: 21 cells, 166,407 wells (44k North Dakota, 25k Colombia, BC and Utah at the
  left edge, Sodir and NLOG at the right).
- `nd-wells-phone.png`: Watford City at zoom 12, North Dakota's wells from the tiles (80 rendered).
- `nd-dataset-panel-phone.png`: after clicking `nd-dmr/wells#23634` (HEGG 11-29SH) with the record
  selected (E32 note 7), the dataset panel; no console errors. L0 "never verified" because a local
  build has no `build/verification`.
