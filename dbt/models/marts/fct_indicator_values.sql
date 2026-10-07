-- Observations in scope: the EU27 aggregate, the 27 Member States and their regions.
select
    o.indicator_id,
    o.geo,
    d.geo_level,
    d.country_code,
    d.in_gisco_nuts2024,
    o.time_period,
    o.obs_value,
    o.obs_flag,
    f.flag_meaning,
    o.has_break,
    o.is_estimated,
    o.is_provisional,
    o.is_low_reliability,
    o.source_last_update
from {{ ref('stg_eurostat__observations') }} as o
inner join {{ ref('dim_geo') }} as d on d.geo = o.geo
left join {{ ref('stg_eurostat__obs_flags') }} as f on f.obs_flag = o.obs_flag
where (d.is_eu27 or d.geo_level = 'eu_aggregate')
  and not d.is_non_regional
