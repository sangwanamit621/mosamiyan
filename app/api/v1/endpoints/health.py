from fastapi import APIRouter
from app.database import fetch_one
from app.db_queries import DB_HEALTH_CHECK_SQL
from app.services.cache_service import get_redis

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    Health check endpoint verifying PostgreSQL and Redis connections.
    """
    db_status = "unhealthy"
    try:
        res = await fetch_one(DB_HEALTH_CHECK_SQL)
        if res and res.get("alive") == 1:
            db_status = "healthy"
    except Exception:
        db_status = "disconnected"

    redis_status = "unhealthy"
    try:
        client = get_redis()
        if client and await client.ping():
            redis_status = "healthy"
    except Exception:
        redis_status = "disconnected"

    overall = "ok" if (db_status == "healthy" and redis_status == "healthy") else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "cache": redis_status,
        "service": "Mosamiyan Weather API v1"
    }
