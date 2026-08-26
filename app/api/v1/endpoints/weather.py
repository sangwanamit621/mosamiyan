from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.config import get_settings
from app.schemas.weather import CurrentWeatherResponse, ForecastResponse
from app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])
settings = get_settings()


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    lat: Optional[float] = Query(None, description="Latitude (-90 to 90)"),
    lon: Optional[float] = Query(None, description="Longitude (-180 to 180)"),
    units: str = Query("metric", description="Unit format: 'metric' or 'imperial'")
):
    """
    Get real-time atmospheric conditions and lifestyle indices.
    Falls back to default city (New Delhi, India) if coordinates are omitted.
    """
    latitude = lat if lat is not None else settings.DEFAULT_LAT
    longitude = lon if lon is not None else settings.DEFAULT_LON

    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise HTTPException(status_code=400, detail="Invalid coordinates range")

    result = await weather_service.get_current_weather(latitude, longitude, units=units)
    if not result:
        raise HTTPException(status_code=503, detail="Weather service currently unavailable")
    return result


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    lat: Optional[float] = Query(None, description="Latitude (-90 to 90)"),
    lon: Optional[float] = Query(None, description="Longitude (-180 to 180)"),
    hourly_steps: int = Query(24, ge=1, le=48, description="Number of hourly steps (1-48)"),
    daily_steps: int = Query(7, ge=1, le=14, description="Number of daily steps (1-14)"),
    units: str = Query("metric", description="Unit format: 'metric' or 'imperial'")
):
    """
    Get combined hourly (24h/48h) and extended daily (7d/14d) forecasts.
    """
    latitude = lat if lat is not None else settings.DEFAULT_LAT
    longitude = lon if lon is not None else settings.DEFAULT_LON

    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise HTTPException(status_code=400, detail="Invalid coordinates range")

    result = await weather_service.get_forecast(
        latitude, longitude, hourly_steps=hourly_steps, daily_steps=daily_steps, units=units
    )
    if not result:
        raise HTTPException(status_code=503, detail="Forecast service currently unavailable")
    return result
