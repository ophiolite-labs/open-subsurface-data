# Bundled STAC schemas

Copies of the JSON schemas `stac-validator` needs to validate `build/catalog/stac/` without network
(E04). `schema-map.json` maps each published URL to its copy here, and the osd extension URL to
`../stac-osd.json`. Paths mirror the URL (`<host>/<path>`). Fetched 23 Oct 2026, unchanged:

- STAC 1.0.0 catalog, collection and item schemas, `schemas.stacspec.org` (Apache-2.0)
- GeoJSON `Feature` and `Geometry`, `geojson.org/schema` (referenced by the item schema)
- JSON Schema draft-07 meta-schema, `json-schema.org`
- File extension v2.1.0, `stac-extensions.github.io/file` (Apache-2.0)

To add an extension: fetch its schema and every schema it references, add each URL to
`schema-map.json`, and keep the offline test in `tests/test_stac.py` green.
