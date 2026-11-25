"""Readers for the files `osd.get` brought (E49 slice 2), the optional extra `osd[readers]`.

Each reader imports its library when called, never at `import osd`; a missing library raises
`ImportError` with the one line to install. A dataset without files of the kind raises `ValueError`
naming the kinds it has.

  well_logs()  .las           -> {well name: pandas.DataFrame indexed by depth}; a well name seen
                                 twice becomes "<name> (<file key>)"; no WELL header: the file key
  segy()       .sgy, .segy    -> {file key: SegyInfo}: text header, traces, samples, interval (us)
  tables()     .csv           -> {file key: pandas.DataFrame}
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

INSTALL = 'pip install "osd[readers] @ git+https://github.com/ophiolite-labs/open-subsurface-data"'
KINDS = {"well_logs": (".las",), "segy": (".sgy", ".segy"), "tables": (".csv",)}


@dataclass(frozen=True)
class SegyInfo:
    path: Path
    text_header: str
    traces: int
    samples: int
    interval_us: float


def _need(module: str):
    try:
        return importlib.import_module(module)
    except ImportError as e:
        raise ImportError(f"reading these files needs {module}, which is not installed: {INSTALL}") from e


def _pick(dataset_id: str, files, reader: str) -> list:
    exts = KINDS[reader]
    out = [f for f in files if f.key.lower().endswith(exts)]
    if not out:
        have = sorted({Path(f.key).suffix.lower() or "(no extension)" for f in files}) or ["no files"]
        raise ValueError(f"{dataset_id} has no {'/'.join(exts)} files for {reader}() (it has: {', '.join(have)})")
    return out


def well_logs(dataset_id: str, files) -> dict:
    lasio = _need("lasio")
    _need("pandas")
    out: dict = {}
    for f in _pick(dataset_id, files, "well_logs"):
        las = lasio.read(str(f.path))
        name = str(las.well["WELL"].value).strip() if "WELL" in las.well else ""
        name = name or f.key
        out[f"{name} ({f.key})" if name in out else name] = las.df()
    return out


def segy(dataset_id: str, files) -> dict:
    segyio = _need("segyio")
    out = {}
    for f in _pick(dataset_id, files, "segy"):
        with segyio.open(str(f.path), ignore_geometry=True) as s:
            out[f.key] = SegyInfo(f.path, segyio.tools.wrap(s.text[0]), s.tracecount, len(s.samples),
                                  float(segyio.tools.dt(s)))
    return out


def tables(dataset_id: str, files) -> dict:
    pd = _need("pandas")
    return {f.key: pd.read_csv(f.path) for f in _pick(dataset_id, files, "tables")}
