with conversions as (

    select *
    from {{ ref('int_conversions_deduplicated') }}

),

leads as (

    select *
    from {{ ref('int_leads_canonical') }}

),

direct_matches as (

    select
        c.conversion_id,
        l.lead_id as matched_lead_id,
        l.created_date as matched_lead_date

    from conversions c

    join leads l
        on c.lead_id = l.lead_id
        and c.email_normalized = l.email_normalized
        and l.created_date <= c.signed_date

),

fallback_candidates as (

    select
        c.conversion_id,
        l.lead_id as matched_lead_id,
        l.created_date as matched_lead_date,

        row_number() over (
            partition by c.conversion_id
            order by l.created_date desc, l.lead_id desc
        ) as fallback_rank

    from conversions c

    left join direct_matches d
        on c.conversion_id = d.conversion_id

    join leads l
        on c.email_normalized = l.email_normalized
        and l.created_date <= c.signed_date

    where d.conversion_id is null

),

fallback_matches as (

    select
        conversion_id,
        matched_lead_id,
        matched_lead_date

    from fallback_candidates

    where fallback_rank = 1

)

select
    c.*,

    coalesce(
        d.matched_lead_id,
        f.matched_lead_id
    ) as matched_lead_id,

    case
        when d.matched_lead_id is not null then 'lead_id'
        when f.matched_lead_id is not null then 'email_temporal'
        else 'unmatched'
    end as match_method,

    case
        when d.matched_lead_id is not null then 'high'
        when f.matched_lead_id is not null then 'medium'
        else 'none'
    end as match_quality,

    date_diff(
        'day',
        coalesce(d.matched_lead_date, f.matched_lead_date),
        c.signed_date
    ) as days_to_conversion

from conversions c

left join direct_matches d
    on c.conversion_id = d.conversion_id

left join fallback_matches f
    on c.conversion_id = f.conversion_id