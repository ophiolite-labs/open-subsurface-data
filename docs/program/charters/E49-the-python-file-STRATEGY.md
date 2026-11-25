# E49 strategy: the Python file (kernel, written at lane open on `c3baa16`, revised on the Codex review `18071f4`)

## What E06 gives today, and what is missing

| Given (file:line on `c3baa16`) | Missing for `osd.get("opm/norne")` |
|---|---|
| `manifest.from_catalog(ids, catalog_dir, catalog_url)` builds a validated manifest dict from a catalogue **directory**: it reads `records.json` and, per selected id, `stac/<collection_id>/collection.json` (`manifest.py:209-236`). The mirror's addresses already sit in each collection's assets as `alternate` (`build.py:132-134`), so `mirror.json` and `collections.json` are not needed. | Reading the published catalogue over HTTP. The smallest set is `records.json` plus one `collection.json` per id, both under `https://opensubsurfacedata.org/data/` (checked: the published `opm--norne` collection carries 5 assets, each with sha256 and a `mirror` alternate). The stop rule does not fire. |
| `get.get(m, dest, opener)` returns one `Outcome` **per asset** (not per entry), tries the mirror first when a sha256 is stated, rehashes a file already on disk, writes through a temporary file and renames only after size and sha256 match, refuses escaping keys and duplicate targets, writes `ATTRIBUTION.md` (`get.py:49-135`). | A call that takes a dataset id; a typed handle (`Dataset`); a raise on mismatch (E06 records `mismatch` and stops, it does not raise). |
| Retry is idempotent and atomic; an interrupted download leaves no partial file (`get.py:79-100`). | Nothing: E49 promises **idempotent atomic retry**, not byte-range resume (F7). |
| `osd/__init__.py` exports `__version__` only; `osd.get` is the **module** `src/osd/get.py`, imported as `from . import get as get_mod` by `cli.py` and `tests/test_manifest.py`. | `osd.get(...)` callable without renaming the module (renaming would edit two files outside the claim). Decision: `get.py` sets its module class to a `ModuleType` subclass whose `__call__` is `api.get`; every existing import keeps the module. Test: `from osd import get as m; m.summary` and `osd.get("fx/…")` both work. |
| The page and the CLI are held equal on manifests by `tests/site/manifest_roundtrip.py`. | The script text from a manifest, so the page (slice 4) renders from the manifest it already builds equal to `osd manifest` (F10). |

## The public contract (slice 1)

