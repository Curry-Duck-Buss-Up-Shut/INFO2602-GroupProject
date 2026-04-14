import logging
from typing import Optional

from sqlmodel import Session, select

from app.models.saved_location import SavedLocation
from app.schemas.watchlist import SavedLocationCreate, SavedLocationUpdate

logger = logging.getLogger(__name__)


class SavedLocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: int) -> list[SavedLocation]:
        statement = (
            select(SavedLocation)
            .where(SavedLocation.user_id == user_id)
            .order_by(SavedLocation.priority.asc(), SavedLocation.created_at.desc())
        )
        return list(self.db.exec(statement).all())

    def get_for_user(self, location_id: int, user_id: int) -> Optional[SavedLocation]:
        statement = select(SavedLocation).where(
            SavedLocation.id == location_id,
            SavedLocation.user_id == user_id,
        )
        return self.db.exec(statement).one_or_none()

    def find_duplicate(self, user_id: int, city_name: str, country_name: str) -> Optional[SavedLocation]:
        statement = select(SavedLocation).where(
            SavedLocation.user_id == user_id,
            SavedLocation.city_name == city_name,
            SavedLocation.country_name == country_name,
        )
        return self.db.exec(statement).one_or_none()

    def create(self, user_id: int, payload: SavedLocationCreate) -> SavedLocation:
        location = SavedLocation(user_id=user_id, **payload.model_dump())
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def update(self, location: SavedLocation, payload: SavedLocationUpdate) -> SavedLocation:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(location, field, value)
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def delete(self, location: SavedLocation) -> None:
        self.db.delete(location)
        self.db.commit()

    def delete_for_user(self, user_id: int) -> None:
        statement = select(SavedLocation).where(SavedLocation.user_id == user_id)
        locations = list(self.db.exec(statement).all())
        for location in locations:
            self.db.delete(location)
        self.db.commit()
