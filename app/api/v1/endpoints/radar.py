import logging
from fastapi import APIRouter
from app.schemas.radar import RadarMetadataResponse
from app.services.weather_service import weather_service

logger = logging.getLogger("mosamiyan.endpoints.radar")
router = APIRouter(prefix="/weather/radar-tiles", tags=["Radar Tiles"])


@router.get("", response_model=RadarMetadataResponse)
async def get_radar_tiles_metadata():
    """
    Get current past and nowcast radar tile frame timestamps and host URL for Leaflet mapping.
    """
    frames = await weather_service.get_radar_frames()
    return frames
