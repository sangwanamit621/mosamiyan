import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.config import get_settings
from app.schemas.alert import WeatherAlertsResponse
from app.services.weather_service import weather_service

logger = logging.getLogger("mosamiyan.endpoints.alerts")
router = APIRouter(prefix="/weather/alerts", tags=["Weather Alerts"])
settings = get_settings()


@router.get("", response_model=WeatherAlertsResponse)
async def get_weather_alerts(
    lat: Optional[float] = Query(None, description="Latitude (-90 to 90)"),
    lon: Optional[float] = Query(None, description="Longitude (-180 to 180)")
):
    """
    Get active meteorological warnings and safety alerts for a geographic coordinate.
    """
    latitude = lat if lat is not None else settings.DEFAULT_LAT
    longitude = lon if lon is not None else settings.DEFAULT_LON

    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise HTTPException(status_code=400, detail="Invalid coordinates range")

    result = await weather_service.get_alerts(latitude, longitude)
    if not result:
        return WeatherAlertsResponse(
            location={"lat": latitude, "lon": longitude, "city": "Current Location"},
            alerts_count=0,
            alerts=[]
        )
    return result
