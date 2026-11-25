select
    cast(t.pickup_at as date) as trip_date,
    z.borough,
    z.zone,
    count(*) as trips,
    sum(t.total_amount) as revenue,
    avg(t.trip_distance) as avg_distance_mi,
    avg(t.duration_min) as avg_duration_min,
    sum(t.tip_amount) / nullif(sum(t.fare_amount), 0) as tip_share
from {{ ref('stg_trips') }} t
left join {{ ref('dim_zones') }} z on t.pickup_zone_id = z.zone_id
group by all
