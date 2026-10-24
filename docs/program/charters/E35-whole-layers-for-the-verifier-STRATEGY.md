# E35 strategy: whole layers for the verifier

Charter: `E35-whole-layers-for-the-verifier.md` (Kernel; its Dispositions table is the contract).
Base: main 8d23039. Written at lane open, 24 Oct; layer facts measured from this host the same day.

## Shape

```
records/<id>.yaml  origin.manifest_url = an ArcGIS layer (?f=json, or the HTML services page)
        |
listings._arcgis / _arcgis_page --> Entry(generated=True, layer=<layer url>)      (design 1: no new file)
        |
check_files: entry.layer set --> verifier/layers.export_layer(layer, get)
        |   get(url) = robots check -> paced opener (2 s per host) -> bytes counted against the
        |              record's 512 MiB share chunk by chunk, before decoding; an abandoned read counts
        |
        |   1 description ?f=json        -> oid, maxRecordCount, supportsPagination, lastEditDate (before)
        |   2 query returnCountOnly       -> count; count > 50,000 -> old path: the first-page export
        |                                    stays a partial export, detail says "above the 50,000 cap"
        |   3 query returnIdsOnly         -> the expected id set (independent of the pages)
        |   4 pages (shared, outlines.extractors): offsets 0,size,..; outFields=*, f=json, orderByFields
        |     oid ASC, no outSR; checks: error JSON / HTTP, full page but the last, oid present, no
        |     duplicate, assembled count == returnCountOnly                               (design 2)
        |   5 assembled id set == returnIdsOnly set, exactly
        |   6 description again           -> lastEditDate (after)                         (design 4)
        |
        +--> canonical esri-json bytes, SHA-256  --> verification.layer_exports[]  (verification/5)
        +--> files-checksummed: pass "whole layer checked (N features, esri-json), not a downloadable file"
```

- **Canonical bytes (design 3).** `{"features":[…],"geometryType":…,"objectIdFieldName":…,
  "spatialReference":…}`, `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)`,
  features sorted by object id. Values are the server's: coordinates and attributes are parsed and
  written back as the shortest round-trip form of the same number (no rounding, no reprojection).
  `fields`, `fieldAliases`, `displayFieldName`, `exceededTransferLimit` are left out: they are page
  metadata, and E29 showed load-balanced nodes differ in description metadata with no feature change.
  Every page must state the same `geometryType` and `spatialReference` (a reason otherwise).
- **`layer_exports` entry.** `{layer, format: "esri-json", features, count, bytes, sha256,
  edit_date_before, edit_date_after}`; the two dates are the publisher's `lastEditDate` (ms) or null.
  An entry is written only when the pages assembled to the id set; a failure before writes none and
  the check names the first failing guard. Never in `files`: `stac._assets`, `osd get`, manifests
  and the mirror read `files` only, so nothing a person downloads changes.
- **Outcomes.** Assembled and dates equal: pass. Dates absent: pass, detail "stability unknown (the
  layer states no edit date)". Dates differ: skip, "edited during paging". Integrity guard (error
  page, short page, duplicate, count, id set, CRS/geometry type differing between pages): fail, as a
  failed file fetch fails today. Robots disallow and the budget: skip, as for files today. Above
  the cap: today's partial-export path, unchanged, with the cap named.
- **Shared paging extraction (design 2, Disposition 7).** `extractors.arcgis_page_query(oid, size,
  offset, fields)` (the page query E29 builds) and `extractors.arcgis_assemble(pages, oid, size,
  count, what, check_page)` (E29's missing / error / full-page / oid / duplicate / count checks, in
  E29's order, returning the raw Esri features). `fetch_parts` and `register_arcgis` call them;
  `register_arcgis` passes its CRS check as `check_page`. Messages unchanged; `tests/test_outlines.py`
  is not edited and stays green, which is the proof of "E29 behaviour unchanged".
- **verification/5.** New top-level `layer_exports` (array of the entry above, `additionalProperties:
  false`); `$id` …/verification/5; /4 frozen as `tests/fixtures/schema/verification-4.schema.json`
  with a hash pin; every stored /3 result and every /4 fixture validates under /5; the build reads a
  /4 and a /5 file (test in `test_whole_layers.py`).

## The candidates on 24 Oct (`returnCountOnly`, maxRecordCount from the description)

| id | count | page | pages | expected |
|---|---|---|---|---|
| **bcer/well-surface-holes-permitted** | 34,431 | 2000 | 18 | multi-page: must pass |
| **nd-dmr/wells** | 44,018 | 2000 | 23 | multi-page: must pass |
| **sgc/banco-informacion-petrolera-pozos** | 25,013 | 2000 | 13 | multi-page: must pass (edit date stated) |
| **ut-dogm/oil-gas-wells** | 40,422 | 2000 | 21 | multi-page: must pass (edit date stated) |
| **va-energy/gas-oil-wells** | 8,605 (E29) | 2000 | 5 | multi-page: must pass (times out from this host; runner reached it 23 Oct) |
| **wa-dnr/geophysics-database** | 7,577 | 2000 | 4 | multi-page: must pass |
| **nbmg/oil-gas-wells-through-2013** | 1,061 | 1000 | 2 | multi-page: must pass |
| inp-mz, nzpam x2, sgudds, wa-demirs, wa-dnr geothermal / groundwater / oil-gas / shear-wave | 255–4,371 | ≥1000 | 1 | one page; nzpam x2 and sgudds answer 403 to the runner (E29) |
| cgs/vrtna-prozkoumanost, pgi/cbdg-boreholes, sk-mer x4 | 68,000–746,805 | — | — | above the cap: partial export, out of scope |

Sizes: about 0.5–1.2 MB per 2,000 features (`f=json`, all fields), so the largest (UT DOGM) is
about 47 MB, well inside 512 MiB; pacing adds about 2 s per page (under a minute for ND DMR).

## Commits

1. Shared paging extraction in `outlines/` (no behaviour change; test_outlines untouched).
2. verification/5: schema, frozen /4, version and old-file tests.
3. `verifier/layers.py`: canonical bytes and `export_layer` (pure over an injected `get`), fixture
   tests for bytes, digests and every failing guard.
4. Listing marker and `check_files` integration: budget, robots, pacing, the cap fallback, the
   STAC-asset exclusion; `docs/program/evidence/e35/mutations.md`.
5. Evidence: the two dispatches, `docs/program/evidence/e35/results.md`.

## Decisions taken by default (inbox `e35.md`)

1. `tests/test_verify.py` pins verification/4 by `$id` (`test_verification_4_identity`) and is not in
   the claim: the one assertion moves to /5 (it is the version test the charter grants in
   test_schema.py, living one file over). Default: edit that line only.
