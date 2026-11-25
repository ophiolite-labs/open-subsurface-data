## E51 Licences per country: the United Kingdom, Norway and the United States as a fourth outline kind, as fresh as the regulator — CHARTERED 25 Nov 2026 (Kernel + Records; strategy at lane open; one Codex round)

Authority: family `MAP-AS-A-SHOP-family.md` (journey J13; R-S3, R-S5); OSD-D29; board Open 02
(`b6.py`); `block-layers.md` beside the prototype (service addresses, counts and what was and was
not verified on 25 Nov 2026). E29, E35, E38 (ArcGIS and WFS readers), H2 (verify in shards), E46.

**The owner's ruling.** No free world layer exists, so licences are read per country from the
regulator, on a schedule. Order: United Kingdom, Norway, United States; then Canada and Australia
once their terms are read. Draw licences (what a company holds), not grid blocks; draw only those
that hold a dataset; name the block in the dataset row.

**Outcome.** On the shop, Licences is a fourth choice of the outline switch in the countries that
are read. A licence is drawn when a real well or survey outline of a dataset lies in it; a click
filters the list to those datasets; an opened dataset row says which block or licence its wells
are in. The date the regulator was last read is shown in the attribution line. A regulator that
does not answer leaves the last good copy in place and says so.

**Context today.** `src/osd/verifier/` reads ArcGIS FeatureServer layers whole (E35) and WFS 2.0.0
GeoJSON (E38), with robots (H3) and shards (H2). `verify.yml` runs on dispatch only; PROGRAM rule
R6 says no timers. E46 defines area/1 and the count for any `kind`. From `block-layers.md`:

| Country | Service (25 Nov) | Layer to draw | Count | Terms as far as read |
|---|---|---|---|---|
| United Kingdom | NSTA ArcGIS Online, `UKCS offshore petroleum licence blocks WGS84` FeatureServer/0 (+ England onshore) | licences via `LICREF`; block name `BLOCKREF` | 698 + 193 block rows | "NSTA Open User Licence"; acknowledgement required; the licence PDF returned 404: **not read in full** |
| Norway | Sodir FactMaps `FactMapsWGS84` FeatureServer 616 (production licences), 802 (blocks) | 616; block name from 802 `blcName` | 1,813 / 1,827 | NLOD by Sodir's open-data page (page returned 403 to the reader): **credit wording not verified** |
| United States | BOEM `MMC_Layers` MapServer 15 (leases), 11 (block grid, 278,438); BLM MLRS leases FeatureServer/0 (466,838 cases) | BOEM leases first; BLM is its own slice | 1,875 | BOEM: no licence text on the service; BLM: "should be cited as the data source" |

**The design the charter fixes.**

1. *Terms first (slice 0, records class, no code).* For NSTA, Sodir, BOEM and BLM: open the
   licence text itself (not a search summary), quote the sentences that allow re-use and
   redistribution of derived tiles and the required credit line, with the address and the date, in
   `areas/SOURCES.md` under "Licences" and in `docs/program/evidence/e51/terms.md`. A human-check
   line per source as for records. Where the text cannot be opened from the controller, the lane
   says how it tried and adds an owner-actions item to open it in a browser; that country waits,
   the others proceed (R-S5).
2. *A regulator is a source with a reader, not a file by hand.* `areas/licence/<cc>.yaml` names
   the service, the layer, the id and name attributes, the block-name attribute or the block layer
   to join, the filter for "current", the licence and credit; `osd areas read <cc>` fetches it
   with the verifier's readers and writes `areas/licence/<cc>.geojson` (area/1, `kind: licence`,
   `source.retrieved` = the read time, one feature per licence: the block rows of one `LICREF`
   dissolved to a multipolygon, `blocks` = the sorted block names). Network: AGENTS.md's network
   line gains "`osd areas read`, which reads the named regulators' public licence layers, run by
   the `areas` workflow or a maintainer". Tests inject the fetcher.
