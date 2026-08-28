# Phase 2 Specification: Enhanced Visuals & Safety

**Product Name:** Web-based Weather Platform "Mosamiyan"  
**Document Type:** Functional & Technical Specification Document (FSD/TSD)  
**Phase:** Phase 2 — Enhanced Visuals & Safety  
**Status:** Approved for Implementation  
**Target Environment:** Containerized Microservices / Python 3.12+ (FastAPI), Redis 7, PostgreSQL 16, Leaflet.js, Tailwind CSS  

---

## 1. Product Overview & Objectives

### 1.1 Phase 2 Mission Statement
Phase 1 established the Minimum Viable Product (MVP) of **Mosamiyan**, delivering core real-time atmospheric metrics across 9 parameters, a 24-hour timeline, 7-day forecasts, omnibox geocoding, asyncpg raw SQL favorites, and multi-tier upstream failover. 

**Phase 2: Enhanced Visuals & Safety** builds on this stable foundation to elevate user situational awareness, safety, and visual comfort. It delivers:
1. **Interactive Weather Radar & Animated Map Layers**: Geographic map visualization with dynamic time-slider scrubbing for precipitation radar, wind streamlines, cloud density, and temperature heatmaps.
2. **Granular Multi-Horizon Forecasts**: Expansion of the hourly forecast from 24 hours to **48 hours** with interactive temperature trendlines and precipitation probability bars; and expansion of the daily forecast from 7 days to **14 days** with interactive accordion drilldowns (daylight duration, sunrise/sunset, UV index, rain/snow accumulation, wind dynamics).
3. **Severe Weather Warnings & Critical Safety Alerts**: Real-time integration of meteorological warning feeds (NOAA, MeteoAlarm, IMD, ECMWF), high-visibility prioritized alert banners with a 4-tier severity hierarchy, and rich protective action modals.
4. **Dark / Light Mode Theming Engine**: Seamless user interface theme switching between crisp daylight high-contrast mode and deep OLED dark mode, supporting system color scheme detection and persistent user preferences.

### 1.2 Target Personas & Value Delivery
- **The Storm-Aware Resident & Commuter**: Sees incoming precipitation bands on an animated radar map and receives immediate severe weather warnings with official safety guidance before hazardous conditions hit.
- **The Long-Term Planner & Traveler**: Leverages 14-day extended forecasts with daylight hours and daily thermal boundaries to plan outdoor events and travel itineraries up to two weeks in advance.
- **The Night-Time & Power User**: Enjoys an eye-strain-free dark mode interface with smooth transitions and persistent settings across visits.

---

## 2. Feature Specifications & Engineering Tasks

### Feature 1: Interactive Weather Radar & Animated Map Layers (FSD Feature 3)

#### 1.1 Overview & Capabilities
Provides an interactive, high-performance map widget embedded within the main dashboard, displaying real-time and projected weather layers.

- **Map Navigation**: Full pan, smooth scroll zoom, pinch-to-zoom on mobile, full-screen expansion mode, and a "Re-center on My Location" quick action button.
- **Layer Toggles**:
  - **Precipitation Radar**: Color-coded radar reflectance transitioning from light drizzle (green) to moderate rain (yellow), heavy downpours (red), and severe hail/snow (purple/white).
  - **Wind Streamlines**: Dynamic animated moving particle vector overlay showing sustained wind speed and directional flow across regions.
  - **Cloud Density**: Satellite imagery overlay showing moving cloud cover.
  - **Temperature Heatmap**: Color-graded regional temperature overlay.
- **Playback & Time-Slider Controls**:
  - Animated playback control bar with **Play**, **Pause**, **Step Forward**, and **Step Backward** buttons.
  - Scrubbing timeline spanning the past **2 hours of observed radar history** through the next **1–2 hours of projected radar movement**.
  - Frame indicator badges showing relative timestamps and clear labels distinguishing **"Observed History"** from **"Projected Forecast"**.
  - Auto-looping playback mode when the Play button is toggled.
- **Active Location Pin**: Custom pinpoint marker anchored to the currently queried city/coordinates.

