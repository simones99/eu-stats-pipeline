select
    code as geo,
    label as geo_label
from {{ source('raw', 'geo_codelist') }}
