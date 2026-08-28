import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.weather_utils import calculate_daylight_duration


def test_calculate_daylight_duration():
    # Regular ISO timestamp strings
    sunrise = "2026-08-28T05:30"
    sunset = "2026-08-28T18:45"
    duration = calculate_daylight_duration(sunrise, sunset)
    assert duration == "13h 15m"

    # HH:MM string format
    assert calculate_daylight_duration("06:00", "18:30") == "12h 30m"
    assert calculate_daylight_duration("05:45", "17:45") == "12h 00m"

    # Fallback for empty strings
    assert calculate_daylight_duration("", "") == "12h 00m"


@pytest.mark.asyncio
async def test_48_hour_and_14_day_forecast_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/weather/forecast?lat=28.6139&lon=77.2090&hourly_steps=48&daily_steps=14")
        assert resp.status_code == 200
        data = resp.json()

        # Check Hourly data
        assert "hourly" in data
        assert len(data["hourly"]) > 24  # Confirms extended horizon beyond 24h
        first_hour = data["hourly"][0]
        assert "time" in first_hour
        assert "temp" in first_hour
        assert "precip_probability" in first_hour

        # Check Daily data
        assert "daily" in data
        assert len(data["daily"]) >= 7
        first_day = data["daily"][0]
        assert "date" in first_day
        assert "day_name" in first_day
        assert "sunrise" in first_day
        assert "sunset" in first_day
        assert "daylight_duration" in first_day
        assert "uv_max" in first_day


@pytest.mark.asyncio
async def test_forecast_unit_conversion():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        metric_resp = await ac.get("/api/v1/weather/forecast?lat=28.6139&lon=77.2090&hourly_steps=1&daily_steps=1&units=metric")
        imperial_resp = await ac.get("/api/v1/weather/forecast?lat=28.6139&lon=77.2090&hourly_steps=1&daily_steps=1&units=imperial")

        assert metric_resp.status_code == 200
        assert imperial_resp.status_code == 200

        m_data = metric_resp.json()
        i_data = imperial_resp.json()

        m_temp = m_data["hourly"][0]["temp"]
        i_temp = i_data["hourly"][0]["temp"]
        expected_f = round((m_temp * 9 / 5) + 32, 1)

        # Allow slight rounding variance
        assert abs(i_temp - expected_f) <= 0.5
