"""Outlines from the data (E03): fetch a record's inputs, derive WGS84 features, check them.

  fetch_inputs  the verifier's Opener (paced, robots.txt obeyed) stores each record input as
                parts under build/inputs/<id>/<input>/ with a SHA256SUMS; the input's identity
                is the sha256 of that SHA256SUMS. The only network in this package.
  derive        pure over the stored parts: one extractor per input (rules.yaml, OSD-D11), every
                feature names its input and carries a feature_id; the collection carries each
                input's identity {url, sha256} and the record's licence once (OSD-D13, D16).
                Refused names the reason; nothing is guessed.
  check         the L3 `outline-derived` outcome for a committed outline file (OSD-D12).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode

import yaml

from .. import paths
from ..records import geometry_problems
from .extractors import (
    EXTRACTORS,
    arcgis_count,
    arcgis_layer,
    arcgis_layer_facts,
    arcgis_out_fields,
    arcgis_page_query,
    geojson_page,
    mdio_header_chunks,
    page_offsets,
)
from .geometry import Refused, simplify

RULES_PATH = Path(__file__).parent / "rules.yaml"
INPUTS_DIR = paths.BUILD_DIR / "inputs"
PART_BYTES = 64 * 1024**2
SIMPLIFY_M = 50  # OSD-D16 default: below the bin size a survey's staircase outline encodes;
POLYGON_DECIMALS = 5  # about 1.1 m, below SIMPLIFY_M; rules.yaml `defaults` may restate both
MAX_PAGES = 200

__all__ = ["Refused", "check", "derive", "fetch_inputs", "load_rules", "stored_inputs", "write_outline"]


def load_rules(path: Path = RULES_PATH) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _dir(inputs_dir: Path, rid: str, name: str = "") -> Path:
    d = inputs_dir / rid.replace("/", "__")
    return d / name if name else d


# --- stored inputs -----------------------------------------------------------------------------

def _sums(parts: list[tuple[str, bytes]]) -> bytes:
    return "".join(f"{hashlib.sha256(b).hexdigest()}  {n}\n" for n, b in parts).encode()


def input_sha256(parts: list[tuple[str, bytes]]) -> str:
    return hashlib.sha256(_sums(parts)).hexdigest()


def store(d: Path, parts: list[tuple[str, bytes]]) -> str:
    d.mkdir(parents=True, exist_ok=True)
    for n, b in parts:
        (d / n).parent.mkdir(parents=True, exist_ok=True)
        (d / n).write_bytes(b)
    (d / "SHA256SUMS").write_bytes(_sums(parts))
    return input_sha256(parts)


def read_parts(d: Path) -> list[tuple[str, bytes]]:
    """The parts in fetch order; a part whose bytes no longer match SHA256SUMS is refused."""
    sums = d / "SHA256SUMS"
    if not sums.exists():
        raise Refused(f"input not fetched: no {sums}")
    parts = []
    for line in sums.read_text().splitlines():
        sha, name = line.split("  ", 1)
        b = (d / name).read_bytes()
        if hashlib.sha256(b).hexdigest() != sha:
            raise Refused(f"stored part {d / name} changed since it was fetched")
        parts.append((name, b))
    return parts


def stored_inputs(rid: str, inputs_dir: Path = INPUTS_DIR) -> dict[str, str]:
    """{input url: input sha256} for every input stored for this record and still intact."""
    index = _dir(inputs_dir, rid) / "inputs.json"
    if not index.exists():
        return {}
    out = {}
    for i in json.loads(index.read_text()):
        try:
            out[i["url"]] = input_sha256(read_parts(_dir(inputs_dir, rid, i["name"])))
        except (Refused, OSError):
            continue
    return out


# --- fetching (network through the injected Opener) ------------------------------------------

def _with(url: str, params: dict) -> str:
    return url + ("&" if "?" in url else "?") + urlencode(params)


def _get(url: str, opener, robots) -> bytes:
    from ..verify import FetchError, _read  # verify imports this package

    if not robots.allowed(url):
        raise Refused(f"robots.txt disallows {url}")
    try:
        b = _read(opener(url), PART_BYTES)
    except FetchError as e:
        raise Refused(f"fetch failed: {e}") from None
    if len(b) >= PART_BYTES:
        raise Refused(f"{url} is larger than {PART_BYTES} bytes: not read in part")
    return b


def fetch_parts(rec_input: dict, rule: dict, opener, robots) -> list[tuple[str, bytes]]:
    url, fmt = rec_input["url"], rec_input["format"]
    if fmt == "wfs":
        parts = []
        if rule.get("hits", True):
            parts.append(("hits", _get(_with(url, {"resultType": "hits"}), opener, robots)))
        size = int(rule["page_size"])
        for page in range(MAX_PAGES):
            start = page * size
            b = _get(_with(url, {**(rule.get("params") or {}), "count": size, "startIndex": start}), opener, robots)
            parts.append((f"page-{start:06d}", b))
            try:
                served = len(geojson_page(b).get("features") or [])
            except ValueError:
                raise Refused(f"{rec_input['name']}: page at {start} is not GeoJSON: {b[:120]!r}") from None
            if served < size:
                return parts
        raise Refused(f"{rec_input['name']}: more than {MAX_PAGES} pages")
    if fmt == "arcgis":   # E29: description, the day's count, then every page in object id order
        layer = arcgis_layer_facts(_get(_with(url, {"f": "json"}), opener, robots))
        oid, size = arcgis_layer(layer)
        count = _get(_with(url + "/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"}), opener, robots)
        parts = [("layer", layer), ("count", count)]
        fields = arcgis_out_fields(rule, oid)
        for off in page_offsets(arcgis_count(count), size):   # native spatial reference: no outSR
            q = arcgis_page_query(oid, size, off, fields)
            parts.append((f"page-{off:06d}", _get(_with(url + "/query", q), opener, robots)))
        return parts
    if fmt == "mdio":
        base = url.rstrip("/") + "/"
        parts = [(".zmetadata", _get(base + ".zmetadata", opener, robots))]
        meta = json.loads(parts[0][1])["metadata"]
        a = meta.get("trace_mask/.zarray") or {}
        if not a:
            raise Refused(f"{rec_input['name']}: MDIO store has no trace_mask")
        (ni, nx), (ci, cx) = a["shape"], a["chunks"]
        for bi in range(-(-ni // ci)):
            for bx in range(-(-nx // cx)):
                parts.append((f"trace_mask/{bi}/{bx}", _get(f"{base}trace_mask/{bi}/{bx}", opener, robots)))
        for name in mdio_header_chunks(dict(parts)):
            parts.append((name, _get(base + name, opener, robots)))
        return parts
    return [("body", _get(url, opener, robots))]


def fetch_inputs(rec: dict, rules: dict, opener, inputs_dir: Path = INPUTS_DIR) -> dict[str, str]:
    """Fetch and store every input of the record that has a rule; {input name: input sha256}."""
    from ..verify import _Robots

    rid, robots = rec["id"], _Robots(opener)
    todo = _inputs_with_rules(rec, rules)
    out, index = {}, []
    for i in todo:
        parts = fetch_parts(i, rules[rid]["inputs"][i["name"]], opener, robots)
        d = _dir(inputs_dir, rid, i["name"])
        if d.exists():
            for old in sorted(d.rglob("*"), reverse=True):
                old.unlink() if old.is_file() else old.rmdir()
        out[i["name"]] = store(d, parts)
        index.append({"name": i["name"], "url": i["url"], "sha256": out[i["name"]]})
    (_dir(inputs_dir, rid) / "inputs.json").write_text(json.dumps(index, indent=2) + "\n")
    return out


def _inputs_with_rules(rec: dict, rules: dict) -> list[dict]:
    rid, inputs = rec["id"], rec.get("inputs") or []
    if not inputs:
        raise Refused("the record declares no inputs")
    names = [i["name"] for i in inputs]
    if len(set(names)) != len(names):
        raise Refused(f"input names repeat: {names}")
    rule = (rules.get(rid) or {}).get("inputs") or {}
    todo = [i for i in inputs if i["name"] in rule]
    if not todo:
        raise Refused(f"no rule in outlines/rules.yaml for any input of {rid}")
    return todo


# --- deriving (pure) -------------------------------------------------------------------------

def derive(rec: dict, rules: dict, inputs_dir: Path = INPUTS_DIR) -> dict:
    """The FeatureCollection for outlines/<id>.geojson, from the stored inputs only."""
    rid = rec["id"]
    feats, unplaced, used = [], [], {}
    defaults = rules.get("defaults") or {}
    tolerance = rules[rid].get("simplify_m", defaults.get("simplify_m", SIMPLIFY_M))
    decimals = rules[rid].get("polygon_decimals", defaults.get("polygon_decimals", POLYGON_DECIMALS))
    exteriors = set(rules[rid].get("exteriors_only") or [])
    for i in _inputs_with_rules(rec, rules):
        rule = rules[rid]["inputs"][i["name"]]
        parts = read_parts(_dir(inputs_dir, rid, i["name"]))
        used[i["name"]] = {"url": i["url"], "sha256": input_sha256(parts)}
        if rule.get("period_fields"):  # outline/3: the service properties the dates were read from
            used[i["name"]]["period_fields"] = dict(rule["period_fields"])
        for f in EXTRACTORS[rule["extractor"]](i, rule, parts):
            g = f.pop("geometry")
            key = f.get("publisher_id") or f.get("uwi") or i["name"]
            if rule.get("id_scope"):  # a publisher numbering several registers from one sequence
                key = f"{rule['id_scope']}/{key}"
            if g is None:  # the register lists it without a position (rule unplaced: report)
                unplaced.append(f"{rid}#{key}")
                continue
            how = ""
            if g["type"] in ("Polygon", "MultiPolygon"):  # OSD-D16; points stay exact
                ext = f["kind"] in exteriors
                g, f["rings_dropped"] = simplify(g, tolerance, ext, decimals)
                f["simplified_m"] = tolerance
                how = f", simplified {tolerance} m{', exterior only' if ext else ''}, {decimals} decimals"
            bad = geometry_problems(g)
            if bad:
                raise Refused(f"{i['name']}: {f.get('publisher_id') or f['name']}: {bad[0]}")
            props = {"record_id": rid, "kind": f.pop("kind"), "name": f.pop("name"), "approximate": False,
                     "source": f"{rule['extractor']} ({i['name']}){how}", **f, "feature_id": f"{rid}#{key}",
                     "input": i["name"]}
            feats.append({"type": "Feature", "properties": props, "geometry": g})
    dup = [k for k, n in Counter([f["properties"]["feature_id"] for f in feats] + unplaced).items() if n > 1]
    if dup:
        raise Refused(f"{len(dup)} feature_id collisions, e.g. {dup[0]}")
    feats.sort(key=lambda f: f["properties"]["feature_id"])
    fc = {"type": "FeatureCollection", "licence": rec["licence"]["name"], "inputs": used, "features": feats}
    if unplaced:
        fc["unplaced"] = sorted(unplaced)  # GeoJSON foreign member: listed, no position to draw
    return fc


def write_outline(fc: dict, path: Path) -> None:
    """One feature per line: a rerun is a reviewable diff (OSD-D12)."""
    lines = [json.dumps(f, ensure_ascii=False, separators=(",", ":")) for f in fc["features"]]
    head = '{"type":"FeatureCollection",'
    for k in ("licence", "inputs"):
        if k in fc:
            head += json.dumps(k) + ":" + json.dumps(fc[k], ensure_ascii=False, separators=(",", ":")) + ",\n"
    if fc.get("unplaced"):
        head += '"unplaced":' + json.dumps(fc["unplaced"], ensure_ascii=False) + ",\n"
    path.write_text(head + '"features":[\n' + ",\n".join(lines) + "\n]}\n")


# --- the L3 check ------------------------------------------------------------------------------

def check(rec: dict, outline: dict, rule: dict | None, stored: dict[str, str],
          refused: str | None = None) -> tuple[str, str]:
    """(outcome, detail) of `outline-derived`: pass only when every feature is derived and names
    an input of the collection whose (url, sha256) is a stored input of the record, ids are unique
    and the count reaches the rules' min_features."""
    feats = outline.get("features") or []
    if refused:
        return "fail", f"derivation refused this run: {refused}"
    if not feats:
        return "fail", "no features"
    props = [f.get("properties") or {} for f in feats]
    approx = sum(1 for p in props if p.get("approximate") is not False)
    if approx:
        return "fail", f"{approx} approximate features"
    named = outline.get("inputs") or {}
    lacking = sum(1 for p in props if not (p.get("feature_id") and (named.get(p.get("input")) or {}).get("sha256")))
    if lacking:
        return "fail", f"{lacking} features without feature_id or an input the collection carries"
    dup = [k for k, n in Counter(p["feature_id"] for p in props).items() if n > 1]
    if dup:
        return "fail", f"duplicate feature_id {dup[0]}"
    declared = {i["url"] for i in rec.get("inputs") or []}
    if not declared:
        return "fail", "the record declares no inputs"
    used = {(named[p["input"]]["url"], named[p["input"]]["sha256"]) for p in props}
    if any(u not in declared for u, _ in used):
        return "fail", "features name an input the record does not declare"
    want = (rule or {}).get("min_features")
    if not isinstance(want, int) or want < 1:
        return "fail", "no min_features for this record in outlines/rules.yaml"
    if len(feats) < want:
        return "fail", f"{len(feats)} features, fewer than the {want} the rules record"
    if not stored:
        return "skip", "inputs not stored on this runner: `osd verify --outlines` fetches them"
    stale = sorted(u for u, s in used if stored.get(u) != s)
    if stale:
        return "fail", f"derived from bytes that differ from the stored input {stale[0]}: rerun --outlines, review the diff"
    unplaced = f"; {len(outline['unplaced'])} listed without a position" if outline.get("unplaced") else ""
    return "pass", (f"{len(feats)} features derived from {len(used)} inputs, every input sha256 equal to the "
                    f"stored bytes (min_features {want}){unplaced}")
