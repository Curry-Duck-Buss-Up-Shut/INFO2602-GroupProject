from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class WeatherCurrentSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    timezone_name: str = Field(default="auto", index=True)
    weather_json: str
    source_name: str = "Open-Meteo"
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
