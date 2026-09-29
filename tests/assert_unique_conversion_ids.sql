select
    conversion_id,
    count(*) as record_count

from {{ ref('int_conversions_deduplicated') }}

group by conversion_id

having count(*) > 1