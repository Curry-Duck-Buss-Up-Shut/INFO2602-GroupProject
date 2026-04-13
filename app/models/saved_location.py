from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime, timezone

class SavedLocation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    city_name: str = Field(index=True)
    country_name: str = Field(index=True)
    latitude: float
    longitude: float
    timezone: str = "auto"
    nickname: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