#### 1.2 Engineering Tasks for Feature 1
- [ ] **Task 1.1**: Integrate Leaflet.js (v1.9.4) map container and base tile layer (CartoDB Positron for light theme, CartoDB Dark Matter for dark theme, OpenStreetMap fallback).
- [ ] **Task 1.2**: Implement backend radar metadata proxy/endpoint `GET /api/v1/weather/radar-tiles` that interfaces with RainViewer API / OpenWeatherMap tile services, returning valid timestamp frame arrays with 10-minute caching in Redis.
- [ ] **Task 1.3**: Build the frontend radar animation engine with frame preloading, canvas/tile layer swapping, time-slider scrubber, and Play/Pause loop state machine.
- [ ] **Task 1.4**: Implement dynamic layer toggle switcher allowing users to toggle between Precipitation Radar, Cloud Cover, and Temperature overlays.
- [ ] **Task 1.5**: Implement map controls (Fullscreen toggle, Zoom in/out, Re-center on active location marker).

---

### Feature 2: 48-Hour Hourly Scrubber & 14-Day Extended Daily Forecast (FSD Feature 2)

#### 2.1 Overview & Capabilities
Expands the temporal forecasting resolution to give users precise short-term and extended planning data.

- **48-Hour Interactive Hourly Scrubber**:
  - Expanded horizontal scroll carousel presenting 48 consecutive 1-hour intervals.
  - Continuous SVG/Canvas temperature trendline overlaid across the hourly slots.
  - Vertical probability of precipitation (PoP) bars (0% to 100%) with blue gradient styling.
  - Atmospheric condition micro-icons, temperature readings, and wind speeds per hour.
  - Interactive touch/hover tooltips displaying exact timestamp, localized temperature, precipitation amount (mm/in), and wind gusts.
  - Timezone-aware timestamp formatting using the searched location's IANA timezone.
- **14-Day Extended Daily Outlook with Accordion Drilldowns**:
  - Formatted daily list displaying Day Name, Calendar Date, Condition Icon, Rain Probability (%), and a dual-ended horizontal thermal range bar (Min Temp to Max Temp).
  - High-contrast **"Today"** badge on the current day's card.
  - **Expandable Accordion Drilldown**: Clicking any day smoothly expands an internal card revealing:
    - Exact Sunrise and Sunset times.
    - Calculated daylight duration (hours and minutes).
    - Peak UV index with safety rating.
    - Total expected precipitation accumulation (liquid equivalent / snowfall).
    - Wind speed range and dominant cardinal direction.

#### 2.2 Engineering Tasks for Feature 2
- [ ] **Task 2.1**: Update backend forecast schemas in `app/schemas/weather.py` to support 48-hour hourly entries and 14-day daily items including sunrise, sunset, daylight duration, UV peak, accumulation, and wind metrics.
- [ ] **Task 2.2**: Update upstream provider adapters (`openmeteo_provider.py`, `openweathermap_provider.py`, `weatherapi_provider.py`) to query and normalize 48 hourly points and 14 daily forecast records.
- [ ] **Task 2.3**: Update Redis forecast caching:
  - `weather:hourly:{lat}:{lon}` (48-hour dataset, TTL: 1800s / 30 mins).
  - `weather:daily:{lat}:{lon}` (14-day dataset, TTL: 3600s / 1 hour).
- [ ] **Task 2.4**: Upgrade frontend hourly scrubber in `app/static/app.js` and `app/templates/index.html` to render 48 interactive slots with smooth horizontal drag/scroll and SVG temperature spline.
- [ ] **Task 2.5**: Upgrade frontend daily forecast cards to 14 days with smooth CSS accordion expansion/collapse mechanics and unit-switching support.

---

### Feature 3: Severe Weather Warnings & Critical Safety Alerts (FSD Feature 4)

#### 3.1 Overview & Capabilities
Surfaces life-safety weather emergencies and meteorological warnings with maximum visual prominence and actionable instructions.

- **Global Pinned Alert Banner**:
  - High-contrast banner fixed to the top of the dashboard whenever active warnings exist for the queried location.
  - 4-Tier Severity Color Hierarchy:
    - 🟡 **Advisory** (Yellow / Amber): Potential inconvenience, minor hazards.
    - 🟠 **Watch** (Orange): Favorable atmospheric conditions for severe weather; be prepared.
    - 🔴 **Warning** (Red): Severe hazardous weather occurring or imminent; take immediate action.
    - 🟣 **Emergency** (Purple): Catastrophic threat to life or property.
  - Displays alert title, issuing agency, effective expiration timer, and an **"Action & Details"** button.
  - Multiple Alerts Counter (e.g. *"2 Active Alerts — Flood Warning & High Wind Watch"*).
