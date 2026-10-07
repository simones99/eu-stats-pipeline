-- Every geographic unit that appears in the data, classified by level.
with codes as (
    select distinct geo from {{ ref('stg_eurostat__observations') }}
),

classified as (
    select
        geo,
        case
            when geo = 'EU27_2020' then 'eu_aggregate'
            when length(geo) = 2 then 'country'
            when length(geo) = 3 then 'nuts1'
            when length(geo) = 4 then 'nuts2'
            else 'other_aggregate'
        end as geo_level
    from codes
)

select
    c.geo,
    g.geo_label,
    c.geo_level,
    case when c.geo_level in ('country', 'nuts1', 'nuts2') then left(c.geo, 2) end as country_code,
    eu.country_code is not null as is_eu27,
    -- Extra-regio (e.g. ITZZ) and "not regionalised" (e.g. FRXX) units hold data
    -- that cannot be assigned to a territorial region.
    c.geo_level in ('nuts1', 'nuts2') and (c.geo like '__Z%' or c.geo like '__X%')
        as is_non_regional,
    n.nuts_id is not null as in_gisco_nuts2024
from classified as c
left join {{ ref('stg_eurostat__geo') }} as g on g.geo = c.geo
left join {{ ref('eu27_countries') }} as eu
    on eu.country_code = case when c.geo_level <> 'eu_aggregate' then left(c.geo, 2) end
left join {{ ref('stg_gisco__nuts2') }} as n on n.nuts_id = c.geo
