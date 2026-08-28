import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_weather_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Current weather
        cur_resp = await ac.get("/api/v1/weather/current?lat=51.5074&lon=-0.1278")
        assert cur_resp.status_code == 200
        cur_data = cur_resp.json()
        assert "current" in cur_data
        assert "temp" in cur_data["current"]
        assert "wind" in cur_data["current"]
        assert "lifestyle_indices" in cur_data

        # Forecast
        fc_resp = await ac.get("/api/v1/weather/forecast?lat=51.5074&lon=-0.1278&hourly_steps=24&daily_steps=7")
        assert fc_resp.status_code == 200
        fc_data = fc_resp.json()
        assert len(fc_data["hourly"]) > 0
        assert len(fc_data["daily"]) > 0


@pytest.mark.asyncio
async def test_location_search():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/locations/search?q=New Delhi")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert any("New Delhi" in r["name"] for r in data["results"])


@pytest.mark.asyncio
async def test_favorites_crud():
    from app.database import get_db_pool
    if not get_db_pool():
        pytest.skip("PostgreSQL database not connected, skipping live database favorites CRUD test.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Add favorite
        fav_payload = {
            "city_name": "Paris",
            "country_code": "FR",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "display_order": 1
        }
        add_resp = await ac.post("/api/v1/locations/favorites", json=fav_payload)
        assert add_resp.status_code in [200, 201]
        fav_id = add_resp.json()["id"]

        # List favorites
        list_resp = await ac.get("/api/v1/locations/favorites")
        assert list_resp.status_code == 200
        favs = list_resp.json()
        assert any(f["id"] == fav_id for f in favs)

        # Delete favorite
        del_resp = await ac.delete(f"/api/v1/locations/favorites/{fav_id}")
        assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_ui_carto_key():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        assert "window.CARTO_BASEMAPS_API_KEY" in resp.text
