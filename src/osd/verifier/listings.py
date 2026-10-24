"""Listing readers (E23): which files a publisher's listing names, chosen by the response's shape.

A reader is selected by what the body is (JSON keys, an HTML title or marker, an XML root), never by
the host that served it. Structured readers return dataset assets only: landing pages, API metadata,
services and documentation links are left out, and an error body raises ListingError with the
publisher's message. The generic readers of E02 (JSON walk, S3 XML, HTML links, text lines) stay
for everything else, so E07's mirror selection through `parse_listing` is unchanged.

A `manifest_url` whose response is itself a data file (H1 design 8: a content type other than HTML,
JSON, XML or plain text, or `Content-Disposition: attachment`) is not read as a listing at all: it
is the one entry, `file_listing`. A CSV served as `text/csv` is a file, never a text list of URLs.

A publisher's checksum, when the listing states one, rides on the entry as `{algorithm, digest}`
verbatim; `osd.verify` decides whether it can be compared. A generated export (an ArcGIS query) is
marked so the hasher watches it for truncation; an ArcGIS export names its layer, which the verifier
reads whole (E35, osd.verifier.layers) before falling back to the export.

A `manifest_url` that names a WFS feature type (`service=WFS` with `typeNames`) or an OGC API
Features collection (a path ending `/collections/<id>` or `/collections/<id>/items`) is not a
listing either: `ogc_service` recognises it from the URL alone, and the verifier reads the layer
whole (E38) before it opens the URL or looks at its headers.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import NamedTuple
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlsplit

FIRST_BYTES = 40
SERVICE_FORMAT = re.compile(r"^\s*(API\b|HTML?\s*$|WEB\s*PAGE|W[MFC]T?S\s*$|ESRI\s*REST|ARCGIS|OGC\b)", re.IGNORECASE)
TRUNCATED = re.compile(rb'"exceededTransferLimit"\s*:\s*true')
SOCRATA_ID = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$")
LISTING_TYPES = frozenset({"text/html", "application/xhtml+xml", "application/json", "text/json",
                           "application/xml", "text/xml", "text/plain"})  # and every +json, +xml


class ListingError(ValueError):
    """The listing answered, but not with a list of files this verifier can read."""


@dataclass(frozen=True)
class Entry:
    name: str  # as the listing states it
    url: str
    size: int | None = None
    checksum: dict | None = field(default=None, compare=False)  # {algorithm, digest} as stated
    generated: bool = False  # a server-side export: may come back truncated
    layer: str | None = field(default=None, compare=False)  # E35: the ArcGIS layer this export queries


@dataclass(frozen=True)
class Listing:
    shape: str
    entries: list[Entry]
    listed_at: str | None = None  # the publisher's own date for the listed data, when it states one


def _size(v) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def _basename(url: str) -> str:
    return unquote(urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]) or url


def _date(ms_or_s, scale: int = 1) -> str | None:
    if isinstance(ms_or_s, (int, float)) and not isinstance(ms_or_s, bool) and ms_or_s > 0:
        return datetime.fromtimestamp(ms_or_s / scale, UTC).date().isoformat()
    return None


def stated_checksum(value) -> dict | None:
    """A publisher's checksum as stated: "md5:…", {"type": "MD5", "value": …}, or bare hex."""
    if isinstance(value, dict):
        alg = value.get("type") or value.get("algorithm") or ""
        dig = value.get("value") or value.get("digest") or ""
        return {"algorithm": str(alg)[:64], "digest": str(dig)[:256]} if dig else None
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    if ":" in value:
        alg, dig = value.split(":", 1)
        return {"algorithm": alg[:64], "digest": dig[:256]}
    alg = {32: "md5", 40: "sha1", 64: "sha256"}.get(len(value)) if re.fullmatch(r"[0-9a-fA-F]+", value) else None
    return {"algorithm": alg or "unstated", "digest": value[:256]}


class OgcService(NamedTuple):
    protocol: str   # "wfs" or "ogcapi"
    url: str        # the WFS endpoint without its query, or the collection URL
    name: str       # the WFS typeNames, or the collection's query (format parameters) to keep

