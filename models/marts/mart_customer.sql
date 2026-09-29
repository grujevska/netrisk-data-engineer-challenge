with leads as (

    select *
    from {{ ref('int_leads_canonical') }}

),

conversions as (

    select *
    from {{ ref('int_conversions_deduplicated') }}

),

lead_summary as (

    select
        email_normalized as customer_id,

        count(*) as lead_count,

        min(created_date) as first_lead_date,
        max(created_date) as latest_lead_date

    from leads

    group by email_normalized

),

conversion_summary as (

    select
        email_normalized as customer_id,

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
        ) as total_active_premium

    from conversions

    group by email_normalized

)

select
    coalesce(l.customer_id, c.customer_id) as customer_id,

    coalesce(l.lead_count, 0) as lead_count,

    coalesce(c.conversion_count, 0) as conversion_count,

    coalesce(c.active_contract_count, 0) as active_contract_count,

    coalesce(c.pending_contract_count, 0) as pending_contract_count,

    case
        when coalesce(c.active_contract_count, 0) = 0 then 0
        else c.total_active_premium
    end as total_active_premium,

    coalesce(c.active_contract_count, 0) > 0 as has_active_contract,

    l.first_lead_date,
    l.latest_lead_date

from lead_summary l

full outer join conversion_summary c
    on l.customer_id = c.customer_id