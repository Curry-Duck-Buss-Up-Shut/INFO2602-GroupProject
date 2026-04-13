from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

class SavedLocationCreate(SQLModel):
    city_name: str
    country_name: str
    latitude: float
    longitude: float
    timezone: str = "auto"
    nickname: Optional[str] = None
    priority: int = 3

class SavedLocationUpdate(SQLModel):
    nickname: Optional[str] = None
    priority: Optional[int] = None

class SavedLocationResponse(SQLModel):
    id: int
    user_id: int
    city_name: str
    country_name: str
    latitude: float
    longitude: float
    timezone: str
    nickname: Optional[str]
    priority: int 
    created_at: datetime
