from typing import List, Optional
from pydantic import BaseModel, Field


class WindData(BaseModel):
    speed_kmh: float
    gust_kmh: float
    direction_deg: int
    cardinal: str


class AirQualityData(BaseModel):
    aqi_us: int
    category: str
    pm2_5: float
    pm10: float


class LocationSchema(BaseModel):
    name: str
    region: Optional[str] = None
    country: str
    timezone: str
    lat: float
    lon: float


class AtmosphericCondition(BaseModel):
    timestamp: int
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    condition: str
    condition_code: str
    humidity: int
    dew_point: float
    pressure_hpa: float
    pressure_trend: str
    wind: WindData
    uv_index: float
    uv_category: str
    visibility_km: float
    cloud_cover_pct: int
    air_quality: AirQualityData


class LifestyleIndices(BaseModel):
    outdoor_running: dict = Field(default_factory=dict)
    car_wash: dict = Field(default_factory=dict)
    sun_protection: dict = Field(default_factory=dict)


class CurrentWeatherResponse(BaseModel):
    location: LocationSchema
    current: AtmosphericCondition
    lifestyle_indices: Optional[LifestyleIndices] = None
    source: str = "upstream"
    provider: str = "open-meteo"


class HourlyForecastItem(BaseModel):
    time: str
    temp: float
    feels_like: float
    precip_probability: int
    precip_amount_mm: float
    condition: str
    condition_code: str
    wind_speed_kmh: float


class DailyForecastItem(BaseModel):
    date: str
    day_name: str
    temp_min: float
    temp_max: float
    condition: str
    condition_code: str
    precip_probability: int
    precip_accumulation_mm: float
    sunrise: str
    sunset: str
    uv_max: float
    wind_speed_max_kmh: float
    wind_direction_dominant: str


class ForecastResponse(BaseModel):
    location: LocationSchema
    hourly: List[HourlyForecastItem]
    daily: List[DailyForecastItem]
    source: str = "upstream"
    provider: str = "open-meteo"
