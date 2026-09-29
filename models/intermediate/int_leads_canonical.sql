with leads as (

    select *
    from {{ ref('stg_leads') }}

),

canonical as (

    select
        lead_id,

        case
            when count(distinct email_normalized) = 1
            then min(email_normalized)
        end as email_normalized,

        case
            when count(distinct vertical) <= 1
            then min(vertical)
        end as vertical,

        case
            when count(distinct source) <= 1
            then min(source)
        end as source,

        case
            when count(distinct created_date) = 1
            then min(created_date)
        end as created_date,

        case
            when count(distinct region) <= 1
            then min(region)
        end as region,

        count(*) as source_record_count,

        count(*) > 1 as was_duplicated,

        count(distinct email_normalized) > 1 as has_email_conflict,
        count(distinct vertical) > 1 as has_vertical_conflict,
        count(distinct source) > 1 as has_source_conflict,
        count(distinct created_date) > 1 as has_created_date_conflict,
        count(distinct region) > 1 as has_region_conflict

    from leads

    group by lead_id

)

select
    *,

    (
        has_email_conflict
        or has_vertical_conflict
        or has_source_conflict
        or has_created_date_conflict
        or has_region_conflict
    ) as has_attribute_conflict

from canonical