- **Safety Details Modal**:
  - Dedicated accessible modal dialogue opened upon clicking the banner.
  - Detailed metadata: Official Issuing Agency (e.g. National Weather Service, MeteoAlarm, IMD), Event Severity, Certainty, and Urgency.
  - Effective Start Time and Expiration Time formatted in local timezone.
  - Full threat description, geographic scope, and specific protective action recommendations.
- **Deduplication & Caching**:
  - Alerts cached in Redis under `weather:alerts:{lat_norm}:{lon_norm}` with a 120-second TTL (2 minutes) to ensure immediate freshness.
  - Audit logging of active alert hashes in PostgreSQL `weather_alerts` table.

#### 3.2 Engineering Tasks for Feature 3
- [ ] **Task 3.1**: Create `app/schemas/alert.py` Pydantic models (`WeatherAlertItem`, `WeatherAlertsResponse`, `AlertSeverityEnum`).
- [ ] **Task 3.2**: Implement alert parsing in provider adapters (`openmeteo_provider.py`, `openweathermap_provider.py`, `weatherapi_provider.py`) with fallback support.
- [ ] **Task 3.3**: Create REST endpoint `GET /api/v1/weather/alerts?lat={lat}&lon={lon}` with Redis 120s caching and asyncpg audit logging.
- [ ] **Task 3.4**: Build frontend global alert banner in `app/templates/index.html` with animated pulse indicators and severity badge styles.
- [ ] **Task 3.5**: Build accessible alert details modal in `app/static/app.js` with focus management, backdrop blur, and keyboard escape handling.

---

### Feature 4: Dark / Light Mode Theme Engine (FSD Feature 7)

#### 4.1 Overview & Capabilities
Delivers a complete, eye-friendly theme switching experience across all screens, cards, maps, and modals.

- **Theme Modes**:
  - **Light Mode**: Crisp, high-contrast daylight aesthetic with clean slate and white cards.
  - **Dark Mode**: Deep navy/slate-950 dark theme optimized for low-light viewing and OLED energy savings.
- **Theme Switcher Control**:
  - Prominent toggle icon button in the top navigation bar (Sun ☀️ / Moon 🌙) with smooth 360-degree rotation animation.
- **System Preference Auto-Detection**:
  - Automatically respects OS setting (`prefers-color-scheme: dark`) on initial user visit.
- **Zero-Flicker Client Initialization**:
  - Inline head script evaluates `localStorage.getItem('theme')` prior to DOM render, preventing Flash of Unstyled Theme (FOUT).
- **Dynamic Leaflet Map Tile Theme Synchronization**:
  - Automatically swaps Leaflet basemap between light and dark CartoDB tiles when theme changes.

#### 4.2 Engineering Tasks for Feature 4
- [ ] **Task 4.1**: Configure Tailwind CSS `darkMode: 'class'` and define color tokens for dark/light surfaces, typography, borders, and glassmorphic card overlays.
- [ ] **Task 4.2**: Add zero-flicker theme detection inline script in `<head>` of `app/templates/index.html`.
- [ ] **Task 4.3**: Implement theme toggle controller in `app/static/app.js` with `localStorage` persistence and event dispatching for map tile updates.
- [ ] **Task 4.4**: Update all UI elements (Hero card, 48h timeline, 14d accordion rows, Omnibox dropdown, Alert modal, and scrollbars) with complete dark mode styles.
- [ ] **Task 4.5**: Implement Leaflet tile layer theme switcher to dynamically toggle between CartoDB Positron and CartoDB Dark Matter tile basemaps.

---

## 3. User Experience & UI Layout Requirements

