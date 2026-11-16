select
    city,
    weather_date,
    temp_max_c,
    temp_min_c,
    round((temp_max_c + temp_min_c) / 2, 2) as temp_avg_c,
    rain_mm,
    wind_kmh
from {{ ref('stg_weather') }}