-- Comparability (warning): NUTS 2 regions with recent data that have no NUTS 2024
-- geometry. These are usually codes from an older NUTS version and cannot be mapped.
{{ config(severity = 'warn') }}

select distinct
    f.indicator_id,
    f.geo,
    max(f.time_period) as latest_period
from {{ ref('fct_indicator_values') }} as f
inner join {{ ref('dim_geo') }} as d on d.geo = f.geo
where f.geo_level = 'nuts2'
  and not d.in_gisco_nuts2024
  and f.obs_value is not null
group by f.indicator_id, f.geo
having max(f.time_period) >= (select max(time_period) - 2 from {{ ref('fct_indicator_values') }})
