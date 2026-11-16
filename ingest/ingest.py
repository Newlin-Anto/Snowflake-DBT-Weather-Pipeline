import os
import json
import requests
import snowflake.connector

cities = [
    ("Bengaluru", 12.97, 77.59),
    ("Chennai", 13.08, 80.27),
    ("Mumbai", 19.08, 72.88),
    ("Delhi", 28.61, 77.21),
    ("Kolkata", 22.57, 88.36),
    ("Hyderabad", 17.38, 78.48),
    ("Pune", 18.52, 73.86),
    ("Ahmedabad", 23.02, 72.57),
    ("Jaipur", 26.91, 75.79),
    ("Kochi", 9.93, 76.27),
]

url = "https://api.open-meteo.com/v1/forecast"

conn = snowflake.connector.connect(
    account=os.environ["SF_ACCOUNT"],#use snowflake Account identifier
    user=os.environ["SF_USER"],#use snowflake username
    password=os.environ["SF_PASSWORD"],#use snowflake password
    role="ACCOUNTADMIN",
    warehouse="WEATHER_WH",
    database="WEATHER_DB",
    schema="RAW",
)
cursor = conn.cursor()

for city, lat, lon in cities:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "Asia/Kolkata",
        "past_days": 7,
        "forecast_days": 1,
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    cursor.execute(
        "INSERT INTO WEATHER_RAW (CITY, LATITUDE, LONGITUDE, PAYLOAD, SOURCE_URL) "
        "SELECT %s, %s, %s, PARSE_JSON(%s), %s",
        (city, lat, lon, json.dumps(data), response.url),
    )
    print("Saved", city)

conn.commit()
conn.close()
print("Done!")