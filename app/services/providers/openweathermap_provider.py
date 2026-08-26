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
from app.services.providers.base_provider import BaseWeatherProvider
from app.services.weather_utils import compute_lifestyle_indices, deg_to_cardinal, uv_to_category

logger = logging.getLogger("mosamiyan.provider.openweathermap")


class OpenWeatherMapProvider(BaseWeatherProvider):
    """
    Secondary fallback weather provider and primary provider for radar layers.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

    def __init__(self):
        self.settings = get_settings()

    @property
    def name(self) -> str:
        return "openweathermap"

    async def get_current_weather(self, lat: float, lon: float) -> Optional[CurrentWeatherResponse]:
        api_key = self.settings.OPENWEATHERMAP_API_KEY
        if not api_key:
            logger.debug("OpenWeatherMap API key not configured, skipping fallback provider.")
            return None

        try:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric"
            }
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.BASE_URL}/weather", params=params)
                resp.raise_for_status()
                data = resp.json()

            main = data.get("main", {})
            wind = data.get("wind", {})
            weather_arr = data.get("weather", [{}])
            w_item = weather_arr[0] if weather_arr else {}

            temp = float(main.get("temp", 20.0))
            feels_like = float(main.get("feels_like", temp))
            temp_min = float(main.get("temp_min", temp - 2))
            temp_max = float(main.get("temp_max", temp + 2))
            humidity = int(main.get("humidity", 50))
            pressure = float(main.get("pressure", 1013.25))

            wind_speed = float(wind.get("speed", 0.0)) * 3.6  # m/s to km/h
            wind_gusts = float(wind.get("gust", wind.get("speed", 0.0))) * 3.6
            wind_deg = int(wind.get("deg", 0))

            lifestyle = compute_lifestyle_indices(
                temp_c=temp,
                humidity=humidity,
                wind_kmh=wind_speed,
                precip_prob=0,
                uv_index=3.0
            )

            return CurrentWeatherResponse(
                location=LocationSchema(
                    name=data.get("name", "Current Location"),
                    region="",
                    country=data.get("sys", {}).get("country", ""),
                    timezone="UTC",
                    lat=lat,
                    lon=lon
                ),
                current=AtmosphericCondition(
                    timestamp=int(time.time()),
                    temp=round(temp, 1),
                    feels_like=round(feels_like, 1),
                    temp_min=round(temp_min, 1),
                    temp_max=round(temp_max, 1),
                    condition=w_item.get("main", "Clear"),
                    condition_code=w_item.get("icon", "clear_day"),
                    humidity=humidity,
                    dew_point=round(temp - ((100 - humidity) / 5), 1),
                    pressure_hpa=round(pressure, 1),
                    pressure_trend="steady",
                    wind=WindData(
                        speed_kmh=round(wind_speed, 1),
                        gust_kmh=round(wind_gusts, 1),
                        direction_deg=wind_deg,
                        cardinal=deg_to_cardinal(wind_deg)
                    ),
                    uv_index=3.0,
                    uv_category=uv_to_category(3.0),
                    visibility_km=round(float(data.get("visibility", 10000)) / 1000.0, 1),
                    cloud_cover_pct=int(data.get("clouds", {}).get("all", 0)),
                    air_quality=AirQualityData(
                        aqi_us=40,
                        category="Good",
                        pm2_5=8.0,
                        pm10=12.0
                    )
                ),
                lifestyle_indices=lifestyle,
                source="upstream",
                provider=self.name
            )
        except Exception as e:
            logger.warning(f"OpenWeatherMap current weather fallback failed: {e}")
            return None

    async def get_forecast(
        self, lat: float, lon: float, hourly_steps: int = 24, daily_steps: int = 7
    ) -> Optional[ForecastResponse]:
        # OWM 5-day / 3-hour forecast fallback
        return None

    async def search_locations(self, query: str) -> List[LocationSearchResult]:
        api_key = self.settings.OPENWEATHERMAP_API_KEY
        if not api_key:
            return []
        try:
            params = {"q": query.strip(), "limit": 5, "appid": api_key}
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(self.GEO_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            results: List[LocationSearchResult] = []
            for item in data:
                lat = float(item.get("lat"))
                lon = float(item.get("lon"))
                results.append(
                    LocationSearchResult(
                        id=f"owm_{lat}_{lon}",
                        name=item.get("name", ""),
                        administrative_area=item.get("state", ""),
                        country=item.get("country", ""),
                        country_code=item.get("country", ""),
                        lat=lat,
                        lon=lon,
                        timezone="UTC"
                    )
                )
            return results
        except Exception as e:
            logger.warning(f"OpenWeatherMap geocoding fallback failed: {e}")
            return []
