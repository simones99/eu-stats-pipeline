select
    indicator_id,
    dataset_code,
    label,
    unit,
    valid_min,
    valid_max
from {{ source('raw', 'dataset_config') }}
