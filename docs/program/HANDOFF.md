# Handoff

Repository: https://github.com/ophiolite-labs/open-subsurface-data (public, OSD-D1). Site: https://opensubsurfacedata.org (OSD-D4).

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
E03 merged (PR #7, 7ddecf0): real outlines, record/2 (`inputs`), outline/2 (`feature_id`, collection `inputs`); `osd verify --outline-inputs` in the workflow (a dispatched run now takes about 10 minutes). E04 merged (PR #8, aced173): STAC tree under site/data/stac/, offline validation with bundled schemas in `make check`, `period` optional on record/2, GeoJSON `id` = `feature_id`. E15 rebases over its two build.py edits. E16 (periods, records slot) opened. STAC address for clients: https://opensubsurfacedata.org/data/stac/catalog.json. E15 was the follow-up noted here (Surface, small): a build step that writes `site/data/outlines.pmtiles` from `outlines.geojson` (the E05 page already prefers it when present), so register outlines of several MB stop loading whole. E14 merged (PR #6): 68 records. E14 findings for the planner: a `microseismic` or `potential-fields` kind would admit Otway Stage 3 fibre-optic data and NRCan GDR; blocked or unreachable on 23 Oct: Mexico CNH, WAPIMS, PGI CBDG hosts, Colorado ECMC (geo-block), AOGCC, BRGM, ICDP site pages, publications.iodp.org (Zenodo deposits used instead); North Dakota DMR data is paid; Wyoming states no terms. Held back for the publisher cap: COSC-1 operational data, Northern Lights Eos thermo-mechanical set, further Ketzin sets. The open-list candidate pool is thinning: the next records lane should be chartered against a named source (one register's named datasets, or the held-back items), not another sweep.
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
