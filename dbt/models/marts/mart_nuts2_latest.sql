-- Latest available value of each indicator for each NUTS 2024 region (dashboard input).
-- Codes from older NUTS versions are left out because they cannot be mapped.
with ranked as (
    select
        indicator_id,
        geo,
        country_code,
        time_period,
        obs_value,
        obs_flag,
        row_number() over (
            partition by indicator_id, geo order by time_period desc
        ) as recency_rank
    from {{ ref('fct_indicator_values') }}
    where geo_level = 'nuts2'
      and in_gisco_nuts2024
      and obs_value is not null
)

select
    r.indicator_id,
    r.geo,
    d.geo_label,
    r.country_code,
    r.time_period,
    r.obs_value,
    r.obs_flag
from ranked as r
inner join {{ ref('dim_geo') }} as d on d.geo = r.geo
where r.recency_rank = 1
