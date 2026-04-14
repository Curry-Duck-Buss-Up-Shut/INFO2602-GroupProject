from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.disaster_event import DisasterEvent
from app.schemas.disaster import DisasterEventCreate, DisasterEventUpdate


class DisasterEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_events(
        self,
        category: Optional[str] = None,
        country: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list[DisasterEvent]:
        statement = select(DisasterEvent)
        if category:
            statement = statement.where(DisasterEvent.category == category)
        if country:
            statement = statement.where(DisasterEvent.country == country)
        if severity:
            statement = statement.where(DisasterEvent.severity == severity)
        statement = statement.order_by(DisasterEvent.event_date.desc(), DisasterEvent.created_at.desc())
        return list(self.db.exec(statement).all())

    def get_by_id(self, event_id: int) -> Optional[DisasterEvent]:
        return self.db.get(DisasterEvent, event_id)

    def get_by_external_reference(self, external_source: str, external_id: str) -> Optional[DisasterEvent]:
        statement = select(DisasterEvent).where(
            DisasterEvent.external_source == external_source,
            DisasterEvent.external_id == external_id,
        )
        return self.db.exec(statement).first()

    def latest_sync_for_source(self, external_source: str) -> Optional[datetime]:
        statement = (
            select(DisasterEvent)
            .where(DisasterEvent.external_source == external_source)
            .order_by(DisasterEvent.last_synced_at.desc(), DisasterEvent.updated_at.desc())
        )
        event = self.db.exec(statement).first()
        return event.last_synced_at if event else None

    def create(self, payload: DisasterEventCreate, created_by: Optional[int]) -> DisasterEvent:
        event = DisasterEvent(**payload.model_dump(), created_by=created_by)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update(self, event: DisasterEvent, payload: DisasterEventUpdate) -> DisasterEvent:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        event.updated_at = datetime.now(timezone.utc)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def save_external_events(
        self,
        events: list[DisasterEventCreate],
        external_source: str,
        synced_at: datetime,
        created_by: Optional[int],
    ) -> dict[str, int]:
        imported = 0
        updated = 0

        for payload in events:
            payload_data = payload.model_dump()
            external_id = payload_data.get("external_id")
            if not external_id:
                continue

            existing = self.get_by_external_reference(external_source, external_id)
            if existing:
                for field, value in payload_data.items():
                    setattr(existing, field, value)
                existing.created_by = existing.created_by or created_by
                existing.last_synced_at = synced_at
                existing.updated_at = synced_at
                self.db.add(existing)
                updated += 1
            else:
                event = DisasterEvent(
                    **payload_data,
                    created_by=created_by,
                    last_synced_at=synced_at,
                )
                self.db.add(event)
                imported += 1

        self.db.commit()
        return {"imported": imported, "updated": updated}

    def clear_created_by(self, user_id: int) -> None:
        statement = select(DisasterEvent).where(DisasterEvent.created_by == user_id)
        events = list(self.db.exec(statement).all())
        if not events:
            return

        updated_at = datetime.now(timezone.utc)
        for event in events:
            event.created_by = None
            event.updated_at = updated_at
            self.db.add(event)

        self.db.commit()

    def delete(self, event: DisasterEvent) -> None:
        self.db.delete(event)
        self.db.commit()
