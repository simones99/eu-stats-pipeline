-- Coherence: for each country and year, the sum of NUTS 2 populations must match
-- the national total within the configured tolerance. Only NUTS 2024 regions are summed:
-- the dataset also carries codes from older NUTS versions, which would double count.
-- Non-regional units (extra-regio, not regionalised) are already excluded upstream.
{{ config(severity = 'error') }}

with regional as (
    select country_code, time_period, sum(obs_value) as regional_sum, count(*) as n_regions
    from {{ ref('fct_indicator_values') }}
    where indicator_id = 'population' and geo_level = 'nuts2' and in_gisco_nuts2024
    group by country_code, time_period
),

national as (
    select geo as country_code, time_period, obs_value as national_total
    from {{ ref('fct_indicator_values') }}
    where indicator_id = 'population' and geo_level = 'country'
)

select
    n.country_code,
    n.time_period,
    n.national_total,
    r.regional_sum,
    r.n_regions,
    (r.regional_sum - n.national_total) / n.national_total as relative_gap
from national as n
inner join regional as r using (country_code, time_period)
where abs(r.regional_sum - n.national_total) / n.national_total
    > {{ var('population_coherence_tolerance') }}
