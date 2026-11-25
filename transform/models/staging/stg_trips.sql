-- PyIceberg writes a new metadata file on every commit; job.sh passes the current one in
select
    vendor_id,
    pickup_at,
    dropoff_at,
    passenger_count,
    trip_distance,
    pickup_zone_id,
    dropoff_zone_id,
    payment_type,
    fare_amount,
    tip_amount,
    total_amount,
    coalesce(cbd_congestion_fee, 0) as cbd_congestion_fee,
    date_diff('second', pickup_at, dropoff_at) / 60.0 as duration_min
from iceberg_scan('{{ var("trips_metadata") }}')
where trip_distance > 0
  and total_amount > 0
  and dropoff_at > pickup_at
