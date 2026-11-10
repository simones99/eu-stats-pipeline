# Data quality report

Generated 2026-11-10 17:16 UTC by `eustats report`. Structure follows the quality dimensions of the European Statistical System (ESS).

**Validation summary:** 29 checks, 0 failed, 2 warnings for manual review.

## Sources and lineage

Every raw file is recorded in `data/raw/manifest.json` with its source URL, retrieval time and SHA-256 checksum.

| file | dataset_code | rows | sha256_prefix | retrieved_at | offline_fixture |
|---|---|---|---|---|---|
| gdp_pps_pct_eu27.csv | [nama_10r_2gdp](https://ec.europa.eu/eurostat/databrowser/view/nama_10r_2gdp/default/table?lang=en) | 4256 | 436ffe1c2365 | 2026-11-10T17:16:04+00:00 | False |
| gdp_pps_per_inhabitant.csv | [nama_10r_2gdp](https://ec.europa.eu/eurostat/databrowser/view/nama_10r_2gdp/default/table?lang=en) | 4256 | da5b441cd694 | 2026-11-10T17:16:04+00:00 | False |
| geo_codelist.csv | ESTAT:GEO | 4292 | cf6fa01431eb | 2026-11-10T17:16:04+00:00 | False |
| nuts2_2024.geojson | GISCO:NUTS_2024_LEVL_2 |  | 33124a7520d3 | 2026-11-10T17:16:04+00:00 | False |
| obs_flag_codelist.csv | ESTAT:OBS_FLAG | 42 | beea4f08234d | 2026-11-10T17:16:04+00:00 | False |
| population.csv | [demo_r_d2jan](https://ec.europa.eu/eurostat/databrowser/view/demo_r_d2jan/default/table?lang=en) | 5257 | 1374c2c41912 | 2026-11-10T17:16:04+00:00 | False |
| population_density.csv | [demo_r_d3dens](https://ec.europa.eu/eurostat/databrowser/view/demo_r_d3dens/default/table?lang=en) | 18346 | b460d8406cc9 | 2026-11-10T17:16:04+00:00 | False |
| unemployment_rate.csv | [lfst_r_lfu3rt](https://ec.europa.eu/eurostat/databrowser/view/lfst_r_lfu3rt/default/table?lang=en) | 5055 | 8c2ebfedb85c | 2026-11-10T17:16:04+00:00 | False |

## 1. Relevance

Indicators, coverage of the EU27 Member States and NUTS 2024 level-2 regions.

| indicator_id | dataset_code | label | unit | first_year | last_year | countries | nuts2_regions |
|---|---|---|---|---|---|---|---|
| gdp_pps_pct_eu27 | nama_10r_2gdp | GDP per inhabitant, EU27 = 100 | PPS per inhabitant, % of the EU27 average | 2015 | 2024 | 27 | 244 |
| gdp_pps_per_inhabitant | nama_10r_2gdp | GDP per inhabitant | PPS (EU27 from 2020) per inhabitant | 2015 | 2024 | 27 | 244 |
| population | demo_r_d2jan | Population on 1 January | Persons | 2015 | 2025 | 27 | 244 |
| population_density | demo_r_d3dens | Population density | Persons per km² | 2015 | 2024 | 27 | 242 |
| unemployment_rate | lfst_r_lfu3rt | Unemployment rate, 15-74 years | Percentage of labour force | 2015 | 2025 | 27 | 244 |

## 2. Accuracy and reliability

Share of observations by Eurostat status flag (combined flags count for each component).

| indicator_id | observations | pct_missing | pct_estimated | pct_provisional | pct_low_reliability | pct_series_break |
|---|---|---|---|---|---|---|
| gdp_pps_pct_eu27 | 3640 | 0.0 | 1.0 | 18.1 | 0.0 | 1.5 |
| gdp_pps_per_inhabitant | 3640 | 0.0 | 1.0 | 18.1 | 0.0 | 1.5 |
| population | 4051 | 0.0 | 3.4 | 4.5 | 0.0 | 2.4 |
| population_density | 3602 | 0.0 | 3.6 | 6.3 | 0.0 | 12.6 |
| unemployment_rate | 3991 | 1.2 | 0.0 | 0.0 | 5.1 | 15.6 |

Completeness of the latest year with regional data, against all NUTS 2024 level-2 regions of the EU27:

| indicator_id | latest_year | regions_with_value | eu_nuts2_regions | pct_complete |
|---|---|---|---|---|
| gdp_pps_pct_eu27 | 2024 | 244 | 244 | 100.0 |
| gdp_pps_per_inhabitant | 2024 | 244 | 244 | 100.0 |
| population | 2025 | 244 | 244 | 100.0 |
| population_density | 2024 | 242 | 244 | 99.2 |
| unemployment_rate | 2025 | 241 | 244 | 98.8 |

Validation checks (dbt tests):

| check | status | rows_flagged |
|---|---|---|
| assert_no_extreme_year_on_year_changes | warn | 21 |
| assert_nuts2_codes_in_gisco_2024 | warn | 5 |
| accepted_values_dim_geo_geo_level__eu_aggregate__country__nuts1__nuts2__nuts3__other_aggregate | pass | 0 |
| assert_regional_population_matches_national | pass | 0 |
| not_null_dim_geo_geo | pass | 0 |
| not_null_fct_indicator_values_geo | pass | 0 |
| not_null_fct_indicator_values_indicator_id | pass | 0 |
| not_null_stg_config__indicators_indicator_id | pass | 0 |
| not_null_stg_config__indicators_map_log_scale | pass | 0 |
| not_null_stg_config__indicators_on_dashboard | pass | 0 |
| not_null_stg_eurostat__geo_geo | pass | 0 |
| not_null_stg_eurostat__obs_flags_obs_flag | pass | 0 |
| not_null_stg_eurostat__observations_geo | pass | 0 |
| not_null_stg_eurostat__observations_indicator_id | pass | 0 |
| not_null_stg_eurostat__observations_time_period | pass | 0 |
| not_null_stg_gisco__nuts2_nuts_id | pass | 0 |
| relationships_fct_indicator_values_geo__geo__ref_dim_geo_ | pass | 0 |
| relationships_fct_indicator_values_indicator_id__indicator_id__ref_stg_config__indicators_ | pass | 0 |
| relationships_stg_eurostat__observations_geo__geo__ref_stg_eurostat__geo_ | pass | 0 |
| relationships_stg_eurostat__observations_obs_flag__obs_flag__ref_stg_eurostat__obs_flags_ | pass | 0 |
| unique_combination_of_columns_fct_indicator_values_indicator_id__geo__time_period | pass | 0 |
| unique_combination_of_columns_mart_nuts2_latest_indicator_id__geo | pass | 0 |
| unique_combination_of_columns_stg_eurostat__observations_indicator_id__geo__time_period | pass | 0 |
| unique_dim_geo_geo | pass | 0 |
| unique_stg_config__indicators_indicator_id | pass | 0 |
| unique_stg_eurostat__geo_geo | pass | 0 |
| unique_stg_eurostat__obs_flags_obs_flag | pass | 0 |
| unique_stg_gisco__nuts2_nuts_id | pass | 0 |
| value_in_configured_range_fct_indicator_values_obs_value | pass | 0 |

## 3. Timeliness and punctuality

| indicator_id | latest_reference_year | eurostat_last_update | years_since_reference |
|---|---|---|---|
| gdp_pps_pct_eu27 | 2024 | 2026-02-10 | 2 |
| gdp_pps_per_inhabitant | 2024 | 2026-02-10 | 2 |
| population | 2025 | 2026-08-28 | 1 |
| population_density | 2024 | 2026-02-25 | 2 |
| unemployment_rate | 2025 | 2026-10-30 | 1 |

Regional accounts and labour-market statistics are published with a lag of one to two years after the reference year.

## 4. Coherence and comparability

**Regional vs national population.** The sum of NUTS 2024 level-2 populations is checked against the national total for every country and year.

All countries and years are within tolerance.

**NUTS versions.** Regions with recent data but no NUTS 2024 geometry. These are codes from an older NUTS version: they are kept in `fct_indicator_values` but excluded from maps and from the coherence check, to avoid double counting.

| indicator_id | geo | latest_period |
|---|---|---|
| population | NL31 | 2023 |
| population | NL33 | 2023 |
| population | PT16 | 2023 |
| population | PT17 | 2023 |
| population | PT18 | 2023 |

## 5. Plausibility review

Year-on-year changes above the review thresholds (population ±5 %, GDP per inhabitant ±25 %, unemployment ±5 percentage points). A flag `b` marks a break in series declared by Eurostat; unflagged rows should be checked against the source metadata.

| indicator_id | geo | years | previous_value | obs_value | change | flag |
|---|---|---|---|---|---|---|
| gdp_pps_per_inhabitant | BG34 | 2020-2021 | 12300.0 | 15400.0 | +25.2 % |  |
| gdp_pps_per_inhabitant | BG34 | 2021-2022 | 15400.0 | 20800.0 | +35.1 % |  |
| gdp_pps_per_inhabitant | NL11 | 2021-2022 | 40100.0 | 50600.0 | +26.2 % |  |
| gdp_pps_per_inhabitant | PT15 | 2021-2022 | 23700.0 | 30200.0 | +27.4 % |  |
| population | CZ01 | 2022-2023 | 1275406.0 | 1357326.0 | +6.4 % |  |
| population | PL62 | 2020-2021 | 1399038.0 | 1322861.0 | -5.4 % | b |
| population | PL72 | 2020-2021 | 1218743.0 | 1154493.0 | -5.3 % | b |
| population | PL81 | 2020-2021 | 2088292.0 | 1981180.0 | -5.1 % | b |
| population | PL82 | 2020-2021 | 2084447.0 | 1979297.0 | -5.0 % | b |
| population | PL91 | 2020-2021 | 3082399.0 | 3242890.0 | +5.2 % | b |
| population | RO42 | 2021-2022 | 1758582.0 | 1669531.0 | -5.1 % | e |
| population | SK01 | 2021-2022 | 677024.0 | 723714.0 | +6.9 % |  |
| unemployment_rate | EL4 | 2021-2022 | 16.6 | 11.6 | -5.0 pp |  |
| unemployment_rate | EL42 | 2021-2022 | 18.8 | 10.7 | -8.1 pp |  |
| unemployment_rate | EL43 | 2019-2020 | 11.7 | 17.3 | +5.6 pp |  |
| unemployment_rate | EL62 | 2024-2025 | 16.2 | 9.0 | -7.2 pp |  |
| unemployment_rate | ES63 | 2017-2018 | 22.4 | 29.0 | +6.6 pp |  |
| unemployment_rate | ES63 | 2020-2021 | 24.5 | 30.8 | +6.3 pp | bd |
| unemployment_rate | ES7 | 2021-2022 | 23.5 | 17.6 | -5.9 pp | d |
| unemployment_rate | ES70 | 2021-2022 | 23.5 | 17.6 | -5.9 pp | d |
| unemployment_rate | FRY5 | 2017-2018 | 29.6 | 35.1 | +5.5 pp |  |

## 6. Accessibility and clarity

- Source tables: Eurostat data browser links in the lineage table above.
- Column definitions: [data dictionary](data-dictionary.md).
- Methods: [methodology note](methodology.md).
