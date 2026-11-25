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
| OSD-D21 | Starter projects: which dataset proves the chain first | F3 (`terranubis/f3-demo-2020`): replicate dGB's F3 Demo through the chain and judge the result against dGB's own survey (family "Ready for your tools", E42) | DECIDED by the owner 28 Oct 2026, 06:45 CET |
| OSD-D22 | Deposited origins: may a maintainer deposit files a publisher hands only to registered persons, when the licence allows redistribution? | Yes, as a verification fact with who/when/licence text captured, never for `restricted` or `unknown`, under the OSD-D6 caps (E41). The person registers; the tool never does | DEFAULT 28 Oct (planner), owner may overturn |
| OSD-D23 | Paid starter projects | Free, no account, no key (R-T6). A paid tier (currency, support, a target nobody else builds) is reopened only on evidence of use: a design partner asking, or request issues (E43) naming a willingness to pay | DEFAULT 28 Oct (planner); the owner raised the idea and accepted "free first" |
| OSD-D24 | Which datasets follow F3 (E44) | Planner's candidates: NLOG wells for one Dutch area, one NLOG-released 3D survey, Drogon for ResInsight; Volve as a fourth | ANSWERED by the owner 31 Oct 2026: the five TerraNubis datasets the owner downloaded (F3 Demo 2023, OGA MNSH, OGA Rockall Trough, USGS Central Alaska 2023, Poseidon 3D), all deposited; every content kind must translate to Ophiolite data types (E44 ruling, R-44.1–R-44.4); the planner's candidates move to a later round |
| OSD-D26 | The site becomes one page, "the map as a shop" (search bar, a list that follows the map window, the map; Filters is one button; a round green plus per row, a tick when in the bag; a small icon for how the dataset is obtained; Ophiolite look: Merriweather, Roboto, night blue; base map in familiar colours; Flat and Globe; no legend on the map; no colour on the map for what is in the bag). Supersedes OSD-D3 for the new page | Family `charters/MAP-AS-A-SHOP-family.md`, E47, E48, E53 | DECIDED by the owner 25 Nov 2026 (Paper boards Shop 01–06) |
| OSD-D27 | Outlines: one exclusive switch Countries / Provinces / Basins, later Licences; an area is drawn only when a dataset sits in it; every drawn area is clickable and filters the list; Names on / off, one name per area. "Sits in it" is counted when the catalogue is built, from real well positions and survey outlines; a dataset without positions uses the middle of its box; a country-wide dataset counts for the country | E46 (the count), E48 (the switch) | DECIDED by the owner 25 Nov 2026 (board Open 01). Supervisor default within it (E46 inbox note 1): Natural Earth countries are land, so an offshore dataset whose positions lie in no country counts for its stated `region.country`; no sea-zone source is added |
| OSD-D28 | Sources for the outlines: countries and provinces Natural Earth (public domain); basins USGS "Geologic Provinces of the World" (use constraints none, credit U.S. Geological Survey) | `areas/SOURCES.md` with E46 slice 1 | DECIDED by the owner 25 Nov 2026 |
| OSD-D29 | Licences: no free world layer exists; read per country from the regulator on a schedule. Order United Kingdom, Norway, United States; then Canada and Australia once their terms are read. Draw licences, only those holding a dataset; name the block in the dataset row. The schedule is a stated exception to rule R6 (no timers): a weekly workflow that opens a pull request, never pushes to main | E51 | DECIDED by the owner 25 Nov 2026 (board Open 02); the weekly period and the pull-request form are the supervisor's DEFAULT |
| OSD-D30 | The bag has three ways out: download the files, get a Python file, open in Ophiolite. The "Open in Ophiolite" button is not shipped (absent, not disabled) until the whole path works; Ophiolite's supervisor sends the landing address shape | E47 (bag), E49 (Python file); the button waits outside this family | DECIDED by the owner 25 Nov 2026 (boards Shop 04, 05) |
| OSD-D31 | Speed: map usable within 2 s, 60 pictures a second while moving, no download for an area visited before in the same visit, no download of our files on a return visit; the practices of board Shop 06; order of work: keep the present host, measure a return visit in a real browser first, add a browser cache only if that shows downloads. Four measurements are owed (real laptop and phone, return visit in a browser, zooming, globe with all wells) | E50, numbers in its PR | DECIDED by the owner 25 Nov 2026 (board Shop 06) |
| OSD-D32 | Where `import osd` comes from for the Python file | Installed from this repository (`pip install "osd[readers] @ git+https://github.com/ophiolite-labs/open-subsurface-data"`); publishing the package to PyPI is the owner's (an account and a name) and is not needed for E49 | DEFAULT (supervisor, 25 Nov 2026) |
| OSD-D33 | How the redesign lands without breaking the live site | A second path, `/shop.html`, with no link from the live pages, until the journey test (`MAP-AS-A-SHOP-family.md`, J1–J15) passes whole; then E53 replaces the front page in one PR that deletes the old page | DEFAULT (supervisor, 25 Nov 2026; brief: "behind a flag or a second path") |
| OSD-D34 | Work in progress for this family | R1 (two coding lanes plus one records lane) is a floor, not a cap, for E46–E53: as many Opus lanes side by side as have disjoint claimed paths; the claims board keeps them apart; the controller's disk is checked before a lane is added | DECIDED by the owner 25 Nov 2026 ("open as many agents as you need … so that we don't wait for features too long") |
| OSD-D35 | How a record says it covers a country | record/6, optional `region.national: true`: the publisher presents the dataset as covering the country in `region.country`. A publisher fact, filled by E52 from the publisher's page; replaces the prototype's guess from the size of the box | DEFAULT (supervisor, 25 Nov 2026) |
| OSD-D36 | The board for the Python file showed `osd.get("nlog/nlog", area="F03")`. The catalogue has no contract that says which downloadable file belongs to which well, block or area (assets are per dataset), so narrowing by area cannot be done without guessing | E49 ships `osd.get(id)` and the readers; `area=` refuses with "this dataset cannot be narrowed by area yet" before any request. Narrowing by area needs its own charter first: a versioned per-file membership in the listings | DEFAULT (supervisor, 25 Nov 2026; E49 inbox note 1, Codex F8). Owner: say if narrowing by area should be chartered next |

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
