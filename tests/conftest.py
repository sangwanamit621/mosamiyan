import pytest
from app.database import close_db_pool, init_db_pool
from app.services.cache_service import close_redis_pool, init_redis_pool
from app.services.http_client import close_http_client, init_http_client


@pytest.fixture(autouse=True, scope="function")
async def setup_test_environment():
    """Ensure database connection pool, redis, and http client are initialized per test function loop."""
    await init_db_pool()
    await init_redis_pool()
    await init_http_client()
    yield
    await close_http_client()
    await close_db_pool()
    await close_redis_pool()
