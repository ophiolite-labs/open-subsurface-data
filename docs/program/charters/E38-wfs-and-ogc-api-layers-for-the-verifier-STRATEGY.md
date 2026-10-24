# E38 strategy: WFS and OGC API Features layers for the verifier

Charter: `E38-wfs-and-ogc-api-layers-for-the-verifier.md` (Kernel; its Dispositions table is the
contract). Base: main 8023654 (H3 merged). Written at lane open, 24 Oct; endpoint facts measured
from this host the same day (`docs/program/evidence/e38/candidates.md`).

## Shape

```
records/<id>.yaml  origin.manifest_url = a WFS GetFeature (service=WFS, typeNames=…)
                                       or an OGC API Features collection (/collections/<id>[/items])
        |
check_files: samples.yaml entry read (list, or {sort: <property>} for WFS)
        |    listings.ogc_service(manifest) recognises the URL  --> BEFORE robots/open/bare-file   (design 3)
        |    (file: true and Content-Disposition: attachment are never consulted for these URLs)
        v
verifier/layers.export_wfs(base, type_name, sort, manifest, get)   verifier/layers.export_ogcapi(collection, query, get)
  1 GetCapabilities (2.0.0)  version, typeName listed,              1 collection description: the items link (geo+json)
    JSON output format, ImplementsResultPaging, ImplementsSorting    2 first page items?limit=N: numberMatched (or none)
    CountDefault                    -> partial (deferred) if not    3 next link only; seen-URL set (loop), dup ids
  2 GetFeature resultType=hits: numberMatched                        4 assembled == numberMatched, or unconfirmed
  3 > 50,000 -> partial; the manifest's own count-bounded GetFeature   > 50,000 -> partial; the first page kept
    kept as a partial export (as DOV's file was hashed before)
  4 sort property named?           -> partial (unsortable) if not
  5 pages startIndex 0,N,..; count N; sortBy=<prop> ASC; JSON;
    full pages but the last; ids; duplicates; same crs
  6 assembled == hits
        |
        v   Outcome(status, reason, entry, body, evidence)          (design 2)
complete    -> layer_exports[{format wfs-geojson|ogcapi-geojson, count, completeness: complete}]; pass L2,
               "whole layer checked (N features, …), not a downloadable file; stability unknown (…)"
unconfirmed -> layer_exports[{count: null, completeness: unconfirmed}]; skip: no L2
partial     -> nothing in layer_exports; the cap's evidence in partial_exports (partial: true); skip
failed      -> fail, the first failing guard named; nothing written
declined    -> skip (robots.txt on any request, the budget): as E35
```

`get(url)` is E35's `_layer_get`: robots through H3's `_Robots` on every request (a refusal on page
3 is a refusal), the paced opener, bytes counted against the record's 512 MiB share chunk by chunk
before decoding, an abandoned read counted (design 7). Nothing new on the network side.

## The outcome type (design 2)

```python
@dataclass(frozen=True)
class Outcome:
    status: str             # complete | unconfirmed | partial | failed | declined
    reason: str = ""        # partial/failed/declined: why; complete: the stability sentence
    entry: dict | None = None    # complete, unconfirmed: the layer_exports entry
    body: bytes = b""            # its canonical bytes
    evidence: dict | None = None # partial at the cap: {path, url, bytes, sha256, partial: True}
```

The readers return an Outcome and never raise: inside, guards raise `Refused` (failed), `Partial`
and E35's `Incomplete(…, "skip")` (declined), caught once at the reader's edge. Completeness is
decided only from the protocol's own count (hits or `numberMatched`) against the ids assembled;
nothing reads `exceededTransferLimit`, `totalFeatures`, `numberReturned` of a page as a completeness
signal (design 2: never inferred from an absent truncation flag). Only `complete` reaches L2; only
`files` reaches STAC, `osd get`, manifests and the mirror, and these readers never write `files`.

## verification/6 (design 1)

`$id` …/verification/6. `layer_exports.items` becomes `oneOf` two closed shapes:

- `esri-json`: E35's shape, byte for byte the same properties and required list.
- `wfs-geojson` | `ogcapi-geojson`: `{layer, format, features, count, completeness, bytes, sha256}`,
  `completeness` ∈ {`complete`, `unconfirmed`}, `count` integer or null; `complete` requires an
  integer count and `null` requires `unconfirmed` (if/then both ways). No revision fields: neither
  WFS 2.0 (`updateSequence` is the capabilities document's, not a feature type's) nor OGC API
  Features Part 1 states a revision for a feature type or collection, so the detail always says
  "stability unknown" (design 6) and the dispatch evidence lists disagreements.

