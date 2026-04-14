from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.weather_current_snapshot import WeatherCurrentSnapshot


class WeatherCurrentSnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_snapshot(self, latitude: float, longitude: float, timezone_name: str) -> Optional[WeatherCurrentSnapshot]:
        statement = (
            select(WeatherCurrentSnapshot)
            .where(
                WeatherCurrentSnapshot.latitude == latitude,
                WeatherCurrentSnapshot.longitude == longitude,
                WeatherCurrentSnapshot.timezone_name == timezone_name,
            )
            .order_by(WeatherCurrentSnapshot.fetched_at.desc())
        )
        return self.db.exec(statement).first()

    def upsert_snapshot(
        self,
        latitude: float,
        longitude: float,
        timezone_name: str,
        weather_json: str,
        fetched_at: datetime,
    ) -> WeatherCurrentSnapshot:
        snapshot = self.get_snapshot(latitude, longitude, timezone_name)
        now = datetime.now(timezone.utc)

        if snapshot is None:
            snapshot = WeatherCurrentSnapshot(
                latitude=latitude,
                longitude=longitude,
                timezone_name=timezone_name,
                weather_json=weather_json,
                fetched_at=fetched_at,
                updated_at=now,
            )
        else:
            snapshot.weather_json = weather_json
            snapshot.fetched_at = fetched_at
            snapshot.updated_at = now

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
