# E21 evidence: the map says when

Written by the site test (`npm run site-test`, tests/site/site.test.mjs, "period:" tests) against
`make build` of the rebased branch; copied here from `build/site-test/`.

- `when-filter.png`: desktop, `#t=1990-2000&dated=1`: the From/to years and "only dated datasets"
  under the level select, the list with the period years after the publisher, the map filtered to
  the same records.
- `when-detail.png`: desktop, `#sel=equinor/volve`: the detail's When row, "2008 to 2016" and the
  publisher's stated sentence beneath, in the licence row's plain style.
- `when-phone-sheet.png`: 390 px wide, the same filter: the year inputs fit the bottom sheet.
- `site-test-transcript.txt`: the 23 site tests, all passing, including the E05 performance test
  and the E06/E19 select tests (manifest byte-for-byte unchanged).
