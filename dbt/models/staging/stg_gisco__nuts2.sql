select
    nuts_id,
    country_code,
    name_latn
from {{ source('raw', 'gisco_nuts2') }}
