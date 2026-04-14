from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.weather_forecast_snapshot import WeatherForecastSnapshot


class WeatherForecastSnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_snapshot(self, latitude: float, longitude: float, timezone_name: str) -> Optional[WeatherForecastSnapshot]:
        statement = (
            select(WeatherForecastSnapshot)
            .where(
                WeatherForecastSnapshot.latitude == latitude,
                WeatherForecastSnapshot.longitude == longitude,
                WeatherForecastSnapshot.timezone_name == timezone_name,
            )
            .order_by(WeatherForecastSnapshot.fetched_at.desc())
        )
        return self.db.exec(statement).first()

    def upsert_snapshot(
        self,
        latitude: float,
        longitude: float,
        timezone_name: str,
        forecast_json: str,
        fetched_at: datetime,
    ) -> WeatherForecastSnapshot:
        snapshot = self.get_snapshot(latitude, longitude, timezone_name)
        now = datetime.now(timezone.utc)

        if snapshot is None:
            snapshot = WeatherForecastSnapshot(
                latitude=latitude,
                longitude=longitude,
                timezone_name=timezone_name,
                forecast_json=forecast_json,
                fetched_at=fetched_at,
                updated_at=now,
            )
        else:
            snapshot.forecast_json = forecast_json
            snapshot.fetched_at = fetched_at
            snapshot.updated_at = now

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot
