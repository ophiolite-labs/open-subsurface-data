# Contributing

Three kinds of contribution, in order of how welcome they are:

1. **A record.** Copy `records/_template.yaml` to `records/<publisher>/<dataset>.yaml`. Write only
   what the publisher states; `unknown` is a valid licence answer and better than a guess.
   Open a pull request. CI validates the file and verifies the origin on the network, and
   comments the level it reached. A reviewer checks the licence fields against the publisher's
   page, nothing else. Merged the same day when the check is green.
2. **An outline.** `outlines/<publisher>__<dataset>.geojson`, WGS84, one feature per wellbore
   or survey, with the `source` property saying how the geometry was derived. `approximate: true`
   is allowed and is drawn dashed; it keeps the record at L1.
3. **A tool or site change.** Read `docs/ENGINEERING.md` first. One pull request per outcome a
   user can observe. `make check` is the whole gate.

Nothing here gives legal advice about a dataset's licence. The record repeats what the
publisher says; the publisher's page is the authority.
