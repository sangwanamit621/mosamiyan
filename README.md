# Mosamiyan — Modern Weather Platform

**Mosamiyan** (Phase 2 — Enhanced Visuals & Safety) is a high-performance, containerized weather platform built with Python 3.12 (FastAPI), PostgreSQL 16, Redis 7, Leaflet.js, and Tailwind CSS. It delivers real-time atmospheric metrics, 48-hour hourly scrubbing, 14-day extended outlooks with accordion drilldowns, interactive precipitation radar maps with time-slider playback, severe weather warning alerts with protective instructions, typeahead geocoding, multi-tier provider failover, and dark/light mode theming.

---

## 🌟 Key Features (Phase 2 Enhanced)

- **Hyperlocal Weather & 9 Atmospheric Metrics**: Real-time Temperature, Feels Like, High/Low, Humidity & Dew Point, Wind Compass (Direction & Peak Gusts), Barometric Pressure & Trend, UV Index (WHO safety category), Visibility, Cloud Cover, and US Air Quality Index (AQI).
- **🗺️ Interactive Weather Radar & Animated Map Layers**: Leaflet.js map with dynamic time-slider scrubbing for precipitation radar (past 2h history + next 1–2h projected nowcast), satellite cloud density, and temperature heatmaps, centered on active location pin.
- **🕒 48-Hour Hourly Timeline**: Extended horizontal scrollable timeline with temperature trends, vertical precipitation probability bars (0–100%), condition icons, and touch tooltips.
- **📅 14-Day Extended Forecast with Accordion Drilldowns**: 14-day outlook highlighting "Today" with interactive click-to-expand details (Sunrise/Sunset, calculated Daylight Duration, UV Max, rain/snow accumulation, and wind dynamics).
- **⚠️ Severe Weather Warnings & Critical Safety Alerts**: Top-pinned high-contrast alert banner with 4-tier severity hierarchy (🟡 Advisory, 🟠 Watch, 🔴 Warning, 🟣 Emergency) and an accessible safety details modal with issuing agency, timing, and protective actions.
- **☀️/🌙 Dark & Light Mode Theming Engine**: Instant theme switcher with system OS detection (`prefers-color-scheme`), zero-flicker head script, `localStorage` persistence, and dynamic CartoDB Positron / Dark Matter basemap tile synchronization.
- **Multi-Tier Provider Failover**: Primary: **Open-Meteo** → Secondary: **OpenWeatherMap** → Tertiary: **WeatherAPI.com**.
- **Spatial Coordinate Caching**: Redis-backed cache with 2-decimal spatial normalization (`~1.1 km` equator precision) to eliminate GPS drift fragmentation.
- **Raw SQL Persistence**: High-speed, parameterised PostgreSQL queries via `asyncpg` connection pool (no ORM overhead).
- **Favorites & Search**: Predictive Omnibox geocoding search and saved locations quick-access bar.
- **Instant Unit Toggle**: Live switch between Metric (°C, km/h, mm) and Imperial (°F, mph, in) without full page reload.

---

## 🏗️ Architecture Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic v2, `asyncpg`, `redis-py` (async), `httpx`
- **Frontend / Dashboard**: Modern responsive UI with HTML5, Tailwind CSS (with Dark Mode), FontAwesome, Leaflet.js, and Vanilla JS
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

Once running:

- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger API Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 API Endpoints Reference

### 1. Health Check
`GET /api/v1/health`  
Verifies connection health for PostgreSQL, Redis, and upstream services.

### 2. Current Weather
`GET /api/v1/weather/current?lat={lat}&lon={lon}&units={metric|imperial}`  
Returns localized atmospheric metrics and computed lifestyle comfort scores.

### 3. Combined Forecast (48h / 14d)
`GET /api/v1/weather/forecast?lat={lat}&lon={lon}&hourly_steps=48&daily_steps=14&units={metric|imperial}`  
Returns 48-hour hourly timeline and 14-day extended daily forecast with daylight calculations.

### 4. Severe Weather Alerts
`GET /api/v1/weather/alerts?lat={lat}&lon={lon}`  
Returns active meteorological emergency alerts, severity ranking, and safety instructions.

### 5. Weather Radar Tiles Metadata
`GET /api/v1/weather/radar-tiles`  
Returns past and nowcast radar tile frame timestamps and host URL for Leaflet mapping.

### 6. Location Search (Geocoding Autocomplete)
`GET /api/v1/locations/search?q={query}`  
Typeahead autocomplete search for global cities and administrative regions.

### 7. Saved Locations (Favorites)
- `GET /api/v1/locations/favorites`: List user's saved cities.
- `POST /api/v1/locations/favorites`: Save a new city.
- `DELETE /api/v1/locations/favorites/{id}`: Remove a saved city.

---

## 🧪 Running Automated Tests

To execute the automated test suite locally:

```bash
# Run pytest with virtual environment
./.venv/bin/pytest tests/ -v
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
│   │       └── endpoints/      # REST route handlers (health, weather, alerts, radar, locations)
│   ├── schemas/                # Pydantic v2 schemas (weather, alert, radar, location)
│   ├── services/               # Core business logic, caching & provider failover
│   │   ├── cache_service.py
│   │   ├── weather_service.py
│   │   ├── location_service.py
│   │   ├── weather_utils.py
│   │   └── providers/          # Upstream providers (Open-Meteo, OWM, WeatherAPI)
│   ├── static/                 # Frontend JavaScript & styling assets
│   └── templates/              # HTML5 dashboard template (index.html)
└── tests/                      # Automated test suite (17 comprehensive tests)
```
