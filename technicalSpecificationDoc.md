# Technical Specification Document: Modern Weather Platform

**Document Version:** 1.0

**Backend Runtime:** Python 3.12+ (FastAPI)

**Frontend Runtime:** Node.js 20+, React 18+, Next.js 14+ (Use Python based libraries if installation issues faced)

**Database:** PostgreSQL 16+ (Docker)

**Cache:** Redis 7+ (Docker)

**Target Environment:** Containerized Microservices / Cloud Native (Docker, Docker Compose)

# 1. System Architecture & Component Design

The platform uses a layered, asynchronous microservice/modular monolith architecture designed around upstream data resilience, aggressive multi-tier caching, and non-blocking I/O.

                  ┌─────────────────────────────────────────┐
                  │      Frontend (Next.js / Tailwind)      │
                  └────────────────────┬────────────────────┘
                                       │ HTTPS / WSS
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    Edge Reverse Proxy / CDN (Caddy)     │
                  │   - SSL Termination & Rate Limiting     │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      Backend API (Python / FastAPI)     │
                  │   - Asynchronous Request Router         │
                  │   - Pydantic Schema Validation          │
                  │   - Lifestyle Calculation Engine        │
                  └─────────┬─────────────────────┬─────────┘
                            │                     │
               Read / Write │                     │ Cache Query (Hit/Miss)
                            ▼                     ▼
             ┌─────────────────────────┐   ┌─────────────────────────┐
             │ PostgreSQL 16           │   │ Redis 7 (In-Memory)     │
             │ - User Profiles         │   │ - Geocache Data         │
             │ - Saved Locations       │   │ - 5-min Weather Blobs   │
             │ - Push Subscriptions    │   │ - Rate Limit Counters   │
             └─────────────────────────┘   └─────────────────────────┘
                            ▲
                            │ Background Worker (Celery / ARQ)
                            │ - Active Alert Poller (NOAA/MeteoAlarm)
                            │ - Web Push Dispatcher
                            ▼
             ┌────────────────────────────────────────────────────────┐
             │ Upstream Providers: Open-Meteo, OpenWeather, Mapbox    │
             └────────────────────────────────────────────────────────┘


# 2. Database Schema Design (PostgreSQL)
```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    unit_preference VARCHAR(10) DEFAULT 'metric' CHECK (unit_preference IN ('metric', 'imperial')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Saved Locations Table
CREATE TABLE saved_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    city_name VARCHAR(150) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, latitude, longitude)
);

-- 3. Web Push Subscriptions Table
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Severe Weather Alerts History (Audit & Deduplication)
CREATE TABLE weather_alerts (
    id VARCHAR(100) PRIMARY KEY, -- Hash of provider alert ID
    event_title VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    headline TEXT,
    description TEXT,
    instructions TEXT,
    boundary_geom GEOMETRY(Polygon, 4326),
    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_saved_locations_user ON saved_locations(user_id);
CREATE INDEX idx_push_subs_coords ON push_subscriptions(latitude, longitude);
CREATE INDEX idx_alerts_expiry ON weather_alerts(expires_at);
```

# 3. Caching & Data Normalization Strategy

To minimize latency and avoid exceeding third-party API rate limits, all coordinate queries are normalized and cached via Redis.

## Coordinate Spatial Rounding

Coordinates are rounded to 2 decimal places (~1.1 km precision at the equator), preventing cache fragmentation from slight GPS drift.

$$\text{lat}_{\text{norm}} = \text{round}(\text{lat}, 2), \quad \text{lon}_{\text{norm}} = \text{round}(\text{lon}, 2)$$

## Redis Key Schema & TTL Policy

- Current Weather: weather:current:{lat_norm}:{lon_norm} → TTL: 300 seconds (5 min)

- Hourly Forecast (48h): weather:hourly:{lat_norm}:{lon_norm} → TTL: 1800 seconds (30 min)

- Daily Forecast (14d): weather:daily:{lat_norm}:{lon_norm} → TTL: 3600 seconds (1 hour)

