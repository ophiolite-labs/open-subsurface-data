# Listing fixtures (E23)

Real responses saved verbatim on 23 Oct 2026 from ophiolite-epic-01, one request per host, with the
verifier's User-Agent. They feed the reader tests in `tests/test_verify.py`; nothing is fetched in tests.

| File | URL | HTTP, content type |
|---|---|---|
| `ak-dggs.html` | https://dggs.alaska.gov/webpubs/dggs/gmc/well_data/ | 200 text/html |
| `socrata-anh.json` | https://www.datos.gov.co/api/views/fdvb-hsrf.json | 200 application/json |
| `ckan-ar-energia-fractura.json` | https://datos.gob.ar/api/3/action/package_show?id=datos-de-fractura-de-pozos-adjunto-iv | 200 application/json |
| `arcgis-mapserver-bcer.json` | https://geoweb-ags.bc-er.ca/arcgis/rest/services/PASR/PASR_WELL_SURFACE_STATE_PT/MapServer/0?f=json | 200 application/json |
| `datagovtw-cpc.json` | https://data.gov.tw/api/v2/rest/dataset/62919 | 200 application/json |
| `ckan-gsq.json` | https://www.data.qld.gov.au/api/3/action/package_show?id=ds000005 | 200 application/json |
| `jamstec-cruises.json` | https://www.jamstec.go.jp/obsmcs_db/e/survey/db/list_cruise.json | 200 application/json |
| `kigam-metadata.json` | https://data.kigam.re.kr/search/metadata?subject=OilUndersea | 200 application/json |
| `danegovpl-cbdg.json` | https://api.dane.gov.pl/1.4/datasets/677/resources | 200 application/vnd.api+json |
| `arcgis-featureserver-sgc.html` | https://services1.arcgis.com/Og2nrTKe5bptW02d/arcgis/rest/services/Banco_de_Informaci%C3%B3n_Petrolera_Pozos/FeatureServer/0 | 200 text/html |
| `arcgis-featureserver-ut.html` | https://services.arcgis.com/ZzrwjTRez6FJiOq4/arcgis/rest/services/viewAGRC_WellData_Surf/FeatureServer/0 | 200 text/html |
| `github-repo-csp11.html` | https://github.com/Simulation-Benchmarks/11thSPE-CSP | 200 text/html |
| `datacite-egg.json` | https://api.datacite.org/dois/10.4121/uuid:916c86cd-3558-4672-829a-105c62985ab2 | 200 application/json |
| `ckan-wa-demirs.json` | https://catalogue.data.wa.gov.au/api/3/action/package_show?id=wa-onshore-petroleum-wells-dmirs-025 | 200 application/json |
| `zenodo-record.json` | https://zenodo.org/api/records/14534965 (cited by an IODP record's notes) | 200 application/json |
| `dataverse-geus.json` | https://dataverse.geus.dk/api/datasets/:persistentId/?persistentId=doi:10.22008/FK2/44TKZR (cited by a GEUS record) | 200 application/json |
| `github-release-cli.json` | https://api.github.com/repos/cli/cli/releases/latest (a release with asset digests; no catalogue record uses this shape yet) | 200 application/json |
| `figshare-article.json` | **synthetic**: api.figshare.com answered 403 to the verifier's User-Agent on 23 Oct 2026; written from figshare's documented v2 article shape (`files[].download_url`, `supplied_md5`, `computed_md5`, `is_link_only`) | — |

The hosts of Sodir, NLOG, NOPIMS (S3) and OPM (GitHub contents) were not fetched: their readers and
samples predate E23 and are covered by the E02 and E07 tests.
