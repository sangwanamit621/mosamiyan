import pytest
from app.services.weather_service import WeatherService
from app.schemas.weather import CurrentWeatherResponse, LocationSchema, AtmosphericCondition, WindData, AirQualityData
import time


class MockFailingProvider:
    name = "mock_failing_provider"
    async def get_current_weather(self, lat, lon):
        raise RuntimeError("Provider connection timeout")
    async def get_forecast(self, lat, lon, hourly_steps=24, daily_steps=7):
        raise RuntimeError("Provider connection timeout")
    async def search_locations(self, query):
        return []


class MockSuccessfulProvider:
    name = "mock_backup_provider"
    async def get_current_weather(self, lat, lon):
        return CurrentWeatherResponse(
            location=LocationSchema(name="Backup City", country="GB", timezone="UTC", lat=lat, lon=lon),
            current=AtmosphericCondition(
                timestamp=int(time.time()),
                temp=18.5,
                feels_like=18.0,
                temp_min=15.0,
                temp_max=22.0,
                condition="Clear",
                condition_code="clear_day",
                humidity=45,
                dew_point=7.0,
                pressure_hpa=1015.0,
                pressure_trend="rising",
                wind=WindData(speed_kmh=12.0, gust_kmh=18.0, direction_deg=180, cardinal="S"),
                uv_index=4.0,
                uv_category="Moderate",
                visibility_km=10.0,
                cloud_cover_pct=10,
                air_quality=AirQualityData(aqi_us=25, category="Good", pm2_5=5.0, pm10=8.0)
            ),
            source="upstream",
            provider=self.name
        )
    async def get_forecast(self, lat, lon, hourly_steps=24, daily_steps=7):
        return None
    async def search_locations(self, query):
        return []


@pytest.mark.asyncio
async def test_multi_tier_fallback_resilience():
    service = WeatherService()
    # Inject primary failure and backup success
    service.providers = [MockFailingProvider(), MockSuccessfulProvider()]

    res = await service.get_current_weather(35.68, 139.76, units="metric")
    assert res is not None
    assert res.provider == "mock_backup_provider"
    assert res.current.temp == 18.5
