import logging
from typing import List, Optional
from app.config import get_settings
from app.schemas.weather import CurrentWeatherResponse, ForecastResponse
from app.services.cache_service import (
    get_cached_json,
    make_current_weather_key,
    make_forecast_key,
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
        c.wind.speed_kmh = speed_mph  # Field holds the unit value requested
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
        self, lat: float, lon: float, hourly_steps: int = 24, daily_steps: int = 7, units: str = "metric"
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


# Global singleton instance
weather_service = WeatherService()
