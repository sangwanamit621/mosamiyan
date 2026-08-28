import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.alert import AlertSeverityEnum, WeatherAlertItem, WeatherAlertsResponse
from app.services.weather_utils import normalize_alert_severity, severity_to_level


def test_alert_severity_normalization():
    assert normalize_alert_severity("Flash Flood Warning") == "warning"
    assert normalize_alert_severity("Tornado Emergency") == "emergency"
    assert normalize_alert_severity("Winter Storm Watch") == "watch"
    assert normalize_alert_severity("Dense Fog Advisory") == "advisory"
    assert normalize_alert_severity("Unknown text") == "advisory"


def test_severity_level_ranking():
    assert severity_to_level("advisory") == 1
    assert severity_to_level("watch") == 2
    assert severity_to_level("warning") == 3
    assert severity_to_level("emergency") == 4


def test_alert_schema_validation():
    alert = WeatherAlertItem(
        id="test_alert_1",
        event_title="Flood Warning",
        severity=AlertSeverityEnum.WARNING,
        severity_level=3,
        headline="Heavy flooding expected in low-lying areas",
        description="Water levels are rising rapidly.",
        instructions="Move to higher ground immediately.",
        starts_at="2026-08-28T10:00:00Z",
        expires_at="2026-08-28T22:00:00Z"
    )
    assert alert.severity == "warning"
    assert alert.severity_level == 3
    assert alert.is_active is True

    response = WeatherAlertsResponse(
        location={"lat": 28.61, "lon": 77.21, "city": "New Delhi"},
        alerts_count=1,
        highest_severity=AlertSeverityEnum.WARNING,
        alerts=[alert]
    )
    assert response.alerts_count == 1
    assert response.highest_severity == "warning"


@pytest.mark.asyncio
async def test_alerts_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/weather/alerts?lat=28.6139&lon=77.2090")
        assert resp.status_code == 200
        data = resp.json()
        assert "location" in data
        assert "alerts_count" in data
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
