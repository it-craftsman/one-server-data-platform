select
    date_trunc('month', pickup_at) as month,
    count(*) as trips,
    sum(total_amount) as revenue,
    avg(total_amount) as avg_ticket,
    avg(case when payment_type = 1 then 1 else 0 end) as card_share,
    sum(cbd_congestion_fee) as cbd_fees
from {{ ref('stg_trips') }}
group by all
order by month
