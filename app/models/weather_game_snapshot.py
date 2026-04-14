from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

class WeatherGameSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    city_name: str = Field(index=True)
    country_name: str
    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    timezone_name: str = Field(default="auto", index=True)
    temperature: float
    apparent_temperature: float
    humidity: int
    wind_speed: float
    precipitation: float
    weather_code: int
    weather_label: str
    is_day: bool = True
    source_name: str = "StormScope game snapshot"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
