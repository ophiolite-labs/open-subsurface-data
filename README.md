# Open Subsurface Data

A verified catalogue of open subsurface datasets (wells, seismic, horizons, production),
shown on one map, retrievable with one manifest, and readable by [Ophiolite](https://ophiolite.dev)
and by any tool that reads GeoJSON or STAC.

Status: scaffold, 23 October 2026. Nine records, placeholder outlines, verifier at level L1.

## What "verified" means

Every record carries a level produced by `osd verify`, never typed by hand:

| Level | Meaning | Who establishes it |
|---|---|---|
| L0 | Listed: a record exists with publisher, origin and licence as stated | a contributor, by pull request |
| L1 | Reachable: the origin page answers | the verifier, on the network |
| L2 | Checksummed: files hashed, licence text captured | the verifier (E02) |
| L3 | Outlined: wellbores and survey outlines derived from the data itself | the outline extractor (E03) |
| L4 | Converted: read into a canonical type with a fidelity record | the Ophiolite readers (E09) |

A level never skips a rung. A placeholder outline drawn by hand keeps a record at L1.

## Layout

```
records/<publisher>/<dataset>.yaml   facts about the dataset as published (schema/record.schema.json)
outlines/<publisher>__<dataset>.geojson  outlines in WGS84 (schema/outline.schema.json)
schema/                              the three contracts: record, verification, outline
src/osd/                             tools: validate, verify, build, status
site/                                the map (static, MapLibre, no server)
build/                               generated: catalog/ (published) and verification/ (per record)
docs/                                ARCHITECTURE.md, ENGINEERING.md, program/ (queue and charters)
```

## Run it

```
uv sync
make check        # lint, tests, validate, build: the one CI check, offline
make verify       # network: reach every origin and write build/verification/
make site         # http://localhost:8765
```

## From Python

```
pip install "osd[readers] @ git+https://github.com/ophiolite-labs/open-subsurface-data"
```

```python
import osd

norne = osd.get("opm/norne")   # the files the catalogue lists, mirror first, each checked by sha256
print(norne)                   # what arrived, from where, and what is left to do
```

With the extra `osd[readers]` (lasio, segyio, pandas) a dataset opens its common kinds:
`well_logs()` (LAS, a table per well), `segy()` (SEG-Y headers) and `tables()` (CSV). Without it
`import osd` and every command work; a reader says what to install.

`osd.get` reads the published catalogue, downloads to `./osd-data/<publisher>/<dataset>/` and
writes `ATTRIBUTION.md` there; a file already present with the right digest is not fetched again.
A dataset behind a sign-in returns no files and a `todo` line naming where to sign in; a file whose
bytes do not match the recorded sha256 raises. `python -m osd.script opm/norne nlog/nlog -o get.py`
writes the same kind of file for several datasets from a built catalogue.

## Contribute a dataset

Copy `records/_template.yaml` to `records/<publisher>/<dataset>.yaml`, fill in what the
publisher states, open a pull request. CI validates the record and verifies the origin.
See `CONTRIBUTING.md`.

## Licences

Code: Apache-2.0 (`LICENSE`). Records and outlines: CC0 1.0 (`records/LICENSE`), facts about
public datasets. The datasets themselves keep their publishers' licences, named in each record.
