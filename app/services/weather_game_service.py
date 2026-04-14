from __future__ import annotations

import random
from typing import Any

from app.repositories.weather_game_snapshot import WeatherGameSnapshotRepository


class WeatherGameService:
    def __init__(self, snapshot_repo: WeatherGameSnapshotRepository):
        self.snapshot_repo = snapshot_repo

    def build_round(self) -> dict[str, Any]:
        snapshots = list(self.snapshot_repo.list_snapshots())
        if len(snapshots) < 2:
            raise ValueError("The CSV mini game deck is not ready yet.")

        for _ in range(8):
            left, right = random.sample(snapshots, 2)
            if abs(left.temperature - right.temperature) >= 1:
                return self._serialize_round(left, right)

        left, right = random.sample(snapshots, 2)
        return self._serialize_round(left, right)

    def _serialize_round(self, left, right) -> dict[str, Any]:
        weather = [self._serialize_weather(left), self._serialize_weather(right)]
        return {
            "cities": [
                self._serialize_city(left),
                self._serialize_city(right),
            ],
            "weather": weather,
            "hotterIndex": 0 if left.temperature >= right.temperature else 1,
        }

    def _serialize_city(self, snapshot) -> dict[str, Any]:
        return {
            "name": snapshot.city_name,
            "country": snapshot.country_name,
            "latitude": snapshot.latitude,
            "longitude": snapshot.longitude,
            "timezone": snapshot.timezone_name,
        }

    def _serialize_weather(self, snapshot) -> dict[str, Any]:
        return {
            "temperature": snapshot.temperature,
            "apparent_temperature": snapshot.apparent_temperature,
            "humidity": snapshot.humidity,
            "wind_speed": snapshot.wind_speed,
            "precipitation": snapshot.precipitation,
            "weather_code": snapshot.weather_code,
            "weather_label": snapshot.weather_label,
            "is_day": snapshot.is_day,
            "local_time": None,
            "source_name": snapshot.source_name,
        }
