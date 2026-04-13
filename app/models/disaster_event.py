from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime, timezone

class DisasterEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    country: str = Field(index=True)
    region: Optional[str] = Field(default=None, index=True)
    category: str = Field(index=True)
    event_date: str = Field(index=True)
    severity: str = Field(default="Moderate", index=True)
    short_summary: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_name: str = "StormScope Desk"
    source_url: Optional[str] = None
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    external_id: Optional[str] = None
    external_source: Optional[str] = None
    geometry_type: Optional[str] = None
    geometry_json: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    