with source as (

    select *
    from {{ ref('leads') }}

),

cleaned as (

    select
        lead_id,

        email as email_raw,
        lower(trim(email)) as email_normalized,

        vertical as vertical_raw,
        lower(trim(vertical)) as vertical,

        source as source_raw,
        lower(trim(source)) as source,

        created_at as created_at_raw,

        cast(
            coalesce(
                try_strptime(created_at, '%Y-%m-%d'),
                try_strptime(created_at, '%d.%m.%Y'),
                try_strptime(created_at, '%m/%d/%Y')
            )
            as date
        ) as created_date,

        region as region_raw,
        trim(region) as region

    from source

)

select *
from cleaned