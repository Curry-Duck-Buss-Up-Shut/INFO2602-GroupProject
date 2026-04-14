from typing import Sequence

from sqlmodel import Session, select

from app.models.weather_game_snapshot import WeatherGameSnapshot


class WeatherGameSnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_snapshots(self) -> Sequence[WeatherGameSnapshot]:
        statement = select(WeatherGameSnapshot).order_by(WeatherGameSnapshot.city_name.asc())
        return self.db.exec(statement).all()

    def has_snapshots(self) -> bool:
        statement = select(WeatherGameSnapshot.id)
        return self.db.exec(statement).first() is not None

    def replace_all(self, snapshots: list[WeatherGameSnapshot]) -> None:
        existing = self.list_snapshots()
        for snapshot in existing:
            self.db.delete(snapshot)
        self.db.add_all(snapshots)
        self.db.commit()
