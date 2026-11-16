# End-to-End ELT Pipeline: Weather API → Snowflake → dbt

## Project Overview

This project demonstrates an end-to-end ELT (Extract, Load, Transform) data engineering pipeline built using a REST API, Python, Snowflake, dbt Cloud, and GitHub.

A Python script extracts daily weather data for 10 major Indian cities from the Open-Meteo API and loads the raw JSON, unchanged, into a Snowflake RAW table. dbt then transforms the raw data inside Snowflake: it flattens the semi-structured JSON, removes duplicates, runs data quality tests, and builds a dimension table and fact tables for analytics.

## Architecture

```
                    ┌──────────────────────┐
                    │   Open-Meteo API     │
                    │                      │
                    │  • Daily Weather     │
                    │  • 10 Indian Cities  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Python (ingest.py) │
                    │                      │
                    │  • API Requests      │
                    │  • Load Raw JSON     │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌──────────────────────────────┐
              │          Snowflake           │
              │                              │
              │   RAW.WEATHER_RAW            │
              │   (raw JSON in VARIANT)      │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │          dbt Cloud           │
              │                              │
              │   ┌──────────────────────┐   │
              │   │ Staging              │   │
              │   │ • Flatten JSON       │   │
              │   │ • Remove Duplicates  │   │
              │   └──────────────────────┘   │
              │   ┌──────────────────────┐   │
              │   │ Marts                │   │
              │   │ • Dimension Table    │   │
              │   │ • Fact Tables        │   │
              │   └──────────────────────┘   │
              │   ┌──────────────────────┐   │
              │   │ Data Quality Tests   │   │
              │   └──────────────────────┘   │
              └──────────────┬───────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
          ┌─────────────────┐  ┌─────────────────┐
          │ FCT_DAILY       │  │ FCT_MONTHLY     │
          │ _WEATHER        │  │ _SUMMARY        │
          └─────────────────┘  └─────────────────┘
```

## 🛠️ Technologies Used

- Python
- REST API (Open-Meteo)
- Snowflake
- dbt Cloud
- SQL
- GitHub
- JSON / VARIANT (semi-structured data)

## Snowflake Infrastructure

The Snowflake environment is created with `sql/setup.sql`, which sets up:

- A virtual warehouse `WEATHER_WH` (X-Small, auto-suspend after 60 seconds)
- A database `WEATHER_DB`
- Schemas `RAW`, `STAGING` and `MARTS`
- The landing table `RAW.WEATHER_RAW`

## 🗂️ Project Structure

```
snowflake-dbt-weather-pipeline/
│
├── ingest/
│   └── ingest.py
│       └── Extracts weather data from the API and loads raw JSON into Snowflake
│
├── sql/
│   └── setup.sql
│       └── Creates the warehouse, database, schemas and raw table
│
├── models/
│   ├── schema.yml
│   │   └── Data quality tests
│   │
│   ├── staging/
│   │   ├── sources.yml
│   │   │   └── Declares the raw source table
│   │   └── stg_weather.sql
│   │       └── Flattens JSON and removes duplicates
│   │
│   └── marts/
│       ├── dim_city.sql
│       │   └── City dimension table
│       ├── fct_daily_weather.sql
│       │   └── Daily weather fact table
│       └── fct_monthly_summary.sql
│           └── Monthly weather summary
│
├── images/
│   └── fct_daily_weather.png
│
├── dbt_project.yml
└── README.md
```

## Data Architecture

The project follows a simple Raw → Staging → Marts layered design.

### 🥉 Raw Layer: Untouched Source Data

The raw layer stores the API response exactly as received, as JSON in a `VARIANT` column.

```
WEATHER_DB.RAW.WEATHER_RAW
```

Columns: `CITY`, `LATITUDE`, `LONGITUDE`, `PAYLOAD` (JSON), `SOURCE_URL`, `LOADED_AT`

### 🥈 Staging Layer: Cleaned Data

The staging layer converts the raw JSON into clean, typed rows. It is built as a **view**.

```
stg_weather
```

### 🥇 Marts Layer: Analytics-Ready Tables

