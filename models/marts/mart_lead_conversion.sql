with leads as (

    select *
    from {{ ref('int_leads_canonical') }}

),

conversions as (

    select *
    from {{ ref('int_conversion_attribution') }}

    where matched_lead_id is not null

),

aggregated_conversions as (

    select
        matched_lead_id,

        count(*) filter (
            where status in ('active', 'cancelled')
        ) as conversion_count,

        count(*) filter (
            where status = 'active'
        ) as active_contract_count,

        count(*) filter (
            where status = 'pending'
        ) as pending_contract_count,

        sum(premium) filter (
            where status = 'active'
        ) as total_active_premium,

        min(signed_date) filter (
            where status in ('active', 'cancelled')
        ) as first_conversion_date

    from conversions

    group by matched_lead_id

)

select
    l.lead_id,
    l.email_normalized as customer_id,
    l.vertical,
    l.source,
    l.region,
    l.created_date,

    coalesce(c.conversion_count, 0) as conversion_count,

    coalesce(c.conversion_count, 0) > 0 as has_conversion,

    coalesce(c.active_contract_count, 0) as active_contract_count,
    coalesce(c.pending_contract_count, 0) as pending_contract_count,
    coalesce(c.total_active_premium, 0) as total_active_premium,

    c.first_conversion_date,

    l.was_duplicated as lead_was_duplicated,
    l.has_attribute_conflict as lead_has_attribute_conflict

from leads l

left join aggregated_conversions c
    on l.lead_id = c.matched_lead_id