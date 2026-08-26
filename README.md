# Mosamiyan — Modern Weather Platform

**Mosamiyan** (Phase 1 MVP) is a high-performance, containerized weather platform built with Python 3.12 (FastAPI), PostgreSQL 16, and Redis 7. It delivers real-time atmospheric metrics, 24-hour hourly scrubbing, 7-day extended outlooks, typeahead geocoding, multi-tier provider failover, and interactive lifestyle indices.

---

## 🌟 Key Features

- **Hyperlocal Weather & 9 Atmospheric Metrics**: Real-time Temperature, Feels Like, High/Low, Humidity & Dew Point, Wind Compass (Direction & Peak Gusts), Barometric Pressure & Trend, UV Index (WHO safety category), Visibility, Cloud Cover, and US Air Quality Index (AQI).
- **24-Hour Hourly Timeline**: Scrollable timeline with temperature trends, precipitation probability bars, and condition icons.
- **7-Day Extended Forecast**: Daily outlook with thermal boundaries and precipitation forecasts.
- **Multi-Tier Provider Failover**: Primary: **Open-Meteo** → Secondary: **OpenWeatherMap** → Tertiary: **WeatherAPI.com**.
- **Spatial Coordinate Caching**: Redis-backed cache with 2-decimal spatial normalization (`~1.1 km` equator precision) to eliminate GPS drift fragmentation.
- **Raw SQL Persistence**: High-speed, parameterised PostgreSQL queries via `asyncpg` connection pool (no ORM overhead).
- **Favorites & Search**: Predictive Omnibox geocoding search and saved locations quick-access bar (up to 5 cities for MVP).
- **Instant Unit Toggle**: Live switch between Metric (°C, km/h) and Imperial (°F, mph) without full page reload.

---

## 🏗️ Architecture Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic v2, `asyncpg`, `redis-py` (async), `httpx`
- **Frontend / Dashboard**: Modern responsive UI with HTML5, Tailwind CSS, FontAwesome, and Vanilla JS
- **Database**: PostgreSQL 16 (Docker)
- **Cache**: Redis 7 (Docker, In-Memory)
- **Containerization**: Multi-stage `Dockerfile` and `docker-compose.yml`

---

## 🚀 Quick Start & Container Setup

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- Python 3.12+ (optional for local non-container development)

### 2. Clone and Configure Environment
Copy the example environment file and adjust if necessary:
```bash
cp .env.example .env
```

Default configuration (`.env`):
```ini
APP_NAME=Mosamiyan Weather Platform
PORT=8000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mosamiyan
DEFAULT_LAT=28.6139
DEFAULT_LON=77.2090
DEFAULT_CITY=New Delhi
DEFAULT_COUNTRY=IN
```

### 3. Build & Run Containers with Docker Compose

Start the full stack (FastAPI app, PostgreSQL database, and Redis cache):
```bash
docker compose up --build -d
```

Check the status of running containers:
```bash
docker compose ps
```

To stop containers:
```bash
docker compose down
```

---

## 🌐 Accessing the Application

Once containers are running:

- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger API Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 API Endpoints Reference

### 1. Health Check
`GET /api/v1/health`
Verifies connection health for both PostgreSQL and Redis.

### 2. Current Weather
`GET /api/v1/weather/current?lat={lat}&lon={lon}&units={metric|imperial}`
Returns localized atmospheric metrics and computed lifestyle comfort scores.

### 3. Combined Forecast
`GET /api/v1/weather/forecast?lat={lat}&lon={lon}&hourly_steps=24&daily_steps=7&units={metric|imperial}`
Returns hourly timeline scrubbing data and extended daily forecasts.

### 4. Location Search (Geocoding Autocomplete)
`GET /api/v1/locations/search?q={query}`
Typeahead autocomplete search for global cities and administrative regions.

### 5. Saved Locations (Favorites)
- `GET /api/v1/locations/favorites`: List user's saved cities.
- `POST /api/v1/locations/favorites`: Save a new city (enforcing max 5 for MVP).
- `DELETE /api/v1/locations/favorites/{id}`: Remove a saved city.

---

## 🧪 Running Automated Tests

To execute the automated test suite locally:

```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run pytest
pytest tests/ -v
```

---

## 📁 Project Structure

```text
├── Dockerfile                  # Multi-stage production container image
├── docker-compose.yml          # Container orchestration (App, Postgres, Redis)
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .env.example                # Sample environment variables
├── README.md                   # Project documentation
├── app/
│   ├── main.py                 # FastAPI application entry & UI router
│   ├── config.py               # Pydantic BaseSettings
│   ├── database.py             # asyncpg connection pool manager
│   ├── db_queries.py           # Parameterised raw SQL queries
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/      # REST route handlers (health, weather, locations)
│   ├── models/                 # Data definitions
│   ├── schemas/                # Pydantic v2 schemas (weather, location)
│   ├── services/               # Core business logic, caching & provider failover
│   │   ├── cache_service.py
│   │   ├── weather_service.py
│   │   ├── location_service.py
│   │   ├── weather_utils.py
│   │   └── providers/          # Upstream providers (Open-Meteo, OWM, WeatherAPI)
│   ├── static/                 # Frontend JavaScript & styling assets
│   └── templates/              # HTML5 dashboard template (index.html)
├── scripts/
│   └── init_db.sql             # Relational schema initialization script
└── tests/                      # Automated test suite
```
