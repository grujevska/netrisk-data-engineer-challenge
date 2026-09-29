with leads as (

    select *
    from {{ ref('mart_lead_conversion') }}

)

select
    date_trunc('month', created_date) as lead_month,

    coalesce(vertical, 'unknown') as vertical,
    coalesce(source, 'unknown') as source,

    count(*) as lead_count,

    count(*) filter (
        where has_conversion
    ) as converted_lead_count,

    sum(conversion_count) as conversion_count,

    round(
        count(*) filter (where has_conversion) * 1.0
        / nullif(count(*), 0),
        4
    ) as conversion_rate

from leads

group by
    lead_month,
    coalesce(vertical, 'unknown'),
    coalesce(source, 'unknown')

order by
    lead_month,
    vertical,
    source