### 3.1 Visual Hierarchy & Component Wireframe
```
+----------------------------------------------------------------------------------------+
|  [Mosamiyan Logo]     [Omnibox Search Bar 🔍]      [°C / °F]  [☀️/🌙 Theme] [Starred]  |
+----------------------------------------------------------------------------------------+
|  🔴 [ALERT BANNER]: Flash Flood Warning in effect until 8:00 PM  [View Details >]      |
+----------------------------------------------------------------------------------------+
|  [Saved Favorites Bar: ★ New Delhi  ★ London  ★ Tokyo  ★ New York  ★ Paris]            |
+----------------------------------------------------------------------------------------+
|                                                                                        |
|  +-------------------------------------+  +-------------------------------------+      |
|  | HERO CURRENT WEATHER                |  | 9 ATMOSPHERIC METRIC TILES          |      |
|  | New Delhi, IN (28.61°N, 77.20°E)    |  | • Humidity: 54%  • Dew Pt: 18°C     |      |
|  | 32°C  Partly Cloudy                 |  | • Wind: 14 km/h NW (Gust: 22 km/h)  |      |
|  | Feels like: 34°C | H: 36° L: 24°    |  | • Pressure: 1012 hPa (Steady)       |      |
|  | Updated: Just now                   |  | • UV: 7 (High)  • AQI: 88 (Moderate)|      |
|  +-------------------------------------+  +-------------------------------------+      |
|  +-------------------------------------------------------------------------------+     |
|  | 🕒 48-HOUR HOURLY TIMELINE & PRECIPITATION SCRUBBER                            |    |
|  | [Now: 32° | 10%] [1h: 31° | 15%] ... [24h: 28° | 60%] ... [48h: 29° | 20%]   |      |
|  | ~~~~~ Temperature Trend Spline ~~~~~~~ [ Precipitation Probability Bars █ ]    |    |
|  +-------------------------------------------------------------------------------+     |
|                                                                                        |
|  +--------------------------------------------------------------------------------+    |
|  | 🗺️ INTERACTIVE WEATHER RADAR & ANIMATED MAP                                    |    |
|  | [ Layers: 🔘 Precipitation | 🔘 Wind | 🔘 Clouds | 🔘 Temp ]  [ ⛶ Fullscreen ] |    |
|  |                                                                                |    |
|  |      [ Map Display with Color-Coded Radar Reflectivity & Location Pin ]        |    |
|  |                                                                                |    |
|  | [ ◀ Step ] [ ▶ Play / ⏸ Pause ] [ Step ▶ ]  [==== Time Slider ====== ● Now ]  |    |
|  | Status: Observed History (15 mins ago)                                         |    |
|  +-------------------------------------------------------------------------------+     |
|                                                                                        |
|  +---------------------------------------------------------------------------------+   |
|  | 📅 14-DAY EXTENDED FORECAST (ACCORDION DRILLDOWN)                               |   |
|  | ▶ Today, Aug 28   • Sunny         • 0%  Rain   [===== 24°C - 36°C =====]  ▼     |   |
|  |   └─ Sunrise: 05:58 | Sunset: 18:52 | Daylight: 12h 54m | UV Max: 8 | Rain: 0mm |   |
|  | ▶ Friday, Aug 29  • Thunderstorm  • 75% Rain   [==== 22°C - 31°C ====]   ▼      |   |
|  | ▶ Saturday, Aug 30• Scattered Rain• 40% Rain   [==== 23°C - 33°C ====]   ▼      |   |
|  | ... (Up to 14 days)                                                             |   |
|  +---------------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------------+
```

### 3.2 Accessibility (a11y) & Responsiveness
- **WCAG 2.1 Level AA Compliance**: Contrast ratios of >= 4.5:1 for all text labels in both light and dark themes.
- **Keyboard Navigation**: Full tab focus rings on search, accordion headers, radar player buttons, and modal escape key handling (`Escape` closes modals).
- **Responsive Layout Breakpoints**:
  - **Mobile (<640px)**: Single-column stacked cards, full-width touch-draggable hourly scrubber, collapsed map default height (280px), full-width accordions.
  - **Tablet (640px - 1024px)**: 2-column hero atmospheric tiles, medium map height (380px).
  - **Desktop (>1024px)**: Full multi-column dashboard layout with expanded map height (480px) and side-by-side metric tiles.

---

## 4. Business Logic, Data Contracts & Display Rules

### 4.1 Redis Caching & Normalization Architecture
All coordinates are rounded to 2 decimal places (`~1.1 km` spatial accuracy) to eliminate GPS drift fragmentation:
$$\text{lat}_{\text{norm}} = \text{round}(\text{lat}, 2), \quad \text{lon}_{\text{norm}} = \text{round}(\text{lon}, 2)$$

