-- Plausibility (warning): year-on-year changes large enough to deserve a manual check.
-- Thresholds: population +/-5 %, GDP per inhabitant +/-25 %, unemployment +/-5 percentage points.
-- Rows flagged as a break in series are reported too, with the flag, so the reviewer can tell
-- an expected methodological break from a possible data error.
{{ config(severity = 'warn') }}

with series as (
    select
        indicator_id,
        geo,
        time_period,
        obs_value,
        obs_flag,
        lag(obs_value) over (partition by indicator_id, geo order by time_period) as previous_value,
        lag(time_period) over (partition by indicator_id, geo order by time_period) as previous_period
    from {{ ref('fct_indicator_values') }}
    where obs_value is not null
)

select
    indicator_id,
    geo,
    previous_period,
    time_period,
    previous_value,
    obs_value,
    obs_flag,
    case
        when indicator_id = 'unemployment_rate' then obs_value - previous_value
        else obs_value / previous_value - 1
    end as change
from series
where previous_value is not null
  and time_period = previous_period + 1
  and (
      (indicator_id = 'population' and abs(obs_value / previous_value - 1) > 0.05)
      or (indicator_id = 'gdp_pps_per_inhabitant' and abs(obs_value / previous_value - 1) > 0.25)
      or (indicator_id = 'unemployment_rate' and abs(obs_value - previous_value) > 5)
  )
