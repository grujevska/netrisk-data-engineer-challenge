with conversions as (

    select *
    from {{ ref('stg_conversions') }}

),

ranked as (

    select
        *,
        row_number() over (
            partition by conversion_id
            order by conversion_id
        ) as duplicate_rank,

        count(*) over (
            partition by conversion_id
        ) as source_record_count

    from conversions

)

select
    * exclude (duplicate_rank),
    source_record_count > 1 as was_duplicated

from ranked

where duplicate_rank = 1