# H2 strategy: verify in shards

Charter: `H2-verify-in-shards.md` (Kernel, hardening). Base: main dd06ac9 (E29 merged, 176 records,
119 origin hosts). Written at lane open, 23 Oct. Measurements from two results sets of the same day:
main run 39997774390 (the stored `verification-results`, 160 records, verify step 53.9 min) and
E29's all-record branch run 39998588144 (artifact `verification`, 160 records with outline inputs,
verify step 42.2 min). Script: `docs/program/evidence/h2/estimate.py`; hosts:
`uv run python -m osd.shards hosts -n 12 --vdir <results>` (output in `evidence/h2/hosts-n12.json`).

## N = 12

Per-record seconds are the gaps between consecutive `checked_at` stamps (serial run), the last to
the step's end; records new since then get the median (5 to 6 s). Summed per shard of the
origin-host hash:

| N | slowest shard, E29 branch run | slowest shard, main run | records per shard (176) |
|---|---|---|---|
| 8 | 13.1 min | 16.1 min | 10 to 37 |
| 10 | 10.1 min | 13.3 min | 5 to 30 |
| 12 | 9.4 min | 11.0 min | 8 to 42 |
| 16 | 11.0 min | 13.1 min | 3 to 20 |

The floor is one host: `gisappl.saskatchewan.ca` (sk-mer, two records, 8.0 to 8.3 min; one record
is 471 to 489 s). Above 12, the hash puts more of the slow hosts together and nothing improves; 12
leaves margin under GitHub's 20 concurrent jobs for the free plan, so CI of other lanes still runs
during a verify. Projection for today: slowest shard ~11 min plus ~2 min of job setup (checkout,
uv sync, snapshot download) is ~13 min, finishing job (status, report, `make check-full` ~1.6 min,
store) ~3 min: ~16 min end to end, under 25. Doubling (a projection): each shard's sum doubles,
2 x 11.0 + 2 + 3 = 27 min, under 40. The main run after merge measures it.

## The per-host measurement

Design 1 keeps one origin host in one shard. Other hosts a record reaches (manifest_url, licence
page, outline-input layer, hashed file URLs from the E29 run): 50, none of which is also an
origin host. At N = 12, 42 of them are reached from one shard only (so the 2 s pause holds for
them too). The rest:

| host | shards that can reach it at once | what |
|---|---|---|
| creativecommons.org | 10 | licence pages |
| opendatacommons.org | 3 | licence pages |
| www.arcgis.com | 3 | licence/item pages of ArcGIS-hosted layers |
| api.github.com, raw.githubusercontent.com | 2 | listings and files of two GitHub-hosted records |
| data.geus.dk, www.nzpam.govt.nz, www.opendefinition.org | 2 | files, licence pages |

Each shard paces its own requests at 2 s per host, so a host reached from k shards sees at most k
requests per 2 s; for creativecommons.org that is at most 5 per second, a few times per run (one
licence page per record). Accepted; stated, not engineered around (charter: the pause value is out of
scope).

## Budget (design 2)

The 2 GiB L2 byte budget stays per process: a dispatch of 12 shards may hash up to 24 GiB. Measured
bytes hashed per shard (N = 12): main run 1 to 334 MiB (total 1,293 MiB), E29 run 0 to 258 MiB
(total 838 MiB); no shard is near its 2 GiB. The finishing job's summary states bytes per shard.

## Artifact layout (designs 3 and 4)

```
snapshot job      git archive origin/verification-results -> artifact `snapshot` (+ its commit SHA)
shard job I/12    download `snapshot` -> build/verification
                  osd verify --outline-inputs --shard I/12 --ids-out shard/ids.txt
                  shard/ids.txt                    ids it verified, one per line
                  shard/verification/<id__>.json   exactly those records' files
                  shard/shard.json                 {"shard": I, "of": 12, "started", "finished"}
                  -> artifact `shard-I` (uploaded only when every step before it succeeded)
finish job        download `snapshot` -> build/verification-before; `shard-*` -> build/shards/shard-I/
                  python -m osd.shards overlay: snapshot copied to build/verification, then each accepted
                  shard's files over it; fresh ids -> build/fresh-ids.txt; summary -> step summary
                  osd status; dead-link report with --verified = fresh ids (none: skipped, said);
                  make check-full (every dispatch); store + Pages on main only
```

A shard is discarded (its records keep their earlier results, the summary names it and them) when
its `ids.txt` is missing, its `shard.json` names another I/N, an id is not a record of the checkout
or hashes to another shard, the files differ from the id list, or a file's `record_id` differs.

Where the code goes: `src/osd/shards.py` (hash, selection, overlay, summary, hosts; `python -m
osd.shards`), `src/osd/cli.py` (`--shard`, `--ids-out` on `osd verify`, selection in `cmd_verify`),
`.github/workflows/verify.yml`. The existing `verify` job keeps pull requests and explicit-id
dispatches (one job, unchanged steps; `tests/test_report.py` and `tests/test_stac.py` read it). The
sharded path is three new jobs for a dispatch with empty `ids`. A branch-only input
`fail_shard` makes that shard exit 1 before verifying (the forced-failure evidence run).

Concurrency (design 5): a workflow-level group `verify-main` for `workflow_dispatch` on main,
`cancel-in-progress: false`; every other run gets its own group (`verify-<run id>`), so pull requests
and branch dispatches stay outside.

## Commits

1. this strategy and the measurement (evidence/h2)
2. `osd.shards`: hash, selection; `osd verify --shard I/N --ids-out`; CLI, partition and stability tests
3. overlay and summary; overlay tests
4. `verify.yml`: snapshot, shards, finishing job, concurrency; report test on the finishing step
5. mutations recorded (`evidence/h2/mutations.md`), branch runs recorded
