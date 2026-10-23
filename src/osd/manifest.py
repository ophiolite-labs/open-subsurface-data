"""Retrieval manifests, osd.manifest/4 (E06; alternates E07; snapshot E09; record/3 vocabulary E19): write one from the built catalogue, read one typed.

`from_catalog(ids)` reads build/catalog/ (records.json, stac/, outlines.geojson) and returns a
manifest dict for a Collection selection (record or collection ids) or an Item selection (feature
ids, `publisher/dataset#local`), never a mix. Assets are the Collection's STAC assets as E04 wrote
them from the verifier's files[]: a sample (`coverage: sampled`). Items carry no assets, so an Item
selection lists its Collection and says why nothing is fetched. The licence object is the
record's, whole.

`read(path)` is the interface Ophiolite's intake reads (E09): it validates against
schema/manifest.schema.json and returns frozen dataclasses with `sha256` decoded from the
multihash; any other checksum algorithm raises.

osd.manifest/2 (E07) adds `alternates` per asset: other locations of the same bytes (the mirror,
from the STAC asset's `alternate`). A manifest is written as /2 only when an asset has one, so
a manifest without alternates stays readable by a /1 reader; both read here.

osd.manifest/3 (E09) adds `metadata.catalog`, the snapshot identity of the catalogue it was written
from (records.json `catalog`, copied whole), which a fidelity/1 record carries back. It is written
whenever records.json has one; a catalogue built before E09 still gives /1 or /2, and those read
with `catalog` None. The licence keeps exactly the keys the record states (`Licence.stated`), so a
missing statement stays missing and an `attribution: null` stays null (/3 only).

osd.manifest/4 (E19) carries the record/3 vocabulary: `access: purchase` and `licence.terms`, the
publisher's terms copied whole (`Terms.stated_keys`: absent and null differ here too). A manifest is
written as /4 only when an entry carries one of them, so every other manifest is what it was; /4
carries `metadata.catalog` like /3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from . import paths
from .stac import collection_id

FORMAT = "osd.manifest/1"
FORMAT_2 = "osd.manifest/2"
FORMAT_3 = "osd.manifest/3"
FORMAT_4 = "osd.manifest/4"
CATALOG_URL = "https://opensubsurfacedata.org/data/stac/catalog.json"
SHA256_MULTIHASH = "1220"
LICENCE_FIELDS = ("name", "spdx", "url", "redistribution", "attribution", "share_alike", "statement", "terms")
TERMS_FIELDS = ("stated", "duration", "review_before_publication", "expires")


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class Asset:
    key: str
    href: str
    size: int | None
    sha256: str | None
    title: str | None = None
    alternates: tuple[tuple[str, str], ...] = ()   # (name, href), tried before href (E07)


@dataclass(frozen=True)
class Terms:
    """licence.terms (record/3): the publisher's words; nothing here is computed."""
    stated: str
    duration: str | None = None                    # the publisher's wording, e.g. "at most 10 years from purchase"
    review_before_publication: bool | None = None
    expires: str | None = None                     # YYYY-MM-DD, only when the publisher states the date
    stated_keys: frozenset[str] = frozenset()      # the keys the manifest states: absent and null differ


@dataclass(frozen=True)
class Licence:
    name: str
    redistribution: str
    attribution: str | None             # None: stated as null (/3), the source gives no value
    spdx: str | None = None
    url: str | None = None
    share_alike: bool | None = None   # None: the record does not state it
    statement: str | None = None      # None: the publisher prescribes none we know of
    terms: Terms | None = None        # None: the record states no terms (record/3, manifest/4)
    stated: frozenset[str] = frozenset()   # the keys the manifest states: absent and null differ

    def __post_init__(self):
        if isinstance(self.terms, dict):   # a licence mapping read whole (here and in custody, E07)
            t = {k: self.terms[k] for k in TERMS_FIELDS if k in self.terms}
            object.__setattr__(self, "terms", Terms(**t, stated_keys=frozenset(t)))