- Active Alerts: weather:alerts:{lat_norm}:{lon_norm} → TTL: 120 seconds (2 min)

- Geocoding Autocomplete: geo:search:{normalized_query} → TTL: 86400 seconds (24 hours)

# 4. API Contracts & Endpoint Specifications

## 4.1 GET /api/v1/weather/current
Fetches real-time localized atmospheric metrics.

Query Parameters:

- lat (float, required): Latitude (-90.0 to 90.0)

- lon (float, required): Longitude (-180.0 to 180.0)

- units (string, optional): metric (default) or imperial

Response (`200 OK`):
```json
{
  "location": {
    "name": "Seattle",
    "region": "Washington",
    "country": "US",
    "timezone": "America/Los_Angeles",
    "lat": 47.61,
    "lon": -122.33
  },
  "current": {
    "timestamp": 1774828800,
    "temp": 14.5,
    "feels_like": 13.8,
    "temp_min": 11.0,
    "temp_max": 17.2,
    "condition": "Light Rain",
    "condition_code": "rain_light",
    "humidity": 78,
    "dew_point": 10.8,
    "pressure_hpa": 1014.2,
    "pressure_trend": "falling",
    "wind": {
      "speed_kmh": 18.5,
      "gust_kmh": 26.0,
      "direction_deg": 220,
      "cardinal": "SW"
    },
    "uv_index": 3.2,
    "uv_category": "Moderate",
    "visibility_km": 9.5,
    "cloud_cover_pct": 85,
    "air_quality": {
      "aqi_us": 42,
      "category": "Good",
      "pm2_5": 8.4,
      "pm10": 14.1
    }
  },
  "lifestyle_indices": {
    "outdoor_running": { "score": 68, "rating": "Good", "summary": "Mild temperatures, expect light drizzle." },
    "car_wash": { "rating": "Poor", "summary": "Rain expected within next 12 hours." },
    "sun_protection": { "time_to_burn_mins": 45, "recommendation": "SPF 30 recommended around midday." }
  },
  "source": "cache"
}
```

## 4.2 GET /api/v1/weather/forecast
Fetches combined hourly and daily projected data.

Query Parameters:

- lat (float, required)
- lon (float, required)
- hourly_steps (int, default: 48)
- daily_steps (int, default: 14)

Response Payload (`200 OK`):
```json
{
  "hourly": [
    {
      "time": "2026-08-25T00:00:00-07:00",
      "temp": 14.0,
      "feels_like": 13.5,
      "precip_probability": 65,
      "precip_amount_mm": 0.8,
      "condition_code": "rain_light",
      "wind_speed_kmh": 16.0
    }
  ],
  "daily": [
    {
      "date": "2026-08-25",
      "temp_min": 11.2,
      "temp_max": 18.4,
      "condition_code": "partly_cloudy",
      "precip_probability": 20,
      "precip_accumulation_mm": 0.2,
      "sunrise": "2026-08-25T06:22:00-07:00",
      "sunset": "2026-08-25T20:05:00-07:00",
      "uv_max": 6.5
    }
  ]
}
```

## 4.3 GET /api/v1/locations/search
Typeahead search endpoint with debounced geocoding.

Query Parameters:

- q (string, required): Query string (min length: 2)

Response (`200 OK`):
```json
{
  "results": [
    {
      "id": "geo_47.6062_-122.3321",
      "name": "Seattle",
      "administrative_area": "Washington",
      "country": "United States",
      "country_code": "US",
      "lat": 47.6062,
      "lon": -122.3321,
      "timezone": "America/Los_Angeles"
    }
  ]
}
```

