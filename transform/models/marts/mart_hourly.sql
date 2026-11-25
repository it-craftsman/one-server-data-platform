select
    isodow(pickup_at) as weekday,
    hour(pickup_at) as hour,
    count(*) as trips,
    median(duration_min) as median_duration_min
from {{ ref('stg_trips') }}
group by all
