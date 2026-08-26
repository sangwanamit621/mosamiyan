from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.db_queries import DEMO_USER_ID
from app.schemas.location import (
    FavoriteLocationCreate,
    FavoriteLocationResponse,
    LocationSearchResponse,
)
from app.services.location_service import location_service

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/search", response_model=LocationSearchResponse)
async def search_locations(
    q: str = Query(..., min_length=2, description="Typeahead location query")
):
    """
    Predictive typeahead geocoding search for global cities.
    """
    results = await location_service.search_locations(q)
    return LocationSearchResponse(results=results)


@router.get("/favorites", response_model=List[FavoriteLocationResponse])
async def get_favorites():
    """
    Retrieve user saved favorite locations (up to 5 for MVP).
    """
    return await location_service.get_user_favorites(DEMO_USER_ID)


@router.post("/favorites", response_model=FavoriteLocationResponse, status_code=201)
async def add_favorite(location: FavoriteLocationCreate):
    """
    Save a new favorite location using parameterised raw SQL.
    """
    try:
        fav = await location_service.add_favorite(location, DEMO_USER_ID)
        if not fav:
            raise HTTPException(status_code=500, detail="Failed to save favorite location")
        return fav
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.delete("/favorites/{favorite_id}")
async def delete_favorite(favorite_id: str):
    """
    Remove a saved favorite location.
    """
    success = await location_service.remove_favorite(favorite_id, DEMO_USER_ID)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite location not found")
    return {"message": "Favorite location removed successfully"}