@dataclass(frozen=True)
class Entry:
    collection_id: str
    record_id: str
    title: str
    origin_url: str
    access: str
    licence: Licence
    assets: tuple[Asset, ...]
    item_id: str | None = None
    feature_id: str | None = None
    coverage: str | None = None
    unresolved: str | None = None
    known_issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class Catalog:
    source_commit: str | None
    verification_commit: str | None
    built_at: str
    records_digest: str


@dataclass(frozen=True)
class Manifest:
    created: str
    catalog_url: str
    selection: str
    entries: tuple[Entry, ...]
    catalog: Catalog | None = None   # /3 and /4; None for /1 and /2


def _validator() -> Draft202012Validator:
    schema = json.loads((paths.SCHEMA_DIR / "manifest.schema.json").read_text())
    return Draft202012Validator(schema, format_checker=FormatChecker())


def problems(doc: dict) -> list[str]:
    return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
            for e in sorted(_validator().iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))]


def sha256_of(checksum: str | None, where: str) -> str | None:
    """STAC File `file:checksum` (multihash, hex) to a sha256 hex digest; other algorithms raise."""
    if checksum is None:
        return None
    if not checksum.startswith(SHA256_MULTIHASH) or len(checksum) != len(SHA256_MULTIHASH) + 64:
        raise ManifestError(f"{where}: file:checksum {checksum[:12]}… is not sha2-256 (multihash 1220); "
                            "osd get verifies sha256 only and refuses to guess")
    return checksum[len(SHA256_MULTIHASH):]


def read(path: Path | str) -> Manifest:
    return read_doc(json.loads(Path(path).read_text()), str(path))


def read_doc(doc: dict, where: str = "manifest") -> Manifest:
    bad = problems(doc)
    if bad:
        raise ManifestError(f"{where}: not an {FORMAT}, {FORMAT_2}, {FORMAT_3} or {FORMAT_4} manifest:\n  " + "\n  ".join(bad))
    entries = []
    for i, e in enumerate(doc["entries"]):
        assets = tuple(Asset(key=k, href=a["href"], size=a.get("file:size"), title=a.get("title"),
                             sha256=sha256_of(a.get("file:checksum"), f"entries/{i}/assets/{k}"),
                             alternates=tuple((n, x["href"]) for n, x in a.get("alternates", {}).items()))
                       for k, a in e["assets"].items())
        stated = {k: e["licence"][k] for k in LICENCE_FIELDS if k in e["licence"]}
        lic = Licence(**stated, stated=frozenset(stated))
        entries.append(Entry(collection_id=e["collection_id"], record_id=e["record_id"], title=e["title"],
                             origin_url=e["origin_url"], access=e["access"], licence=lic, assets=assets,
                             item_id=e.get("item_id"), feature_id=e.get("feature_id"),
                             coverage=e.get("coverage"), unresolved=e.get("unresolved"),
                             known_issues=tuple(e.get("known_issues", []))))
    cat = doc.get("metadata", {}).get("catalog")
    return Manifest(created=doc["created"], catalog_url=doc["catalog_url"], selection=doc["selection"],
                    entries=tuple(entries), catalog=Catalog(**cat) if cat else None)


def _no_assets_reason(rec: dict) -> str:
    access = rec["origin"]["access"]
    if access in ("registration", "request"):
        return f"access {access}: sign in or ask at the origin page; no file address is published to us"
    if access == "purchase":
        return "access purchase: the publisher sells the files; buy them at the origin page"
    return "the verifier has hashed no file with a fetch address for this record; get the files at the origin page"


def _entry(rec: dict) -> dict:
    e = {"collection_id": collection_id(rec["id"]), "record_id": rec["id"], "title": rec["title"],
         "origin_url": rec["origin"]["url"], "access": rec["origin"]["access"],
         "licence": {k: rec["licence"][k] for k in LICENCE_FIELDS if k in rec["licence"]}}
    if rec.get("known_issues"):
        e["known_issues"] = list(rec["known_issues"])
    return e


