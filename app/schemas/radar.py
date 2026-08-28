from typing import List, Optional
from pydantic import BaseModel, Field


class RadarFrame(BaseModel):
    time: int
    path: str
    type: str = "past"  # "past" or "nowcast"


class RadarMetadataResponse(BaseModel):
    host: str = "https://tilecache.rainviewer.com"
    generated_at: int
    past_frames: List[RadarFrame] = Field(default_factory=list)
    nowcast_frames: List[RadarFrame] = Field(default_factory=list)
    color_scheme: int = 2
    smooth: int = 1
