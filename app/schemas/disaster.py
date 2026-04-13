from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime, date

class DisasterEventBase(SQLModel):
    title: str 
    country: str
    region: Optional[str] = None
    category: str 
    event_date: date
    severity: str
    short_summary: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_name: str = "StormScope Desk"
    source_url: Optional[str] = None
    external_id: Optional[str] = None
    external_source: Optional[str] = None
    geometry_type: Optional[str] = None
    geometry_json: Optional[str] = None

class DisasterEventCreate(DisasterEventBase):
    pass

class DisasterEventUpdate(SQLModel):
    title: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    category: Optional[str] = None
    event_date: Optional[date] = None
    severity: Optional[str] = None
    short_summary: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None

class DisasterEventResponse(DisasterEventBase):
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

class DisasterImportResponse(SQLModel):
    imported: int
    updated: int
    total_seen: int
