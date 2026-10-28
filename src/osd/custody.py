"""Custody documents, osd.custody/1 (E07) and /2 (E40): one per copy the mirror holds, keyed by sha256.

`document()` writes what a copy is from the record (publisher facts) and the verification run that
inventoried it (tool facts), as /1. custody/2 adds two provenances besides that verified download: a
maintainer's `deposit` (`deposit_document()`, E41) and a starter pack's `derived` artefact
(`derived_document()`, E41); every reader here takes both versions through the live schema, and
`provenance()` says which of the three a document is. `problems()` is the schema plus what a schema cannot say: the store key
names the record, the digest and the file; a `.removed.json` name holds a tombstone and nothing else
does; and, given the stored object's size, `bytes` agrees with it.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import cache

from jsonschema import Draft202012Validator, FormatChecker

from . import paths
from .get import entry_attribution
from .manifest import LICENCE_FIELDS, Entry, Licence
from .stac import collection_id

FORMAT = "osd.custody/1"
FORMAT_2 = "osd.custody/2"
TAKEDOWN_URL = ("https://github.com/ophiolite-labs/open-subsurface-data/issues/new"
                "?template=takedown.yml")


@cache
def _validator() -> Draft202012Validator:
    schema = json.loads((paths.SCHEMA_DIR / "custody.schema.json").read_text())
    return Draft202012Validator(schema, format_checker=FormatChecker())


def object_name(path: str) -> str:
    """The listing path's last segment, path-safe."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", path.rstrip("/").rsplit("/", 1)[-1]).lstrip(".") or "_"


def object_key(record_id: str, sha256: str, path: str) -> str:
    return f"mirror/{record_id}/{sha256}/{object_name(path)}"


def provenance(doc: dict) -> str:
    """verified, deposit or derived, for a document the schema accepts (exactly one holds)."""
    return "deposit" if "deposit" in doc else "derived" if "derived" in doc else "verified"


def problems(doc: dict, name: str | None = None, object_bytes: int | None = None) -> list[str]:
    out = [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
           for e in sorted(_validator().iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))]
    if out:
        return out
    if doc["key"] != object_key(doc["record_id"], doc["sha256"], doc["path"]):
        out.append(f"key {doc['key']} is not {object_key(doc['record_id'], doc['sha256'], doc['path'])}")
    if name is not None:
        tomb = name.endswith(".removed.json")
        if name != doc["sha256"] + (".removed.json" if tomb else ".json"):
            out.append(f"file name {name} does not name the digest {doc['sha256']}")
        if tomb != (doc["removal"]["state"] == "removed"):
            out.append(f"removal state {doc['removal']['state']} in {name}")
    if object_bytes is not None and object_bytes != doc["bytes"]:
        out.append(f"inconsistent size: the document states {doc['bytes']} bytes, the stored object has {object_bytes}")
    return out


def _entry(rec: dict) -> Entry:
    lic = Licence(**{k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]})
    return Entry(collection_id=collection_id(rec["id"]), record_id=rec["id"], title=rec["title"],
                 origin_url=rec["origin"]["url"], access=rec["origin"]["access"], licence=lic, assets=(),
                 known_issues=tuple(rec.get("known_issues", [])))


def document(rec: dict, verification: dict, f: dict, href: str, now: datetime) -> dict:
    return {
        "format": FORMAT, "record_id": rec["id"], "path": f["path"], "origin_href": f["url"],
        "key": object_key(rec["id"], f["sha256"], f["path"]), "href": href,
        "sha256": f["sha256"], "bytes": f["bytes"], "copied_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verifier_run": {"checked_at": verification["checked_at"], "tool_version": verification["tool_version"]},
        "licence": {k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]},
        "licence_text_sha256": verification.get("licence_text_sha256"),
        "attribution": entry_attribution(_entry(rec)),
        "takedown": TAKEDOWN_URL,
        "removal": {"state": "held"},
    }


def _stamp(now: datetime) -> str:
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def deposit_document(rec: dict, path: str, sha256: str, n: int, href: str, now: datetime, deposit: dict) -> dict:
    """custody/2 for a maintainer's deposit (E41 design 1): the record's licence and attribution, no
    origin, the deposit block (when, by which role, the page and licence text captured then)."""
    return {
        "format": FORMAT_2, "record_id": rec["id"], "path": path, "origin_href": None,
        "key": object_key(rec["id"], sha256, path), "href": href, "sha256": sha256, "bytes": n,
        "copied_at": _stamp(now), "deposit": dict(deposit),
        "licence": {k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]},
        "licence_text_sha256": deposit["licence_text_sha256"],
        "attribution": entry_attribution(_entry(rec)),
        "takedown": TAKEDOWN_URL,
        "removal": {"state": "held"},
    }


def derived_document(rec: dict, licence: dict, path: str, sha256: str, n: int, href: str, now: datetime,
                     derived: dict) -> dict:
    """custody/2 for a starter pack's artefact (E41 design 5): the pack's computed licence (without
    `sources`), attribution worded from it, no origin and no licence text of its own, the lineage."""
    return {
        "format": FORMAT_2, "record_id": rec["id"], "path": path, "origin_href": None,
        "key": object_key(rec["id"], sha256, path), "href": href, "sha256": sha256, "bytes": n,
        "copied_at": _stamp(now), "derived": dict(derived), "licence": dict(licence),
        "licence_text_sha256": None,
        "attribution": entry_attribution(_entry(dict(rec, licence=licence))),
        "takedown": TAKEDOWN_URL,
        "removal": {"state": "held"},
    }
