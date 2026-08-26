import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.config import get_settings

logger = logging.getLogger("mosamiyan.cache")

_redis_client: Optional[aioredis.Redis] = None


async def init_redis_pool() -> aioredis.Redis:
    """Initialize async Redis client pool."""
    global _redis_client
    settings = get_settings()
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3.0,
                max_connections=20
            )
            await _redis_client.ping()
            logger.info("Redis client connection pool established.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            _redis_client = None
    return _redis_client


async def close_redis_pool() -> None:
    """Close async Redis pool connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis client pool closed.")


def get_redis() -> Optional[aioredis.Redis]:
    """Retrieve active Redis client."""
    return _redis_client


def normalize_coords(lat: float, lon: float) -> tuple[float, float]:
    """
    Spatial Coordinate Rounding:
    Rounds coordinates to 2 decimal places (~1.1 km precision at the equator)
    to prevent cache fragmentation caused by minor GPS jitter.
    """
    return round(float(lat), 2), round(float(lon), 2)


def make_current_weather_key(lat: float, lon: float) -> str:
    norm_lat, norm_lon = normalize_coords(lat, lon)
    return f"weather:current:{norm_lat}:{norm_lon}"


def make_forecast_key(lat: float, lon: float, hourly_steps: int, daily_steps: int) -> str:
    norm_lat, norm_lon = normalize_coords(lat, lon)
    return f"weather:forecast:{norm_lat}:{norm_lon}:{hourly_steps}:{daily_steps}"


def make_geo_search_key(query: str) -> str:
    norm_q = query.strip().lower()
    return f"geo:search:{norm_q}"


async def get_cached_json(key: str) -> Optional[Any]:
    """Fetch and parse JSON from Redis key."""
    client = get_redis()
    if not client:
        return None
    try:
        data = await client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Redis get error for key {key}: {e}")
    return None


async def set_cached_json(key: str, value: Any, ttl_seconds: int) -> bool:
    """Serialize and store data in Redis key with TTL."""
    client = get_redis()
    if not client:
        return False
    try:
        await client.set(key, json.dumps(value), ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Redis set error for key {key}: {e}")
        return False
