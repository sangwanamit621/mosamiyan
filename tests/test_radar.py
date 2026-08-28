import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.radar import RadarFrame, RadarMetadataResponse
from app.services.weather_service import weather_service


def test_radar_schema():
    frame = RadarFrame(time=1774828800, path="/v2/radar/1774828800/256/1/1/1/2/1_1.png", type="past")
    assert frame.time == 1774828800
    assert frame.type == "past"

    meta = RadarMetadataResponse(
        host="https://tilecache.rainviewer.com",
        generated_at=1774828800,
        past_frames=[frame],
        nowcast_frames=[]
    )
    assert meta.host == "https://tilecache.rainviewer.com"
    assert len(meta.past_frames) == 1
    assert len(meta.nowcast_frames) == 0


@pytest.mark.asyncio
async def test_radar_tiles_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/weather/radar-tiles")
        assert resp.status_code == 200
        data = resp.json()
        assert "host" in data
        assert "generated_at" in data
        assert "past_frames" in data
        assert "nowcast_frames" in data
        assert isinstance(data["past_frames"], list)
