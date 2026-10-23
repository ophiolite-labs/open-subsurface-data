# Claims

One row per open lane. A lane may touch only the paths in its row. Two open rows never share a
path. `schema/` edits are kernel and announced in the pull request title. Rows move to MERGED
with the merge commit.

| Lane | Branch | Paths | Status | Since |
|---|---|---|---|---|
| scaffold | main | everything | MERGED (initial commit) | 2026-10-23 |
| E01 | e01-twenty-records | `records/**` | MERGED (PR #1) | 2026-10-23 |
| E11 | main | `.github/workflows/**`, `site/robots.txt`, `docs/program/**` | MERGED (domain live) | 2026-10-23 |
| E02 | e02-verifier-to-l2 | `src/osd/verify.py`, `src/osd/build.py`, `src/osd/cli.py`, `schema/verification.schema.json`, `src/osd/verifier/**` (sampling policy), `tests/test_verify.py`, `.github/workflows/verify.yml` (announced), `docs/program/charters/E02-*` (dispositions), `records/sodir/factpages.yaml`, `records/opm/norne.yaml`, `records/nopims/poseidon.yaml` (manifest_url only; records slot, ruled 23 Oct; sampling policy goes to src/osd/verifier/samples.yaml per OSD-D11) | MERGED (PR #3, 37c010c) | 2026-10-23 |
| E05 | e05-map-that-scales | `site/**`, `tools/shot.mjs`, `tests/site/**`, `package.json`, `package-lock.json`, `.gitignore` (one line, ruled 23 Oct), `Makefile` (site targets only), `.github/workflows/ci.yml` (site test step only, announced), `docs/program/evidence/e05/**` | MERGED (PR #2, 6c232cf) | 2026-10-23 |
| E13 | e13-registers-second-twenty | `records/**` except `records/sodir/factpages.yaml`, `records/opm/norne.yaml`, `records/nopims/poseidon.yaml` (E02); `docs/program/evidence/e13/**` | MERGED (PR #4, 6429445) | 2026-10-23 |
| E03 | e03-outlines-from-the-data | `src/osd/outlines/**`, `src/osd/verify.py` (outline checks only), `src/osd/records.py` (outline validation), `schema/record.schema.json` (record/2: `inputs`, announced), `schema/outline.schema.json`, `outlines/**`, `records/<targets>.yaml` (`inputs` only: sodir/factpages, nlog/nlog, terranubis/f3-demo-2020, rmotc/teapot-dome, nopims/poseidon, nzpam/parihaka, nzpam/kerry-3d; E13 must not edit these seven), `pyproject.toml` (pyproj, segyio), `tests/test_outlines.py`, `tests/fixtures/outlines/**`, `docs/program/charters/E03-*` (strategy), `docs/program/evidence/e03/**` | OPEN (worker osd-e03, worktree ../osd-e03-outlines-from-the-data) | 2026-10-23 |
| E08 | e08-curation-that-runs-itself | `.github/**` (announced; not `ci.yml`'s check job), `site/status.html`, `site/index.html` (one link to status.html only), `src/osd/new.py`, `src/osd/report.py`, `src/osd/cli.py` (`new` and `report` subcommands only), `tests/test_report.py`, `tests/site/status.test.mjs`, `package.json` (`site-test` script line only), `CONTRIBUTING.md`, `docs/program/evidence/e08/**` (ruled 23 Oct on the E08 inbox note) | MERGED (PR #5, e408adb) | 2026-10-23 |
| E14 | e14-records-third-twenty | `records/**` except the seven E03 files (`sodir/factpages`, `nlog/nlog`, `terranubis/f3-demo-2020`, `rmotc/teapot-dome`, `nopims/poseidon`, `nzpam/parihaka`, `nzpam/kerry-3d`); `docs/program/evidence/e14/**` | OPEN (worker osd-e14, worktree ../osd-e14-records-third-twenty) | 2026-10-23 |