- `osd.get(id, dest=None, area=None, catalog=None, opener=None) -> Dataset`. `id` is a record id present in the catalogue's `records.json` (or its collection id); anything else, a feature id (`#`) included, raises `osd.api.DatasetError` before any asset request. `catalog`: `None` = `https://opensubsurfacedata.org/data/`; a string starting `http://` or `https://` = a catalogue root (a trailing `/` is added); anything else = a local directory with the `osd build` layout. Over HTTP only `<root>records.json` and `<root>stac/<collection_id>/collection.json` are read, the collection id computed from a record id found in `records.json` (no caller text reaches a URL path). Bytes are held in memory for the process (`dict` keyed by URL; no disk cache, no refresh, nothing at import). A failed read raises `DatasetError` naming the URL. `opener` (default `verify.http_open`) serves both catalogue and asset reads; tests inject it. `area` other than `None` raises `ValueError("this dataset cannot be narrowed by area yet")` before any request (F8).
- `dest` defaults to `./osd-data/<publisher>/<dataset>`. Under `dest` the tree is exactly what `osd get <manifest for id> --dest <dest>` writes: `<dest>/<collection_id>/<asset key>` and `<dest>/ATTRIBUTION.md`; one directory per dataset so a second dataset never overwrites the first's attribution.
- `Dataset` (frozen): `id`, `title`, `licence` (`manifest.Licence`), `attribution` (the `ATTRIBUTION.md` block of the entry, text), `path` (`dest`), `files: tuple[File, ...]`, `todo: tuple[str, ...]`, `outcomes: tuple[get.Outcome, ...]`, `manifest`. `str(dataset)` is the title line plus `get.summary(...)`, the words `osd get` prints.
- `File` (frozen): `key: str`, `path: Path`, `size: int`, `sha256: str | None`, `source: str` (`"mirror"` or another alternate's name, `"publisher"` for origin, `"disk"` when already present), `checked: str` (`"verified"` or `"no checksum recorded"`). Only files on disk are `files`; `needs-sign-in` and `origin-dead` assets become `todo` lines `"<key>: <outcome>: <detail>"`; an entry without assets becomes `"<unresolved> -> <origin_url>"`.
- A `mismatch` raises `osd.api.ChecksumMismatch(ValueError)` with `.key` and the E06 detail (both digests, or both sizes) after the run; E06 has already left nothing of that file on disk.
- `python -m osd.script <id> [<id> …] [-o file.py] [--catalog DIR] [--today YYYY-MM-DD]` writes the file (offline: a local catalogue only). The `osd script` subcommand line is added to `cli.py` after E46 slice 0 merges (F14). `osd.script.render(entries, today)` takes the manifest entries `from_catalog` wrote for the ids.

## Rule table for the file text (`render(entries, today)`)

| # | Rule |
|---|---|
| T1 | Ids: as given, duplicates dropped at first occurrence (as `from_catalog`); unknown id: error, no file. |
| T2 | Line 1: `# open-subsurface-data, made <D Mon YYYY> for <n> dataset(s)`; day without leading zero, English month abbreviation; `dataset` when n = 1. |
| T3 | Line 2: `# pip install "osd @ git+https://github.com/ophiolite-labs/open-subsurface-data"` (slice 2: `osd[readers]`). Line 3 blank, line 4 `import osd`, line 5 blank. |
| T4 | One line per dataset: `<var> = osd.get("<id>")`, then spaces to the column of the longest such line + 2, then `# <comment>`. |
| T5 | `<var>`: the part after `/`, lower-case, every character outside `[a-z0-9_]` to `_`; leading digit gets `d_`; a Python keyword or `osd` gets a trailing `_`; a repeat gets `_2`, `_3`, … |
| T6 | Comment, entry with assets: `<n> file(s) from our mirror` (alternate present and sha256 stated) / `<n> file(s) from the publisher` / `<n> files: <m> from our mirror and <p> from the publisher`; then `, checked` when every asset has a sha256, `, no checksum recorded` when none, `, <k> checked` otherwise. |
| T7 | Comment, entry without assets: `sign-in needed: left out, sign in at <origin_url>` (registration), `request needed: left out, ask at <origin_url>` (request), `for sale: left out, see <origin_url>` (purchase), `no file address known: left out, see <origin_url>` (other). |
| T8 | Blank line, then `print(<var>)` for each dataset in order (slice 2 adds two reader lines for the first dataset with a `.las` asset). File ends with one newline. |

## Acceptance line -> test (`tests/test_api.py`, `tests/test_script.py`; fixture catalogue `tests/fixtures/api/catalog/`)

| Acceptance | Test | Mutation shown to fail |
|---|---|---|
| 1 mirror, verified, second call 0 requests | `test_get_from_mirror_checked_then_idempotent` | rehash of an existing file removed (`get.py` `_fetch_one` returns early) / alternates loop removed |
| 2 registration: no files, todo with address, no request | `test_registration_is_todo_and_requests_nothing` | `_no_assets_reason` branch bypassed |
| 3 corrupted byte raises with key and both digests, nothing left | `test_mismatch_raises_with_both_digests` | raise removed in `api.get` |
| 4 same tree and outcomes as `osd get`, one seam | `test_api_and_cli_leave_identical_trees` (local 127.0.0.1 server, both via `http_open`; spy on `get.get` sees both calls with equal manifests) | API fetching by its own loop |
| 5 golden file | `test_script_equals_golden` (`python -m osd.script` for three fixture ids, `--today 2026-11-25`) | any rule in T1–T8 changed |
| F13 guards | `test_unknown_or_feature_id_refused_before_request`, `test_catalogue_url_built_from_records_only`, `test_area_refused_before_request`, `test_import_osd_is_offline_and_reader_free`, `test_osd_get_module_still_importable` | id passed into URL unchecked / area ignored / eager import |
| 6, 7 (slice 2) | `test_golden_runs_offline` (subprocess runs a test-side wrapper that sets the fixture catalogue and opener, then `runpy` the golden file), `test_readers_missing_name_the_extra` (subprocess blocks `lasio`/`pandas` by a meta-path finder, F17) | lazy import made eager |
| 8 (slice 3) | parked, inbox e49 note 1 | |
| 10 real run | not in the gate: `osd.get("opm/norne")` once on this host, intentional retrieval, in a scratch directory, recorded in the PR | |

## Slices

1. `api.py`, callable `osd.get`, `script.py`, fixtures, golden file, AGENTS.md network sentence. 2. `readers.py`: `well_logs()` (`.las` -> `dict[well name, pandas.DataFrame]`, a repeated name becomes `"<name> (<key>)"`), `segy()` (`.sgy`/`.segy` -> `dict[key, SegyInfo]`: text header, trace count, sample count, interval, read with `segyio` and closed), `tables()` (`.csv` -> `dict[key, DataFrame]`); a dataset without such files raises `ValueError` naming the kinds it has; a missing library raises `ImportError` naming `pip install "osd[readers]"`; extra `readers = ["lasio>=0.31", "segyio>=1.9", "pandas>=2.0"]`. 3. `area=`: parked (F8). 4. bag button after E47.
