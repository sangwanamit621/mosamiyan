from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.locations import router as locations_router
from app.api.v1.endpoints.radar import router as radar_router
from app.api.v1.endpoints.weather import router as weather_router
from app.config import get_settings
from app.database import close_db_pool, init_db_pool
from app.services.cache_service import close_redis_pool, init_redis_pool
from app.services.http_client import close_http_client, init_http_client

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB, Redis, and HTTP client connection pools
    await init_db_pool()
    await init_redis_pool()
    await init_http_client()
    yield
    # Shutdown: Cleanly close connection pools
    await close_http_client()
    await close_db_pool()
    await close_redis_pool()


app = FastAPI(
    title=settings.APP_NAME,
    description="Modern Weather Platform API & Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Jinja2 Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Mount API Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(weather_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(radar_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def serve_dashboard(request: Request):
    """
    Serve main interactive weather dashboard.
    """
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME,
            "default_lat": settings.DEFAULT_LAT,
            "default_lon": settings.DEFAULT_LON,
            "default_city": settings.DEFAULT_CITY,
            "carto_api_key": settings.CARTO_BASEMAPS_API_KEY or ""
        }
    )
