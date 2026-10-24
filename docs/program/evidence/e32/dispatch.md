# E32 design 4: the all-record dispatch on the branch and `make check-full` on its output

## Dispatch

`verify.yml`, `workflow_dispatch` on `e32-registers-with-a-hundred-thousand-wells` at 6724a93 (design
4), all records, `--outline-inputs`: run
[40014701044](https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/40014701044),
19:51:28Z to 20:43:54Z on 23 Oct, **52 min 26 s** (the `osd verify` step 52 min 7 s), success,
artifact `verification` (176 result files). Levels over all records: 16 L0, 102 L1, 56 L2, 2 L3.

The five registers (from the artifact):

| Record | Level | First failing check | outline-present | outline-derived |
|---|---|---|---|---|
| va-energy/gas-oil-wells | L1 | `files-checksummed` skip: export truncated by the server (exceededTransferLimit), query export of at most 2000 features kept as partial | pass, 8605 features | pass, input sha256 equal |
| bcer/well-surface-holes-permitted | L1 | same | pass, 34431 | pass |
| sgc/banco-informacion-petrolera-pozos | L1 | same | pass, 25013 | pass |
| ut-dogm/oil-gas-wells | L1 | same | pass, 40422 | pass |
| nd-dmr/wells | L1 | same | pass, 44018 | pass |

No outage: every origin answered (HTTP 200, Utah 206). L2 is not reached because the verifier's
ArcGIS listing reader keeps a truncated export as partial, and L3 needs L2. The listing reader is
out of this charter's scope, so the Levels line is **partial for all five** (inbox e32.md note 1;
E29's note 1 had the same cause).

## `make check-full` on that output

The artifact's files in `build/verification/`, tippecanoe 2.79.0 first on `PATH`, at dd37c51:

```
stac: 177891 Items, 196.2 MB in stac/; collections.json 0.8 MB, records.json 0.5 MB
tiles: outlines.pmtiles 149.9 MB, z0-12, tippecanoe v2.79.0
built {'records': 176, 'features': 177895, 'collections': 176}
178161 STAC objects valid
check-full wall 1519.49 s
```

Green. 25 min wall on the VPS under load average 10 to 14 from other lanes; every one of the
178,161 objects (root, 176 Collections, 93 shard Catalogs, 177,891 Items) validated against the
vendored schemas, the shards' Items included. With the verification the staged site is 485,691,863
bytes (`records.json` 465,927, `collections.json` 770,447), still under 500 MB.
