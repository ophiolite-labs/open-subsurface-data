# H2 branch runs

Both are `workflow_dispatch` on branch `h2-verify-in-shards` with empty `ids` (the sharded path), on
the 176-record catalogue of main dd06ac9 (E29 merged). Branch runs store nothing, open and close no
issue (dry run), and do not republish.

## Run 40009341905: all records (head d9e3612)

Dispatched 19:10:48Z, finish job done 19:29:04Z: **18.3 min end to end**. Snapshot job 8 s.
176 of 176 records verified (fresh ids = the checkout's record set); 0 kept.

| shard | records | job | verify step | bytes hashed | slowest record |
|---|---|---|---|---|---|
| 1/12 | 11 | 4.3 min | 4.1 min | 211,226,521 | tno/bro-geological-boreholes (185 s) |
| 2/12 | 12 | 2.9 min | 2.7 min | 88,821,665 | dgh/national-data-repository (88 s) |
| 3/12 | 9 | 2.5 min | 2.4 min | 10,730,347 | ns-energy/onshore-petroleum-well-log-database (47 s) |
| 4/12 | 8 | 5.4 min | 5.2 min | 183,383,860 | soton/scanner-pockmark-velocity-models (253 s) |
| 5/12 | 11 | 2.5 min | 2.3 min | 264,926,355 | nzpam/petroleum-wells (28 s) |
| 6/12 | 13 | 2.8 min | 2.5 min | 4,713,661 | tudelft/egg-model (42 s) |
| 7/12 | 15 | 3.2 min | 3.1 min | 46,004,661 | cpc/onshore-well-locations (63 s) |
| 8/12 | 11 | 7.7 min | 7.5 min | 350,605,955 | bgs/single-onshore-borehole-index (193 s) |
| 9/12 | 42 | 6.5 min | 6.3 min | 143,197,679 | nysdec/oil-and-gas-annual-production (33 s) |
| 10/12 | 14 | 2.1 min | 1.9 min | 19,427,328 | ak-dggs/tax-credit-well-data (50 s) |
| 11/12 | 10 | 4.7 min | 4.5 min | 20,971,391 | pau/petroleum-data (148 s) |
| 12/12 | 20 | 15.0 min | 14.8 min | 72,995,842 | opm/spe9 (492 s) |

Finish job 3.1 min (overlay, status, report, `make check-full`: 25,579 STAC objects valid).
Slowest records: opm/spe9 (492 s), soton/scanner-pockmark-velocity-models (253 s),
bgs/single-onshore-borehole-index (193 s), tno/bro-geological-boreholes (185 s), pau/petroleum-data
(148 s), ibm-research/netherlands-f3-interpretation (135 s), dgh/national-data-repository (88 s).
Dead-link report (dry run): would close #45 (spe/csp10-model-2) and #46 (spe/csp11), both freshly
verified at L1+. Bytes: at most 351 MB in one shard, 1.42 GB across all twelve (budget 2 GiB each).

The slowest shard is one record: opm/spe9 (492 s, about a third of shard 12). The strategy's
estimate (slowest shard ~11 min, sk-mer) was made from the serial runs' `checked_at` gaps; on these
runs sk-mer was not the floor and opm/spe9 was. Per-record time here is the gap between
consecutive `checked_at` stamps in the shard, so it includes the next record's outline-input fetch.

## Run 40012093005: shard 3 forced to fail (`fail_shard=3`, head 019f7c8)

Dispatched 19:31:33Z, finish job done 19:50:46Z (19.2 min). Run conclusion `failure` (shard 3
exited 1 in its forced-failure step, 9 s); the finishing job ran and succeeded. Snapshot:
verification-results 73a85d7b74d8660abca494a1a41efd7dc0f74d22.

Step summary (finish job):

    167 of 176 records verified in this run; 9 keep their earlier result.
    | 3/12 | 9 | **failed**: no id list (the shard failed, was cancelled or uploaded nothing) | | |
    Shard 3/12 failed (no id list (...)); its records keep their earlier results:
    - anh-bo/exploracion-y-explotacion
    - equinor/volve
    - inp-mz/actividade-de-pesquisa-e-producao
    - manitoba-petroleum/technical-well-files
    - ns-energy/onshore-2d-seismic-navigation
    - ns-energy/onshore-petroleum-well-log-database
    - perupetro/banco-de-datos
    - petronas/myprodata
    - staatsolie/open-door-data-offering
    Records without a fresh result: (the same nine)

Earlier results kept: each of the nine files in the run's `verification` artifact is byte-equal to
the one in its `snapshot` artifact (checked by downloading both). `make check-full`: 25,579 STAC
objects valid. Dead-link report (dry run): would open "origin dead: eug/national-data-repository"
(timeout on 2026-10-23; freshly verified), nothing for the nine kept records.

## Scaling (a projection)

From run 40009341905: per-shard verify time against records per shard is not proportional (shard 9:
42 records, 6.3 min; shard 12: 20 records, 14.8 min); time follows the slow records, and one host
stays in one shard. Projection for twice the catalogue, assuming each shard's work doubles with
the same mix: slowest shard 2 x 14.8 = 29.6 min verify + 0.2 min setup, snapshot 0.2 min, finish
3.1 min: **33.1 min**, under 40. The main-run measurement after merge replaces these numbers.