/5 frozen as `tests/fixtures/schema/verification-5.schema.json` with a SHA-256 pin (main 8023654);
every /3, /4, /5 fixture and `stored-3.jsonl.gz` validates under /6; `tests/test_verify.py`'s one
`$id` assertion moves to /6.

## Canonical bytes (design 6)

`{"type":"FeatureCollection","features":[…]}` plus `"crs"` only when the pages state one (GeoServer
WFS does; every page must state the same), `json.dumps(sort_keys=True, separators=(",",":"),
ensure_ascii=False)`. Features as returned (type, id, geometry, properties, and whatever members the
server puts on a feature), sorted by feature `id` (`(is-string, value)` so numbers and strings never
compare). Page members (`numberMatched`, `numberReturned`, `totalFeatures`, `timeStamp`, `links`,
page `bbox`) are left out. Numbers are parsed and written back in the shortest round-trip form.

Ids are the feature `id` in both protocols (GeoServer's fid in WFS GeoJSON). A feature without one
fails; a repeated one fails ("served twice"). In WFS the sort property orders the pages; the ids
check what the pages assembled.

## Dispatch (design 3)

`listings.ogc_service(url)`: OGC API when the path ends `/collections/<id>` or `/collections/<id>/items`
(a STAC item path `…/items/<item>` is not); WFS when the query has `service=WFS` (any case) and
`typeNames` or `typeName`. Called in `check_files` right after the samples entry is read, before the
manifest robots check, the open and `names_a_file`. `file: true` is removed from the six WFS
manifests in `samples.yaml` (DOV x4, GSNSW, GSV) and replaced by `{sort: <property>}`.

## Records (design 8)

- ga/stratdat-biostratigraphy: `manifest_url` GetFeature `resfacs:Biostratigraphy`, count=1000, JSON.
- ga/resfacs-porosity-permeability: GetFeature `resfacs:PorosityPermeability`, count=1000, JSON.
- wogcc/wyde-wells: GetFeature `WY_SHPS:WELL`, count=1000, JSON.
- `origin.notes` of the three: the "No manifest_url" sentence replaced by what the manifest_url is.
- DOV x4, GSNSW, GSV: no record edit (their manifests are already WFS GetFeatures).

## Commits

0. Strategy and candidates (this file, `evidence/e38/candidates.md`).
1. Contract: verification/6, /5 frozen with hash pin, version and old-file tests; fixtures
   `tests/fixtures/ogc_layers/` (features, capabilities, exception report).
2. Outcome type, canonical GeoJSON bytes, `export_ogcapi` with its guards and tests.
3. `export_wfs` (capabilities, hits, cap, sort, pages) with its guards and tests.
4. Dispatch: `ogc_service`, `check_files` precedence and outcomes, end to end through
   `verify_record` with an injected opener (robots on a later page, budget, pacing, STAC).
5. Records and samples.yaml (design 8, design 3's removed overrides).
6. Mutations (`evidence/e38/mutations.md`, `mutate.py`), then the two dispatches and
   `evidence/e38/results.md`.

## Decisions taken by default (inbox `e38.md`)

1. The six existing WFS manifests all move to the reader (design 3 read literally), not DOV boringen
   alone: DOV boringen and formele-stratigrafie drop from L2 to L1 (above the cap: partial), DOV
   geothermie and graviteit, GSNSW and GSV keep L2 on whole-layer evidence; all six lose the
   GetFeature response as a STAC asset and `osd get` file.
2. OGC API Features has no eligible record (every record whose publisher serves it keeps a
   downloadable manifest): its dispatch outcome is recorded incomplete with that reason, and the
   reader is exercised against SGU borrhal (36,672 features, multi-page) by a lane-local run of
   `export_ogcapi` through the verifier's get, twice, recorded in results.md as reader evidence, not
   a level.
3. The WFS sort property is tool configuration (`sort:` in samples.yaml), because WFS 2.0 sorts by a
   property and GeoServer refuses `@gml:id`; a WFS record without one is partial ("unsortable").
4. Page size: WFS `min(CountDefault, 5000)`, 1000 when unstated; OGC API `limit=1000`. WFS output
   format: `application/json` first, then `application/geo+json` (DOV lists geo+json and refuses it).
5. Cap fallback evidence: WFS hashes the manifest's own GetFeature when it states a `count` (the
   bytes DOV's file check hashed before, now a partial export); OGC API keeps the first page.
