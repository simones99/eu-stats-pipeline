select
    code as obs_flag,
    label as flag_meaning
from {{ source('raw', 'obs_flag_codelist') }}
