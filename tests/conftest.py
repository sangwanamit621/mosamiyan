import json
import pytest
import httpx
from unittest.mock import patch
from datetime import datetime, timedelta

from app.database import close_db_pool, init_db_pool
from app.services.cache_service import close_redis_pool, init_redis_pool
from app.services.http_client import close_http_client, init_http_client
import app.services.http_client as http_client_module


def generate_mock_openmeteo_forecast(lat=28.61, lon=77.21):
    now = datetime.now()
    hourly_times = [(now + timedelta(hours=i)).strftime("%Y-%m-%dT%H:00") for i in range(48)]
    daily_times = [(now + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(16)]

    return {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Asia/Kolkata",
        "current": {
            "time": now.strftime("%Y-%m-%dT%H:00"),
            "temperature_2m": 25.0,
            "relative_humidity_2m": 60,
            "apparent_temperature": 26.0,
            "surface_pressure": 1012.0,
            "wind_speed_10m": 12.0,
            "wind_direction_10m": 180,
            "wind_gusts_10m": 18.0,
            "weather_code": 1,
            "cloud_cover": 20,
            "dew_point_2m": 16.0,
            "visibility": 10000.0,
            "uv_index": 5.0
        },
        "hourly": {
            "time": hourly_times,
            "temperature_2m": [25.0 + (i % 5) for i in range(48)],
            "relative_humidity_2m": [60 for _ in range(48)],
            "apparent_temperature": [26.0 for _ in range(48)],
            "precipitation_probability": [20 for _ in range(48)],
            "precipitation": [0.0 for _ in range(48)],
            "weather_code": [1 for _ in range(48)],
            "surface_pressure": [1012.0 for _ in range(48)],
            "wind_speed_10m": [12.0 for _ in range(48)],
            "wind_direction_10m": [180 for _ in range(48)],
            "wind_gusts_10m": [18.0 for _ in range(48)],
            "uv_index": [4.0 for _ in range(48)],
            "visibility": [10000.0 for _ in range(48)],
            "dew_point_2m": [16.0 for _ in range(48)]
        },
        "daily": {
            "time": daily_times,
            "weather_code": [1 for _ in range(16)],
            "temperature_2m_max": [30.0 for _ in range(16)],
            "temperature_2m_min": [20.0 for _ in range(16)],
            "apparent_temperature_max": [31.0 for _ in range(16)],
            "apparent_temperature_min": [21.0 for _ in range(16)],
            "precipitation_sum": [0.0 for _ in range(16)],
            "precipitation_probability_max": [25 for _ in range(16)],
            "wind_speed_10m_max": [15.0 for _ in range(16)],
            "wind_gusts_10m_max": [22.0 for _ in range(16)],
            "wind_direction_10m_dominant": [180 for _ in range(16)],
            "uv_index_max": [6.0 for _ in range(16)],
            "sunrise": [f"{d}T05:30" for d in daily_times],
            "sunset": [f"{d}T18:45" for d in daily_times]
        }
    }


def generate_mock_air_quality():
    return {
        "current": {
            "us_aqi": 35,
            "pm2_5": 8.0,
            "pm10": 15.0
        }
    }


def generate_mock_geocoding():
    return {
        "results": [
            {
                "id": 1,
                "name": "New Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "country_code": "IN",
                "country": "India",
                "admin1": "Delhi",
                "timezone": "Asia/Kolkata"
            }
        ]
    }


def generate_mock_rainviewer():
    return {
        "host": "https://tilecache.rainviewer.com",
        "generated": 1774828800,
        "radar": {
            "past": [{"time": 1774828800, "path": "/v2/radar/1774828800/256/1/1/1/2/1_1.png"}],
            "nowcast": [{"time": 1774832400, "path": "/v2/radar/1774832400/256/1/1/1/2/1_1.png"}]
        }
    }


class MockNetworkTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)

        if "api.open-meteo.com" in url_str:
            data = generate_mock_openmeteo_forecast()
            return httpx.Response(200, json=data, request=request)

        if "air-quality-api.open-meteo.com" in url_str:
            data = generate_mock_air_quality()
            return httpx.Response(200, json=data, request=request)

        if "geocoding-api.open-meteo.com" in url_str:
            data = generate_mock_geocoding()
            return httpx.Response(200, json=data, request=request)

        if "rainviewer.com" in url_str:
            data = generate_mock_rainviewer()
            return httpx.Response(200, json=data, request=request)

        return httpx.Response(200, json={}, request=request)


@pytest.fixture(autouse=True, scope="function")
async def setup_test_environment():
    """Ensure database connection pool, redis, and mock http client are initialized per test function."""
    await init_db_pool()
    await init_redis_pool()

    # Initialize client with mock transport for hermetic tests
    mock_client = httpx.AsyncClient(
        transport=MockNetworkTransport(),
        timeout=httpx.Timeout(10.0)
    )
    http_client_module._http_client = mock_client

    yield

    if http_client_module._http_client and not http_client_module._http_client.is_closed:
        await http_client_module._http_client.aclose()
    http_client_module._http_client = None

    await close_db_pool()
    await close_redis_pool()
