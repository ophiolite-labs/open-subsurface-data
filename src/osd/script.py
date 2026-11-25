"""The Python file the bag writes (E49): `python -m osd.script <id> [<id> ...] [-o file.py]`.

`render(entries, today)` is a pure function of the manifest entries `osd manifest <ids>` writes
(`manifest.from_catalog`, which the page already writes equal, E06) and the date; the rule table is
docs/program/charters/E49-the-python-file-STRATEGY.md (T1-T8). Offline: a local catalogue only.
"""

from __future__ import annotations

import argparse
import keyword
import re
import sys
from datetime import date
from pathlib import Path

from . import manifest as mf
from . import paths

INSTALL = 'pip install "osd @ git+https://github.com/ophiolite-labs/open-subsurface-data"'
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
LEFT_OUT = {"registration": "sign-in needed: left out, sign in at {}",
            "request": "request needed: left out, ask at {}",
            "purchase": "for sale: left out, see {}"}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def variable(record_id: str, taken: set[str]) -> str:
    """T5: the dataset part, lower-case, safe as a Python name, unique in the file."""
    v = re.sub(r"[^a-z0-9_]", "_", record_id.split("/", 1)[-1].lower())
    if v[:1].isdigit():
        v = "d_" + v
    if keyword.iskeyword(v) or v == "osd":
        v += "_"
    out, n = v, 2
    while out in taken:
        out, n = f"{v}_{n}", n + 1
    taken.add(out)
    return out


def comment(entry: dict) -> str:
    """T6 and T7: where the files come from and how many, or why the dataset is left out."""
    assets = list(entry["assets"].values())
    if not assets:
        return LEFT_OUT.get(entry["access"], "no file address known: left out, see {}").format(entry["origin_url"])
    summed = [a for a in assets if "file:checksum" in a]
    mirror = sum(1 for a in summed if a.get("alternates"))
    publisher = len(assets) - mirror
    if not publisher:
        where = f"{_plural(mirror, 'file')} from our mirror"
    elif not mirror:
        where = f"{_plural(publisher, 'file')} from the publisher"
    else:
        where = f"{_plural(len(assets), 'file')}: {mirror} from our mirror and {publisher} from the publisher"
    k = len(summed)
    checked = "checked" if k == len(assets) else "no checksum recorded" if not k else f"{k} checked"
    return f"{where}, {checked}"


def render(entries: list[dict], today: date) -> str:
    taken: set[str] = set()
    code = [(f'{variable(e["record_id"], taken)} = osd.get("{e["record_id"]}")', comment(e)) for e in entries]
    width = max(len(c) for c, _ in code) + 2
    n = len(entries)
    lines = [(f"# open-subsurface-data, made {today.day} {MONTHS[today.month - 1]} {today.year} "
             f"for {_plural(n, 'dataset')}"),
             f"# {INSTALL}", "", "import osd", ""]
    lines += [f"{c:<{width}}# {why}" for c, why in code]
    lines += [""] + [f"print({c.split(' = ', 1)[0]})" for c, _ in code]
    return "\n".join(lines) + "\n"


def write(ids: list[str], catalog_dir: Path, today: date) -> str:
    if any("#" in i for i in ids):
        raise mf.ManifestError("the Python file takes dataset ids, not feature ids")
    return render(mf.from_catalog(ids, catalog_dir)["entries"], today)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m osd.script",
                                 description="write the Python file that fetches these datasets with osd.get")
    ap.add_argument("ids", nargs="+", help="dataset ids, e.g. opm/norne")
    ap.add_argument("-o", "--out", help="file to write (default: standard output)")
    ap.add_argument("--catalog", default=str(paths.CATALOG_DIR), help="the built catalogue (osd build)")
    ap.add_argument("--today", type=date.fromisoformat, default=None, help="YYYY-MM-DD for the first line")
    a = ap.parse_args(argv)
    try:
        text = write(a.ids, Path(a.catalog), a.today or date.today())
    except (mf.ManifestError, FileNotFoundError) as e:
        print(f"osd script: {e}", file=sys.stderr)
        return 2
    if a.out:
        Path(a.out).write_text(text)
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
