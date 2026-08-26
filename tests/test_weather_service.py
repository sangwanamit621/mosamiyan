import pytest
from app.services.cache_service import normalize_coords, make_current_weather_key, make_forecast_key
from app.services.weather_utils import deg_to_cardinal, uv_to_category, compute_lifestyle_indices
from app.services.weather_service import weather_service


def test_coordinate_normalization():
    lat, lon = normalize_coords(51.507351, -0.127758)
    assert lat == 51.51
    assert lon == -0.13

    key = make_current_weather_key(51.507351, -0.127758)
    assert key == "weather:current:51.51:-0.13"


def test_weather_utils():
    assert deg_to_cardinal(0) == "N"
    assert deg_to_cardinal(90) == "E"
    assert deg_to_cardinal(180) == "S"
    assert deg_to_cardinal(270) == "W"

    assert uv_to_category(2.0) == "Low"
    assert uv_to_category(4.5) == "Moderate"
    assert uv_to_category(7.5) == "High"
    assert uv_to_category(9.0) == "Very High"
    assert uv_to_category(12.0) == "Extreme"

    indices = compute_lifestyle_indices(
        temp_c=15.0, humidity=50, wind_kmh=10.0, precip_prob=0, uv_index=4.0
    )
    assert indices["outdoor_running"]["rating"] in ["Optimal", "Good"]
    assert indices["car_wash"]["rating"] == "Great"


@pytest.mark.asyncio
async def test_live_weather_fetch():
    res = await weather_service.get_current_weather(51.5074, -0.1278, units="metric")
    assert res is not None
    assert res.current.temp is not None
    assert res.current.humidity > 0

    # Test Imperial Conversion
    res_imp = await weather_service.get_current_weather(51.5074, -0.1278, units="imperial")
    assert res_imp is not None
    assert res_imp.current.temp is not None
