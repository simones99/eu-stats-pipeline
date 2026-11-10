# Methodology note

## Scope

Five annual regional indicators for the EU27 aggregate, the 27 Member States and their NUTS 1 and NUTS 2 regions, from reference year 2015:

| Indicator | Eurostat dataset | SDMX series key | Unit | On the dashboard |
|---|---|---|---|---|
| GDP per inhabitant | `nama_10r_2gdp` | `A.PPS_EU27_2020_HAB.` | PPS (EU27 from 2020) per inhabitant | no |
| GDP per inhabitant, EU27 = 100 | `nama_10r_2gdp` | `A.PPS_HAB_EU27_2020.` | PPS per inhabitant, % of the EU27 average | yes |
| Population on 1 January | `demo_r_d2jan` | `A.NR.T.TOTAL.` | Persons | no |
| Population density | `demo_r_d3dens` | `A.PER_KM2.` | Persons per km² | yes |
| Unemployment rate, 15–74 years | `lfst_r_lfu3rt` | `A.TOTAL.T.Y15-74.PC.` | % of labour force | yes |

The list lives in `config/datasets.yml`. Adding an indicator means adding an entry there and its name to the `indicators` variable in `dbt/dbt_project.yml`.

The index (EU27 = 100) and the density are the series Eurostat publishes, not values recomputed here. The dashboard shows them instead of GDP in PPS and absolute population, because both compare regions of different size and price level directly. The two absolute series stay in the pipeline: they appear in the quality report, and the population feeds the regional-to-national coherence check.

## Processing steps

1. **Ingestion.** Data come from the Eurostat SDMX 2.1 REST API in SDMX-CSV format. The GEO and OBS_FLAG codelists come as SDMX-ML. NUTS 2024 level-2 boundaries come from GISCO. Each file is recorded in `data/raw/manifest.json` with its URL, retrieval time, SHA-256 checksum and row count.
2. **Raw layer.** Files are loaded into DuckDB unchanged, every column as text (`raw` schema).
3. **Staging.** dbt views type the columns, parse Eurostat's last-update timestamp and split combined status flags (for example `bep`) into separate booleans: break, estimated, provisional and low reliability.
4. **Marts.**
   - `dim_geo` classifies each code by level. It marks units that are not territorial regions: extra-regio codes ending in `Z`/`ZZ`, and "not regionalised" codes ending in `X`/`XX`, which Eurostat publishes with value 0. It also records whether a code exists in NUTS 2024.
   - `fct_indicator_values` keeps the EU27 scope and drops non-regional units and NUTS 3 regions.
   - `mart_nuts2_latest` keeps the latest value per NUTS 2024 region, for mapping.
5. **Validation.** dbt tests run on every build. Errors stop the pipeline. Warnings go into the quality report for manual review.
6. **Outputs.**
   - `docs/quality-report.md`, structured by the ESS quality dimensions.
   - `docs/data-dictionary.md`, generated from the dbt model and column descriptions.
   - `site/index.html`, a static dashboard.

## Validation rules

| Rule | Type | Severity |
|---|---|---|
| One row per indicator, geo and year | Structure | error |
| Codes exist in the Eurostat GEO and OBS_FLAG codelists | Conformity | error |
| Value within the plausibility range set per indicator | Plausibility | error |
| Sum of NUTS 2024 level-2 populations equals the national total (±0.5 %) | Coherence | error |
| Year-on-year change above review threshold (population ±5 %, GDP per inhabitant ±25 %, unemployment ±5 pp) | Plausibility | warning |
| NUTS 2 codes with recent data but no NUTS 2024 geometry | Comparability | warning |

## Findings worth knowing

- **Mixed NUTS versions.** The regional datasets carry codes from more than one NUTS version for the same country. For example, the Netherlands and Portugal have NUTS 2021 regions (`NL33`, `PT17`) next to their NUTS 2024 successors. Summing every 4-character code double counts the population, by up to 56 % for Portugal. The coherence check therefore sums NUTS 2024 regions only. The older codes stay in the fact table, flagged by `in_gisco_nuts2024 = false`.
- **Non-regional units.** `FRXX` and `HUXX` ("not regionalised") hold zeros. They are not regions and are excluded, like extra-regio units.
- **NUTS 3 rows.** The density dataset (`demo_r_d3dens`) also delivers NUTS 3 regions, and the SDMX key cannot select a NUTS level. `dim_geo` classifies them as `nuts3` and the fact table leaves them out, so the scope stays the same for every indicator.
- **Series breaks.** Poland's regional population shows changes of about 5 % between 2020 and 2021, flagged `b` by Eurostat. This is consistent with the 2021 census revision. These rows appear in the plausibility review with their flag, so an expected break can be told apart from a possible error.

## Limitations

- The density map uses a logarithmic colour scale, because a few city regions are more than a hundred times denser than the least populated ones.
- The year-on-year review covers population, GDP per inhabitant in PPS and unemployment. The index and the density have no thresholds of their own.
- Outermost regions are in the data but outside the map frame.
- The thresholds of the plausibility review are judgement calls, not official Eurostat validation rules.

## Sources and reuse

- Eurostat data: © European Union, reused under the [Eurostat copyright notice](https://ec.europa.eu/eurostat/about-us/policies/copyright) (Commission Decision 2011/833/EU).
- NUTS boundaries: © EuroGeographics for the administrative boundaries, distributed by [GISCO](https://ec.europa.eu/eurostat/web/gisco).
- The sample files in `tests/fixtures/` are an unmodified subset of the same public data (Italy, the Netherlands, Portugal and Poland).
