{#- Values outside the plausibility range set per indicator in config/datasets.yml. -#}
{% test value_in_configured_range(model, column_name) %}
select
    m.indicator_id,
    m.geo,
    m.time_period,
    m.{{ column_name }} as value,
    c.valid_min,
    c.valid_max
from {{ model }} as m
inner join {{ ref('stg_config__indicators') }} as c on c.indicator_id = m.indicator_id
where m.{{ column_name }} is not null
  and (m.{{ column_name }} < c.valid_min or m.{{ column_name }} > c.valid_max)
{% endtest %}
