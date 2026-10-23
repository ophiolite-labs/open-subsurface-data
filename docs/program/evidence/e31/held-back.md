# E31: candidates held back

Each candidate below has public data, but a publisher clause kept it out of this lane. A later lane
can add it once the publisher has been asked and has agreed.

## Tomakomai CCS demonstration (Japan CCS Co., Ltd., JP)

- Page: http://www.jccs-tomakomai-monitoring.com/JCCS/index.php/top_e/ ("Tomakomai CCUS Demonstration
  Project Information Site"). robots.txt answered 404 at 18:06:32 UTC on 23 Oct 2026; the page was
  read at 18:06:34 UTC.
- It lists monthly PDFs from Jun.2018 to Sep.2026, for example
  `.../JCCS/wp-content/uploads/2026/09/202609_ENG.pdf` (5,450,947 bytes, read 18:06:42 UTC). The
  PDFs report formation pressure and temperature at the well bottom of the injection wells and of
  the observation wells OB-1 and OB-3, plus micro-seismicity from seismometers in an observation
  well and on the seabed.
- Japan CCS's Terms and Conditions of Use (https://www.japanccs.com/en/copyright/, read at
  18:08:31 UTC; the server returned status 404 but sent the full terms text) contain two clauses
  that keep it out:
  - "Please contact JCCS prior permission to provide links"
  - "it is prohibited to copy, modify, reproduce in whole or in part, upload, transmit, or distribute
    any of the contents, without JCCS's prior written permission except for the personal use or the
    use within the scope indicated by applicable laws."
- Supervisor's decision on 23 Oct 2026: it stays out of the catalogue until JCCS has been asked.
  If JCCS gives permission, the record would be `japanccs/tomakomai-monitoring` with kinds
  pressure and reports. Its manifest_url would be the top_e page, with the newest `*_ENG.pdf` as
  the sample.

## Four finished records held back under the `unknown` cap

The charter allows at most six new records with `licence.redistribution: unknown`. The lane wrote ten
such records. It kept six: the four new records that carry a `manifest_url` and the two that add new
countries with a listing (anh-bo for BO, noc-ly for LY). It held back the four below and moved them
unchanged into `held-back/`, so a later lane can restore them with `git mv` once its cap allows.
Their evidence rows are in `sources.md` part A.

| Record (file in `held-back/`) | Country | Why it was the one held back |
|---|---|---|
| fig-dmr/offshore-data-release | FK (new) | access `request`, no listing |
| mra-pg/geoscientific-data | PG (new) | access `purchase`, no listing |
| pdasl/national-petroleum-data-repository | LK (new) | access `request` ('qualified operators'), no listing |
| sd-danr/oil-gas-production-injection | US | has a listing, but Idaho's LAS files were kept in its place |

To restore sd-danr, add this samples.yaml entry as well:
`sd-danr/oil-gas-production-injection: ["*/pubs/og/Oil_Gas_Production_All_Years.xlsx"]   # data page links the production and injection workbooks on sddenr.net; production, 14,332,260 bytes`
