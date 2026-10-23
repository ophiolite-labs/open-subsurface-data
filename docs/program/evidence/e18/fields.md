# E18 lane open: date fields on the live registers (23 Oct 2026, from ophiolite-epic-01)

Requests: one `GetFeature` (`count=2..3`, all properties) and `DescribeFeatureType` per layer the
rules read, plus one NLOG filter `START_DATE_DRILLING < 1830-01-01`. Nothing else was fetched
before `osd verify --outlines sodir/factpages nlog/nlog`.

## Sodir FactMaps WFS (`FactMapsWGS84`, GeoJSON output)

| Layer (rule input) | Start | End | Type (DescribeFeatureType) | Form in the GeoJSON |
|---|---|---|---|---|
| `Wellbores__all` (wellbores) | `Entered_date` | `Completed_date` | `xsd:dateTime` | `2/15/1983`, `5/8/1983` |
| `Seismic_surveys__finished` (seismic-finished) | `Start_date` | `Completed_date` | `xsd:dateTime` | `5/1/2021 2:19:33 PM`, `6/3/2021 7:07:27 AM` |
| `Seismic_surveys__ongoing`, `__paused` | `Start_date` | `Completed_date` (null while ongoing) | `xsd:dateTime` | `8/15/2026 9:35:11 AM`, `null` |

- The GeoJSON writes dates month first: wellbore NPDID 2 has `Entered_date` `2/15/1983` and
  `Entry_day` 15, `Entry_month` 2, `Entry_year` 1983. No zone is stated; read as UTC (charter).
- E16 named `Entry_year` and `Entered_date`; `Completed_date` is the completion field. Planned
  dates (`Start_date___planned`, `Completed_date___planned`) are not used: they are not when the
  survey was shot.

## NLOG GDN WFS (`nlog`, `application/json`)

| Layer (rule input) | Start | End | Type | Form |
|---|---|---|---|---|
| `gdw_ng_wll_all_utm` (boreholes) | `START_DATE_DRILLING` | `END_DATE_DRILLING` | `xsd:date` | `1984-07-02`, `1984-09-19` |
| `gdw_ng_smc_grid_utm` (surveys-3d) | none | none | — | the layer's only date is `DATE_RELEASE` (`2018-02-01`), a release date |

- Stop rule: NLOG 3D surveys expose no acquisition date; their Items keep the collection period.
- `START_DATE_DRILLING < 1830-01-01`: SM-02, SM-08, SM-19, DB-092, MS-BTR at `1800-01-01`, each
  ending `1801-01-01`; DOM-MS-NE, DOM-MS-WL1 at `1828-01-01`, ending `1829-01-01`. The service
  marks none of them as unknown; both groups have the year-precision shape (1 January, end one year
  later). Not confirmed as a placeholder: NLOG `period_placeholders` is empty.
