"""`osd new <url>`: scaffold a record from records/_template.yaml and the page's title.

A maintainer runs it on a "Suggest a dataset" issue. It writes only what the address and the page
title state (id, title, origin, the publisher's site, listed_by, added) and leaves every field a
human must read from the publisher's page as `null` or empty, so `osd validate` lists exactly
those until they are filled: publisher name, access, licence name, redistribution, attribution
and kinds. It reads one page, once; `--title` skips even that.
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from . import paths
from .records import _schema
from .verify import Fetcher, http_fetch

TEMPLATE = paths.RECORDS_DIR / "_template.yaml"


def page_title(body: bytes) -> str | None:
    m = re.search(rb"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    t = " ".join(html.unescape(m.group(1).decode("utf-8", "replace")).split())
    return t[:120] or None


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def record_id(url: str) -> str:
    """example.org/x -> example/x; data.equinor.com/volve.html -> equinor/volve."""
    u = urlsplit(url)
    labels = (u.hostname or "").removeprefix("www.").split(".")
    publisher = _slug(labels[-2] if len(labels) >= 2 else labels[0]) or "publisher"
    segments = [s for s in u.path.split("/") if s]
    dataset = _slug(segments[-1].rsplit(".", 1)[0]) if segments else ""
    return f"{publisher}/{dataset or 'dataset'}"


def choices() -> dict[str, str]:
    """The scaffold's comment lists, read from schema/record.schema.json so they never drift (E19; kinds E26)."""
    p = _schema("record")["properties"]
    return {"access": " | ".join(p["origin"]["properties"]["access"]["enum"]),
            "redistribution": " | ".join(p["licence"]["properties"]["redistribution"]["enum"]),
            "attribution": " | ".join(p["licence"]["properties"]["attribution"]["enum"]),
            "listed_by": " | ".join(p["listed_by"]["items"]["enum"]),
            "kinds": " | ".join(p["kinds"]["items"]["enum"])}


def scaffold(url: str, title: str | None, rid: str, today: date) -> str:
    u = urlsplit(url)
    c = choices()
    header = [line for line in TEMPLATE.read_text().splitlines() if line.startswith("#")]
    q = json.dumps  # a JSON string is a YAML string, whatever the title holds
    return "\n".join([
        *header,
        f"# Scaffolded by `osd new` on {today.isoformat()}. Every null or empty value below is for a",
        "# human to fill from the publisher's page; `osd validate` lists them until they are.",
        f"id: {rid}",
        f"title: {q(title) if title else 'null'}" + ("" if title else "   # fill: the dataset's name"),
        "publisher:",
        "  name: null                                      # fill: the publisher as it names itself",
        f"  url: {u.scheme}://{u.netloc}",
        "origin:",
        f"  url: {q(url)}",
        f"  access: null                                    # fill: {c['access']}",
        "licence:",
        "  name: null                                      # fill: the licence as the publisher names it",
        "  spdx: null                                      # CC-BY-4.0, CC-BY-SA-4.0, OGL-UK-3.0, NLOD-2.0 or null",
        f"  redistribution: null                            # fill: {c['redistribution']}",
        f"  attribution: null                               # fill: {c['attribution']}",
        f"kinds: []                                         # fill: {c['kinds']}",
        "region: {}                                        # country, basin, bbox when the publisher states them",
        f"listed_by: [community]                            # {c['listed_by']}",
        f"added: {today.isoformat()}",
        "",
    ])


def new_record(url: str, *, title: str | None = None, rid: str | None = None,
               fetch: Fetcher | None = None, records_dir: Path = paths.RECORDS_DIR,
               today: date | None = None) -> Path:
    """Write records/<id>.yaml and return its path; refuses to overwrite an existing record."""
    rid = rid or record_id(url)
    out = records_dir / f"{rid}.yaml"
    if out.exists():
        raise FileExistsError(f"{out} exists")
    if title is None:
        f = (fetch or http_fetch)(url)
        title = page_title(f.body) if 200 <= f.status < 400 else None
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(scaffold(url, title, rid, today or date.today()))
    return out
