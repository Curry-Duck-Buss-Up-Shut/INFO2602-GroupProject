import json
from datetime import UTC, date, datetime, timedelta

from app.models.user import User
from app.repositories.disaster_event import DisasterEventRepository
from app.schemas.disaster import DisasterEventCreate, DisasterEventUpdate
from app.services.weather_service import WeatherService

NASA_EXTERNAL_SOURCE = "NASA EONET"


class DisasterService:
    def __init__(self, repo: DisasterEventRepository):
        self.repo = repo

    async def list_events(
        self,
        category: str | None = None,
        country: str | None = None,
        severity: str | None = None,
        include_live_nasa: bool = True,
    ):
        if include_live_nasa:
            try:
                await self.sync_nasa_feed(limit=120, include_wildfires=True, max_age_minutes=30)
            except Exception:
                pass
        return self.repo.list_events(category=category, country=country, severity=severity)

    def get_event(self, event_id: int):
        event = self.repo.get_by_id(event_id)
        if not event:
            raise LookupError("Disaster event not found")
        return event

    def create_event(self, user: User, payload: DisasterEventCreate):
        return self.repo.create(payload, created_by=user.id)

    def update_event(self, event_id: int, payload: DisasterEventUpdate):
        event = self.repo.get_by_id(event_id)
        if not event:
            raise LookupError("Disaster event not found")
        if event.external_source == NASA_EXTERNAL_SOURCE:
            raise PermissionError("NASA-synced records are read-only. Refresh the NASA sync instead.")
        return self.repo.update(event, payload)

    def delete_event(self, event_id: int):
        event = self.repo.get_by_id(event_id)
        if not event:
            raise LookupError("Disaster event not found")
        if event.external_source == NASA_EXTERNAL_SOURCE:
            raise PermissionError("NASA-synced records are read-only. Refresh the NASA sync instead.")
        self.repo.delete(event)

    async def sync_nasa_feed(
        self,
        limit: int = 60,
        include_wildfires: bool = True,
        max_age_minutes: int = 30,
        created_by: int | None = None,
        force: bool = False,
    ):
        if not force and self._sync_is_fresh(max_age_minutes=max_age_minutes):
            return {"imported": 0, "updated": 0, "total_seen": 0}

        events = await WeatherService().get_live_eonet_events(
            limit=limit,
            caribbean_only=False,
            include_wildfires=include_wildfires,
        )
        normalized_events = [self._normalize_nasa_event(event) for event in events]
        valid_events = [event for event in normalized_events if event]
        synced_at = datetime.now(UTC)
        results = self.repo.save_external_events(
            valid_events,
            external_source=NASA_EXTERNAL_SOURCE,
            synced_at=synced_at,
            created_by=created_by,
        )
        return {**results, "total_seen": len(valid_events)}

    def _sync_is_fresh(self, max_age_minutes: int) -> bool:
        latest_sync = self.repo.latest_sync_for_source(NASA_EXTERNAL_SOURCE)
        if not latest_sync:
            return False
        if latest_sync.tzinfo is None:
            latest_sync = latest_sync.replace(tzinfo=UTC)
        return latest_sync >= datetime.now(UTC) - timedelta(minutes=max_age_minutes)

    def _normalize_nasa_event(self, event: dict) -> DisasterEventCreate | None:
        event_id = event.get("id")
        event_date = self._parse_nasa_date(event.get("date"))
        if not event_id or not event_date:
            return None

        region = self._extract_region_from_title(event.get("title"))
        category = event.get("category") or "NASA live event"
        source_name = event.get("source") or NASA_EXTERNAL_SOURCE
        title = event.get("title") or f"NASA event {event_id}"

        return DisasterEventCreate(
            title=title,
            country="Global feed",
            region=region,
            category=category,
            event_date=event_date,
            severity=self._map_severity(category),
            short_summary=self._build_summary(title=title, category=category, region=region),
            latitude=event.get("latitude"),
            longitude=event.get("longitude"),
            source_name=source_name,
            source_url=event.get("link"),
            external_id=event_id,
            external_source=NASA_EXTERNAL_SOURCE,
            geometry_type=event.get("geometry_type"),
            geometry_json=json.dumps(event.get("geometry")) if event.get("geometry") is not None else None,
        )

    def _parse_nasa_date(self, value: str | None) -> date | None:
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            return None

    def _extract_region_from_title(self, title: str | None) -> str | None:
        if not title or "," not in title:
            return None
        parts = [part.strip() for part in title.split(",") if part.strip()]
        if len(parts) < 2:
            return None
        return ", ".join(parts[1:])

    def _map_severity(self, category: str) -> str:
        lowered = category.lower()
        if any(keyword in lowered for keyword in ["wildfire", "volcano", "severe storm"]):
            return "High"
        if any(keyword in lowered for keyword in ["flood", "landslide", "temperature extreme"]):
            return "Moderate"
        return "Low"

    def _build_summary(self, title: str, category: str, region: str | None) -> str:
        location = region or "the global feed"
        return f"Imported from NASA EONET as a live {category.lower()} event affecting {location}."