## 5. Upstream Provider Integration & Failover Architecture
To guarantee 99.9% uptime and bypass provider-specific rate limit ceilings, the backend implements a Circuit Breaker Pattern using Python's `httpx` async client.

                     ┌─────────────────────────────┐
                     │ Client Request -> /current  │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │   Check Redis Cache Hit?    │
                     └──────┬───────────────┬──────┘
                       Yes  │               │ No
              ┌─────────────┘               └─────────────┐
              ▼                                           ▼
       [Return Cached JSON]                 ┌───────────────────────────┐
                                            │ Primary Provider          │
                                            │ (Open-Meteo / Tomorrow)   │
                                            └─────────────┬─────────────┘
                                                          │
                                                Success ? │
                                              ┌───────────┴───────────┐
                                              ▼ (Yes)                 ▼ (No / Timeout > 1500ms)
                                     ┌─────────────────┐    ┌───────────────────────────┐
                                     │ Cache in Redis  │    │ Fallback Provider         │
                                     │ Return Response │    │ (OpenWeatherMap)          │
                                     └─────────────────┘    └─────────────┬─────────────┘
                                                                          │
                                                                Success ? │
                                                              ┌───────────┴───────────┐
                                                              ▼ (Yes)                 ▼ (No)
                                                     ┌─────────────────┐    ┌───────────────────┐
                                                     │ Cache in Redis  │    │ Serve Stale Cache │
                                                     │ Return Response │    │ Or Throw 503      │
                                                     └─────────────────┘    └───────────────────┘

### Circuit Breaker Configuration

- Failure Threshold: 5 consecutive HTTP 5xx responses or timeouts within 30 seconds.

- Open State Timeout: 60 seconds (trips traffic to secondary provider without pinging the failing primary).

- Half-Open Probe: Single canary request sent after 60s; if successful, circuit resets to Closed.


## 6. Background Worker: Alert Polling & Push Notifications
- Task Framework: ARQ (Async Redis Queue) or Celery on Python.

- Cron Interval: Runs every 120 seconds.

- Execution Flow:

    - Pull active CAP (Common Alerting Protocol) RSS/JSON feeds from NOAA, Environment Canada, and MeteoAlarm.

    - Parse active alert polygons and compute spatial bounding intersections against unique stored coordinates in push_subscriptions.

    - Filter out previously notified alerts using weather_alerts table hashes.

    - Dispatch batch encrypted web push payloads using pywebpush to affected endpoints via HTTP/2.

## 7. Lifestyle Index Algorithms (Python Implementation)

```python
def compute_outdoor_running_score(temp_c: float, humidity: float, wind_kmh: float, precip_prob: int) -> dict:
    """
    Computes a 0-100 running comfort score based on meteorological stress factors.
    """
    score = 100.0
    
    # Temperature penalties (Ideal range: 10°C - 18°C)
    if temp_c < 10.0:
        score -= (10.0 - temp_c) * 2.5
    elif temp_c > 18.0:
        score -= (temp_c - 18.0) * 3.5
        
    # High humidity heat penalty
    if temp_c > 22.0 and humidity > 70:
        score -= (humidity - 70) * 0.4
        
    # Wind drag penalty
    if wind_kmh > 20.0:
        score -= (wind_kmh - 20.0) * 1.2
        
    # Precipitation risk penalty
    score -= (precip_prob * 0.35)
    
    final_score = int(max(0, min(100, round(score))))
    
    if final_score >= 80:
        rating = "Optimal"
    elif final_score >= 60:
        rating = "Good"
    elif final_score >= 40:
        rating = "Fair"
    else:
        rating = "Poor"
        
    return {
        "score": final_score,
        "rating": rating
    }
```

## 8. Rate Limiting & Production Deployment

- CORS: Restricted to verified production web origin domains.

- Rate Limiting: Redis-backed sliding window counter enforced at the gateway (e.g., 60 requests/minute per unauthenticated IP, 300 requests/minute for authenticated users).

### Infrastructure & Containerization

- App Container: Multi-stage Dockerfile with lightweight python:3.12-slim base, running non-root uvicorn workers behind an asynchronous ASGI server.

- Production Command:
    ```bash
    uvicorn app.main:app --host [IP_ADDRESS] --port 8000 --workers 3 --proxy-headers
    ```
