select
    city,
    date_trunc('month', weather_date) as month_start,
    round(avg(temp_max_c), 2) as avg_max_temp_c,
    max(temp_max_c) as hottest_day_c,
    round(sum(rain_mm), 2) as total_rain_mm
from {{ ref('fct_daily_weather') }}
group by city, date_trunc('month', weather_date)