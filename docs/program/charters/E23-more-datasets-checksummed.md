## E23 More datasets checksummed — QUEUED · Kernel · one Codex round

Authority: E02 (verifier to L2) and its strategy; OSD-D9 (blocked awards no level), OSD-D11
(sampling policy is tool configuration, never a record field); the catalogue's thesis that a level
is earned by a check the catalogue ran itself.

**Outcome.** A person who filters the map to "level at least L2" sees every dataset whose publisher
lists its files in a machine-readable way, not three; and for each dataset still at L1 the
verification says in one sentence why its files were not checksummed.

**Context today (verified 23 Oct, main 3d5841c).** 96 records; 3 at L2 (Sodir FactPages, Norne,
NLOG), 1 at L3, the rest at L1 or L0. Ten records carry `origin.manifest_url` (Sodir, Norne,
NOPIMS Poseidon, NLOG, Argentina Energía ×3, CPC Taiwan, GSQ QPED, Alaska DGGS tax-credit wells,
ANH, BCER, GSMMA hydrogeological drilling, KIGAM Korea Strait); `src/osd/verifier/samples.yaml`
names a sample for four of them, so six skip with "no sample for this record". `parse_listing`
reads HTML directory listings and walks any JSON for URLs; it does not know CKAN `package_show`
(datos.gob.ar, data.gov.tw, datos.gov.co), Socrata (`/api/views/<id>/rows.csv` and the
`metadata` endpoint), ArcGIS Hub or Zenodo/figshare/Dataverse record APIs, so a `manifest_url`
pointing at one of those lists nothing usable or the wrong objects. The run budget is 2 GB per
run and the sample must hash one file fully to pass (E02 C6). Records lanes add `manifest_url`
to records; this lane edits no record (E22 holds `records/**`).

**The design the lane must map to.**
1. Listing readers, each a small function selected by the shape of the response, not by the
   host: CKAN (`package_show` → resources `url`, `size`, `hash` when present), Socrata (a
   `rows.csv` export is one entry; the views metadata gives `rowsUpdatedAt`), ArcGIS Hub/Feature
   Server (`/query?f=geojson` export is one entry; `editingInfo.lastEditDate` when present),
   Zenodo, figshare and Dataverse (files with `checksum`), GitHub releases (assets), plus the
   HTML and generic-JSON readers that exist. A publisher's stated checksum, when the listing
   carries one, is recorded beside ours and compared; a mismatch fails the check with both values.
2. `samples.yaml` gains an entry for every record with a `manifest_url` (ten today), with a
   comment saying what the sample is and roughly how large. A record whose listing names only
   one object samples that object.
3. The `files-checksummed` skip detail names the exact reason in one sentence a reader can act
   on: "no origin.manifest_url", "listing format not recognised (first bytes: …)", "robots.txt
   disallows the listing", "sample would exceed the run budget (… bytes)", "no sample for this
   record in verifier/samples.yaml". E02's stop rules stand (robots.txt is respected, never worked
   around; a cut sample says so).
4. Verification document unchanged in shape (verification/3): `inventory` and the new
   `publisher_checksum` field under each file entry are the only additions, optional, so stored
   results and the E127 fixtures validate as before. If a schema bump is unavoidable, it is
   verification/4 with the frozen /3 under `tests/fixtures/schema/`.
5. `osd status` shows, for each L1 record, the one-sentence reason from design 3 in a column, so
   the next records lane sees which publishers would reach L2 with a `manifest_url`.
6. Tests: one fixture listing per reader shape under `tests/fixtures/listings/`, offline;
   mutation tests for a stated-checksum mismatch and for each skip reason.

**Acceptance.**
- The PR's verify comment shows at least eight of the ten `manifest_url` records at L2, each with
  the coverage sentence; every other `manifest_url` record states a design-3 reason.
- A listing with a publisher checksum that disagrees with ours fails the check (mutation test).
- `make check` green; `make check-full` green on the branch (run once, reported in the PR).
- `uv run osd status` lists the reason column; the PR pastes it.
- No record file changed.

**Claim.** `src/osd/verify.py`, `src/osd/verifier/**`, `src/osd/cli.py` (status column only), `schema/verification.schema.json` (optional field only), `tests/test_verify.py`, `tests/fixtures/listings/**`, `tests/fixtures/verification/**`, `docs/program/charters/E23-*STRATEGY.md`, `docs/program/evidence/e23/**`.
