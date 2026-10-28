# E41 runs

## Local transcript (28 Oct 2026, this branch, a `LocalDirectory` store; no keys on this host)

The fixture deposit, the read-back against `sha256sum`, a rerun, two refusals by name on real
records, and the F3 fixture pack's artefacts through `put-derived` (their digests are the ones
E40's custody fixtures hold).

```
$ uv run osd mirror deposit terranubis/f3-demo-2020 tests/fixtures/deposits/f3-demo-2023 --obtained 2026-10-29 --by maintainer --page-url https://terranubis.com/datainfo/F3-Demo-2023 --page .../page.html --licence-text .../licence.html --store $STORE --public-url https://mirror.test/
  published   terranubis/f3-demo-2020 F3_Demo_2023.zip 0debce384922  (3600 bytes)
  published   terranubis/f3-demo-2020 docs/README.txt 43da0b573234  (99 bytes)
  published   terranubis/f3-demo-2020 wells/F02-1.las 0ea5076c27ee  (134 bytes)
3 files, 3833 bytes in $STORE: 3 published, 0 present
$ sha256sum (the download) ; read-back of the stored objects
0debce3849227a20dfc7f457af6a2949d32ee705810c69fae8c48af8f531c91d  F3_Demo_2023.zip
43da0b573234d1eca227ddbebabc068be48ce6da0abf10373e5ed42c780986d5  docs/README.txt
0ea5076c27eea4084752eeea4dc2bf22ad219c006f631894d985a396768381c7  wells/F02-1.las
0debce3849227a20dfc7f457af6a2949d32ee705810c69fae8c48af8f531c91d  mirror/terranubis/f3-demo-2020/0debce3849227a20dfc7f457af6a2949d32ee705810c69fae8c48af8f531c91d/F3_Demo_2023.zip
0ea5076c27eea4084752eeea4dc2bf22ad219c006f631894d985a396768381c7  mirror/terranubis/f3-demo-2020/0ea5076c27eea4084752eeea4dc2bf22ad219c006f631894d985a396768381c7/F02-1.las
43da0b573234d1eca227ddbebabc068be48ce6da0abf10373e5ed42c780986d5  mirror/terranubis/f3-demo-2020/43da0b573234d1eca227ddbebabc068be48ce6da0abf10373e5ed42c780986d5/README.txt
$ uv run osd mirror deposit ... --store $STORE (rerun)
3 files, 3833 bytes in $STORE: 0 published, 3 present
$ uv run osd mirror deposit boem/paleontologic-data ... ($(grep redistribution records/boem/paleontologic-data.yaml | tr -s ' '))
redistribution: unknown
refused: boem/paleontologic-data: redistribution unknown, not allowed (OSD-D6)
$ uv run osd mirror deposit sztfh/seismic-and-well-log-databases ... ($(grep redistribution records/sztfh/seismic-and-well-log-databases.yaml | tr -s ' '))
redistribution: restricted
refused: sztfh/seismic-and-well-log-databases: redistribution restricted, not allowed (OSD-D6)
$ uv run osd mirror put-derived terranubis/f3-demo-2020/starter tests/fixtures/starters/artefacts/terranubis__f3-demo-2020__starter --pack <the F3 fixture pack, unpublished, keys removed> --store $STORE
  published   terranubis/f3-demo-2020 opendtect/import_f3.py d182c1880dd8  (65 bytes)
  published   terranubis/f3-demo-2020 python/f3_starter.ipynb d1b93a151ac8  (78 bytes)
  published   terranubis/f3-demo-2020 python/requirements.txt d42a911551cf  (27 bytes)
  published   terranubis/f3-demo-2020 resinsight/import_f3.py dde928461118  (33 bytes)
  published   terranubis/f3-demo-2020 standard/F02-1.las b4fd569aca77  (32 bytes)
  published   terranubis/f3-demo-2020 standard/F03-2.las 9512410c91ee  (32 bytes)
  published   terranubis/f3-demo-2020 standard/F03-4.las 39f0557e918a  (32 bytes)
  published   terranubis/f3-demo-2020 standard/F06-1.las a131aa023c5c  (32 bytes)
  published   terranubis/f3-demo-2020 standard/F3.sgy a6b4ec0d3420  (68 bytes)
  published   terranubis/f3-demo-2020 standard/horizons.xyz dfc2c8c8dd3d  (43 bytes)
10 files, 442 bytes in $STORE: 10 published, 0 present
```

## Gate

`make check` locally: lint clean, `osd validate` 236 records 0 problems, build green, tests 777
passed and 1 failed: `tests/test_build.py::test_crossing_strings_keep_their_own_features`, the
known host condition (tippecanoe 2.49.0 here, CI pins 2.79.0). Wall time 113 s. The E41 tests
alone: 48 selected in 6.7 s.

## Acceptance 6 (real data): waiting on owner item 112

Run by the supervisor on the VPS when the download is in
`/mnt/HC_Volume_107082112/osd-deposits/terranubis/f3-demo-2023/` (S3 keys in the environment, never
printed):

1. Read the licence files inside the archive (stop rule); quote them in `terms.md`.
2. `licence.html` (the BY-SA 3.0 deed) is already saved beside `page.html` (supervisor answer 1).
3. `uv run osd mirror deposit terranubis/f3-demo-2020 /mnt/HC_Volume_107082112/osd-deposits/terranubis/f3-demo-2023 --obtained <day of the download> --by maintainer --page-url https://terranubis.com/datainfo/F3-Demo-2023 --page .../page.html --licence-text .../licence.html --store s3://osd-mirror`
4. Two verify dispatches on main with ids `terranubis/f3-demo-2020` (each copies the bucket's
   custody before verifying, supervisor answer 2, so the first already counts): both show `terranubis/f3-demo-2020` at L2 with "deposited by a
   maintainer from the publisher's download, <date>" (map detail panel and status page,
   screenshot); `osd mirror eligible --vdir build/verification` lists it; `osd manifest
   terranubis/f3-demo-2020` from the published catalogue, cut to one asset, and `osd get` fetch one
   file from the real mirror with digest equal (transcript here).