| Data Type | Redis Key Pattern | TTL Policy | Fallback / Failover |
| :--- | :--- | :--- | :--- |
| **Current Weather** | `weather:current:{lat_norm}:{lon_norm}` | 300s (5 min) | Open-Meteo → OWM → WeatherAPI |
| **48-Hour Hourly** | `weather:hourly:{lat_norm}:{lon_norm}` | 1800s (30 min) | Open-Meteo → OWM → WeatherAPI |
| **14-Day Daily** | `weather:daily:{lat_norm}:{lon_norm}` | 3600s (1 hour) | Open-Meteo → OWM → WeatherAPI |
| **Active Alerts** | `weather:alerts:{lat_norm}:{lon_norm}` | 120s (2 min) | Open-Meteo Alerts → WeatherAPI / OWM |
| **Radar Frame List** | `radar:frames:metadata` | 600s (10 min) | RainViewer API → OpenWeatherMap Tiles |
| **Geocoding Search**| `geo:search:{normalized_query}` | 86400s (24 hr) | Open-Meteo Geocoding → Local DB |

---

### 4.2 API Contracts & Endpoint Specifications

#### 1. GET `/api/v1/weather/forecast`
**Query Parameters**:
- `lat` (float, required): Latitude (-90.0 to 90.0)
- `lon` (float, required): Longitude (-180.0 to 180.0)
- `hourly_steps` (int, optional, default: 48, min: 1, max: 48)
- `daily_steps` (int, optional, default: 14, min: 1, max: 16)
- `units` (string, optional, default: "metric", enum: ["metric", "imperial"])

**Response Schema (`200 OK`)**:
```json
{
  "location": {
    "name": "New Delhi",
    "region": "Delhi",
    "country": "India",
    "timezone": "Asia/Kolkata",
    "lat": 28.61,
    "lon": 77.21
  },
  "hourly": [
    {
      "time": "2026-08-28T20:00:00+05:30",
      "temp": 31.4,
      "feels_like": 34.2,
      "precip_probability": 15,
      "precip_amount_mm": 0.0,
      "condition": "Partly Cloudy",
      "condition_code": "partly_cloudy_night",
      "wind_speed_kmh": 12.0
    }
  ],
  "daily": [
    {
      "date": "2026-08-28",
      "day_name": "Today",
      "temp_min": 24.5,
      "temp_max": 35.8,
      "condition": "Partly Cloudy",
      "condition_code": "partly_cloudy_day",
      "precip_probability": 20,
      "precip_accumulation_mm": 0.2,
      "sunrise": "2026-08-28T05:58:00+05:30",
      "sunset": "2026-08-28T18:52:00+05:30",
      "daylight_duration": "12h 54m",
      "uv_max": 7.8,
      "wind_speed_max_kmh": 18.5,
      "wind_direction_dominant": "NW"
    }
  ],
  "source": "cache",
  "provider": "open-meteo"
}
```

---

#### 2. GET `/api/v1/weather/alerts`
**Query Parameters**:
- `lat` (float, required): Latitude
- `lon` (float, required): Longitude

**Response Schema (`200 OK`)**:
```json
{
  "location": {
    "lat": 28.61,
    "lon": 77.21,
    "city": "New Delhi"
  },
  "alerts_count": 1,
  "highest_severity": "warning",
  "alerts": [
    {
      "id": "alert_delhi_heat_20260828",
      "event_title": "Severe Heatwave Warning",
      "severity": "warning",
      "severity_level": 3,
      "urgency": "Immediate",
      "certainty": "Observed",
      "issuing_agency": "India Meteorological Department (IMD)",
      "headline": "Severe heatwave conditions expected across Delhi NCR with temps up to 42°C",
      "description": "High daytime temperatures combined with elevated humidity pose a risk of heat cramps and exhaustion.",
      "instructions": "Avoid direct sun exposure between 12:00 PM and 4:00 PM. Stay hydrated and wear lightweight light-colored clothing.",
      "starts_at": "2026-08-28T10:00:00+05:30",
      "expires_at": "2026-08-28T21:00:00+05:30",
      "is_active": true
    }
  ],
  "source": "upstream",
  "cached": false
}
```

---

