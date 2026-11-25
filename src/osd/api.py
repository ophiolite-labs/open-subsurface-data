"""`osd.get(id)` from Python (E49): the E06 retrieval of one dataset, called by its id.

    import osd
    norne = osd.get("opm/norne")    # files under ./osd-data/opm/norne/, each checked by sha256
    print(norne)

One code path with `osd get <manifest>`: the manifest is the one `osd manifest <id>` writes
(`manifest.from_catalog`, unchanged), read back by `manifest.read_doc` and fetched by `get.get`,
mirror first, sha256 checked, atomic and idempotent. The tree under `dest` is the tree `osd get
--dest` writes.

Network: only when called, only the catalogue's `records.json`, the chosen collection's
`stac/<collection_id>/collection.json` and the assets (AGENTS.md). The collection id is computed
from a record id found in `records.json`; no caller text reaches a URL. Catalogue bytes are held in
memory for the process; nothing is cached on disk, nothing is read at import.

What cannot be fetched is said in `todo`, not raised. A checksum or size mismatch raises
`ChecksumMismatch` after the run; E06 has written nothing of that file.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import get as get_mod
from . import manifest as mf
from .stac import collection_id
from .verify import FetchError, Opener, http_open

DEFAULT_CATALOG = "https://opensubsurfacedata.org/data/"
AREA_REFUSAL = "this dataset cannot be narrowed by area yet"

_cache: dict[str, bytes] = {}   # catalogue bytes by URL, for the life of the process


class DatasetError(ValueError):
    """The id or the catalogue: nothing was fetched."""


class ChecksumMismatch(ValueError):
    def __init__(self, key: str, detail: str):
        super().__init__(f"{key}: {detail}")
        self.key, self.detail = key, detail


@dataclass(frozen=True)
class File:
    key: str
    path: Path
    size: int
    sha256: str | None
    source: str    # "mirror" (or another alternate's name), "publisher", or "disk" when already present
    checked: str   # "verified" or "no checksum recorded"


@dataclass(frozen=True)
class Dataset:
    id: str
    title: str
    licence: mf.Licence
    attribution: str
    path: Path
    files: tuple[File, ...]
    todo: tuple[str, ...]
    outcomes: tuple[get_mod.Outcome, ...]
    manifest: mf.Manifest

    def __str__(self) -> str:
        return "\n".join([f"{self.id}: {self.title} -> {self.path}",
                          *get_mod.summary(self.manifest, list(self.outcomes))])


def _read(url: str, opener: Opener) -> bytes:
    if url not in _cache:
        try:
            _cache[url] = b"".join(opener(url))
        except FetchError as e:
            raise DatasetError(f"could not read the catalogue at {url}: {e}") from e
    return _cache[url]


def _catalogue_url(catalog: str) -> str:
    return catalog if catalog.endswith("/") else catalog + "/"


def _manifest(id: str, catalog: str | Path, opener: Opener) -> dict:
    """The manifest `osd manifest <id>` writes, from a local catalogue or a catalogue root URL."""
    if "#" in id:
        raise DatasetError(f"'{id}' is a feature id; osd.get takes a dataset id such as 'opm/norne'")
    if isinstance(catalog, str) and catalog.startswith(("http://", "https://")):
        root = _catalogue_url(catalog)
        records = _read(root + "records.json", opener)
        rids = {r["id"] for r in json.loads(records)["records"]}
        rid = id if id in rids else next((r for r in rids if collection_id(r) == id), None)
        if rid is None:
            raise DatasetError(f"'{id}' is not a dataset in the catalogue at {root}")
        cid = collection_id(rid)
        col = _read(f"{root}stac/{cid}/collection.json", opener)
        with tempfile.TemporaryDirectory(prefix="osd-catalog-") as tmp:
            d = Path(tmp)
            (d / "records.json").write_bytes(records)
            (d / "stac" / cid).mkdir(parents=True)
            (d / "stac" / cid / "collection.json").write_bytes(col)
            return mf.from_catalog([rid], d, root + "stac/catalog.json")
    try:
        return mf.from_catalog([id], Path(catalog))
    except FileNotFoundError as e:
        raise DatasetError(f"no built catalogue at {catalog}: {e.filename}") from e
    except mf.ManifestError as e:
        raise DatasetError(str(e)) from e


def get(id: str, dest: str | Path | None = None, area: str | None = None,
        catalog: str | Path | None = None, opener: Opener | None = None) -> Dataset:
    """Fetch one dataset's files into `dest` (default ./osd-data/<publisher>/<dataset>), checked."""
    if area is not None:
        raise ValueError(AREA_REFUSAL)
    opener = opener or http_open
    m = mf.read_doc(_manifest(id, DEFAULT_CATALOG if catalog is None else catalog, opener), id)
    (e,) = m.entries
    dest = Path(dest) if dest is not None else Path("osd-data", *e.record_id.split("/", 1))
    outcomes = get_mod.get(m, dest, opener)
    bad = next((r for r in outcomes if r.outcome == "mismatch"), None)
    if bad:
        raise ChecksumMismatch(f"{bad.collection_id}/{bad.key}", bad.detail)
    assets = {a.key: a for a in e.assets}
    files, todo = [], []
    for r in outcomes:
        a = assets[r.key]
        if r.outcome in ("verified", "fetched"):
            p = get_mod.target(dest, e, r.key)
            files.append(File(r.key, p, p.stat().st_size, a.sha256,
                              "publisher" if r.source == "origin" else r.source,
                              "verified" if r.outcome == "verified" else "no checksum recorded"))
        else:
            todo.append(f"{r.key}: {r.outcome}: {r.detail}")
    if not e.assets:
        todo.append(f"{e.unresolved} -> {e.origin_url}")
    return Dataset(id=e.record_id, title=e.title, licence=e.licence,
                   attribution="\n".join(get_mod.entry_attribution(e)), path=dest, files=tuple(files),
                   todo=tuple(todo), outcomes=tuple(outcomes), manifest=m)
