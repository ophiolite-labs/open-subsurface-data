# H1 branch run 39976675015 (verify.yml dispatched on h1-origins-that-recover-and-hide, 23 Oct 2026)

https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/39976675015 — success; all records
(ids empty), dry run (branch dispatch), nothing stored, no issue touched. Read from the run's
`verification` artifact.

Reachability over 121 records: ok 106, moved 1, blocked 6, dead 8.

| record | level | checked | reachability | origin-reachable detail |
|---|---|---|---|---|
| nm-ocd/oil-and-gas-wells | L0 | 2026-10-23T15:23:31Z | blocked | answers a browser, not the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent); blocked since 2026-10-23 |
| pa-dep/oil-and-gas-well-locations | L0 | 2026-10-23T15:25:32Z | blocked | answers a browser, not the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent); blocked since 2026-10-23 |
| odnr/oil-and-gas-well-database | L0 | 2026-10-23T15:25:11Z | blocked | answers a browser, not the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent); blocked since 2026-10-23 |

The open origin-dead issues (#17, #23 to #27), as this run saw their origins; none answered, the
browser probe included, so none would close:

| issue | record | level | detail |
|---|---|---|---|
| #17 | geus/deep-subsurface-data | L0 dead | HTTP 404 from https://eng.geus.dk/products-services-facilities/data-and-maps/subsurface-data-denmark |
| #23 | co2datashare/eos-31-5-7-rock-mechanics | L0 dead | HTTP 502 from co2datashare.org |
| #24 | co2datashare/illinois-basin-decatur | L0 dead | HTTP 502 from co2datashare.org |
| #25 | co2datashare/sleipner-2019-benchmark-model | L0 dead | HTTP 502 from co2datashare.org |
| #26 | co2datashare/sleipner-4d-seismic | L0 dead | HTTP 502 from co2datashare.org |
| #27 | co2datashare/smeaheia | L0 dead | HTTP 502 from co2datashare.org |

Dead-link report step (dry run, issue list read): "0 issues to open, 0 already reported, 0 blocked
(no issue, OSD-D9), 0 to close (recovered)".
