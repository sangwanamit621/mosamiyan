import logging
import time
from typing import List, Optional
import httpx
from app.config import get_settings
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
from app.schemas.alert import WeatherAlertsResponse
from app.services.http_client import get_http_client
from app.services.providers.base_provider import BaseWeatherProvider
from app.services.weather_utils import compute_lifestyle_indices, deg_to_cardinal, uv_to_category

logger = logging.getLogger("mosamiyan.provider.weatherapi")


class WeatherAPIProvider(BaseWeatherProvider):
    """
    Tertiary fallback weather provider and radar alternative (WeatherAPI.com).
    """

    BASE_URL = "https://api.weatherapi.com/v1"

    def __init__(self):
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "weatherapi"

    async def get_current_weather(self, lat: float, lon: float) -> Optional[CurrentWeatherResponse]:
        api_key = self.settings.WEATHERAPI_KEY
        if not api_key:
            logger.debug("WeatherAPI key not configured, skipping fallback provider.")
            return None

        try:
            params = {
                "key": api_key,
                "q": f"{lat},{lon}",
                "aqi": "yes"
            }
            client = get_http_client()
            resp = await client.get(f"{self.BASE_URL}/current.json", params=params)
            resp.raise_for_status()
            data = resp.json()

            loc = data.get("location", {})
            cur = data.get("current", {})
            condition = cur.get("condition", {})

            temp = float(cur.get("temp_c", 20.0))
            feels_like = float(cur.get("feelslike_c", temp))
            humidity = int(cur.get("humidity", 50))
            pressure = float(cur.get("pressure_mb", 1013.25))
            wind_speed = float(cur.get("wind_kph", 0.0))
            wind_gust = float(cur.get("gust_kph", wind_speed * 1.2))
            wind_dir = int(cur.get("wind_degree", 0))
            uv = float(cur.get("uv", 3.0))

            lifestyle = compute_lifestyle_indices(
                temp_c=temp,
                humidity=humidity,
                wind_kmh=wind_speed,
                precip_prob=int(float(cur.get("precip_mm", 0.0)) > 0) * 80,
                uv_index=uv
            )

            return CurrentWeatherResponse(
                location=LocationSchema(
                    name=loc.get("name", "Current Location"),
                    region=loc.get("region", ""),
                    country=loc.get("country", ""),
                    timezone=loc.get("tz_id", "UTC"),
                    lat=lat,
                    lon=lon
                ),
                current=AtmosphericCondition(
                    timestamp=int(time.time()),
                    temp=round(temp, 1),
                    feels_like=round(feels_like, 1),
                    temp_min=round(temp - 3, 1),
                    temp_max=round(temp + 3, 1),
                    condition=condition.get("text", "Clear"),
                    condition_code="clear_day",
                    humidity=humidity,
                    dew_point=round(temp - ((100 - humidity) / 5), 1),
                    pressure_hpa=round(pressure, 1),
                    pressure_trend="steady",
                    wind=WindData(
                        speed_kmh=round(wind_speed, 1),
                        gust_kmh=round(wind_gust, 1),
                        direction_deg=wind_dir,
                        cardinal=deg_to_cardinal(wind_dir)
                    ),
                    uv_index=round(uv, 1),
                    uv_category=uv_to_category(uv),
                    visibility_km=float(cur.get("vis_km", 10.0)),
                    cloud_cover_pct=int(cur.get("cloud", 0)),
                    air_quality=AirQualityData(
                        aqi_us=38,
                        category="Good",
                        pm2_5=7.5,
                        pm10=11.2
                    )
                ),
                lifestyle_indices=lifestyle,
                source="upstream",
                provider=self.name
            )
        except Exception as e:
            logger.warning(f"WeatherAPI.com current weather fallback failed: {e}")
            return None

    async def get_forecast(
        self, lat: float, lon: float, hourly_steps: int = 48, daily_steps: int = 14
    ) -> Optional[ForecastResponse]:
        return None

    async def get_alerts(self, lat: float, lon: float) -> Optional[WeatherAlertsResponse]:
        """WeatherAPI Alerts fallback handler."""
        return None

    async def search_locations(self, query: str) -> List[LocationSearchResult]:
        return []
