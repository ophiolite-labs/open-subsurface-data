# Decisions

Open items are for the owner. A default is applied under the standing delegation (Ophiolite,
18 Oct 2026) and recorded; the owner can overturn it.

| # | Question | Default applied | Status |
|---|---|---|---|
| OSD-D1 | Repository home and name | `ophiolite-labs/open-subsurface-data`, public | DECIDED by the owner 23 Oct |
| OSD-D2 | Licences: Apache-2.0 for code, CC0 for records and outlines | Applied in `LICENSE`, `records/LICENSE` | DEFAULT |
| OSD-D3 | Basemap and theme: OpenFreeMap Positron (light) under a dark panel today; a dark basemap when one without a key is confirmed | Positron | DEFAULT |
| OSD-D4 | Domain | `opensubsurfacedata.org`, bought by the owner at Spaceship 23 Oct; apex to GitHub Pages, `www` CNAME | DECIDED by the owner 23 Oct; DNS records are an owner action |
| OSD-D5 | Where verification results live | A `verification-results` branch the verify workflow force-pushes; pages reads it. No bucket and no secret until mirrors (E07) need bytes; then a separate Hetzner project `open-subsurface-data` so its keys cannot reach Ophiolite's buckets | DEFAULT 23 Oct (replaces the bucket-first default) |
| OSD-D6 | Mirror policy: mirror only `redistribution: allowed`, under 20 GB, with a takedown contact; never `unknown` | As stated | DEFAULT |
| OSD-D7 | First twenty datasets: the SEG open-data list plus Sodir, NLOG, NDR, NOPIMS, NZP&M registers | As stated; E01 may swap entries with reasons | DEFAULT |
| OSD-D8 | Codex review: one round per kernel charter, none for surface and records | As stated | DEFAULT |
| OSD-D9 | Publishers that refuse automated requests | Revised 23 Oct on the E02 charter review: a 403 or challenge page is a separate observation `blocked` and awards no level (a challenge proves an intermediary answered, not that the content is reachable); the map shows "blocked since <date>" next to L0; E08 never opens a dead-link issue for a blocked record. Measured 23 Oct: SEG wiki and NOPIMS block the VPS and GitHub-hosted runners alike | DEFAULT 23 Oct, revised |
| OSD-D10 | Name of the product on the site: "Open Subsurface Data" | As stated | DEFAULT |
| OSD-D11 | Record versus tool boundary | Records hold publisher facts only, including publisher-declared listings and asset addresses with their CRS. Verifier sampling policy and outline extraction rules live in tool configuration under `src/osd/` (`verifier/samples.yaml`, `outlines/rules.yaml`), keyed by record id. No tool policy field enters `schema/record.schema.json` | DEFAULT 23 Oct (E02/E03 reviews) |
| OSD-D12 | Derived outlines are committed | `outlines/*.geojson` are committed although derived, because their inputs are remote and mutable: a rerun is a reviewable diff, and the file is the contract E04/E05 read. Every derived feature carries the input identity (address and sha256 of the bytes used). This is the one recorded exception to ENGINEERING rule R7 | DEFAULT 23 Oct (E03 review) |
| OSD-D13 | Outline licence | Outlines derived from a publisher's data carry that publisher's licence, not CC0: each feature gets `licence` from its record, and `records/LICENSE` dedicates only the hand-written records and catalogue metadata | DEFAULT 23 Oct (E03 review) |
| OSD-D14 | STAC items and time | STAC Items need a datetime or a bounded interval. Collections are always emitted; Items only for features whose record declares a `period` (publisher-stated acquisition or release interval) or whose feature carries a publisher date. The GeoJSON stays the per-feature address for everything else | DEFAULT 23 Oct (E04 review) |
| OSD-D15 | Licence statement for outlines from a register | A publisher's own entry in its national open-data catalogue (Geonorge for Sodir: FactMaps data and service, NLOD) counts as the publisher's licence statement for outlines derived from that register when the service itself carries none. A version discrepancy between catalogue and terms page is recorded in the record's `known_issues`, not resolved by us | DEFAULT 23 Oct (E03 inbox) |
| OSD-D16 | Size of derived outlines | Survey polygons derived from bin grids are simplified in the extractor with a tolerance named per record in `src/osd/outlines/rules.yaml` (default 50 m, below the bin size the staircase encodes) and `simplified_m` is recorded on each feature; wellbore points stay exact; target under 2 MB per outline file, except register outlines (Sodir, NLOG: thousands of wellbores and hundreds of surveys), which may reach 8 MB until a tiling lane produces PMTiles; input identity is carried once per file in the collection's `inputs` member and features name their input; polygon rings with area below tolerance² are dropped and counted; 2D survey polygons (buffered line networks) are written as exteriors only and polygon coordinates are rounded to 5 decimals (E03-3, Sodir 10 MB otherwise). Amended 23 Oct on E03-2 (Sodir 14 MB after simplification, mostly repeated identity). Amended 24 Oct on E32 (supervisor): since E15 the site reads PMTiles, not outline files, so a register outline file of a layer above 20,000 features may reach 25 MB (North Dakota 17.5 MB, Utah 13.6, BCER 13.3, SGC 9.0); the staged site stays under 500 MB (E32 measured 485.6 MB). The simplified file is the committed contract (OSD-D12). Tiling at scale stays the PMTiles path the E05 page already loads | DEFAULT 23 Oct (E03 inbox; NLOG and Sodir outlines were 12 MB each unsimplified) |
| OSD-D17 | STAC extension schema URL | The `osd` STAC extension schema is published at the repository's raw URL on `main` (`schema/stac-osd.json`); the program has no tags, so a breaking change publishes a new file name and the old URL keeps serving the old schema. Validation in CI maps the URL to the local file and never fetches it | DEFAULT 23 Oct (E04 inbox) |

