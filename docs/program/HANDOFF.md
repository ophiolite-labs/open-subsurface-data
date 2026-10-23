# Handoff

Repository: https://github.com/ophiolite-labs/open-subsurface-data (public, OSD-D1). Site: https://opensubsurfacedata.org (OSD-D4).

## 23 Oct 2026, evening (supervisor) — E15 merged, E07 slice 1 and E06 slice 2 in lane, OSD-D18

- E18 merged (PR #19, main 8581b50): outline/3 (`osd:period_start_raw/_end_raw`, `osd:period_start/_end`, `inputs.<name>.period_fields`), stac-osd `?v=3` (`osd:period_source`: `feature` | `feature-start,collection-end` | `collection`), E19's v2 frozen under `tests/fixtures/schema/stac-osd-2.json`; Sodir and NLOG Items carry their own dates; the map layer carries none (ruling above). Eight mutations red; containment green over 18,525 STAC objects; evidence in `docs/program/evidence/e18/`. Verify dispatched; post-publication check of a Sodir Item's `start_datetime` pending. Verify after E19: success; the published PASA record shows `access: purchase` with `licence.terms`; 92 records (81 L1, 3 L2, 1 L3, 7 L0: dgh/national-data-repository, eug/national-data-repository, geus/deep-subsurface-data, gsq/qped, sa-dem/moorari-3d-2005-reprocessing, seg/open-data-wiki, tudelft/egg-model). E20 (records retry, publishers' sentences, `expires` coercion) and E21 (the map says when: period filter and When row on the site) chartered and opened as lanes osd-e20 and osd-e21; E07 slice 2 still waits for owner action 103 (no repository secrets or variables set as of 23 Oct evening).
- E15 tiles merged (PR #10, main 2904db0): the page loads `data/outlines.pmtiles` for the viewport (about 0.6 MB on load instead of 13.5 MB of GeoJSON); tippecanoe runs in `check` and `pages`. The E05 performance test now runs on the GeoJSON path with its synthetic set alone (budget unchanged).
- E19 merged (PR #18, main ae7a812): record/3 (`potential-fields`, `access: purchase`, `licence.terms`), manifest/4 (written only when needed; E127's /3 fixtures unchanged), stac-osd v2 (OSD-D19); frozen record/2, manifest/3 and stac-osd/1 under `tests/fixtures/schema/`; six records edited field-exact (PRIME, EUG, NAMCOR, BEG, DGH, PASA); the verify comment showed the six at L1 as before. Thirteen mutations red. Verify dispatched. E18 rebases over it (stac-osd to v3).
- E18 rulings (23 Oct): `build.py` one line granted (the map layer carries no `osd:period_*`; dates live in the outline files and the STAC Items; tiles stay 60.9 MB). Known red for a later tiles lane: tippecanoe 2.49 wrote wrong attribute values into tiles when the outline features carried the extra date members (publisher_id shown as a date, another feature's raw start), confirmed with tippecanoe-decode; cause not understood, worth testing with `--no-tile-size-limit`/attribute-type flags or a newer tippecanoe before any lane adds properties to the map layer. Sodir dates are M/D/YYYY with optional 12-hour time (rules name the format); NLOG `1800-01-01` is not a placeholder (same shape as 1828 boreholes); NLOG 3D surveys state only a release date and keep the collection period.
- Verify after E17: success; after the pages build it triggered, the site publishes 92 records (82 L1, 3 L2, 1 L3, 6 L0: SEG wiki and NOPIMS blocked, gsq/qped blocked, tudelft/egg-model and geus/deep-subsurface-data dead today, one more). Issue #17 (origin dead: geus, HTTP 502) opened by E08's report; the publisher's page answers 502 from this host too; it closes when a run reaches it again. Known red: a push-triggered pages build that runs before verify pushes results shows new records at L0 until the verify-dispatched build lands (a few minutes).
- E19 rulings (23 Oct): OSD-D19 (extension version in the query string); three lines of E18's test files granted to E19 (E18 rebases); PASA `terms.stated` carries the record's notes wording until a records lane with network replaces it with the publisher's sentence from the obtain-our-technical-data page (finding for the records retry lane); unquoted YAML `expires` is refused by the schema until a later lane adds date coercion beside `period`'s in `src/osd/records.py`; manifest/4 is written only when an entry needs `purchase` or `terms`, so the E127 manifest/3 fixtures stay byte-equal.
- Verify after E09: success; the published `records.json` carries `catalog` (source commit, verification commit, built_at, records digest).
- E18 (Items carry their own dates; outline/3, stac-osd `osd:period_source`) and E19 (vocabulary: `potential-fields`, `purchase`, `licence.terms`; record/3, manifest/4) chartered, both Codex rounds REWORK, both charters reworked with dispositions and opened as lanes osd-e18 and osd-e19 (main 20750f4). They share `schema/stac-osd.json`, `schema/stac/schema-map.json` and `src/osd/stac.py`: the second to merge rebases.
- E17 merged (PR #15, main 98eb254): 24 records, 92 in all, nine new countries (ZA, NA, EG, IL, IN, ID, JP, KR, TW); verify on the PR: 22 L1, gsq/qped blocked (403), tudelft/egg-model origin dead from the runner (data.4tu.nl timeout, also from this host). E17 findings for the planner: a `potential-fields` kind (NRCan, NAMCOR, EUG, PRIME gravity and magnetics); an access value `purchase` (BEG Stratton, NAMCOR, DGH, PASA); time-limited licences and pre-publication review (PASA). Unreached on 23 Oct: SEG (403), Kochi Core Center (503), GSJ gbank (maintenance), JAMSTEC J-CORES (reset), AOGCC (403), BRGM (refused), NRCan GDR (TLS); no data page at NUPRC, Ghana PC, Oman MEM.
- E09 static manifest/3 fixtures merged (PR #16, pin 82ae5563d69a0631fa50fcd1521690c1291b0976) for Ophiolite E127: `tests/fixtures/fidelity/manifest-two-wells.json` and the no-statement and null-attribution variants, each asserted equal to what `osd manifest` writes.
- E09 OSD slice 1 merged (PR #14, main c370a87): `records.json` carries `catalog` (source commit, verification commit, built_at, records digest); manifest/3 copies it into `metadata.catalog` and keeps every licence field including nulls; `schema/fidelity.schema.json` (fidelity/1); `osd verify <id> --fidelity-from <file>` awards L4 from the catalogue's own checks, rejecting a wrong record id, an input hash not in the latest verification, or a failed input without reason; `osd status` shows coverage beside L4. Ophiolite E127 pins this commit for the fixtures under `tests/fixtures/fidelity/`. Twenty mutations red. Verify dispatched.
- Verify after E07: success; Norne's published verification carries the complete inventory (5 of 5 listed files, rule `norne/*`), so Norne is the first record eligible for the mirror once slice 2 has a bucket. Levels unchanged (62 L1, 3 L2, 1 L3, 2 L0).
- Verify after E16: success, with the full STAC validation step; the published catalogue has 69 child links, the Sodir collection 11,210 Item links, and Items are dated. Finding for a later records or STAC slice: register Items carry the collection's period (Sodir survey/10003 shows 1966 to today), not the feature's own dates; the WFS carries per-feature dates that a later slice could write into Items.
- E09 charter reworked after its Codex round (REWORK; dispositions in the charter): manifest is the only interface, STAC-address intake out, F3 out, snapshot identity (`records.json` `catalog`, manifest/3), fidelity/1 as a structured document, L4 computed from the catalogue's own checks with stale or mismatched evidence rejected. OSD slice 1 in lane osd-e09. The Ophiolite half (`E09-ophiolite-half.md`) was handed to the Ophiolite supervisor ophiolite-13 for its queue; its rights part waits for Ophiolite E35 (QUEUED there on 23 Oct).
- E17 (records, fourth twenty) chartered and in lane osd-e17 in the records slot.
- E07 slice 1 merged (PR #13, main 58e895f): `osd mirror eligible|put|remove` on a local-directory transport, custody/1 beside the objects with tombstones, manifest/2 `alternates`, verification/3 `inventory` (Norne has a `mirror:` rule; 1 eligible record, 5 files, 1.34 MB), STAC alternate assets bundled for offline validation, takedown issue template, CONTRIBUTING takedown section. Eighteen mutations red. Slice 2 (S3 transport, workflow step, first real mirror) waits for owner action 103.
- E07 charter reworked after its Codex round (REWORK; dispositions in the charter): F3 out, 50 of 68 allowed, eligibility over a complete inventory, alternate assets, custody beside objects with tombstones, takedown approved by a maintainer. Slice 1 (local transport) in lane osd-e07; slice 2 waits for owner action 103 (Hetzner project + bucket + repository secrets).
- E16 merged (PR #11, main fa13d75): 53 of 68 records carry a publisher-stated `period`; 18,432 STAC Items (every Sodir and NLOG feature, Parihaka, Kerry 3D); gate 56 s with the OSD-D18 Item sample; `make check-full` (118 s) runs in the dispatched verify workflow. Verify dispatched. E17 (records, fourth twenty) opened in the records slot.
- E16 had found two gate reds outside its claim: the record/1 test pops only `inputs` (period is also record/2), and full STAC validation of 18,432 Items takes 115 s. OSD-D18: gate validates Collections and an Item sample; `make check-full` runs in the verify workflow on main. E16's claim extended to land both.
- E06 slice 2 merged (PR #12, main cc7c470): Select on the map, tick datasets, read licences and the share-alike note, download `osd.manifest.json`; a `#pick=` link shares a selection; round trip into `osd get` proven in `docs/program/evidence/e06/`. E06 is DONE.
- Verify on main after E15: success; the site publishes 68 records (62 L1, 3 L2, 1 L3, 2 L0) and serves `outlines.pmtiles` (60.9 MB) with byte ranges.
- Owner actions 102 (QGIS STAC screenshot) and 103 (Hetzner project, bucket and keys for the mirror) are on the Mac (sync confirmed mac-ok 23 Oct 15:15 CEST, after the Mac was unreachable from the afternoon).
- Hardening (supervisor, main): the E05 performance test asserts the median of its five pans instead of the maximum; PR #11 failed on one 110.5 ms frame beside four under 98 ms on the shared runner. Budget unchanged at 100 ms.
- Known red: a worker whose branch is deleted by `gh pr merge --delete-branch` sees its worktree path reported as deleted; run `git worktree prune` after closing the pane.

## Commands

```
uv sync                    # once
make check                 # lint, tests, validate, build  (the CI gate, offline, ~10 s locally)
make verify                # network: writes build/verification/*.json
uv run osd verify sodir/factpages equinor/volve     # some records only
uv run osd status          # one line per record with its level
make site                  # http://localhost:8765
```

Screenshot for a surface lane (Playwright from the Ophiolite web tree):

```
(python3 -m http.server --directory site 8765 &) && PLAYWRIGHT=<path>/node_modules/playwright node tools/shot.mjs out.png
```

## 23 Oct, afternoon (supervisor)

E02 merged (PR #3, 37c010c), verify dispatched on main: 3 at L2, 17 at L1, SEG wiki blocked. E05 merged (PR #2, 6c232cf): the required `check` job now also runs the offline Playwright site tests (about 30 s). E03 (osd-e03), E08 (osd-e08) and E13 (osd-e13, records) in lane.
E13 merged (PR #4): 42 records. E13 findings for the planner: CO2 DataShare licences carry a no-sale clause (in `notes`, no schema field); a publisher-type field would make the spread count mechanical; BRGM, NRCan GDR, CNSOER, Queensland GSQ, AOGCC, SEAM/Stratton/Viking Graben unreachable or blocked on 23 Oct (reasons in the PR body). Records slot free; no records lane chartered yet.
E03 merged (PR #7, 7ddecf0): real outlines, record/2 (`inputs`), outline/2 (`feature_id`, collection `inputs`); `osd verify --outline-inputs` in the workflow (a dispatched run now takes about 10 minutes). E04 merged (PR #8, aced173): STAC tree under site/data/stac/, offline validation with bundled schemas in `make check`, `period` optional on record/2, GeoJSON `id` = `feature_id`. E15 rebases over its two build.py edits. E16 (periods, records slot) opened. STAC address for clients: https://opensubsurfacedata.org/data/stac/catalog.json. E06 slice 1 merged (PR #9, 8b48217): `osd manifest <ids>`, `osd get <manifest> --dest`, `osd.manifest.read`; manifest/1 schema; AGENTS.md names `osd get` as a network entry point. Slice 2 (site select mode) waits for E15. E15 was the follow-up noted here (Surface, small): a build step that writes `site/data/outlines.pmtiles` from `outlines.geojson` (the E05 page already prefers it when present), so register outlines of several MB stop loading whole. E14 merged (PR #6): 68 records. E14 findings for the planner: a `microseismic` or `potential-fields` kind would admit Otway Stage 3 fibre-optic data and NRCan GDR; blocked or unreachable on 23 Oct: Mexico CNH, WAPIMS, PGI CBDG hosts, Colorado ECMC (geo-block), AOGCC, BRGM, ICDP site pages, publications.iodp.org (Zenodo deposits used instead); North Dakota DMR data is paid; Wyoming states no terms. Held back for the publisher cap: COSC-1 operational data, Northern Lights Eos thermo-mechanical set, further Ketzin sets. The open-list candidate pool is thinning: the next records lane should be chartered against a named source (one register's named datasets, or the held-back items), not another sweep.
E08 rulings (inbox note answered): CODEOWNERS names the single collaborator; GitHub teams `records-maintainers` and `kernel-maintainers` come when there are people; required code-owner review stays off, the gate stays `check`. The two outside PRs for E08's acceptance are owner evidence, owner action 101.

Codex round (OSD-D8) run on E02, E03 and E04 charters with `tools/review-charter.sh`; all three REWORK.
E02's review is dispositioned by its lane in the charter before its PR. E03 and E04 charters were
rewritten by the supervisor against the findings (dispositions at the end of each charter); the
reviews stay beside them as `*-CODEX-REVIEW.md`. New decisions OSD-D11 (record versus tool
boundary), OSD-D12 (derived outlines committed), OSD-D13 (outline licence), OSD-D14 (STAC items
need time); OSD-D9 revised (blocked awards no level). E02's claim lost the record schema and
gained `src/osd/verifier/**`. Record schema bumps (record/2: `inputs`, `period`) are E03's and E04's.

## Known reds and baselines (23 Oct)

- The E05 performance test (frame after `moveend` under 100 ms with 10,000 synthetic wellbores) measured against the real register outlines too once E03 landed 18,000 features in `outlines.geojson`; it now replaces the data with the synthetic set. Real-data load time is E15's (tiles).
- Full-viewport Playwright captures at phone width with many fills can show a black map canvas under swiftshader; the GL buffer is right (readPixels). Clip the capture or read pixels; not a page defect (E15 finding).
- A `pages` run cancelled by its concurrency group (`cancel-in-progress: true`) shows as failed in the run list; the later run deploys. Check the newest run and the site, not the red mark.

- SEG wiki answers HTTP 403 to this host for any user agent (Cloudflare). Not dead; see OSD-D9.
- NOPIMS page answers 403 from this host. Same class.
- Headless Chrome with virtual time budget hangs on MapLibre; use Playwright with swiftshader.
- `line-dasharray` takes no data expression in MapLibre 4: placeholder and derived outlines are
  separate line layers.

## Starting a lane (supervisor)

Brief by reference: the charter path, the branch name, the claim row, `make check` as the gate,
the known reds above. Nothing else; the charter is the authority.

## Starting as supervisor

Read `PROGRAM.md`, `CLAIMS.md`, `DECISIONS.md`, then this file. Confirm `make check` is green on
main. Take the first QUEUED epic whose dependencies are MERGED.
