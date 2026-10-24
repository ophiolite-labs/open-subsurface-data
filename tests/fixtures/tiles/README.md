# Tiles fixture: two registers whose strings cross (E32)

`crossing.geojson` is `outlines.geojson` as `osd build` writes it for two point registers. Register
B's `feature_id`s and register A's well names were chosen so that their 64-bit FNV-1a hashes
(tippecanoe's string pool hash, `fnv1a(s, type)` with type 0 for a string) differ but share the low
32 bits:

| register A `name` | register B `feature_id` | fnv1a |
|---|---|---|
| `A-001377 WELL` | `crossing/register-b#900540` | `0xc324188dd2b39b05` / `0x464149d5d2b39b05` |
| `A-002095 WELL` | `crossing/register-b#904407` | `0xc9e40ba824360c3b` / `0x4f70df6624360c3b` |

Before tippecanoe 2.55.0 the pool compared hashes as `(int)(ahash - bhash)`, so such a pair compared
equal and the later string was stored as the earlier one (felt/tippecanoe#239). Tiled by 2.49.0 or
2.53.0, register B's features carry `A-001377 WELL` and `A-002095 WELL` as `feature_id`, as North
Dakota #18505 and Utah #11965 carried BCER well names on the real data (E29, E32). The pair was found
by hashing `crossing/register-b#<n>` and `A-<m:06d> WELL` for n, m below 10^6 and matching the low
32 bits.
