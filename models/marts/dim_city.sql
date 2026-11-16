select
    city,
    max(latitude) as latitude,
    max(longitude) as longitude
from {{ ref('stg_weather') }}
group by city