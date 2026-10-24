# E35 results: two explicit-id dispatches over the 22 candidates (24 Oct 2026)

Branch `e35-whole-layers` at 3bb7f7c (code as of 953b6ad; later commits are evidence only).

| run | dispatched | verify step | conclusion |
|---|---|---|---|
| [40049335755](https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/40049335755) | 01:20:27 UTC | 01:20:35 to 01:34:29 (13 min 54 s) | success |
| [40050525735](https://github.com/ophiolite-labs/open-subsurface-data/actions/runs/40050525735) | 01:35:56 UTC, when the first completed | 01:36:05 to 01:49:19 (13 min 14 s) | success |

## Outcome

- **15 layers read whole** on the first run, with `files-checksummed` passing ("whole layer checked
  (N features, esri-json), not a downloadable file"). **Five records rise from L1 to L2** against the stored
  main results of 24 Oct (\`verification-results\`): BCER, ND DMR, SGC, UT DOGM, WA DNR geophysics (each a
  partial export before). INP Mozambique and WA DNR geothermal, groundwater, oil-gas and shear-wave stay L2,
  now on whole-layer evidence instead of a one-page export; WA DEMIRS stays L3.
- **Checksums equal on the second run for all 14 layers read twice** (every one whose edit date did not
  change; none changed). SGUDDS was not read on the second run: its layer answered "Could not find service.
  Service may be stopped" (an outage on the publisher's side, not a disagreement). Stop rule not met.
- **Multi-page candidates under the cap** (from the strategy's 24 Oct table): bcer (18 pages), nd-dmr (23),
  sgc (13), ut-dogm (21), wa-dnr/geophysics (4), nbmg (2) pass on both runs. **va-energy** has outage
  evidence: on both runs the origin refused the connection from the runner (`origin-reachable` fail,
  http_status 0, "connection at https://energy.virginia.gov/gas-oil/GasOil.shtml", checked 01:32:04 and
  01:47:05 UTC, and from this VPS earlier the same day the description request got no answer within 30 s); the layer was not tried.
- nbmg, nzpam x2 and sgudds pass the whole-layer check but stay L0 on `origin-reachable` (blocked: NBMG
  answers 404 to the verifier and 200 to a browser; NZP&M and SGUDDS 403 to the runner, as in E29).
- The six layers above 50,000 features stay partial exports, the cap named in the detail (out of scope).

## Per record, run 40049335755

| record | level | features | bytes | sha256 | edit before = after | files-checksummed / first failing check |
|---|---|---|---|---|---|---|
| bcer/well-surface-holes-permitted | L2 | 34431 | 19138213 | `e94d0fd8ffa86198…` | none stated | pass: whole layer checked (34431 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| cgs/vrtna-prozkoumanost | L1 |  |  | `` |  | skip: not read whole: the layer counts 746805 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| inp-mz/actividade-de-pesquisa-e-producao | L2 | 255 | 86980 | `b0ea5231d3a1dad1…` | equal | pass: whole layer checked (255 features, esri-json), not a downloadable file; edit date 2026-02-10T09:33:05+00:00 unchanged during paging; listing dated 2026-02-10<br>first non-pass: outline-present fail: no outlines file |
| nbmg/oil-gas-wells-through-2013 | L0 | 1061 | 391556 | `c7fded3752274c9c…` | none stated | pass: whole layer checked (1061 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: answers a browser, not the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent); blocked |
| nd-dmr/wells | L2 | 44018 | 22046769 | `29758d85658e6733…` | none stated | pass: whole layer checked (44018 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| nzpam/petroleum-wells | L0 | 1302 | 876489 | `99799c0c820ff0bc…` | none stated | pass: whole layer checked (1302 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: blocked from this runner (HTTP 403, HTTP 403 from https://gis.nzpam.govt.nz/server/rest/services/Pub |
| nzpam/seismic-surveys-2d | L0 | 990 | 7617740 | `68e0f627aaf9aeef…` | none stated | pass: whole layer checked (990 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: blocked from this runner (HTTP 403, HTTP 403 from https://gis.nzpam.govt.nz/server/rest/services/Pub |
| pgi/cbdg-boreholes | L1 |  |  | `` |  | skip: not read whole: the layer counts 334145 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| sgc/banco-informacion-petrolera-pozos | L2 | 25013 | 12054174 | `47a45145d5cf7256…` | equal | pass: whole layer checked (25013 features, esri-json), not a downloadable file; edit date 2022-10-20T15:36:57+00:00 unchanged during paging; listing dated 2022-10-20<br>first non-pass: outline-present fail: no outlines file |
| sgudds/register-geotermalnych-vrtov | L0 | 307 | 337971 | `ee4b13d182e3b245…` | none stated | pass: whole layer checked (307 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: blocked from this runner (HTTP 403, HTTP 403 from https://www.geology.sk/geoinfoportal/mapovy-portal |
| sk-mer/drill-core | L1 |  |  | `` |  | skip: not read whole: the layer counts 104754 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| sk-mer/drill-cuttings | L1 |  |  | `` |  | skip: not read whole: the layer counts 73632 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceeded |
| sk-mer/non-vertical-wells | L1 |  |  | `` |  | skip: not read whole: the layer counts 68000 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceeded |
| sk-mer/vertical-wells | L1 |  |  | `` |  | skip: not read whole: the layer counts 119595 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| ut-dogm/oil-gas-wells | L2 | 40422 | 46936130 | `953bd802aadaad4d…` | equal | pass: whole layer checked (40422 features, esri-json), not a downloadable file; edit date 2026-10-23T09:41:43+00:00 unchanged during paging; listing dated 2026-10-23<br>first non-pass: outline-present fail: no outlines file |
| va-energy/gas-oil-wells | L0 |  |  | `` |  | skip: origin not reachable<br>first non-pass: origin-reachable fail: connection at https://energy.virginia.gov/gas-oil/GasOil.shtml |
| wa-demirs/petroleum-wells | L3 | 4371 | 1725840 | `f0d0d5ef305a2085…` | none stated | pass: whole layer checked (4371 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: canonical-conversion skip: no fidelity record (osd verify <id> --fidelity-from) |
| wa-dnr/geophysics-database | L2 | 7577 | 11453522 | `236a6a17b6279867…` | none stated | pass: whole layer checked (7577 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/geothermal-wells | L2 | 489 | 619864 | `9a799df2a06fcfeb…` | none stated | pass: whole layer checked (489 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/groundwater-chemistry | L2 | 1501 | 4051583 | `e8f103e20f60316b…` | none stated | pass: whole layer checked (1501 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/oil-gas-wells | L2 | 830 | 645201 | `0d481afbdc8a40bd…` | none stated | pass: whole layer checked (830 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/shear-wave-database | L2 | 599 | 482897 | `4d2a229a52b452b1…` | none stated | pass: whole layer checked (599 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |

## Per record, run 40050525735

| record | level | features | bytes | sha256 | edit before = after | files-checksummed / first failing check |
|---|---|---|---|---|---|---|
| bcer/well-surface-holes-permitted | L2 | 34431 | 19138213 | `e94d0fd8ffa86198…` | none stated | pass: whole layer checked (34431 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| cgs/vrtna-prozkoumanost | L1 |  |  | `` |  | skip: not read whole: the layer counts 746805 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| inp-mz/actividade-de-pesquisa-e-producao | L2 | 255 | 86980 | `b0ea5231d3a1dad1…` | equal | pass: whole layer checked (255 features, esri-json), not a downloadable file; edit date 2026-02-10T09:33:05+00:00 unchanged during paging; listing dated 2026-02-10<br>first non-pass: outline-present fail: no outlines file |
| nbmg/oil-gas-wells-through-2013 | L0 | 1061 | 391556 | `c7fded3752274c9c…` | none stated | pass: whole layer checked (1061 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: answers a browser, not the verifier (HTTP 404 to osd-verifier, HTTP 200 to a browser agent); blocked |
| nd-dmr/wells | L2 | 44018 | 22046769 | `29758d85658e6733…` | none stated | pass: whole layer checked (44018 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| nzpam/petroleum-wells | L0 | 1302 | 876489 | `99799c0c820ff0bc…` | none stated | pass: whole layer checked (1302 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: blocked from this runner (HTTP 403, HTTP 403 from https://gis.nzpam.govt.nz/server/rest/services/Pub |
| nzpam/seismic-surveys-2d | L0 | 990 | 7617740 | `68e0f627aaf9aeef…` | none stated | pass: whole layer checked (990 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: origin-reachable skip: blocked from this runner (HTTP 403, HTTP 403 from https://gis.nzpam.govt.nz/server/rest/services/Pub |
| pgi/cbdg-boreholes | L1 |  |  | `` |  | skip: not read whole: the layer counts 334145 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| sgc/banco-informacion-petrolera-pozos | L2 | 25013 | 12054174 | `47a45145d5cf7256…` | equal | pass: whole layer checked (25013 features, esri-json), not a downloadable file; edit date 2022-10-20T15:36:57+00:00 unchanged during paging; listing dated 2022-10-20<br>first non-pass: outline-present fail: no outlines file |
| sgudds/register-geotermalnych-vrtov | L0 |  |  | `` |  | fail: the listing is an error response: Error handling service request :Could not find service. Service may be stopped or it may not be configured.<br>first non-pass: origin-reachable skip: blocked from this runner (HTTP 403, HTTP 403 from https://www.geology.sk/geoinfoportal/mapovy-portal |
| sk-mer/drill-core | L1 |  |  | `` |  | skip: not read whole: the layer counts 104754 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| sk-mer/drill-cuttings | L1 |  |  | `` |  | skip: not read whole: the layer counts 73632 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceeded |
| sk-mer/non-vertical-wells | L1 |  |  | `` |  | skip: not read whole: the layer counts 68000 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceeded |
| sk-mer/vertical-wells | L1 |  |  | `` |  | skip: not read whole: the layer counts 119595 features, above the 50000 a whole layer is read to; the one-page export instead; export truncated by the server (exceede |
| ut-dogm/oil-gas-wells | L2 | 40422 | 46936130 | `953bd802aadaad4d…` | equal | pass: whole layer checked (40422 features, esri-json), not a downloadable file; edit date 2026-10-23T09:41:43+00:00 unchanged during paging; listing dated 2026-10-23<br>first non-pass: outline-present fail: no outlines file |
| va-energy/gas-oil-wells | L0 |  |  | `` |  | skip: origin not reachable<br>first non-pass: origin-reachable fail: connection at https://energy.virginia.gov/gas-oil/GasOil.shtml |
| wa-demirs/petroleum-wells | L3 | 4371 | 1725840 | `f0d0d5ef305a2085…` | none stated | pass: whole layer checked (4371 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: canonical-conversion skip: no fidelity record (osd verify <id> --fidelity-from) |
| wa-dnr/geophysics-database | L2 | 7577 | 11453522 | `236a6a17b6279867…` | none stated | pass: whole layer checked (7577 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/geothermal-wells | L2 | 489 | 619864 | `9a799df2a06fcfeb…` | none stated | pass: whole layer checked (489 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/groundwater-chemistry | L2 | 1501 | 4051583 | `e8f103e20f60316b…` | none stated | pass: whole layer checked (1501 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/oil-gas-wells | L2 | 830 | 645201 | `0d481afbdc8a40bd…` | none stated | pass: whole layer checked (830 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |
| wa-dnr/shear-wave-database | L2 | 599 | 482897 | `4d2a229a52b452b1…` | none stated | pass: whole layer checked (599 features, esri-json), not a downloadable file; stability unknown (the layer states no edit date)<br>first non-pass: outline-present fail: no outlines file |

## Checksums compared

| record | features | run 40049335755 sha256 | run 40050525735 sha256 | lastEditDate (both runs) | equal |
|---|---|---|---|---|---|
| bcer/well-surface-holes-permitted | 34431 | `e94d0fd8ffa861987d8b39a1e54da54418197e5e193d5bbee5605753563c38d7` | `e94d0fd8ffa861987d8b39a1e54da54418197e5e193d5bbee5605753563c38d7` | none stated / none stated | yes |
| inp-mz/actividade-de-pesquisa-e-producao | 255 | `b0ea5231d3a1dad1fac7d77d7810d17b83808f26a91fb7e08d19774592582371` | `b0ea5231d3a1dad1fac7d77d7810d17b83808f26a91fb7e08d19774592582371` | 1770715985605 / 1770715985605 | yes |
| nbmg/oil-gas-wells-through-2013 | 1061 | `c7fded3752274c9cac35dc014aed456699a9994ffade1f8dd841ce4a0ede9fd0` | `c7fded3752274c9cac35dc014aed456699a9994ffade1f8dd841ce4a0ede9fd0` | none stated / none stated | yes |
| nd-dmr/wells | 44018 | `29758d85658e67332c03a838a984a8d941d22e08020e2b5b3d76b5148f6ea2e1` | `29758d85658e67332c03a838a984a8d941d22e08020e2b5b3d76b5148f6ea2e1` | none stated / none stated | yes |
| nzpam/petroleum-wells | 1302 | `99799c0c820ff0bcd42a7b93f03f0c1ff5035bfef215e82b7eba4634f2ca2662` | `99799c0c820ff0bcd42a7b93f03f0c1ff5035bfef215e82b7eba4634f2ca2662` | none stated / none stated | yes |
| nzpam/seismic-surveys-2d | 990 | `68e0f627aaf9aeef20f8e7bc564cffa3d92d246a862f6883c241a1fdc0758bc8` | `68e0f627aaf9aeef20f8e7bc564cffa3d92d246a862f6883c241a1fdc0758bc8` | none stated / none stated | yes |
| sgc/banco-informacion-petrolera-pozos | 25013 | `47a45145d5cf72563832ec3bb99af408e7044667fb877e4067e8232584a64877` | `47a45145d5cf72563832ec3bb99af408e7044667fb877e4067e8232584a64877` | 1666280217499 / 1666280217499 | yes |
| sgudds/register-geotermalnych-vrtov | 307 | `ee4b13d182e3b245c5974f54fbb6d13528c7549a53599b992da9fd20ca44bb3c` | `—` | none stated / — | no (see below) |
| ut-dogm/oil-gas-wells | 40422 | `953bd802aadaad4d1d2a0d40deecb451f288598435c785bd1bb011fb578fe0d7` | `953bd802aadaad4d1d2a0d40deecb451f288598435c785bd1bb011fb578fe0d7` | 1792748503702 / 1792748503702 | yes |
| wa-demirs/petroleum-wells | 4371 | `f0d0d5ef305a2085062425f66008498100d07f5a94ddbb93e0faa98afe9e9298` | `f0d0d5ef305a2085062425f66008498100d07f5a94ddbb93e0faa98afe9e9298` | none stated / none stated | yes |
| wa-dnr/geophysics-database | 7577 | `236a6a17b6279867489e955b77b16573673245fbc96a9e81531e1b95566277bf` | `236a6a17b6279867489e955b77b16573673245fbc96a9e81531e1b95566277bf` | none stated / none stated | yes |
| wa-dnr/geothermal-wells | 489 | `9a799df2a06fcfeb222108e8fc0684703e78a6ef16620375c4ac306c8bab2a3e` | `9a799df2a06fcfeb222108e8fc0684703e78a6ef16620375c4ac306c8bab2a3e` | none stated / none stated | yes |
| wa-dnr/groundwater-chemistry | 1501 | `e8f103e20f60316b7b651f994ad5b8b529474833db89d37e1e37fedc05ba644c` | `e8f103e20f60316b7b651f994ad5b8b529474833db89d37e1e37fedc05ba644c` | none stated / none stated | yes |
| wa-dnr/oil-gas-wells | 830 | `0d481afbdc8a40bd7e2c251391713ae050073acf9568a05f04b53c00a199f699` | `0d481afbdc8a40bd7e2c251391713ae050073acf9568a05f04b53c00a199f699` | none stated / none stated | yes |
| wa-dnr/shear-wave-database | 599 | `4d2a229a52b452b1ff0a11f61c85f1ebe8a8bc0425a021ec56734191f306ffb6` | `4d2a229a52b452b1ff0a11f61c85f1ebe8a8bc0425a021ec56734191f306ffb6` | none stated / none stated | yes |

Tables made from the runs' `verification` artifacts (`gh run download <id> -n verification`).
