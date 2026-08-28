from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AlertSeverityEnum(str, Enum):
    ADVISORY = "advisory"
    WATCH = "watch"
    WARNING = "warning"
    EMERGENCY = "emergency"


class WeatherAlertItem(BaseModel):
    id: str
    event_title: str
    severity: AlertSeverityEnum = AlertSeverityEnum.ADVISORY
    severity_level: int = Field(default=1, ge=1, le=4, description="1=Advisory, 2=Watch, 3=Warning, 4=Emergency")
    urgency: Optional[str] = "Expected"
    certainty: Optional[str] = "Observed"
    issuing_agency: str = "National Meteorological Service"
    headline: str
    description: str
    instructions: Optional[str] = None
    starts_at: str
    expires_at: str
    is_active: bool = True


class AlertLocation(BaseModel):
    lat: float
    lon: float
    city: Optional[str] = None


class WeatherAlertsResponse(BaseModel):
    location: AlertLocation
    alerts_count: int = 0
    highest_severity: Optional[AlertSeverityEnum] = None
    alerts: List[WeatherAlertItem] = Field(default_factory=list)
    source: str = "upstream"
    cached: bool = False
