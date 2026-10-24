# E38 results: two explicit-id dispatches over the nine WFS records (24 Oct 2026)

Branch `e38-wfs-and-ogc-api-layers`: run 1 at 15632bd (code final), run 2 at a5ce847 (mutation
evidence only, no code change).

| run | dispatched | verify job | conclusion |
|---|---|---|---|
| [40059167280](https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/40059167280) | 03:39:04 UTC | 03:39:07 to 03:42:36 (3 min 29 s) | success |
| [40059433566](https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/40059433566) | 03:42:59 UTC, when the first completed | 03:43:03 to 03:47:02 (3 min 59 s) | success |

## Outcome per protocol

- **WFS 2.0.0: passes.** Two eligible multi-page candidates read whole on both runs with equal
  checksums: dov/boringen-geothermie (24,979 features, 5 pages of 5,000, `fa299388f183863e…`) and
  dov/graviteit-data-punten (16,915 features, 4 pages, `16391c699c41a0bf…`). The one-page layers
  gsnsw/drillholes-petroleum (1,221) and gsv/faults-latrobe-group-gippsland (47) also pass, equal on
  both runs. Stability is unknown for all four (WFS 2.0 states no revision for a feature type); no
  checksum disagreement among whole layers to list.
- **OGC API Features: recorded incomplete.** No eligible record: every record whose publisher serves
  a collection keeps its downloadable manifest (design 8; `candidates.md`), so no branch dispatch
  can exercise the protocol. Reader evidence instead, not a level: `export_ogcapi` through the
  verifier's own get (robots, paced opener, budget share) from ophiolite-epic-01 against SGU borrhal,
  `https://api.sgu.se/oppnadata/borrhal/ogc/features/v1/collections/borrhal`, 37 pages by next link:
  03:36 UTC complete, 36,672 features = numberMatched, 42,345,357 bytes, `3d929ba529869aeb…`;
  03:40:22 to 03:41:55 UTC complete, the same count, bytes and checksum.
- **Above the cap (partial, no L2, no `files`, no STAC asset):** dov/boringen (188,580),
  dov/formele-stratigrafie (107,753), ga/stratdat-biostratigraphy (50,128), ga/resfacs (164,799),
  wogcc/wyde-wells (121,000). Their partial exports (the manifest's 1,000-feature GetFeature) differ
  between runs on every one: GeoServer writes the response `timeStamp` into the body. Listed, not
  exempted; a partial export claims nothing.

## Level changes against the stored main results (`verification-results`, 24 Oct)

| record | before | after | why |
|---|---|---|---|
| dov/boringen | L2 (first 1,000 features hashed as a file) | L1 | above the cap: partial export, now said so |
| dov/formele-stratigrafie | L2 (as above) | L1 | above the cap: partial export |
| dov/boringen-geothermie, dov/graviteit-data-punten, gsnsw/drillholes-petroleum, gsv/faults-latrobe-group-gippsland | L2 (a GetFeature response hashed as a file) | L2 | whole-layer evidence; the GetFeature response is no longer a file, so no STAC asset or `osd get` file |
| ga/stratdat-biostratigraphy, ga/resfacs-porosity-permeability | none (added 24 Oct, not yet verified on main) | L1 | above the cap |
| wogcc/wyde-wells | L1 (no manifest_url) | L1 | above the cap |

All six records that had a WFS GetFeature as a file lose that STAC asset (inbox `e38.md` item 1,
accepted).

## Per record, run 40059167280

| record | level | features | count | bytes | sha256 | files-checksummed / first non-pass |
|---|---|---|---|---|---|---|
| dov/boringen | L1 |  |  | 1099843 | `dda0e3cdf3b5d0e2…` (partial) | skip: not read whole: the feature type counts 188580 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 188580 features, above the 50000 a whole layer is read to; the one-page export k |
| dov/boringen-geothermie | L2 | 24979 | 24979 | 26830771 | `fa299388f183863e…` | pass: whole layer checked (24979 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| dov/formele-stratigrafie | L1 |  |  | 635352 | `1f7dfa8c51032f69…` (partial) | skip: not read whole: the feature type counts 107753 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 107753 features, above the 50000 a whole layer is read to; the one-page export k |
| dov/graviteit-data-punten | L2 | 16915 | 16915 | 4029086 | `16391c699c41a0bf…` | pass: whole layer checked (16915 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| gsnsw/drillholes-petroleum | L2 | 1221 | 1221 | 1624244 | `8b590eda438799aa…` | pass: whole layer checked (1221 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| gsv/faults-latrobe-group-gippsland | L2 | 47 | 47 | 14893 | `06d4f7cd761ce67a…` | pass: whole layer checked (47 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| ga/stratdat-biostratigraphy | L1 |  |  | 2546745 | `00da47b04675abbf…` (partial) | skip: not read whole: the feature type counts 50128 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 50128 features, above the 50000 a whole layer is read to; the one-page export ke |
| ga/resfacs-porosity-permeability | L1 |  |  | 3191977 | `a1cb644c475db0ca…` (partial) | skip: not read whole: the feature type counts 164799 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 164799 features, above the 50000 a whole layer is read to; the one-page export k |
| wogcc/wyde-wells | L1 |  |  | 449199 | `55214871cb30f73e…` (partial) | skip: not read whole: the feature type counts 121000 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 121000 features, above the 50000 a whole layer is read to; the one-page export k |

## Per record, run 40059433566

| record | level | features | count | bytes | sha256 | files-checksummed / first non-pass |
|---|---|---|---|---|---|---|
| dov/boringen | L1 |  |  | 1099843 | `acd2a1d572d62275…` (partial) | skip: not read whole: the feature type counts 188580 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 188580 features, above the 50000 a whole layer is read to; the one-page export k |
| dov/boringen-geothermie | L2 | 24979 | 24979 | 26830771 | `fa299388f183863e…` | pass: whole layer checked (24979 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| dov/formele-stratigrafie | L1 |  |  | 635352 | `81aa7cd59f042cb7…` (partial) | skip: not read whole: the feature type counts 107753 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 107753 features, above the 50000 a whole layer is read to; the one-page export k |
| dov/graviteit-data-punten | L2 | 16915 | 16915 | 4029086 | `16391c699c41a0bf…` | pass: whole layer checked (16915 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| gsnsw/drillholes-petroleum | L2 | 1221 | 1221 | 1624244 | `8b590eda438799aa…` | pass: whole layer checked (1221 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| gsv/faults-latrobe-group-gippsland | L2 | 47 | 47 | 14893 | `06d4f7cd761ce67a…` | pass: whole layer checked (47 features, wfs-geojson), not a downloadable file; stability unknown (WFS 2.0 states no revision for a feature type)<br>first non-pass: outline-present fail: no outlines file |
| ga/stratdat-biostratigraphy | L1 |  |  | 2546745 | `f1f79a6666150216…` (partial) | skip: not read whole: the feature type counts 50128 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 50128 features, above the 50000 a whole layer is read to; the one-page export ke |
| ga/resfacs-porosity-permeability | L1 |  |  | 3191977 | `c7c20fd8d6bc743f…` (partial) | skip: not read whole: the feature type counts 164799 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 164799 features, above the 50000 a whole layer is read to; the one-page export k |
| wogcc/wyde-wells | L1 |  |  | 449199 | `846fb2abd33f4af0…` (partial) | skip: not read whole: the feature type counts 121000 features, above the 50000 a whole layer is read to; the one-page export kept as a partial export, not a hashed file<br>first non-pass: files-checksummed skip: not read whole: the feature type counts 121000 features, above the 50000 a whole layer is read to; the one-page export k |
