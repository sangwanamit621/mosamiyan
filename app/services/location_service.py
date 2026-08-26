import logging
import uuid
from typing import List, Optional
from app.config import get_settings
from app.database import execute_query, fetch_all, fetch_one
from app.db_queries import (
    COUNT_SAVED_LOCATIONS_SQL,
    DELETE_SAVED_LOCATION_SQL,
    DEMO_USER_ID,
    GET_SAVED_LOCATIONS_SQL,
    INSERT_SAVED_LOCATION_SQL,
)
from app.schemas.location import (
    FavoriteLocationCreate,
    FavoriteLocationResponse,
    LocationSearchResult,
)
from app.services.cache_service import get_cached_json, make_geo_search_key, set_cached_json
from app.services.providers.openmeteo_provider import OpenMeteoProvider
from app.services.providers.openweathermap_provider import OpenWeatherMapProvider

logger = logging.getLogger("mosamiyan.location_service")


class LocationService:
    """
    Handles typeahead location searching and favorite location management with parameterised raw SQL.
    """

    def __init__(self):
        self.settings = get_settings()
        self.primary_geo = OpenMeteoProvider()
        self.fallback_geo = OpenWeatherMapProvider()

    async def search_locations(self, query: str) -> List[LocationSearchResult]:
        if not query or len(query.strip()) < 2:
            return []

        cache_key = make_geo_search_key(query)
        cached = await get_cached_json(cache_key)
        if cached:
            return [LocationSearchResult.model_validate(item) for item in cached]

        # Primary provider
        results = await self.primary_geo.search_locations(query)

        # Fallback provider if empty
        if not results:
            results = await self.fallback_geo.search_locations(query)

        if results:
            await set_cached_json(
                cache_key, [r.model_dump() for r in results], self.settings.CACHE_TTL_GEO
            )

        return results

    async def get_user_favorites(self, user_id: str = DEMO_USER_ID) -> List[FavoriteLocationResponse]:
        """Fetch all saved locations using parameterised raw SQL."""
        try:
            records = await fetch_all(GET_SAVED_LOCATIONS_SQL, uuid.UUID(user_id))
            return [
                FavoriteLocationResponse(
                    id=r["id"],
                    user_id=r["user_id"],
                    city_name=r["city_name"],
                    country_code=r["country_code"],
                    latitude=float(r["latitude"]),
                    longitude=float(r["longitude"]),
                    display_order=r["display_order"],
                    created_at=r["created_at"].isoformat() if r["created_at"] else ""
                )
                for r in records
            ]
        except Exception as e:
            logger.error(f"Error fetching favorites from DB: {e}")
            return []

    async def add_favorite(
        self, location: FavoriteLocationCreate, user_id: str = DEMO_USER_ID
    ) -> Optional[FavoriteLocationResponse]:
        """Add a favorite location (enforcing max 5 limit for Phase 1 MVP)."""
        u_uuid = uuid.UUID(user_id)
        # Check current count
        count_rec = await fetch_one(COUNT_SAVED_LOCATIONS_SQL, u_uuid)
        if count_rec and count_rec.get("count", 0) >= 5:
            # Check if this exact coord already exists to allow update
            existing = await fetch_all(
                "SELECT id FROM saved_locations WHERE user_id = $1 AND latitude = $2 AND longitude = $3",
                u_uuid, location.latitude, location.longitude
            )
            if not existing:
                raise ValueError("Maximum limit of 5 favorite locations reached for MVP.")

        record = await fetch_one(
            INSERT_SAVED_LOCATION_SQL,
            u_uuid,
            location.city_name,
            location.country_code,
            location.latitude,
            location.longitude,
            location.display_order
        )

        if record:
            return FavoriteLocationResponse(
                id=record["id"],
                user_id=record["user_id"],
                city_name=record["city_name"],
                country_code=record["country_code"],
                latitude=float(record["latitude"]),
                longitude=float(record["longitude"]),
                display_order=record["display_order"],
                created_at=record["created_at"].isoformat() if record["created_at"] else ""
            )
        return None

    async def remove_favorite(self, favorite_id: str, user_id: str = DEMO_USER_ID) -> bool:
        """Delete a favorite location by ID using raw SQL."""
        try:
            result = await fetch_one(
                DELETE_SAVED_LOCATION_SQL,
                uuid.UUID(favorite_id),
                uuid.UUID(user_id)
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error deleting favorite location {favorite_id}: {e}")
            return False


# Global singleton instance
location_service = LocationService()
