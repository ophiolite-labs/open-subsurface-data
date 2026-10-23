# Program: Open Subsurface Data

Owner: Ophiolite Labs. Supervisor: one Claude session. Workers: at most two coding lanes and
one records lane at a time. Engineering rules: `../ENGINEERING.md`. Charters: `charters/E<nn>-*.md`.
Open questions for the owner: `DECISIONS.md`. Claims: `CLAIMS.md`. Commands: `HANDOFF.md`.

## Queue (23 Oct 2026)

| # | Epic | Class | Status | Depends on | Outcome a user can observe |
|---|---|---|---|---|---|
| 1 | E01 Twenty records from the open lists | Records | MERGED 23 Oct (PR #1, 21 records, 20 at L1) | scaffold | The map lists at least twenty datasets, each with licence and access stated |
| 2 | E02 Verifier to L2 | Kernel | MERGED 23 Oct (PR #3, 37c010c; 18 mutations; three records at L2, SEG wiki blocked) | E01 | Levels on the map are real: dead links show L0, checksummed sets show L2, with a date |
| 3 | E03 Outlines from the data | Kernel | MERGED 23 Oct (PR #7, 7ddecf0; record/2 inputs, outline/2; Sodir, NLOG, Poseidon at L3; F3 and Teapot behind logins) | E02 | Solid outlines for Norway, the Netherlands and the five 3D surveys; dashed placeholders gone |
| 4 | E05 Map that scales | Surface | MERGED 23 Oct (PR #2, 6c232cf; shareable hash, 10k clustered wells, how.html, Playwright site test in CI) | scaffold | Shareable link to a filtered view; thousands of wells without lag; a how-it-works page |
| 5 | E04 STAC catalogue | Kernel | MERGED 23 Oct (PR #8, aced173; 68 Collections validate offline, Items need periods; QGIS screenshot is owner action 102) | E03 | QGIS's STAC browser opens the catalogue and lists items with licence and level |
| 6 | E06 Retrieval by manifest | Kernel | DONE (slice 1 PR #9, slice 2 PR #12, 23 Oct; main cc7c470) | E04 | Select on the map, download a manifest, `osd get` fetches with checksums |
| 7 | E08 Curation that runs itself | Surface | MERGED 23 Oct (PR #5, e408adb; status page, dead-link issues, osd new, CODEOWNERS, labels). DONE when two outside PRs have merged (owner action 101) | E02 | An outside contributor's record merges the same day; dead links become issues |
| 8 | E11 Hosting and domain | Ops | DONE 23 Oct (https apex 200, http 301 to https, domain verified for the organisation; www certificate propagating) | none | The site at opensubsurfacedata.org with real levels |
| 9 | E07 Mirror store and custody | Kernel | slice 1 MERGED (PR #13, 23 Oct; main 58e895f; manifest/2, custody/1, verification/3, local transport; Norne eligible); slice 2 QUEUED after owner action 103 | E06, OSD-D6 | Small, allowed datasets download from the catalogue at full speed with a custody record |
| 10 | E09 Ophiolite reads the catalogue | Kernel, cross-repo | OSD slice 1 MERGED (PR #14, 23 Oct; main c370a87: manifest/3 catalog snapshot, fidelity/1, L4 rule); static manifest/3 fixtures PR #16 (pin 82ae5563d); PARTIAL until Ophiolite E127 lands (after E121 there; rights part after E35) | E06, Ophiolite E85 | An Ophiolite project pulls a manifest in as a source with rights-basis filled |
| 11 | E10 Seismic slices | Kernel | DEFERRED | E07 | A slice of a mirrored cube in a notebook without downloading the cube |
| 13 | E13 Twenty records from the national registers | Records | MERGED 23 Oct (PR #4, 6429445; 42 records, 10 countries with a government publisher, 0 new TerraNubis) | E01 | Forty datasets listed; a government source for at least eight countries |
| 14 | E14 Twenty records: research drilling, CO2 sites, state archives | Records | MERGED 23 Oct (PR #6, 61f9527; 68 records, 26 new, six new countries, all 26 at L1) | E13 | Sixty datasets listed, wider kinds and regions |
| 15 | E15 Tiles for the registers | Surface | MERGED (PR #10, 23 Oct; main 2904db0) | E03 | The map on a phone connection loads tiles for the viewport, not 7 MB of outlines |
| 16 | E16 Periods from the publishers | Records | MERGED (PR #11, 23 Oct; main fa13d75; 53 of 68 records with a period, 18,432 Items; OSD-D18 gate sample) | E04 | STAC clients list Items with publisher-stated periods, not only Collections |
| 17 | E17 Records, fourth twenty (Africa, Middle East, Asia, Canada, open seismic and model sets) | Records | MERGED (PR #15, 23 Oct; main 98eb254; 92 records, 9 new countries) | E16 | The map lists at least 85 datasets on six continents |
| 18 | E18 Items carry their own dates | Kernel | MERGED (PR #19, 23 Oct, main 8581b50; charter reworked after its Codex round) | E03, E04, E16 | Time filters in a STAC client return the wellbores and surveys of that window, not a whole register |
| 19 | E19 Vocabulary from the records lanes (potential fields, purchase, licence terms) | Kernel (small) | MERGED (PR #18, 23 Oct; main ae7a812; record/3, manifest/4, stac-osd v2) | E17 | Records can say gravity/magnetics, sold data and time-limited terms as the publisher states them |
| 20 | E20 Records: the retry and the publishers' sentences | Records | MERGED (PR #21, 23 Oct; main a1f8832; 96 records, NRCan potential-fields, PASA/DGH publisher sentences; six hosts still refuse) | E17, E19 | Unreached publishers are listed when they answer; purchase records carry the publisher's own licence sentence |
| 21 | E21 The map says when | Surface | MERGED (PR #22, 23 Oct; main 3d5841c; period filter `t=`/`dated=1`, When row, journey tests) | E05, E16 | A person filters the map by acquisition years and reads when a dataset was acquired, in the publisher's words |
| 22 | E22 Records, fifth twenty (US states, Iberia and the Alps, Latin America, Africa, geothermal and CO2 sites) | Records | MERGED (PR #30, 23 Oct; main 595a30f; 121 records, ten new countries, seven US states) | E20 | The map lists 116 datasets with the open US state regulators and five more countries |
| 23 | E23 More datasets checksummed | Kernel | MERGED (PR #31, 23 Oct; main 3ece7a2; verification/4, ten listing readers, publisher checksums, a reason per record below L2) | E02, E07 | Every listed dataset has its sample attempted each run; passes show L2, the rest say which check stopped them |
| 24 | E24 Records: files the verifier can reach, and the sixth twenty | Records | MERGED (PR #32, 23 Oct; main 4dcdc56; 140 records; 24 of 49 lane records L2 on the branch run) |
| 25 | E25 Records: the seventh twenty, and the bare files | Records | MERGED (PR #35, 23 Oct; main 8843f3e; 160 records, five new countries; branch run 35 L2 + Poseidon L3) | E24, H1 | At least 156 datasets listed; bare-file records reach L2 or say why |
| 26 | E26 Vocabulary: the kinds the records lanes asked for | Kernel (small) | MERGED (PR #34, 23 Oct; main dcbc1d3; record/4; ten records retagged) | E19, E24 | A record can say velocity model, geological model, airborne EM, radiometrics, stress; ten records lose their want sentence |
| 27 | E27 The map says why | Surface | MERGED (PR #36, 23 Oct; main 16a2f5a; reasons on the map and the status page; frame budget scaled by runner speed) | E23, H1, E08 | A person reads on the map and the status page why a dataset is at its level, in the verifier's words, with the date |
| 28 | E28 Periods and extents for the newer records | Records | MERGED (PR #39, 23 Oct; main 520b4c1; periods 90 → 111 of 160, bbox 136 → 138) | E16, E25 | The time filter and STAC reach the datasets added since E16; first zoom right for every located dataset |
| 29 | E29 Outlines from the registers' map services | Kernel | MERGED (PR #43, 23 Oct; main d0e3241; record/5 arcgis inputs for nine registers; outlines committed for SGUDDS, NZP&M x2, WA DEMIRS (6,970 features), WA at L3; the other five prepared for E32; all-record branch run 42.5 min) | E03, E18, E23, E25, E26 | Registers with an ArcGIS service show their wells and surveys as real points and outlines; L3; one Item per feature |
| 30 | E30 Listings for the datasets people can download | Records | MERGED (PR #40, 23 Oct; main 641f750; 11 listings, 10 of them L2 on the branch run; 80 records with a manifest_url) | E23, E24, E25 | More anonymous-access datasets at L2; the rest say why in the verifier's words |
| 31 | E31 Records: the eighth twenty (offshore regulators, Canadian provinces, CCS sites, the rest of Europe) | Records | MERGED (PR #41, 23 Oct; main 08d3985; 176 records, 16 new, 14 with listings; four held back under the unknown cap, Tomakomai held back by its terms) | E25, E30 | At least 176 datasets, BOEM and C-NLOPB among them, four more countries |
| 32 | E32 Registers with a hundred thousand wells | Kernel | CHARTERED (23 Oct; Codex REWORK, reworked: two-minute gate, child Catalog shards, encoder fix preserving E15's tile contract, 21 dispositions); IN LANE (osd-e32, 23 Oct) | E29, E18, E15 | Virginia, BCER, SGC, Utah and North Dakota wells on the map at L3 with pageable Items; the gate stays under three minutes |
| 33 | E33 Records: the ninth twenty (the four held back, the Americas and Africa that remain, geothermal and CO2 research sites) | Records | MERGED (PR #44, 23 Oct; main 2752137; 196 records: four restored, 16 new, six new countries, 106 with a manifest_url) | E31 | At least 196 datasets, five more countries, geothermal and CO2 research sites on the map |
| 34 | E34 Periods and extents for the eighth and ninth twenty | Records | MERGED (PR #47, 23 Oct; main 2a4e75a; periods 10 of 22 (below the bound of 11, finding), bbox 11 of 22 given, 11 explained; 19 records touched) | E28, E31, E33 | The 36 newest datasets reach the time filter and the first zoom |
| H2 | H2 Verify in shards | Kernel (hardening) | CHARTERED (23 Oct; Codex REWORK, reworked: origin-host shard key, one snapshot per shard, fresh-only issue report, 18 dispositions); IN LANE (osd-h2, 23 Oct) | E29, H1 | An all-record verify on main under 25 minutes (56 after E30), no overwrite between dispatches |
| H1 | H1 Origins that recover, and origins that hide from robots | Kernel (hardening) | MERGED (PR #33, 23 Oct; main 5cbe7af; OSD-D20; issues close on recovery; single-file listings) | E08, E23 | Origin-dead issues close themselves; publishers that hide from the verifier are called blocked, not dead |
| 12 | E12 Catalogue into a workspace | Kernel, cross-repo | DEFERRED | E09, Ophiolite E36 or E79 | A person keeps a derived asset in a private workspace |

Scaffold delivered 23 Oct: schemas, nine records, placeholder outlines, verifier at L1, build,
map, CI (`check`, `verify`, `pages`). Verifier result on the day: five origins at L1, four at L0
(three of them the SEG wiki blocking this host with HTTP 403, one NOPIMS 403; see OSD-D9).
Published 23 Oct: repository public, `check` and `pages` green on the first push, a dispatched
`verify` run on GitHub-hosted runners gave the same five L1 and four 403s and republished the map
with real levels through the `verification-results` branch. `main` requires `check`.
DNS entered and the domain verified for ophiolite-labs by the owner 23 Oct; HTTPS enforced (certificate issued after re-setting the custom domain).
E01 follow-ups for E02: ten of twelve new records come from one aggregator (TerraNubis); origins were
opened by an agent, not a person; Teapot Dome's NETL page redirects to a login.

## The loop

1. The supervisor takes the first QUEUED epic whose dependencies are MERGED and whose paths are
   free on `CLAIMS.md`. Surfaces are disjoint: `records/`, `site/`, `src/osd/`, `.github/`.
2. Kernel: the worker writes a strategy of at most two pages at lane open (acceptance line → test
   name), one Codex round on the charter if not yet reviewed, dispositions recorded in the charter.
   Surface and records: no strategy, the charter's acceptance list is the brief.
3. The worker claims paths, branches `e<nn>-<slug>`, commits in outcome-named slices.
4. The worker pushes unasked when the diff is inside the claim; asks for `schema/` version bumps
   and `.github/` edits.
5. Pull request: outcome sentence, proof (check green, screenshot or verify comment). The
   required status is `check` only.
6. Supervisor merges on green with squash. Main publishes the site. Nobody waits for the
   repeat run on main.
7. Red main: revert within the hour, then a fix lane. No hardening lanes, no item list.
8. Defects under 50 lines ride on the next lane that owns the path. Larger ones get a charter.
9. During any wait the worker starts the next slice on a stacked branch; it is merged after.
10. After a merge the supervisor updates this table, moves the claim rows to MERGED, and
    `/compact`s.

## Rules

- R1 WIP: two coding lanes plus one records lane. A third coding lane waits.
- R2 Gate: `make check` only. Nothing network-bound is ever required.
- R3 Records say what the publisher says; tools say what they established. Never cross.
- R4 Every slice names what a user can do after it merges.
- R5 Surface gets a screenshot, kernel gets tests and one mutation per guard, records get the
  verify comment and a licence read.
- R6 No timers, no nightly, no self-set dates. Act when the precondition holds.
- R7 Nothing a job can regenerate is committed (`build/`, `site/data/`).
