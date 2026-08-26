from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class LocationSearchResult(BaseModel):
    id: str
    name: str
    administrative_area: Optional[str] = None
    country: str
    country_code: str
    lat: float
    lon: float
    timezone: str


class LocationSearchResponse(BaseModel):
    results: List[LocationSearchResult]


class FavoriteLocationCreate(BaseModel):
    city_name: str
    country_code: str
    latitude: float
    longitude: float
    display_order: int = 0


class FavoriteLocationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    city_name: str
    country_code: str
    latitude: float
    longitude: float
    display_order: int
    created_at: str