#### 3. GET `/api/v1/weather/radar-tiles`
**Response Schema (`200 OK`)**:
```json
{
  "host": "https://tilecache.rainviewer.com",
  "generated_at": 1774828800,
  "past_frames": [
    { "time": 1774821600, "path": "/v2/radar/1774821600/256/{z}/{x}/{y}/2/1_1.png", "type": "past" },
    { "time": 1774825200, "path": "/v2/radar/1774825200/256/{z}/{x}/{y}/2/1_1.png", "type": "past" }
  ],
  "nowcast_frames": [
    { "time": 1774832400, "path": "/v2/radar/nowcast_1774832400/256/{z}/{x}/{y}/2/1_1.png", "type": "nowcast" },
    { "time": 1774836000, "path": "/v2/radar/nowcast_1774836000/256/{z}/{x}/{y}/2/1_1.png", "type": "nowcast" }
  ],
  "color_scheme": 2,
  "smooth": 1
}
```

---

## 5. Edge Cases & Exception Handling

| Edge Case Scenario | Expected System Behavior |
| :--- | :--- |
| **No Active Weather Alerts** | API returns `alerts_count: 0` with an empty `alerts: []` list. UI banner remains completely hidden with zero layout shift. |
| **Multiple Active Alerts** | Alert banner highlights the highest severity level (Emergency > Warning > Watch > Advisory), displays an alert counter chip, and the modal renders a tabbed/scrollable list of all alerts. |
| **Expired Alert Timestamp** | Backend automatically filters out expired alerts (`expires_at < current_timestamp`). Frontend auto-dismisses banners if the user keeps the tab open past expiration. |
| **Remote Oceanic / Polar Coordinate (No Radar Tiles)** | Radar overlay renders base geographical map with a lightweight informational banner: *"Radar imagery currently unavailable for this geographic quadrant."* |
| **Upstream Alert Service Down / 500 Error** | Provider failover executes seamlessly. If all fail, returns empty alert response with 30s cache TTL to prevent cascading failure. |
| **Missing Sunrise/Sunset in Upstream Response** | Fallback calculation automatically derives solar dawn/dusk based on latitude, longitude, and day-of-year solar declination angles. |
| **Rapid Theme Switching by User** | Handled purely via CSS class mutation on `document.documentElement` without blocking I/O or rebuilding map DOM instances; map tiles switch dynamically via layer URL swaps. |

---

## 6. Acceptance Criteria

### Feature 1: Interactive Radar Map
- **Scenario 1.1**: Radar Map Initialization & Location Pin
  - **Given** a user navigates to the Mosamiyan dashboard for "Tokyo",
  - **When** the page renders,
  - **Then** an interactive map is displayed centered on Tokyo coordinates with an active location pin, default precipitation layer, and time controls.
- **Scenario 1.2**: Radar Playback Animation Loop
  - **When** the user clicks the "Play" button,
  - **Then** the map advances sequentially through historical and nowcast precipitation frames in an automated loop, updating the timestamp indicator badge at each frame.
- **Scenario 1.3**: Layer Switching
  - **When** the user selects the "Cloud Density" layer,
  - **Then** the precipitation overlay is smoothly removed and replaced with the cloud satellite layer.

### Feature 2: 48-Hour & 14-Day Granular Forecasts
- **Scenario 2.1**: 48-Hour Hourly Scrubber Navigation
  - **Given** a searched location with a distinct timezone,
  - **When** the user scrolls horizontally through the hourly carousel,
  - **Then** 48 full hourly intervals are displayed in local timezone order with temperature spline, rain percentage bars, and condition icons.
- **Scenario 2.2**: 14-Day Accordion Drilldown
  - **Given** the 14-day extended forecast view,
  - **When** the user clicks on any future day's card,
  - **Then** the row smoothly expands to display sunrise, sunset, daylight duration, UV peak index, precipitation accumulation, and wind speed.
- **Scenario 2.3**: Unit Switching
  - **When** the user toggles units from Metric to Imperial,
  - **Then** all 48 hourly temperatures switch from °C to °F, daily rain accumulations convert from mm to inches, and wind speeds convert from km/h to mph instantly.

### Feature 3: Severe Weather Alerts
- **Scenario 3.1**: Active Warning Banner Rendering
  - **Given** an active Severe Thunderstorm Warning for the queried city,
  - **When** the weather data loads,
  - **Then** a prominent red warning banner is displayed at the very top of the screen before all weather cards.
