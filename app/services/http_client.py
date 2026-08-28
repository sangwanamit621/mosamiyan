import logging
from typing import Optional
import httpx

logger = logging.getLogger("mosamiyan.http_client")

_http_client: Optional[httpx.AsyncClient] = None


def _create_client() -> httpx.AsyncClient:
    """Helper to instantiate AsyncClient with HTTP/2 if h2 is present, else HTTP/1.1."""
    try:
        import h2  # noqa: F401
        has_h2 = True
    except ImportError:
        has_h2 = False

    return httpx.AsyncClient(
        timeout=httpx.Timeout(5.0, connect=3.0),
        http2=has_h2,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
    )


async def init_http_client() -> httpx.AsyncClient:
    """Initialize shared singleton AsyncClient with connection pooling."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = _create_client()
        logger.info("Shared singleton httpx.AsyncClient initialized.")
    return _http_client


async def close_http_client() -> None:
    """Close shared singleton AsyncClient gracefully."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
        logger.info("Shared singleton httpx.AsyncClient closed.")


def get_http_client() -> httpx.AsyncClient:
    """
    Get active shared AsyncClient instance.
    If not initialized yet (e.g. during standalone tests), creates an instance.
    """
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = _create_client()
    return _http_client