OGC_COLLECTION = re.compile(r"^(.*/collections/[^/]+?)(?:/items)?/?$")
OGC_PAGING = frozenset({"limit", "offset", "startindex"})


def ogc_service(url: str) -> OgcService | None:
    """E38 design 3: the WFS feature type or the OGC API collection a manifest_url names, or None."""
    u = urlsplit(url)
    q = parse_qsl(u.query, keep_blank_values=True)
    keys = {k.lower(): v for k, v in q}
    names = keys.get("typenames") or keys.get("typename")
    if keys.get("service", "").upper() == "WFS" and names:
        return OgcService("wfs", f"{u.scheme}://{u.netloc}{u.path}", names)
    if m := OGC_COLLECTION.match(u.path):
        kept = urlencode([(k, v) for k, v in q if k.lower() not in OGC_PAGING])
        return OgcService("ogcapi", f"{u.scheme}://{u.netloc}{m.group(1)}", kept)
    return None


# --- structured JSON readers ---------------------------------------------------------------------
# Each takes the parsed document and the listing URL and returns a Listing, or None when the
# document is not its shape. Order matters only where shapes nest (CKAN before the generic walk).

def _ckan(d, base):
    r = d.get("result") if isinstance(d, dict) and "success" in d else None
    if not (isinstance(r, dict) and isinstance(r.get("resources"), list)):
        return None
    out = []
    for res in r["resources"]:
        url = res.get("url") if isinstance(res, dict) else None
        if not isinstance(url, str) or not url or SERVICE_FORMAT.match(str(res.get("format") or "")):
            continue
        out.append(Entry(res.get("name") or _basename(url), urljoin(base, url), _size(res.get("size")),
                         stated_checksum(res.get("hash") or res.get("checksum"))))
    return Listing("ckan", out)


def _datagovtw(d, base):
    r = d.get("result") if isinstance(d, dict) and "success" in d else None
    if not (isinstance(r, dict) and isinstance(r.get("distribution"), list)):
        return None
    out = [Entry(_basename(x["resourceDownloadUrl"]), x["resourceDownloadUrl"])
           for x in r["distribution"] if isinstance(x, dict) and isinstance(x.get("resourceDownloadUrl"), str)
           and x["resourceDownloadUrl"]]
    return Listing("data.gov.tw", out)


def _socrata(d, base):
    if not (isinstance(d, dict) and SOCRATA_ID.match(str(d.get("id", ""))) and "viewType" in d
            and isinstance(d.get("columns"), list)):
        return None
    u = urlsplit(base)
    url = f"{u.scheme}://{u.netloc}/api/views/{d['id']}/rows.csv?accessType=DOWNLOAD"
    return Listing("socrata", [Entry("rows.csv", url, generated=True)], _date(d.get("rowsUpdatedAt")))


def _arcgis_export(layer_url: str, max_records: int) -> Entry:
    url = (f"{layer_url.rstrip('/')}/query?where=1%3D1&outFields=*&f=geojson"
           f"&resultRecordCount={max_records}")
    return Entry(f"query export (geojson, at most {max_records} features)", url, generated=True,
                 layer=layer_url.rstrip("/"))


def _arcgis(d, base):
    if not (isinstance(d, dict) and d.get("type") in ("Feature Layer", "Table")
            and isinstance(d.get("maxRecordCount"), int) and isinstance(d.get("fields"), list)):
        return None
    u = urlsplit(base)
    layer = f"{u.scheme}://{u.netloc}{u.path}"
    edited = (d.get("editingInfo") or {}).get("lastEditDate")
    return Listing("arcgis-layer", [_arcgis_export(layer, d["maxRecordCount"])], _date(edited, 1000))


def _zenodo(d, base):
    if not (isinstance(d, dict) and "conceptrecid" in d and isinstance(d.get("files"), list)):
        return None
    out = [Entry(f["key"], f["links"]["self"], _size(f.get("size")), stated_checksum(f.get("checksum")))
           for f in d["files"] if isinstance(f, dict) and isinstance((f.get("links") or {}).get("self"), str)]
    return Listing("zenodo", out)


