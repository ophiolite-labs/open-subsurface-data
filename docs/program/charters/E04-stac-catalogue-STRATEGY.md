# E04 strategy: STAC catalogue (Kernel)

Charter: `E04-stac-catalogue.md`. Base: main c385c32 (E02, E03 merged). Claim row E04 in `CLAIMS.md`.

## Shape

```
records/*.yaml ─┐                         build/catalog/
outlines/*.geojson ─┼─ osd build ─ stac.write_catalog ─┬─ stac/catalog.json           (root Catalog)
build/verification ─┘   (one call)                 ├─ stac/<cid>/collection.json  (one per record)
                                                   ├─ stac/<cid>/items/<name>.json (period records only)
                                                   └─ collections.json            ({"collections": [...]}, same objects)
make build: cp -R build/catalog/. site/data/  →  site/data/stac/ is the tree Pages serves and the tests validate
```

- `<cid>` = record id with `/` → `--` (unchanged from today). Item `id` = E03's `feature_id`, read from the
  outline file, never recomputed; Item file name = the part after `#`, made path-safe (a lossy name gets an
  8-hex sha256 suffix; a name collision raises).
- Links are relative (`root`, `parent`, `child`, `item`, `collection`); no `self`, so the tree is
  relocatable (local `http.server`, Pages).
- Collection: `license` = SPDX id or `other`; `links` carry `about` (origin) and `license` (licence url,
  else origin); `extent.spatial` = record `region.bbox`, else union of the outline features, else the
  world; `extent.temporal` = `[[start, end]]` from `period`, else `[[null, null]]`; `assets` = E02's
  verified files with a url (`href`, `file:size`, `file:checksum` = multihash `1220<sha256>`); `osd:level`,
  `osd:checked_at`, `osd:access`, `osd:redistribution`, `osd:blocked_since` (only when blocked).
- Item (OSD-D14): only for features with a `feature_id` whose record has `period`; `datetime: null`,
  `start_datetime`/`end_datetime` from the period (start of first day, end of last day, UTC);
  `osd:approximate`, `osd:derivation` (the feature's `source`), `osd:input_sha256` (the collection
  `inputs[input].sha256`, when the feature names an input); `assets: {}`.
- `record.schema.json`: optional `period {start, end, stated}`; `start`/`end` are quoted strings
  `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. record/2 stays record/2 (additive, every record validates).
- `schema/stac-osd.json`: the osd extension, `$id` =
  `https://raw.githubusercontent.com/ophiolite-labs/open-subsurface-data/main/schema/stac-osd.json`,
  closed enums (level L0..L4, access, redistribution), no unknown `osd:` field. `schema/stac/` bundles STAC
  1.0.0 core, GeoJSON, draft-07 and file v2.1.0 schemas; `schema/stac/schema-map.json` maps every URL to
  the bundled file (stac-validator `--schema-config`).
- Identity (design 7): `outlines.geojson` features carry GeoJSON `id` = `feature_id`; a duplicate
  `feature_id` across the build raises (build fails).
- `stac-validator==3.11.0` pinned in `pyproject.toml`/`uv.lock`.

## Acceptance → tests (`tests/test_stac.py`)

| Acceptance line | Test | Mutation shown to fail |
|---|---|---|
| Staged tree validates recursively, local schema map, no network | `test_staged_tree_validates_recursively_offline` (builds the real catalogue, stages with the Makefile's copy, sockets and `requests` raise) | point the schema map at a missing file / remove a bundled schema |
| `make build` publishes the tree recursively | `test_makefile_copies_catalog_recursively` | revert the recipe to `cp build/catalog/*.json` |
| Every relative link resolves in the staged tree | `test_staged_links_resolve` | break an `item` href |
| Reachable collections = record ids exactly | `test_reachable_collections_equal_record_ids` | drop one `child` link |
| Item ids = exact `feature_id` set of features with a period (3 with, 2 without) | `test_item_ids_equal_feature_ids_with_period` | drop one Item |
| L0 record with outlines → its Items and `osd:level: L0`; no outlines → empty Item list | `test_items_independent_of_level[...]` (parametrised) | gate Items on level > L0 |
| `osd:level` removed → invalid; `L9` → invalid | `test_osd_extension_rejects[missing-level]`, `[l9]` | drop `required` / widen the enum |
| Levels equal `records.json` | `test_collection_levels_equal_records_json` (fixture verification at L1 and L2) | hard-code `osd:level: L0` |
| Licence mapping for every record; `proprietary` never appears | `test_licence_mapping_every_record` | map null spdx to `proprietary` |
| Collection assets from E02 files with size and checksum | `test_collection_assets_from_verified_files` | drop `file:checksum` |
| Item time and osd fields from period and outline (input sha from collection `inputs`) | `test_item_time_and_provenance` | recompute instead of reading `inputs` |
| Duplicate `feature_id` fails the build; GeoJSON `id` emitted | `test_duplicate_feature_id_fails_build`, `test_outlines_geojson_carries_feature_id` | remove the duplicate check / the `id` |
| `period` is additive: every current record still validates; a period validates; a bad one does not | `test_period_is_additive_to_record_2` | make `period` required |
| QGIS 3.34 opens the staged tree | not automatable here (no QGIS on this host); supervisor screenshot | - |

## Order of commits

1. Strategy (this file). 2. Tests (red). 3. Schemas: `stac-osd.json`, bundled STAC schemas, `period`.
4. `stac.py` + the one call in `build.py` + `Makefile` copy (green). Each commit keeps `make check` honest
   for its slice; the mutation list goes into the PR body.

## Known limits

- No record declares `period` today, so the published tree has Collections and no Items until a records
  lane adds periods (fixtures prove the Item path). Unquoted YAML dates parse as dates and fail the
  schema; `records.py` (not in this claim) could coerce them like `added`.
- The extension URL is the `main` raw URL (no tags in this program); a breaking change publishes a new
  file name rather than editing this one.
