select
    indicator_id,
    dataset_code,
    label,
    unit,
    valid_min,
    valid_max,
    on_dashboard,
    map_midpoint,
    map_log_scale
from {{ source('raw', 'dataset_config') }}
