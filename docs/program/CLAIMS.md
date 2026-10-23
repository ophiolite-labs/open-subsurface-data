# Claims

One row per open lane. A lane may touch only the paths in its row. Two open rows never share a
path. `schema/` edits are kernel and announced in the pull request title. Rows move to MERGED
with the merge commit.

| Lane | Branch | Paths | Status | Since |
|---|---|---|---|---|
| scaffold | main | everything | MERGED (initial commit) | 2026-10-23 |
| E01 | e01-twenty-records | `records/**` | MERGED (PR #1) | 2026-10-23 |
| E11 | main | `.github/workflows/**`, `site/robots.txt`, `docs/program/**` | MERGED (domain live) | 2026-10-23 |
| E02 | e02-verifier-to-l2 | `src/osd/verify.py`, `src/osd/build.py`, `src/osd/cli.py`, `schema/verification.schema.json`, `src/osd/verifier/**` (sampling policy), `tests/test_verify.py`, `.github/workflows/verify.yml` (announced), `docs/program/charters/E02-*` (dispositions), `records/sodir/factpages.yaml`, `records/opm/norne.yaml`, `records/nopims/poseidon.yaml` (manifest_url only; records slot, ruled 23 Oct; sampling policy goes to src/osd/verifier/samples.yaml per OSD-D11) | OPEN (worker osd-e02, worktree ../osd-e02-verifier-to-l2) | 2026-10-23 |
| E05 | e05-map-that-scales | `site/**`, `tools/shot.mjs`, `tests/site/**`, `package.json`, `Makefile` (site targets only), `.github/workflows/ci.yml` (site test step only, announced) | OPEN (worker osd-e05, worktree ../osd-e05-map-that-scales) | 2026-10-23 |

