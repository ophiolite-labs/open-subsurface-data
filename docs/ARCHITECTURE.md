# Architecture

One sentence: contributors write facts about open datasets, tools turn those facts into verified
levels, outlines and a catalogue, and a static map plus a manifest let anyone find and fetch the
data; Ophiolite will read the same catalogue as a source (its E127; today a contract and a refusing stub).

## The chain

```
  SEG wiki, national        contributor            verifier            outline extractor
  registers, publishers ──► records/*.yaml ──────► build/verification ─► outlines/*.geojson
        (lists)             (facts, CC0)            (levels L1–L2)        (L3, derived)
                                 │                        │                    │
                                 └──────────┬─────────────┴────────────────────┘
                                            ▼
                                     osd build  ─────►  build/catalog/
                                                        records.json · outlines.geojson · collections.json (STAC)
                                            │
                 ┌──────────────────────────┼──────────────────────────────┐
                 ▼                          ▼                              ▼
           site/ (MapLibre)           QGIS / any GIS                 manifest (E06)
           toggles, search,           GeoJSON / STAC by address      osd get · Python reader
           panel, cards                                                   │
                                                                          ▼
                                                              Ophiolite source (E09, L4)
                                                              E85 intake · E35 rights-basis
```

## Components and their boundaries

| Component | Owns | Never does |
|---|---|---|
| **Records** (`records/`, `schema/record.schema.json`) | Facts as the publisher states them: origin, licence, kinds, region | Carry a level, a checksum or anything a tool produced |
| **Verifier** (`src/osd/verify.py`, `schema/verification.schema.json`) | Network checks, checksums, licence text capture, the level ladder | Change a record; run inside the required CI check |
| **Outlines** (`outlines/`, `schema/outline.schema.json`, extractor in E03) | Geometry per wellbore or survey in WGS84, with its derivation named | Invent geometry without saying `approximate: true` |
| **Build** (`src/osd/build.py`) | Joins records, outlines and levels into the published files | Fetch anything |
| **Catalogue** (`build/catalog/`) | The one published artefact; STAC-shaped collections, GeoJSON outlines, records JSON | Hold dataset bytes |
| **Site** (`site/`) | Reading the catalogue and showing it; copyable addresses and snippets | Hold its own data store; need a server |
| **Retrieval** (E06) | A manifest from a selection; a fetcher that verifies checksums | Decode proprietary project files (Ophiolite connector doctrine) |
| **Mirror store** (E07) | Checksummed copies of small or orphaned datasets whose licence allows it | Copy anything with `redistribution: unknown` |
| **Ophiolite bridge** (E09) | The catalogue as an Ophiolite source; rights-basis from the record; fidelity records | Live outside the Ophiolite monorepo's own conventions |
| **Starters** (E40; `starters/`, `schema/starter.schema.json`, `src/osd/starters.py`) | One committed document per starter pack, written by its recipe; the nine validity tests; `starters.json` and the pack manifest | Hold artefact bytes (they live in the mirror under custody/2), publish a pack it could not check, or let anyone write a pack by hand |

## Formats, all standard

- Records: YAML validated by JSON Schema 2020-12. Outlines: GeoJSON, EPSG:4326.
- Catalogue: STAC 1.0 collections and items (full validity is E04), plus one GeoJSON for map and GIS.
- Tiles: PMTiles once outlines exceed what one GeoJSON serves comfortably (E05).
- Manifest: `osd.manifest/1` JSON (E06). Seismic store, if ever: Zarr-based (E10).

## The level ladder

L0 listed → L1 reachable → L2 checksummed and licence captured → L3 outlined from the data →
L4 converted to a canonical type with a fidelity record. No rung is skipped, and a level is
computed from check outcomes, never typed. The ladder is the product's honesty: a dashed outline
on the map is a placeholder and says so.

## What the map is and is not

The map is a view of the catalogue, nothing more. It has no account, no state beyond the URL, no
server. Everything it shows can be opened in QGIS by one address. That is also why the website
and "a GIS layer" are one deliverable rather than two.

## Where Ophiolite comes in

Ophiolite is a consumer of the catalogue, and the catalogue borrows Ophiolite's vocabulary
(kinds from the E55 registry, rights-basis from E35). The two repositories meet at one interface:
a manifest or STAC collection Ophiolite's intake (E85) can read. No Ophiolite code runs here;
no catalogue code runs there.