The marts layer contains business-ready tables. They are built as **tables**.

```
dim_city
fct_daily_weather
fct_monthly_summary
```

## Pipeline 1: Extract and Load (Python)

### 1️⃣ Extract

The script calls the Open-Meteo API for each of the 10 cities using their latitude and longitude.

```
https://api.open-meteo.com/v1/forecast
```

Each request asks for:

- Maximum temperature
- Minimum temperature
- Precipitation (rainfall)
- Maximum wind speed
- The past 7 days plus today

### 2️⃣ Load

The full JSON response for each city is stored, unchanged, in `RAW.WEATHER_RAW` using `PARSE_JSON`. No cleaning happens in Python. This is the ELT approach: load first, transform later inside the warehouse.

The Snowflake login is read from environment variables (`SF_ACCOUNT`, `SF_USER`, `SF_PASSWORD`), so no credentials are stored in the code.

## Pipeline 2: Transform (dbt)

### 1️⃣ Staging: `stg_weather`

- Reads the raw table using `source()`
- Uses `LATERAL FLATTEN` to turn the JSON arrays into one row per city per day
- Casts values to proper data types (date, float)
- Removes duplicate records using `ROW_NUMBER()` and `QUALIFY`, keeping the latest load for each city and day

### 2️⃣ Marts

**`dim_city`**
One row per city with its latitude and longitude.

**`fct_daily_weather`**
One row per city per day containing:

- Maximum temperature
- Minimum temperature
- Average temperature
- Rainfall (mm)
- Wind speed (km/h)

**`fct_monthly_summary`**
One row per city per month containing:

- Average maximum temperature
- Hottest day
- Total rainfall

### 3️⃣ Data Quality Tests

| Model | Column | Test |
|---|---|---|
| stg_weather | city | not_null |
| stg_weather | weather_date | not_null |
| dim_city | city | not_null |
| dim_city | city | unique |

If a test fails, `dbt build` reports the error so bad data is caught before it reaches the marts.

## Output

Sample output of `FCT_DAILY_WEATHER` in Snowflake: 80 rows, 10 cities × 8 days.

![FCT_DAILY_WEATHER output](images/fct_daily_weather.png)

## Complete Data Flow

```
Open-Meteo API
     │
     ▼
Python (ingest.py)
     │
     ▼
Snowflake RAW
(raw JSON)
     │
     ▼
dbt Staging
(flatten + deduplicate)
     │
     ├───────────────────────┐
     ▼                       ▼
dim_city            fct_daily_weather
                             │
                             ▼
                    fct_monthly_summary
```

## How to Run the Project

### Prerequisites

- A Snowflake account
- A dbt Cloud account connected to this GitHub repository
- Python 3 with `requests` and `snowflake-connector-python` installed

### Step 1: Set Up Snowflake

Run `sql/setup.sql` in a Snowflake worksheet. This creates the warehouse, database, schemas and the raw table.

### Step 2: Set Environment Variables

```
SF_ACCOUNT=<your account identifier>
SF_USER=<your username>
SF_PASSWORD=<your password>
```

### Step 3: Run the Ingestion Script

```
pip install requests snowflake-connector-python
python ingest/ingest.py
```

This performs:

```
Call Weather API
        ↓
Load Raw JSON into Snowflake
```

### Step 4: Run dbt

In dbt Cloud, connect Snowflake with database `WEATHER_DB` and warehouse `WEATHER_WH`, then run:

```
dbt build
```

This performs:

```
Build Staging View
        ↓
Build Dimension and Fact Tables
        ↓
Run Data Quality Tests
```

### Step 5: Query the Results

```sql
SELECT * FROM WEATHER_DB.STAGING.FCT_DAILY_WEATHER ORDER BY CITY, WEATHER_DATE;
SELECT * FROM WEATHER_DB.STAGING.FCT_MONTHLY_SUMMARY;
```

## Author

Newlin Anto Marian C

Aspiring Data Engineer

Skills: Python | SQL | PySpark | Snowflake | dbt | Apache Spark | AWS | Linux

🔗 LinkedIn: www.linkedin.com/in/new-lin