- **Scenario 3.2**: Alert Details Modal Interaction
  - **When** the user clicks "View Details" on the warning banner,
  - **Then** an accessible modal opens showing the issuing meteorological agency, valid time window, detailed hazard description, and recommended safety precautions.

### Feature 4: Dark / Light Mode Theming
- **Scenario 4.1**: User Theme Preference Persistence
  - **Given** a user toggles the theme to "Dark Mode",
  - **When** the user navigates between different cities or refreshes the browser,
  - **Then** Dark Mode persists immediately without any white flash (FOUT).
- **Scenario 4.2**: Map Tile Synchronization
  - **When** the user toggles between Light and Dark modes,
  - **Then** the Leaflet basemap dynamically swaps between light and dark tile sets.

---

## 7. Files to be Created and Modified

### 7.1 Files to be Created
1. **`.agents/specs/02-phase_2.md`** — This Phase 2 specification document.
2. **`app/schemas/alert.py`** — Pydantic schemas for weather alert items, severity rankings, and alerts response.
3. **`app/api/v1/endpoints/alerts.py`** — REST endpoint handler for `/api/v1/weather/alerts`.
4. **`app/api/v1/endpoints/radar.py`** — REST endpoint handler for `/api/v1/weather/radar-tiles`.
5. **`tests/test_alerts.py`** — Unit and integration tests for alert schemas, provider parsing, and endpoint responses.
6. **`tests/test_radar.py`** — Automated tests for radar tile frame generation and caching.
7. **`tests/test_extended_forecast.py`** — Automated tests verifying 48-hour hourly and 14-day daily parsing and calculations.

### 7.2 Files to be Modified
1. **`app/main.py`** — Register new alerts and radar API routers.
2. **`app/config.py`** — Add configuration keys for radar tile proxies and alert provider settings.
3. **`app/schemas/weather.py`** — Extend `ForecastResponse`, `HourlyForecastItem`, and `DailyForecastItem` with daylight duration, 48h support, and extended metrics.
4. **`app/services/providers/base_provider.py`** — Add abstract method definitions `fetch_alerts()` and `fetch_extended_forecast()`.
5. **`app/services/providers/openmeteo_provider.py`** — Implement 48-hour hourly queries, 14-day daily queries, astronomical calculations, and alert feed extraction.
6. **`app/services/providers/openweathermap_provider.py`** — Add fallback 48h/14d queries, radar tile links, and alert parsing.
7. **`app/services/providers/weatherapi_provider.py`** — Add tertiary fallback for alerts and extended forecast horizons.
8. **`app/services/weather_service.py`** — Orchestrate multi-tier alert fetching, 48h/14d aggregation, caching, and unit conversion.
9. **`app/templates/index.html`** — Integrate Leaflet CSS/JS, Tailwind dark mode styling, global alert banner, 48h trendline container, radar map widget, and 14-day accordion markup.
10. **`app/static/app.js`** — Implement Leaflet map controller, radar playback loop, 48h SVG trend spline, 14d accordion expander, alert modal controller, and theme switcher logic.
11. **`README.md`** — Update documentation to highlight Phase 2 features, new endpoints, and architecture additions.

---

## 8. New Components, Libraries & External Dependencies

### 8.1 Frontend Libraries (CDN / Static)
- **Leaflet.js (v1.9.4)**: Lightweight open-source interactive mapping library.
  - CDN CSS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
  - CDN JS: `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`
- **RainViewer Free Radar API**: Free public endpoint providing timestamped tile frames for global precipitation radar and nowcasting.
- **CartoDB Tile Basemaps**:
  - Light Basemap: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=YOUR_KEY`
  - Dark Basemap: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=YOUR_KEY`
- **FontAwesome / SVG Icons**: Integrated weather condition icons, radar player controls (Play, Pause, Step), chevron arrows, and Sun/Moon theme icons.

### 8.2 Backend Dependencies
- Utilizes existing Python 3.12 stack: `fastapi`, `uvicorn`, `pydantic v2`, `httpx`, `redis-py`, `asyncpg`.
- Built-in astronomical solar calculation algorithms in `app/services/weather_utils.py` for daylight duration derivation without requiring heavy external astronomical C-extensions.
