-- One row per indicator, geo and year, typed from the raw SDMX-CSV columns.
-- Combined Eurostat flags (e.g. "bep") are split into one boolean per component.
{% for indicator in var('indicators') %}
select
    '{{ indicator }}' as indicator_id,
    split_part(DATAFLOW, '(', 1) as dataflow,
    geo,
    cast(TIME_PERIOD as integer) as time_period,
    try_cast(OBS_VALUE as double) as obs_value,
    nullif(OBS_FLAG, '') as obs_flag,
    coalesce(OBS_FLAG, '') like '%b%' as has_break,
    coalesce(OBS_FLAG, '') like '%e%' as is_estimated,
    coalesce(OBS_FLAG, '') like '%p%' as is_provisional,
    coalesce(OBS_FLAG, '') like '%u%' as is_low_reliability,
    strptime("LAST UPDATE", '%d/%m/%y %H:%M:%S') as source_last_update
from {{ source('raw', indicator) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}