3. *The schedule (an exception to R6, by owner decision OSD-D29).* A workflow `areas.yml`: weekly
   cron and dispatch; runs `osd areas read` per country; opens (or updates) one pull request
   "Licences read <date>" when a file changed, with the count before and after per country; `check`
   gates it like any change; the supervisor merges. It never pushes to main. A failed or empty
   read, or a count that falls by more than a fifth, changes nothing and comments on the standing
   issue for that country: the last good copy stays, with its date.
4. *The count and the row.* E46's rule, unchanged, with `kind: licence`: only licences holding a
   position are written to `areas.json` and the tiles. `records[].areas.licence` lists them; the
   build also writes, per record with at most 25 such licences, `blocks`: the block names of the
   licences its positions are in (the dataset row shows "Blocks 15/9, 15/12 …"; a national
   register with thousands shows the count). `areas.json` carries `retrieved` per country.
5. *The surface, small, at the end of each country slice.* E48's switch shows Licences when the
   kind exists; the attribution shows "Licences: NSTA, read 24 Nov 2026" from `areas.json`; the
   row shows the blocks. J13 is lit with the first country.
6. *Slices (order changed 25 Nov after slice 0 read the terms: OSD-D38, owner action 139).* 0 terms. 1 **Norway** with the contract; the United Kingdom is a later slice and only on the owner's answer. As first written: 0 terms (opens at once). 1 United Kingdom with the contract (`areas read`, the
   workflow, the count for licences). 2 Norway. 3 United States: BOEM leases; BLM only if its
   466,838 cases reduce to current leases holding a dataset inside the size budget, else a
   finding. Each country is one PR.

**Acceptance.**

1. Slice 0: `terms.md` holds, per source, the quoted sentences, the address, the date and the
   credit line, or the sentence "not opened: <how tried>" with the owner item number. No country's
   geometry is committed before its terms line exists (test: `osd validate` refuses a licence area
   file whose `source.licence` or `source.credit` is empty: E46 guard reused).
2. Slice 1: `osd areas read gb` against a recorded fixture response writes the golden
   `gb.geojson`: one feature per licence, block rows dissolved, `blocks` sorted; pagination past
   `maxRecordCount` is exercised by the fixture.
3. A fixture read with zero features, an HTTP error, or a count 30 % lower leaves the committed
   file byte-identical and exits with the finding (three tests; mutation: the guard removed
   replaces the file).
4. Fixture build: a well in licence P1 and none in P2 gives P1 in `areas.json` and not P2;
   the record's `blocks` are P1's; a record with 26 licences gets a count, not a list.
5. Real catalogue, per country PR: the number of licences read, the number holding a dataset, the
   datasets that gained `blocks`, and the size added to git and to the tiles.
6. J13: on the fixture build the switch shows Licences, a click on P1 filters the list, the row
   names its block, the attribution names the regulator and the read date. Without licence data
   the fourth part of the switch is absent.
7. `areas.yml` on a dispatched run in the lane's branch (dry: no PR opened) prints the diff
   summary; the workflow file is announced in the PR title.
8. `make check` remains offline and under 120 s; the licence files add under 10 MB to git for the
   three countries together (else the stop rule).

