# AGENTS.md: conventions for anyone (or any agent) changing this repository

- `make check` is the gate, offline, under two minutes. If it is green and the pull request
  names what a user can do afterwards, it merges. Do not add stations to it.
- Records state publisher facts; tools state verification facts. Never write a level, a
  checksum or a "verified" word into a record.
- Schemas are contracts. A change to `schema/*.json` is a kernel change: bump the `$id`
  version, keep a test that the old files still validate, name the change in the PR title.
- The site is surface: one HTML, one JS, one CSS, no build step, no framework. Deletable modules,
  never migrations. A screenshot is its proof.
- Network only in `osd verify` and the `verify` workflow. Tests inject a fetcher.
- Lanes claim paths in `docs/program/CLAIMS.md` before they start; two open lanes never share a
  path. Branch names are `e<nn>-<slug>`; one squash merge per lane.
- Program state lives in `docs/program/PROGRAM.md` (queue), `docs/program/charters/` (what each
  epic must achieve) and `docs/program/DECISIONS.md` (open questions for the owner).
- Keep the conversation small: read the lines you need, write results to files, brief by reference.
