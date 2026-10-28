# Contributing

Three kinds of contribution, in order of how welcome they are:

1. **A record.** Run `uv run osd new <url of the dataset's page>`. It writes
   `records/<publisher>/<dataset>.yaml` from `records/_template.yaml` and the page's title, and
   lists the fields only a person can fill: the publisher's name, the access, the licence name,
   redistribution and attribution, and the kinds. Fill them with what the publisher states;
   `unknown` is a valid licence answer and better than a guess. (Copying the template by hand
   works too.) `make check` goes green when nothing is left to fill. Open a pull request with the
   publisher's licence page in the description.
2. **An outline.** `outlines/<publisher>__<dataset>.geojson`, WGS84, one feature per wellbore
   or survey, with the `source` property saying how the geometry was derived. `approximate: true`
   is allowed and is drawn dashed; it keeps the record at L1.
3. **A tool or site change.** Read `docs/ENGINEERING.md` first. One pull request per outcome a
   user can observe. `make check` is the whole gate.

Not ready to write a record? Open a "Suggest a dataset" issue with the address; a maintainer
turns it into a record pull request with `osd new`.

## What happens to a record pull request

- It is labelled `record` and a records maintainer is asked to review it (`.github/CODEOWNERS`).
- CI validates the file; the `verify` workflow reaches the origin on the network and comments the
  level it reached. A slow or refusing publisher never blocks the merge.
- The reviewer checks the licence fields against the publisher's page, nothing else. Merged the
  same day when the check is green.

## After it merges

- The level and the date of the last check are on the map and on
  [the status page](https://opensubsurfacedata.org/status.html).
- When a later verify run finds that an origin which was reachable is now dead (no answer, 404,
  410, 5xx after a retry), it opens an issue titled `origin dead: <id>` with the HTTP class and
  the date, labelled `origin-dead`. One issue per death; none while one is open. A publisher that
  refuses automated requests (403, 429, a challenge page) is shown as blocked and never gets an
  issue: blocked is not dead.

## Removing a mirrored copy

The mirror copies only datasets whose records say `redistribution: allowed`, under 20 GB, whose
files a verification run has hashed in full (OSD-D6). Each copy has a custody document saying what
it is, where it came from, its licence and attribution, and where to ask for its removal.

1. Anyone opens a "Ask for a mirrored copy to be removed" issue (`.github/ISSUE_TEMPLATE/takedown.yml`).
2. The maintainer who approves removals is the owner, @tuna-soup. Approval is a comment on the
   issue with the label `takedown-approved` added.
3. The maintainer dispatches the `verify` workflow on `main` with `takedown_sha256` set to the
   copy's digest and `takedown_request` set to the issue URL (the keys live only in GitHub; the job
   refuses unless the issue carries `takedown-approved` added by the maintainer). It runs
   `osd mirror remove` against the store, which writes the tombstone `custody/<sha256>.removed.json` first, then deletes
   every object of that copy. The next build drops the mirror address from the catalogue, and
   `osd mirror put` refuses that digest from then on.

Nothing here gives legal advice about a dataset's licence. The record repeats what the
publisher says; the publisher's page is the authority.