**Out of scope.** Grid blocks as drawn areas; unlicensed or relinquished acreage; Canada,
Australia, the Netherlands, Brazil, New Zealand, Denmark, Germany (terms unread: a follow-on
charter per the owner's order); EMODnet's European compilation (yearly, behind the regulators: not
used where a regulator is read).

**Stop rules.** A source whose terms forbid redistribution of derived data, or stay unread: that
country is not drawn; write the finding and go on with the next. If dissolved licences for one
country exceed 5 MB after simplification, stop with the sizes.

**Ownership and dependencies.** Slice 0: records lane; paths `docs/program/evidence/e51/**` and
the "Licences" section of `areas/SOURCES.md` (handed to the supervisor as a file in the evidence
folder while E46 holds `areas/**`). Slices 1–3: coding lane (kernel) after E46 slice 1 and E48
have merged; paths `areas/licence/**`, `src/osd/areas.py` (the reader and the `blocks` rule),
`src/osd/cli.py` (`areas read`), `src/osd/build.py` (licence layer), `.github/workflows/areas.yml`
(new, announced), `AGENTS.md`, `CLAUDE.md` (network sentence), `tests/test_areas_read.py`,
`tests/fixtures/areas/licence/**`, `site/shop.js`, `tests/site/shop.test.mjs` (the row's blocks
line, the read date, J13).

**Dispositions of the Codex round (slice 1 lane, 25 Nov 2026; strategy `E51-licences-per-country-STRATEGY.md`).**

- F1 accepted as context: the readers are `layers.export_layer` (ArcGIS, reused whole) and `export_wfs`; the 50,000 cap stays.
- F2 accepted: `verify.yml` also runs on pull requests touching records or outlines; nothing here depends on it.
- F3 noted: OSD-D29 is the exception to R6; `areas.yml` is the only timer.
- F4 resolved by time: E46 slice 0 and 1 merged (area/1, record/6, the count, `areas/SOURCES.md`); area/1 already holds `kind: licence`, `country` and `blocks`.
- F5 accepted: the services, layers and counts are now in the strategy from the lane's own read (25 Nov), and in `areas/licence/no.yaml`.
- F6 accepted, no version bump needed: area/1 carries `blocks` and `country` since E46; `retrieved` per country is the source of each file in `areas.json`. `records[].blocks` is a build output field, documented in `build.py` (records.json has no schema).
- F7 accepted: `areas/licence/<cc>.yaml` has a fixed shape, checked by `read_config` (keys in the strategy); ArcGIS only in this slice; WGS84 required.
- F8 accepted, design changed: the join is named per country (licence key, block key, block-name layer); Norway joins 616 `prlName` to 615 `prlName`, 615 `blcNpdidBlock` to 802 `blcNpdidBlock`, name from 802 `blcName`. A licence without blocks, a block row of no current licence and a block id missing from 802 refuse the read. One `retrieved` per file; a country with two services (the United Kingdom) gets one file per service.
- F9 accepted: `records[].blocks` is a sorted list of block names, present when the record sits in 1 to 25 licences; otherwise absent, and the count is the length of `records[].areas.licence`.
- F10 accepted, design changed: `current` is `{field, op, value}` per country (Norway `prlStatus = ACTIVE`, 1,277 of 1,813 rows are not); the fixture carries an INACTIVE licence; a layer without the field refuses the read.
- F11 accepted, design changed: one rule, "more than a fifth of the committed licences missing from the read" refuses; tested at exactly a fifth (read) and above (refused), and with the same count and other ids (refused).
- F12 accepted: acceptance 5 requires at least one Norwegian licence holding a dataset (test on the real build); the numbers are in the PR.
- F13 accepted: the PR and issue texts are built by `osd.areas.pr_text`/`issue_text` and unit-tested; the workflow's dry run on its own pull request proves the read and the summary; cron and the GitHub calls are stated, not run in `check`.
- F14 accepted in part: absent or repeated ids, failed joins, non-WGS84 layers, invalid geometry after simplification, a filter field absent: each a refusal with a test and a mutation. "Dissolve failure" does not arise in Norway (one row per licence; rows of one id are merged as E46 merges parts). "Stale retrieved" is not a guard: an unchanged read keeps the file and its date by design (inbox note 2).
- F15 accepted: `osd validate` refuses a licence file whose `source.url` or `source.credit` does not appear in `areas/SOURCES.md`, where the terms are quoted.
- F16 accepted: this lane owns `areas/SOURCES.md`'s Licences section; Norway only until another country is drawn.
- F17 accepted: the AGENTS.md network sentence lands after E49 slice 4 merges (drafted in the PR).
- F18 accepted: permissions and GitHub calls stated in the strategy and asserted by a test on `areas.yml`; `make check` never invokes it (test).
- F19 accepted for slice 3: BLM needs a server-side filter before paging; Norway's 1,813 rows are read whole.
- F20 accepted: `osd build` and `osd validate` read only committed files; a test runs them with the network patched to fail.
