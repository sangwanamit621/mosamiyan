import logging
from typing import List, Optional
import time
from app.config import get_settings
from app.schemas.weather import CurrentWeatherResponse, ForecastResponse
from app.schemas.alert import WeatherAlertsResponse
from app.schemas.radar import RadarFrame, RadarMetadataResponse
from app.services.http_client import get_http_client
from app.services.cache_service import (
    get_cached_json,
    make_alerts_key,
    make_current_weather_key,
    make_forecast_key,
    make_radar_key,
    set_cached_json,
)
from app.services.providers.base_provider import BaseWeatherProvider
from app.services.providers.openmeteo_provider import OpenMeteoProvider
from app.services.providers.openweathermap_provider import OpenWeatherMapProvider
from app.services.providers.weatherapi_provider import WeatherAPIProvider

logger = logging.getLogger("mosamiyan.weather_service")


class WeatherService:
    """
    Coordinates weather data retrieval with Redis caching and multi-tier provider failover.
    Primary: Open-Meteo -> Secondary: OpenWeatherMap -> Tertiary: WeatherAPI.com
    """

    def __init__(self):
        self.settings = get_settings()
        self.providers: List[BaseWeatherProvider] = [
            OpenMeteoProvider(),
            OpenWeatherMapProvider(),
            WeatherAPIProvider(),
        ]

    def _convert_current_units(self, data: CurrentWeatherResponse, units: str) -> CurrentWeatherResponse:
        """Convert metric values to imperial (°F, mph, in, mi) if requested."""
        if units.lower() != "imperial":
            return data

        c = data.current
        # Celsius to Fahrenheit: (C * 9/5) + 32
        temp_f = round((c.temp * 9 / 5) + 32, 1)
        feels_f = round((c.feels_like * 9 / 5) + 32, 1)
        min_f = round((c.temp_min * 9 / 5) + 32, 1)
        max_f = round((c.temp_max * 9 / 5) + 32, 1)
        dew_f = round((c.dew_point * 9 / 5) + 32, 1)

        # km/h to mph: kmh * 0.621371
        speed_mph = round(c.wind.speed_kmh * 0.621371, 1)
        gust_mph = round(c.wind.gust_kmh * 0.621371, 1)

        # km to miles
        vis_mi = round(c.visibility_km * 0.621371, 1)

        c.temp = temp_f
        c.feels_like = feels_f
        c.temp_min = min_f
        c.temp_max = max_f
        c.dew_point = dew_f
        c.wind.speed_kmh = speed_mph
        c.wind.gust_kmh = gust_mph
        c.visibility_km = vis_mi
        return data

    def _convert_forecast_units(self, data: ForecastResponse, units: str) -> ForecastResponse:
        if units.lower() != "imperial":
            return data

        for h in data.hourly:
            h.temp = round((h.temp * 9 / 5) + 32, 1)
            h.feels_like = round((h.feels_like * 9 / 5) + 32, 1)
            h.wind_speed_kmh = round(h.wind_speed_kmh * 0.621371, 1)
            h.precip_amount_mm = round(h.precip_amount_mm * 0.0393701, 2)  # mm to inches

        for d in data.daily:
            d.temp_min = round((d.temp_min * 9 / 5) + 32, 1)
            d.temp_max = round((d.temp_max * 9 / 5) + 32, 1)
            d.wind_speed_max_kmh = round(d.wind_speed_max_kmh * 0.621371, 1)
            d.precip_accumulation_mm = round(d.precip_accumulation_mm * 0.0393701, 2)

        return data

    async def get_current_weather(
        self, lat: float, lon: float, units: str = "metric"
    ) -> Optional[CurrentWeatherResponse]:
        cache_key = make_current_weather_key(lat, lon)
        cached_data = await get_cached_json(cache_key)

        if cached_data:
            response_obj = CurrentWeatherResponse.model_validate(cached_data)
            response_obj.source = "cache"
            return self._convert_current_units(response_obj, units)

        # Multi-tier upstream failover
        for provider in self.providers:
            try:
                result = await provider.get_current_weather(lat, lon)
                if result:
                    # Store in Redis cache (metric representation)
                    await set_cached_json(cache_key, result.model_dump(), self.settings.CACHE_TTL_CURRENT)
                    result.source = "upstream"
                    return self._convert_current_units(result, units)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed during current weather fetch: {e}")

        logger.error(f"All weather providers failed for coordinates ({lat}, {lon})")
        return None

    async def get_forecast(
        self, lat: float, lon: float, hourly_steps: int = 48, daily_steps: int = 14, units: str = "metric"
    ) -> Optional[ForecastResponse]:
        cache_key = make_forecast_key(lat, lon, hourly_steps, daily_steps)
        cached_data = await get_cached_json(cache_key)

        if cached_data:
            response_obj = ForecastResponse.model_validate(cached_data)
            response_obj.source = "cache"
            return self._convert_forecast_units(response_obj, units)

        # Multi-tier upstream failover
        for provider in self.providers:
            try:
                result = await provider.get_forecast(lat, lon, hourly_steps, daily_steps)
                if result:
                    await set_cached_json(cache_key, result.model_dump(), self.settings.CACHE_TTL_HOURLY)
                    result.source = "upstream"
                    return self._convert_forecast_units(result, units)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed during forecast fetch: {e}")

        logger.error(f"All weather providers failed for forecast ({lat}, {lon})")
        return None

    async def get_alerts(self, lat: float, lon: float) -> Optional[WeatherAlertsResponse]:
        cache_key = make_alerts_key(lat, lon)
        cached_data = await get_cached_json(cache_key)

        if cached_data:
            response_obj = WeatherAlertsResponse.model_validate(cached_data)
            response_obj.cached = True
            return response_obj

        # Multi-tier upstream failover for active alerts
        for provider in self.providers:
            try:
                result = await provider.get_alerts(lat, lon)
                if result:
                    await set_cached_json(cache_key, result.model_dump(), self.settings.CACHE_TTL_ALERTS)
                    result.cached = False
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed during alerts fetch: {e}")

        logger.info(f"No active alerts returned for coordinates ({lat}, {lon})")
        return WeatherAlertsResponse(
            location={"lat": lat, "lon": lon, "city": "Current Location"},
            alerts_count=0,
            alerts=[]
        )

    async def get_radar_frames(self) -> Optional[RadarMetadataResponse]:
        cache_key = make_radar_key()
        cached_data = await get_cached_json(cache_key)

        if cached_data:
            return RadarMetadataResponse.model_validate(cached_data)

        try:
            client = get_http_client()
            resp = await client.get(self.settings.RAINVIEWER_API_URL, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                host = data.get("host", "https://tilecache.rainviewer.com")
                gen_at = int(data.get("generated", time.time()))

                radar_dict = data.get("radar", {})
                past_list = radar_dict.get("past", [])
                nowcast_list = radar_dict.get("nowcast", [])

                past_frames = [
                    RadarFrame(time=int(item.get("time")), path=item.get("path"), type="past")
                    for item in past_list if item.get("path")
                ]
                nowcast_frames = [
                    RadarFrame(time=int(item.get("time")), path=item.get("path"), type="nowcast")
                    for item in nowcast_list if item.get("path")
                ]

                response_obj = RadarMetadataResponse(
                    host=host,
                    generated_at=gen_at,
                    past_frames=past_frames,
                    nowcast_frames=nowcast_frames,
                    color_scheme=2,
                    smooth=1
                )
                await set_cached_json(cache_key, response_obj.model_dump(), self.settings.CACHE_TTL_RADAR)
                return response_obj
        except Exception as e:
            logger.warning(f"RainViewer radar metadata fetch failed: {e}")

        # Fallback empty structure
        now_ts = int(time.time())
        return RadarMetadataResponse(
            host="https://tilecache.rainviewer.com",
            generated_at=now_ts,
            past_frames=[],
            nowcast_frames=[]
        )


# Global singleton instance
weather_service = WeatherService()