def _figshare(d, base):
    if not (isinstance(d, dict) and "figshare_url" in d and isinstance(d.get("files"), list)):
        return None
    out = [Entry(f["name"], f["download_url"], _size(f.get("size")),
                 stated_checksum(f.get("supplied_md5") or f.get("computed_md5")))
           for f in d["files"] if isinstance(f, dict) and not f.get("is_link_only") and f.get("download_url")]
    return Listing("figshare", out)


def _dataverse(d, base):
    v = (d.get("data") or {}).get("latestVersion") if isinstance(d, dict) and d.get("status") == "OK" else None
    if not (isinstance(v, dict) and isinstance(v.get("files"), list)):
        return None
    u = urlsplit(base)
    out = []
    for f in v["files"]:
        df = f.get("dataFile") if isinstance(f, dict) else None
        if not isinstance(df, dict) or f.get("restricted") or "id" not in df:
            continue
        name = "/".join(x for x in (f.get("directoryLabel"), df.get("filename")) if x)
        out.append(Entry(name, f"{u.scheme}://{u.netloc}/api/access/datafile/{df['id']}",
                         _size(df.get("filesize")), stated_checksum(df.get("checksum") or df.get("md5"))))
    return Listing("dataverse", out)


def _github_release(d, base):
    releases = d if isinstance(d, list) else [d]
    if not releases or not all(isinstance(r, dict) and "tag_name" in r and isinstance(r.get("assets"), list)
                               for r in releases):
        return None
    out = [Entry(a["name"], a["browser_download_url"], _size(a.get("size")), stated_checksum(a.get("digest")))
           for r in releases for a in r["assets"] if isinstance(a, dict) and a.get("browser_download_url")]
    return Listing("github-release", out)


def _datacite(d, base):
    data = d.get("data") if isinstance(d, dict) else None
    if not (isinstance(data, dict) and data.get("type") == "dois" and isinstance(data.get("attributes"), dict)):
        return None
    urls = data["attributes"].get("contentUrl") or []
    return Listing("datacite", [Entry(_basename(u), u) for u in urls if isinstance(u, str) and u])


def _jsonapi(d, base):
    data = d.get("data") if isinstance(d, dict) and "jsonapi" in d else None
    if not isinstance(data, list):
        return None
    out = []
    for r in data:
        a = r.get("attributes") if isinstance(r, dict) else None
        if isinstance(a, dict) and isinstance(a.get("file_url"), str) and a["file_url"]:
            out.append(Entry(a.get("title") or _basename(a["file_url"]), a["file_url"], _size(a.get("file_size"))))
    return Listing("json:api", out)


def _error(d) -> str | None:
    if isinstance(d, dict) and d.get("success") is False:
        e = d.get("error")
        return str(e.get("message") if isinstance(e, dict) else e)
    if isinstance(d, dict) and isinstance(d.get("error"), dict) and set(d) <= {"error"}:
        return str(d["error"].get("message") or d["error"].get("code"))
    return None


JSON_READERS = (_ckan, _datagovtw, _socrata, _arcgis, _zenodo, _figshare, _dataverse, _github_release,
                _datacite, _jsonapi)


def _json_walk(node, base: str, out: list[Entry]) -> None:
    """E02's generic reader: GitHub contents, STAC hrefs, name lists."""
    if isinstance(node, list):
        for x in node:
            if isinstance(x, str):
                out.append(Entry(x, urljoin(base, x)))
            else:
                _json_walk(x, base, out)
    elif isinstance(node, dict):
        name = node.get("path") or node.get("name") or node.get("key")
        size = node.get("size") if isinstance(node.get("size"), int) else None
        if "download_url" in node:  # GitHub contents API: directories have none
            if isinstance(node["download_url"], str):
                out.append(Entry(name or node["download_url"], node["download_url"], size))
            return
        for k in ("href", "url"):
            if isinstance(node.get(k), str):
                out.append(Entry(name if isinstance(name, str) else node[k], urljoin(base, node[k]), size))
                break
        for v in node.values():
            if isinstance(v, (list, dict)):
                _json_walk(v, base, out)