def _assets(collection: dict) -> dict:
    keep = ("href", "title", "roles", "file:size", "file:checksum")
    out = {}
    for k, a in collection.get("assets", {}).items():
        out[k] = {f: a[f] for f in keep if f in a}
        if a.get("alternate"):
            out[k]["alternates"] = {n: {"href": x["href"]} for n, x in a["alternate"].items()}
    return out


def from_catalog(ids: list[str], catalog_dir: Path = paths.CATALOG_DIR, catalog_url: str = CATALOG_URL,
                 now: datetime | None = None) -> dict:
    if not ids:
        raise ManifestError("select at least one record, collection or feature id")
    features = [i for i in ids if "#" in i]
    if features and len(features) != len(ids):
        raise ManifestError("a selection is Collections or Items, never a mix: "
                            f"{len(features)} feature ids and {len(ids) - len(features)} record ids given")
    built = json.loads((catalog_dir / "records.json").read_text())
    recs = {r["id"]: r for r in built["records"]}
    by_cid = {collection_id(rid): rid for rid in recs}
    stac_dir = catalog_dir / "stac"

    def collection(rid: str) -> dict:
        return json.loads((stac_dir / collection_id(rid) / "collection.json").read_text())

    entries = []
    if not features:
        for i in dict.fromkeys(ids):
            rid = i if i in recs else by_cid.get(i)
            if rid is None:
                raise ManifestError(f"'{i}' is neither a record id nor a collection id in {catalog_dir}")
            rec, col = recs[rid], collection(rid)
            e, assets = _entry(rec), _assets(col)
            e["assets"] = assets
            if assets:
                e["coverage"] = "sampled"
            else:
                e["unresolved"] = _no_assets_reason(rec)
            entries.append(e)
        selection = "collections"
    else:
        outlines = json.loads((catalog_dir / "outlines.geojson").read_text())["features"]
        known = {f["id"]: f["properties"]["record_id"] for f in outlines if "id" in f}
        for fid in dict.fromkeys(features):
            rid = known.get(fid)
            if rid is None:
                raise ManifestError(f"'{fid}' is not a feature id in {catalog_dir / 'outlines.geojson'}")
            rec, col = recs[rid], collection(rid)
            item_ids = {json.loads((stac_dir / collection_id(rid) / x["href"]).read_text())["id"]
                        for x in col["links"] if x["rel"] == "item"}
            e = _entry(rec)
            has_item = fid in item_ids
            e.update(item_id=fid if has_item else None, feature_id=fid, assets={})
            e["unresolved"] = (
                "STAC Items carry no assets: the files the catalogue knows belong to the Collection "
                f"{e['collection_id']}, not to this feature; select the Collection to fetch them"
                if has_item else
                f"no STAC Item for this feature (the record states no period); it belongs to the "
                f"Collection {e['collection_id']}")
            entries.append(e)
        selection = "items"
    v2 = any("alternates" in a for e in entries for a in e["assets"].values())
    v4 = any(e["access"] == "purchase" or "terms" in e["licence"] for e in entries)
    snapshot = built.get("catalog")   # absent from a catalogue built before E09
    if v4 and not snapshot:
        raise ManifestError("an entry carries record/3 values (purchase, terms) but records.json has no "
                            "`catalog`: rebuild the catalogue")
    doc = {"format": FORMAT_4 if v4 else FORMAT_3 if snapshot else FORMAT_2 if v2 else FORMAT,
           "created": (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "catalog_url": catalog_url, "selection": selection, "entries": entries}
    if snapshot:
        doc["metadata"] = {"catalog": dict(snapshot)}
    bad = problems(doc)
    if bad:   # never write a manifest the reader would refuse
        raise ManifestError("built an invalid manifest:\n  " + "\n  ".join(bad))
    return doc


def write(doc: dict, path: Path) -> Path:
    path.write_text(json.dumps(doc, indent=2) + "\n")
    return path
