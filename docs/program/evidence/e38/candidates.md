# E38 candidates (24 Oct 2026, measured from ophiolite-epic-01, 03:13 to 03:24 UTC)

Every request sent with the verifier's product token. Counts are WFS 2.0.0 `resultType=hits`
`numberMatched` or OGC API Features `numberMatched` of the first items page. "Paging / sorting" are
the WFS capabilities constraints `ImplementsResultPaging` / `ImplementsSorting` (both GeoServer
`DefaultValue`), "page" is `CountDefault`. "Sort property" is the property named in
`verifier/samples.yaml` (`sort:`): WFS 2.0 sorts by a property, and `sortBy=@gml:id` answers
`InvalidParameterValue` (DOV, 03:15).

## WFS 2.0.0: records whose manifest_url is, or becomes, a GetFeature

| record | endpoint, typeName | robots | count | CRS | paging / sorting, page | JSON | sort property | revision signal | expected |
|---|---|---|---|---|---|---|---|---|---|
| dov/boringen-geothermie | www.dov.vlaanderen.be/geoserver/wfs, `geothermie:boringen_geothermie` | 200, only `User-agent: PetalBot` `Disallow: /` | 24,979 | EPSG:31370 | TRUE / TRUE, 10000 | application/json | `id` (string) | none (WFS 2.0 states none per feature type) | multi-page (5 pages of 5,000): must pass |
| dov/graviteit-data-punten | same, `gravimetrie:graviteit_data_punten` | as above | 16,915 | EPSG:31370 | as above | as above | `id` (integer) | none | multi-page (4 pages): must pass |
| dov/boringen | same, `dov-pub:Boringen` | as above | 188,580 | EPSG:31370 | as above | as above | `id` | none | above the cap: partial (the manifest's 1,000-feature GetFeature kept as a partial export) |
| dov/formele-stratigrafie | same, `interpretaties:formele_stratigrafie` | as above | 107,753 | EPSG:31370 | as above | as above | `Interpretatiefiche` (`sortBy=id` answers "Illegal property name: id") | none | above the cap: partial |
| gsnsw/drillholes-petroleum | public-gs.geoscience.nsw.gov.au/geoserver/ows, `drilling:drilling_drillholes_petroleum` | 404 (allow all) | 1,221 | EPSG:4326 | TRUE / TRUE, 1000000 | application/json | `gsnsw_drill_id` | none | one page: pass (existing WFS manifest, `file: true` today) |
| gsv/faults-latrobe-group-gippsland | opendata.maps.vic.gov.au/geoserver/wfs, `open-data-platform:faults_latrobe_gp` | 404 (allow all) | 47 | EPSG:7844 | TRUE / TRUE, 5000 | application/json | `id` (not unique: one page, so order is moot) | none | one page: pass (existing WFS manifest, `file: true` today) |
| ga/stratdat-biostratigraphy | services.ga.gov.au/gis/resfacs/ows, `resfacs:Biostratigraphy` | 403 (CloudFront "Request blocked": 4xx, allow all) | 50,128 | EPSG:4283 | TRUE / TRUE, 1000000 | application/json | `SAMPLE_ID` | none | above the cap by 128: partial |
| ga/resfacs-porosity-permeability | same, `resfacs:PorosityPermeability` (Porosity 140,100, Permeability 62,135) | as above | 164,799 | EPSG:4283 | as above | as above | `SAMPLE_ID` | none | above the cap: partial |
| wogcc/wyde-wells | dataexplorer.wogcc.wyo.gov/geoserver/wfs, `WY_SHPS:WELL` (77 types; `WellGasVertical` 15,329, `WellOilVertical` 48,332) | 404 (allow all) | 121,000 | EPSG:4269 | TRUE / TRUE, 1000000 | application/json | `PKey` (a sorted 2-feature page took 73 s) | none | above the cap: partial |

The record's layer is the one that is the record's dataset: WOGCC's `WELL` (all wells), not a
sub-layer chosen to fit the cap; RESFACS's combined `PorosityPermeability` layer.

## OGC API Features: fixture and regression evidence only

| record | collection | robots | numberMatched | next link | ids | why not a candidate |
|---|---|---|---|---|---|---|
| sgu/borrhal | api.sgu.se/oppnadata/borrhal/ogc/features/v1/collections/borrhal | 404 (allow all) | 36,672 | `startIndex=` (GeoServer) | `borrhal.395` (string) | the record's manifest is the SGU page listing `borrhal.zip` (L2 today): design 8, never replaced |
| bgs/single-onshore-borehole-index | ogcapi.bgs.ac.uk/collections/onshoreboreholeindex | 404 (allow all) | 1,358,946 | `offset=` (pygeoapi) | `1.0` (number) | ZIP kept (Dispositions); above the cap |
| sgu/brunnar, sgu/magnetfalt-detaljerad | api.sgu.se/oppnadata/{brunnar,geofysik-flyg-magnetfalt-detaljerad}/ogc/features/v1 | 404 | not read | | | downloadable ZIP manifests (L2 today) |

No record without a downloadable manifest names an OGC API Features collection (64 anonymous
records without `manifest_url` on main 8023654 searched for `collections`, `ogc`, `wfs`,
`geoserver`): the protocol has no eligible branch-dispatch candidate (inbox `e38.md` item 2).

## Neither protocol

usgs/namss (WMS only; `/namss/wfs` 404), liag/geotis (WMS), ecmc (Socrata page naming a ZIP).
