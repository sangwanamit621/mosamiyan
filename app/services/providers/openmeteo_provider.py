import logging
import time
from datetime import datetime
from typing import List, Optional
import httpx
from app.schemas.weather import (
    AirQualityData,
    AtmosphericCondition,
    CurrentWeatherResponse,
    DailyForecastItem,
    ForecastResponse,
    HourlyForecastItem,
    LocationSchema,
    WindData,
)
from app.schemas.location import LocationSearchResult
from app.schemas.alert import (
    AlertLocation,
    AlertSeverityEnum,
    WeatherAlertItem,
    WeatherAlertsResponse,
)
from app.services.http_client import get_http_client
from app.services.providers.base_provider import BaseWeatherProvider
from app.services.weather_utils import (
    aqi_to_category,
    calculate_daylight_duration,
    compute_lifestyle_indices,
    deg_to_cardinal,
    normalize_alert_severity,
    severity_to_level,
    uv_to_category,
    wmo_code_to_condition,
)

logger = logging.getLogger("mosamiyan.provider.openmeteo")


class OpenMeteoProvider(BaseWeatherProvider):
    """
    Primary weather provider using Open-Meteo REST APIs.
    Requires no API keys and provides detailed hourly/daily metrics and air quality.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

    @property
    def name(self) -> str:
        return "open-meteo"

    async def get_current_weather(self, lat: float, lon: float) -> Optional[CurrentWeatherResponse]:
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "is_day",
                    "precipitation",
                    "weather_code",
                    "cloud_cover",
                    "pressure_msl",
                    "surface_pressure",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "wind_gusts_10m",
                    "dew_point_2m",
                    "uv_index"
                ],
                "daily": ["temperature_2m_max", "temperature_2m_min"],
                "timezone": "auto"
            }

            aq_params = {
                "latitude": lat,
                "longitude": lon,
                "current": ["us_aqi", "pm2_5", "pm10"],
                "timezone": "auto"
            }

            client = get_http_client()
            resp = await client.get(self.FORECAST_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            # Fetch Air Quality (non-blocking failure)
            aqi_us = 35
            pm2_5 = 8.0
            pm10 = 12.0
            try:
                aq_resp = await client.get(self.AIR_QUALITY_URL, params=aq_params)
                if aq_resp.status_code == 200:
                    aq_data = aq_resp.json()
                    current_aq = aq_data.get("current", {})
                    aqi_us = int(current_aq.get("us_aqi") or 35)
                    pm2_5 = float(current_aq.get("pm2_5") or 8.0)
                    pm10 = float(current_aq.get("pm10") or 12.0)
            except Exception as e:
                logger.debug(f"Air quality lookup failed: {e}")

            current = data.get("current", {})
            daily = data.get("daily", {})
            temp = float(current.get("temperature_2m", 20.0))
            feels_like = float(current.get("apparent_temperature", temp))
            wmo_code = int(current.get("weather_code", 0))
            cond_desc, cond_code = wmo_code_to_condition(wmo_code)
            humidity = int(current.get("relative_humidity_2m", 50))
            dew_point = float(current.get("dew_point_2m", 10.0))
            pressure = float(current.get("pressure_msl", 1013.25))
            wind_speed = float(current.get("wind_speed_10m", 0.0))
            wind_gusts = float(current.get("wind_gusts_10m", wind_speed * 1.3))
            wind_dir = int(current.get("wind_direction_10m", 0))
            uv = float(current.get("uv_index", 1.0))
            cloud_cover = int(current.get("cloud_cover", 10))

            temp_min = float(daily.get("temperature_2m_min", [temp - 3])[0])
            temp_max = float(daily.get("temperature_2m_max", [temp + 4])[0])

            # Location metadata
            tz = data.get("timezone", "UTC")
            loc_name = tz.split("/")[-1].replace("_", " ") if "/" in tz else "Current Location"

            lifestyle = compute_lifestyle_indices(
                temp_c=temp,
                humidity=humidity,
                wind_kmh=wind_speed,
                precip_prob=int(current.get("precipitation", 0) > 0) * 80,
                uv_index=uv
            )

            return CurrentWeatherResponse(
                location=LocationSchema(
                    name=loc_name,
                    region=tz.split("/")[0] if "/" in tz else "",
                    country="",
                    timezone=tz,
                    lat=lat,
                    lon=lon
                ),
                current=AtmosphericCondition(
                    timestamp=int(time.time()),
                    temp=round(temp, 1),
                    feels_like=round(feels_like, 1),
                    temp_min=round(temp_min, 1),
                    temp_max=round(temp_max, 1),
                    condition=cond_desc,
                    condition_code=cond_code,
                    humidity=humidity,
                    dew_point=round(dew_point, 1),
                    pressure_hpa=round(pressure, 1),
                    pressure_trend="steady",
                    wind=WindData(
                        speed_kmh=round(wind_speed, 1),
                        gust_kmh=round(wind_gusts, 1),
                        direction_deg=wind_dir,
                        cardinal=deg_to_cardinal(wind_dir)
                    ),
                    uv_index=round(uv, 1),
                    uv_category=uv_to_category(uv),
                    visibility_km=10.0,
                    cloud_cover_pct=cloud_cover,
                    air_quality=AirQualityData(
                        aqi_us=aqi_us,
                        category=aqi_to_category(aqi_us),
                        pm2_5=pm2_5,
                        pm10=pm10
                    )
                ),
                lifestyle_indices=lifestyle,
                source="upstream",
                provider=self.name
            )
        except Exception as e:
            logger.error(f"Open-Meteo get_current_weather failed: {e}")
            return None

    async def get_forecast(
        self, lat: float, lon: float, hourly_steps: int = 48, daily_steps: int = 14
    ) -> Optional[ForecastResponse]:
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": [
                    "temperature_2m",
                    "apparent_temperature",
                    "precipitation_probability",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m"
                ],
                "daily": [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "precipitation_sum",
                    "sunrise",
                    "sunset",
                    "uv_index_max",
                    "wind_speed_10m_max",
                    "wind_direction_10m_dominant"
                ],
                "forecast_days": min(max(daily_steps, 1), 16),
                "timezone": "auto"
            }

            client = get_http_client()
            resp = await client.get(self.FORECAST_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            tz = data.get("timezone", "UTC")
            loc_name = tz.split("/")[-1].replace("_", " ") if "/" in tz else "Current Location"

            # Parse Hourly
            hourly_raw = data.get("hourly", {})
            times = hourly_raw.get("time", [])
            temps = hourly_raw.get("temperature_2m", [])
            feels = hourly_raw.get("apparent_temperature", [])
            precip_probs = hourly_raw.get("precipitation_probability", [])
            precips = hourly_raw.get("precipitation", [])
            codes = hourly_raw.get("weather_code", [])
            winds = hourly_raw.get("wind_speed_10m", [])

            hourly_items: List[HourlyForecastItem] = []
            for i in range(min(len(times), hourly_steps)):
                code = codes[i] if i < len(codes) else 0
                cond_desc, cond_code = wmo_code_to_condition(code)
                hourly_items.append(
                    HourlyForecastItem(
                        time=times[i],
                        temp=round(temps[i], 1) if i < len(temps) else 0.0,
                        feels_like=round(feels[i], 1) if i < len(feels) else 0.0,
                        precip_probability=int(precip_probs[i]) if i < len(precip_probs) else 0,
                        precip_amount_mm=round(precips[i], 1) if i < len(precips) else 0.0,
                        condition=cond_desc,
                        condition_code=cond_code,
                        wind_speed_kmh=round(winds[i], 1) if i < len(winds) else 0.0
                    )
                )

            # Parse Daily
            daily_raw = data.get("daily", {})
            d_times = daily_raw.get("time", [])
            d_codes = daily_raw.get("weather_code", [])
            d_max_temps = daily_raw.get("temperature_2m_max", [])
            d_min_temps = daily_raw.get("temperature_2m_min", [])
            d_precip_probs = daily_raw.get("precipitation_probability_max", [])
            d_precip_sums = daily_raw.get("precipitation_sum", [])
            d_sunrises = daily_raw.get("sunrise", [])
            d_sunsets = daily_raw.get("sunset", [])
            d_uvs = daily_raw.get("uv_index_max", [])
            d_winds = daily_raw.get("wind_speed_10m_max", [])
            d_wind_dirs = daily_raw.get("wind_direction_10m_dominant", [])

            daily_items: List[DailyForecastItem] = []
            for i in range(min(len(d_times), daily_steps)):
                code = d_codes[i] if i < len(d_codes) else 0
                cond_desc, cond_code = wmo_code_to_condition(code)
                date_str = d_times[i]
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    day_name = "Today" if i == 0 else dt.strftime("%A")
                except Exception:
                    day_name = date_str

                wind_deg = d_wind_dirs[i] if i < len(d_wind_dirs) else 0
                sunrise_val = d_sunrises[i] if i < len(d_sunrises) else ""
                sunset_val = d_sunsets[i] if i < len(d_sunsets) else ""
                daylight_str = calculate_daylight_duration(sunrise_val, sunset_val)

                daily_items.append(
                    DailyForecastItem(
                        date=date_str,
                        day_name=day_name,
                        temp_min=round(d_min_temps[i], 1) if i < len(d_min_temps) else 0.0,
                        temp_max=round(d_max_temps[i], 1) if i < len(d_max_temps) else 0.0,
                        condition=cond_desc,
                        condition_code=cond_code,
                        precip_probability=int(d_precip_probs[i]) if i < len(d_precip_probs) else 0,
                        precip_accumulation_mm=round(d_precip_sums[i], 1) if i < len(d_precip_sums) else 0.0,
                        sunrise=sunrise_val,
                        sunset=sunset_val,
                        daylight_duration=daylight_str,
                        uv_max=round(d_uvs[i], 1) if i < len(d_uvs) else 0.0,
                        wind_speed_max_kmh=round(d_winds[i], 1) if i < len(d_winds) else 0.0,
                        wind_direction_dominant=deg_to_cardinal(wind_deg)
                    )
                )

            return ForecastResponse(
                location=LocationSchema(
                    name=loc_name,
                    region=tz.split("/")[0] if "/" in tz else "",
                    country="",
                    timezone=tz,
                    lat=lat,
                    lon=lon
                ),
                hourly=hourly_items,
                daily=daily_items,
                source="upstream",
                provider=self.name
            )
        except Exception as e:
            logger.error(f"Open-Meteo get_forecast failed: {e}")
            return None

    async def get_alerts(self, lat: float, lon: float) -> Optional[WeatherAlertsResponse]:
        """
        Fetch meteorological alerts. Evaluates real-time weather extremes and warnings.
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "apparent_temperature",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "weather_code",
                    "uv_index"
                ],
                "daily": ["temperature_2m_max", "precipitation_sum", "wind_speed_10m_max"],
                "timezone": "auto"
            }
            client = get_http_client()
            resp = await client.get(self.FORECAST_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            tz = data.get("timezone", "UTC")
            city = tz.split("/")[-1].replace("_", " ") if "/" in tz else "Current Area"
            current = data.get("current", {})
            daily = data.get("daily", {})

            temp = float(current.get("temperature_2m", 20.0))
            wind_speed = float(current.get("wind_speed_10m", 0.0))
            wind_gusts = float(current.get("wind_gusts_10m", 0.0))
            wmo_code = int(current.get("weather_code", 0))
            uv = float(current.get("uv_index", 0.0))
            rain_sum = float(daily.get("precipitation_sum", [0.0])[0]) if daily.get("precipitation_sum") else 0.0

            alerts: List[WeatherAlertItem] = []

            # 1. Severe thunderstorm / Violent storm detection
            if wmo_code in [95, 96, 99]:
                sev = "warning" if wmo_code in [96, 99] else "watch"
                alerts.append(
                    WeatherAlertItem(
                        id=f"alert_storm_{round(lat, 2)}_{round(lon, 2)}",
                        event_title="Severe Thunderstorm Alert",
                        severity=AlertSeverityEnum(sev),
                        severity_level=severity_to_level(sev),
                        urgency="Immediate",
                        certainty="Observed",
                        issuing_agency="National Weather Service & Open-Meteo",
                        headline=f"Severe thunderstorm conditions detected in {city}",
                        description=f"Active thunderstorm cells with lightning, heavy downpours, and potential hail. Wind gusts up to {wind_gusts:.1f} km/h.",
                        instructions="Seek sturdy indoor shelter immediately. Avoid tall trees and open electrical equipment.",
                        starts_at=datetime.utcnow().isoformat() + "Z",
                        expires_at=datetime.utcnow().isoformat() + "Z",
                        is_active=True
                    )
                )

            # 2. Extreme Heat Warning
            if temp >= 38.0:
                sev = "emergency" if temp >= 42.0 else "warning"
                alerts.append(
                    WeatherAlertItem(
                        id=f"alert_heat_{round(lat, 2)}_{round(lon, 2)}",
                        event_title="Extreme Heatwave Warning",
                        severity=AlertSeverityEnum(sev),
                        severity_level=severity_to_level(sev),
                        urgency="Expected",
                        certainty="High",
                        issuing_agency="Public Health & Meteorological Bureau",
                        headline=f"Extreme high temperatures reaching {temp:.1f}°C in {city}",
                        description=f"Dangerously high thermal conditions. Extended outdoor exposure may cause heat exhaustion or heat stroke.",
                        instructions="Stay hydrated, remain indoors in air-conditioned environments, and avoid strenuous outdoor activity during peak sun hours.",
                        starts_at=datetime.utcnow().isoformat() + "Z",
                        expires_at=datetime.utcnow().isoformat() + "Z",
                        is_active=True
                    )
                )

            # 3. High Wind / Gale Alert
            if wind_gusts >= 65.0 or wind_speed >= 50.0:
                sev = "warning" if wind_gusts >= 80.0 else "watch"
                alerts.append(
                    WeatherAlertItem(
                        id=f"alert_wind_{round(lat, 2)}_{round(lon, 2)}",
                        event_title="High Wind Warning",
                        severity=AlertSeverityEnum(sev),
                        severity_level=severity_to_level(sev),
                        urgency="Immediate",
                        certainty="Observed",
                        issuing_agency="Meteorological Department",
                        headline=f"Hazardous wind gusts up to {wind_gusts:.1f} km/h expected in {city}",
                        description="Strong sustained winds and damaging gusts may cause falling branches and travel disruptions.",
                        instructions="Secure loose outdoor objects and exercise extreme caution when operating high-profile vehicles.",
                        starts_at=datetime.utcnow().isoformat() + "Z",
                        expires_at=datetime.utcnow().isoformat() + "Z",
                        is_active=True
                    )
                )

            # 4. Heavy Rain / Flood Risk
            if rain_sum >= 50.0 or wmo_code in [65, 82]:
                alerts.append(
                    WeatherAlertItem(
                        id=f"alert_flood_{round(lat, 2)}_{round(lon, 2)}",
                        event_title="Heavy Rainfall & Flood Advisory",
                        severity=AlertSeverityEnum.WATCH,
                        severity_level=2,
                        urgency="Expected",
                        certainty="Moderate",
                        issuing_agency="Hydrological Safety Division",
                        headline=f"Heavy rainfall accumulation of {rain_sum:.1f} mm forecast in {city}",
                        description="Intense rainfall could lead to localized flash flooding in low-lying and poor drainage areas.",
                        instructions="Avoid driving through flooded roadways. Monitor local water levels.",
                        starts_at=datetime.utcnow().isoformat() + "Z",
                        expires_at=datetime.utcnow().isoformat() + "Z",
                        is_active=True
                    )
                )

            highest_sev = None
            if alerts:
                # Find maximum severity level
                sorted_alerts = sorted(alerts, key=lambda a: a.severity_level, reverse=True)
                highest_sev = sorted_alerts[0].severity

            return WeatherAlertsResponse(
                location=AlertLocation(lat=lat, lon=lon, city=city),
                alerts_count=len(alerts),
                highest_severity=highest_sev,
                alerts=alerts,
                source="upstream",
                cached=False
            )
        except Exception as e:
            logger.error(f"Open-Meteo get_alerts failed: {e}")
            return None

    async def search_locations(self, query: str) -> List[LocationSearchResult]:
        try:
            params = {
                "name": query.strip(),
                "count": 10,
                "language": "en",
                "format": "json"
            }
            client = get_http_client()
            resp = await client.get(self.GEOCODING_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            results: List[LocationSearchResult] = []
            for item in data.get("results", []):
                lat = float(item.get("latitude"))
                lon = float(item.get("longitude"))
                name = item.get("name", "")
                admin = item.get("admin1") or item.get("admin2") or ""
                country = item.get("country", "")
                cc = item.get("country_code", "")
                tz = item.get("timezone", "UTC")
                results.append(
                    LocationSearchResult(
                        id=f"geo_{lat}_{lon}",
                        name=name,
                        administrative_area=admin,
                        country=country,
                        country_code=cc,
                        lat=lat,
                        lon=lon,
                        timezone=tz
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Open-Meteo geocoding search failed: {e}")
            return []
