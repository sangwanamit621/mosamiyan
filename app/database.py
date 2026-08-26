import logging
from typing import Any, Dict, List, Optional
import asyncpg
from app.config import get_settings

logger = logging.getLogger("mosamiyan.database")

_pool: Optional[asyncpg.Pool] = None


async def init_db_pool() -> asyncpg.Pool:
    """Initialize asyncpg connection pool."""
    global _pool
    settings = get_settings()
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                min_size=2,
                max_size=10,
                command_timeout=10.0,
            )
            logger.info("PostgreSQL asyncpg connection pool established successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to PostgreSQL on startup: {e}")
            _pool = None
    return _pool


async def close_db_pool() -> None:
    """Close asyncpg connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed.")


def get_db_pool() -> Optional[asyncpg.Pool]:
    """Retrieve active connection pool."""
    return _pool


async def execute_query(query: str, *args) -> str:
    """Execute raw write SQL command (INSERT, UPDATE, DELETE)."""
    pool = get_db_pool()
    if not pool:
        raise ConnectionError("Database connection pool is not initialized")
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """Execute raw SQL query and return a single record as dictionary."""
    pool = get_db_pool()
    if not pool:
        raise ConnectionError("Database connection pool is not initialized")
    async with pool.acquire() as conn:
        record = await conn.fetchrow(query, *args)
        return dict(record) if record else None


async def fetch_all(query: str, *args) -> List[Dict[str, Any]]:
    """Execute raw SQL query and return all records as list of dictionaries."""
    pool = get_db_pool()
    if not pool:
        raise ConnectionError("Database connection pool is not initialized")
    async with pool.acquire() as conn:
        records = await conn.fetch(query, *args)
        return [dict(r) for r in records]
