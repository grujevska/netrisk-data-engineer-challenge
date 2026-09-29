with source as (

    select *
    from {{ ref('conversions') }}

),

cleaned as (

    select
        conversion_id,
        lead_id,

        email as email_raw,
        lower(trim(email)) as email_normalized,

        premium as premium_raw,

        try_cast(
            replace(trim(premium), ',', '.')
            as double
        ) as premium,

        signed_date as signed_date_raw,

        cast(
            coalesce(
                try_strptime(signed_date, '%Y-%m-%d'),
                try_strptime(signed_date, '%d.%m.%Y'),
                try_strptime(signed_date, '%m/%d/%Y')
            )
            as date
        ) as signed_date,

        status as status_raw,
        lower(trim(status)) as status

    from source

)

select *
from cleaned