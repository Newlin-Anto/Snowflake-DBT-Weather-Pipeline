-- Take the raw table
with raw as (
    select * from {{ source('raw', 'weather_raw') }}
),

-- Turn the JSON lists into one row per city per day
flattened as (
    select
        raw.city,
        raw.latitude,
        raw.longitude,
        raw.loaded_at,
        f.value::date as weather_date,
        raw.payload:daily:temperature_2m_max[f.index]::float as temp_max_c,
        raw.payload:daily:temperature_2m_min[f.index]::float as temp_min_c,
        raw.payload:daily:precipitation_sum[f.index]::float as rain_mm,
        raw.payload:daily:wind_speed_10m_max[f.index]::float as wind_kmh
    from raw,
        lateral flatten(input => raw.payload:daily:time) as f
)

-- If a city and day appear twice, keep only the newest one
select *
from flattened
qualify row_number() over (
    partition by city, weather_date
    order by loaded_at desc
) = 1