# --- HTML ------------------------------------------------------------------------------------------

class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href and not href.startswith(("#", "mailto:", "javascript:")):
                self.hrefs.append(href)


def _arcgis_page(text: str, base: str) -> Listing | None:
    """The ArcGIS REST services directory page of one layer (a layer URL without ?f=json)."""
    m = re.search(r"Max Record Count:</b>\s*(\d+)", text)
    if not (m and re.search(r"<title>\s*Layer:", text) and re.search(r"Type:</b>\s*(Feature Layer|Table)", text)):
        return None
    u = urlsplit(base)
    when = re.search(r"Last Edit Date:</b>\s*(\d{1,2})/(\d{1,2})/(\d{4})", text)
    listed = f"{when.group(3)}-{int(when.group(1)):02d}-{int(when.group(2)):02d}" if when else None
    return Listing("arcgis-layer", [_arcgis_export(f"{u.scheme}://{u.netloc}{u.path}", int(m.group(1)))], listed)


def names_a_file(content_type: str, disposition: str = "") -> bool:
    """H1 design 8: the response is a data file, not a listing; decided from the headers alone. An
    unstated content type is not a file (the body's shape decides, as before)."""
    if disposition.split(";", 1)[0].strip().lower() == "attachment":
        return True
    t = content_type.split(";", 1)[0].strip().lower()
    return bool(t) and t not in LISTING_TYPES and not t.endswith(("+json", "+xml"))


def file_listing(url: str, size: int | None = None) -> Listing:
    """The listing of a `manifest_url` that is itself the file: one entry, named by its last path segment."""
    return Listing("file", [Entry(_basename(url), url, size)])


def read_listing(body: bytes, base: str, content_type: str = "") -> Listing:
    """The files a listing names. Raises ListingError for an error body or an unrecognised format."""
    text = body.decode("utf-8", "replace")
    head = text.lstrip()[:600]
    if head.startswith(("{", "[")):
        try:
            doc = json.loads(text)
        except ValueError as e:
            raise ListingError(f"listing is not valid JSON ({e})") from None
        if (err := _error(doc)) is not None:
            raise ListingError(f"the listing is an error response: {err[:200]}")
        for reader in JSON_READERS:
            if (got := reader(doc, base)) is not None:
                return got
        out: list[Entry] = []
        _json_walk(doc, base, out)
        return Listing("json", out)
    if "<ListBucketResult" in head:
        u = urlsplit(base)
        prefix = f"{u.scheme}://{u.netloc}{u.path.rstrip('/')}/"
        out = []
        for c in re.findall(r"<Contents>(.*?)</Contents>", text, re.DOTALL):
            key = html.unescape(re.search(r"<Key>(.*?)</Key>", c, re.DOTALL).group(1))
            size = re.search(r"<Size>(\d+)</Size>", c)
            out.append(Entry(key, prefix + quote(key), int(size.group(1)) if size else None))
        return Listing("s3", out)
    if head.startswith("<"):
        if (got := _arcgis_page(text, base)) is not None:
            return got
        p = _Links()
        p.feed(text)
        if re.search(r"<title>\s*Index of ", head, re.IGNORECASE):   # a server directory index: no parent, no sort links
            return Listing("directory-index", [Entry(unquote(h), urljoin(base, h)) for h in p.hrefs
                                               if not h.startswith(("?", "../", "/")) and h != ".."])
        return Listing("html", [Entry(h, urljoin(base, h)) for h in p.hrefs])
    if text.strip() and b"\x00" not in body[:1024] and not content_type.startswith(("application/octet", "image/")):
        return Listing("text", [Entry(s, urljoin(base, s)) for s in (x.strip() for x in text.splitlines())
                                if s and not s.startswith("#")])
    raise ListingError(f"listing format not recognised (content type {content_type or 'not stated'}, "
                       f"first bytes {repr(body[:FIRST_BYTES])[1:]})")


def parse_listing(body: bytes, base: str) -> list[Entry]:
    """E02/E07 entry point: the entries of `read_listing`."""
    return read_listing(body, base).entries