## OSD-D18 (23 Oct 2026, supervisor): the gate validates every Collection and a sample of Items; the full STAC tree validates in the verify workflow

Facts: E16 gave every Sodir and NLOG feature an Item (18,432 Items). Recursive offline validation of the
whole staged tree takes 115 s locally and pushes `make check` past its two-minute budget (ENGINEERING.md
"The gate"). Ruling: `make check` validates the catalog, every Collection and, per Collection, the first
and last Item plus up to 20 Items chosen by a fixed seed; `make check-full` validates the whole tree and
runs as a step of the dispatched `verify` workflow on main (never on pull-request runs). Items are
generated by one function from one template, so a sample proves the generator; the full run on main
catches data-dependent escapes before publication. The gate budget stays at two minutes. Lane E16 lands
it with its records (claim extended to `tests/test_stac.py`, `tests/test_outlines.py` one line for the
record/2 `period` field, `Makefile` `check-full`, `.github/workflows/verify.yml` one step).

## OSD-D19 (23 Oct 2026, supervisor): the STAC `osd` extension is versioned in its identifier's query string; frozen copies live in the test fixtures

Facts: OSD-D17 placed the extension schema at one file on main's raw URL, which is also its STAC
identifier. AGENTS.md requires a new identifier on a schema change. A path-based version would
need a new file per version at a new URL. Ruling: the identifier gains `?v=<n>` (the host ignores the
query, so every version resolves to the current file online); the current schema accepts documents
naming any earlier version's URL; each superseded version is frozen as `tests/fixtures/schema/
stac-osd-<n>.json` and the compatibility test validates old documents against their frozen copy.
E19 moves to v2, E18 to v3 on its rebase. Revisit if a STAC client refuses a query string in an
extension identifier.


## OSD-D20 (23 Oct 2026, lane H1): an origin that answers the verifier 404, 410 or 5xx but a browser 2xx is `blocked`, not dead

Facts: NM OCD and PA DEP (ArcGIS Hub) and ohiodnr.gov answer 404 to the verifier's agent and 200 to a
browser agent, from the GitHub-hosted runner (verify comment on PR #30) and from the VPS
(`docs/program/evidence/e22/sources.md`); the dead-link report would open an origin-dead issue for a
publisher that is up. OSD-D9 already calls a refusal of automated requests `blocked`, which awards
no level and never opens an issue. Ruling: after the verifier's own probe and its one retry end in a
terminal 404, 410 or 5xx (never after a 403, 429 or challenge page, which are `blocked` already, and
never after 2xx), the verifier sends one more request of the same URL, paced like every other, with
a browser's user agent (`BROWSER_USER_AGENT`), and closes the response without reading it. A 2xx
after redirects makes the origin `blocked` with the detail "answers a browser, not the verifier
(HTTP <first> to osd-verifier, HTTP <second> to a browser agent)"; any other answer leaves it dead.
Headers cannot tell a 200 challenge page from content, so the detail claims no more than that a
browser was answered, and no level is awarded (OSD-D9). The browser agent is used for that one
question only: listings, licence pages, inventories and files are always fetched as the verifier,
under its own name and robots.txt. `origin.http_status` keeps the verifier's status; both statuses
live in the check detail, so verification/4 is unchanged. `osd verify` prints that detail beside
the level and `osd status` gives it as a blocked record's reason. Revisit if a publisher answers a
browser agent with content it refuses the verifier for a reason we should honour (a stated robots
policy for the origin page, a terms-of-use clause on automated access).
