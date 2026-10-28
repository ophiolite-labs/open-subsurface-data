# E43 evidence: ready for your tools on the site

Written by the site test (`npm run site-test`, tests/site/site.test.mjs, "starter:" tests) against
`make build` of this branch, with E40's fixture packs (tests/fixtures/starters) built by `osd.build`
into build/site-test/e43 and served in place of the build's empty starters.json; copied here from
`build/site-test/`. The real F3 pack comes with E42 (acceptance 6, this charter's DONE condition).

- `starter-card-desktop.png`: desktop, `#sel=terranubis/f3-demo-2020`: the fourth card "Starter
  project" after "Get the data", the three application buttons in the pack's order (ResInsight
  chosen), the licence line, "what we decided", the three steps, "Download the pack manifest".
- `starter-card-phone.png`: 360 px, the same card: the buttons wrap, nothing leaves the sheet.
- `starters-desktop.png`, `starters-phone.png` (360 px): starters.html with the two fixture packs:
  dataset and level, where, inside, applications with sizes and the oracle sentence, licence, three
  steps, the decision log (chosen lines marked), "Want a starter project for another dataset?".
- `starters-empty.png`: starters.html when the build has no pack: "No starter projects yet."
- `starter-filter.png`: `#starter=1`: the list and the map narrowed to the two fixture records.
- `site-test-transcript.txt`: the 38 site tests, all passing (the 1 MB tile budget test included).
