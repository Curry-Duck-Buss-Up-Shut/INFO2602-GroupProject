import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as dt_timezone
from threading import Lock
from typing import Any, Awaitable, Callable, Optional

import httpx

from app.config import get_settings
from app.repositories.weather_forecast_snapshot import WeatherForecastSnapshotRepository


WEATHER_CODE_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Heavy rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}

DEFAULT_EONET_CATEGORIES = {
    "Drought",
    "Dust and Haze",
    "Floods",
    "Landslides",
    "Severe Storms",
    "Temperature Extremes",
    "Volcanoes",
}


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: float
    stale_until: float


class UpstreamRateLimitError(RuntimeError):
    def __init__(self, retry_after_seconds: int | None = None):
        self.retry_after_seconds = retry_after_seconds
        message = "The live weather service is temporarily busy. Please try again shortly."
        if retry_after_seconds:
            message = f"The live weather service is temporarily busy. Please try again in about {retry_after_seconds} seconds."
        super().__init__(message)


_response_cache: dict[str, CacheEntry] = {}
_inflight_requests: dict[str, asyncio.Task] = {}
_cache_lock = Lock()


class WeatherService:
    def __init__(self, forecast_repo: WeatherForecastSnapshotRepository | None = None):
        self.forecast_repo = forecast_repo

    async def search_city(self, query: str, count: int = 6) -> list[dict[str, Any]]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        settings = get_settings()
        payload = await self._get_or_fetch_json(
            cache_key=f"weather-search:{normalized_query.lower()}:{count}",
            ttl_seconds=settings.weather_search_cache_ttl_seconds,
            stale_ttl_seconds=settings.weather_stale_ttl_seconds,
            fetcher=lambda: self._request_json(
                settings.open_meteo_geocoding_url,
                params={"name": normalized_query, "count": count, "language": "en", "format": "json"},
            ),
        )
        results = payload.get("results", [])
        return [
            {
                "name": item["name"],
                "country": item.get("country", ""),
                "country_code": item.get("country_code", ""),
                "admin1": item.get("admin1"),
                "feature_code": item.get("feature_code"),
                "latitude": item["latitude"],
                "longitude": item["longitude"],
                "timezone": item.get("timezone", "auto"),
            }
            for item in results
        ]

    async def get_current_weather(self, latitude: float, longitude: float, timezone: str = "auto") -> dict[str, Any]:
        settings = get_settings()
        try:
            normalized_timezone = timezone or "auto"
            data = await self._get_or_fetch_json(
                cache_key=(
                    f"weather-current:{round(latitude, 4)}:{round(longitude, 4)}:{normalized_timezone.lower()}"
                ),
                ttl_seconds=settings.weather_cache_ttl_seconds,
                stale_ttl_seconds=settings.weather_stale_ttl_seconds,
                fetcher=lambda: self._fetch_live_current_weather(latitude, longitude, normalized_timezone),
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise UpstreamRateLimitError(self._parse_retry_after_seconds(exc.response)) from exc
            raise
        current = data.get("current", {})
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "timezone_abbreviation": data.get("timezone_abbreviation"),
            "local_time": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "precipitation": current.get("precipitation"),
            "is_day": bool(current.get("is_day", 1)),
            "weather_code": current.get("weather_code"),
            "weather_label": WEATHER_CODE_LABELS.get(current.get("weather_code"), "Unknown"),
        }

    async def get_forecast(self, latitude: float, longitude: float, timezone: str = "auto") -> dict[str, Any]:
        normalized_latitude = round(latitude, 4)
        normalized_longitude = round(longitude, 4)
        normalized_timezone = timezone or "auto"
        settings = get_settings()
        snapshot = None
        forecast_days: list[dict[str, Any]] | None = None

        if self.forecast_repo:
            snapshot = self.forecast_repo.get_snapshot(normalized_latitude, normalized_longitude, normalized_timezone)
            if snapshot:
                forecast_days = self._deserialize_forecast_days(snapshot.forecast_json)
                if forecast_days and not self._is_forecast_snapshot_stale(
                    snapshot.fetched_at,
                    settings.weather_forecast_snapshot_ttl_seconds,
                ):
                    return {"forecast": forecast_days}

        try:
            data = await self._fetch_live_forecast(normalized_latitude, normalized_longitude, normalized_timezone)
        except httpx.HTTPStatusError as exc:
            if forecast_days and snapshot and self._is_forecast_snapshot_servable(
                snapshot.fetched_at,
                settings.weather_forecast_snapshot_stale_ttl_seconds,
            ):
                return {"forecast": forecast_days}
            if exc.response.status_code == 429:
                raise UpstreamRateLimitError(self._parse_retry_after_seconds(exc.response)) from exc
            raise
        except Exception:
            if forecast_days and snapshot and self._is_forecast_snapshot_servable(
                snapshot.fetched_at,
                settings.weather_forecast_snapshot_stale_ttl_seconds,
            ):
                return {"forecast": forecast_days}
            raise

        daily = data.get("daily", {})
        forecast_days = self._build_forecast_days(daily)

        if self.forecast_repo and forecast_days:
            self.forecast_repo.upsert_snapshot(
                latitude=normalized_latitude,
                longitude=normalized_longitude,
                timezone_name=normalized_timezone,
                forecast_json=json.dumps(forecast_days),
                fetched_at=datetime.now(dt_timezone.utc),
            )

        return {"forecast": forecast_days}

    def _build_forecast_days(self, daily: dict[str, Any]) -> list[dict[str, Any]]:
        dates = daily.get("time", [])
        codes = daily.get("weather_code", [])
        highs = daily.get("temperature_2m_max", [])
        lows = daily.get("temperature_2m_min", [])
        precipitation = daily.get("precipitation_probability_max", [])
        forecast_days = []
        for index, forecast_date in enumerate(dates):
            code = codes[index] if index < len(codes) else None
            forecast_days.append(
                {
                    "date": forecast_date,
                    "weather_code": code,
                    "weather_label": WEATHER_CODE_LABELS.get(code, "Unknown"),
                    "temperature_max": highs[index] if index < len(highs) else None,
                    "temperature_min": lows[index] if index < len(lows) else None,
                    "precipitation_probability": precipitation[index] if index < len(precipitation) else None,
                }
            )
        return forecast_days

    async def get_live_eonet_events(
        self,
        limit: int = 10,
        caribbean_only: bool = True,
        include_wildfires: bool = False,
    ) -> list[dict[str, Any]]:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(settings.nasa_eonet_url, params={"limit": limit, "status": "open"})
            response.raise_for_status()
        payload = response.json()
        events = []
        for event in payload.get("events", []):
            latest_geometry = event.get("geometry", [{}])[-1] if event.get("geometry") else {}
            longitude, latitude = self._extract_point(latest_geometry.get("coordinates"))
            category_titles = [category["title"] for category in event.get("categories", [])]
            if not include_wildfires and "Wildfires" in category_titles:
                continue
            if caribbean_only:
                if latitude is None or longitude is None:
                    continue
                if not self._is_in_caribbean(latitude, longitude):
                    continue
                if not any(category in DEFAULT_EONET_CATEGORIES for category in category_titles):
                    continue
            events.append(
                {
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "category": ", ".join(category_titles),
                    "source": ", ".join(source["id"] for source in event.get("sources", [])),
                    "date": latest_geometry.get("date"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "link": event.get("link"),
                }
            )
        return events

    def _extract_point(self, coordinates: Any) -> tuple[Optional[float], Optional[float]]:
        if not isinstance(coordinates, list):
            return None, None
        if len(coordinates) >= 2 and all(isinstance(value, (int, float)) for value in coordinates[:2]):
            return float(coordinates[0]), float(coordinates[1])
        if coordinates and isinstance(coordinates[0], list):
            return self._extract_point(coordinates[0])
        return None, None

    def _is_in_caribbean(self, latitude: float, longitude: float) -> bool:
        settings = get_settings()
        return (
            settings.caribbean_lat_min <= latitude <= settings.caribbean_lat_max
            and settings.caribbean_lon_min <= longitude <= settings.caribbean_lon_max
        )

    async def _fetch_live_current_weather(self, latitude: float, longitude: float, timezone: Optional[str]) -> dict[str, Any]:
        settings = get_settings()
        normalized_timezone = timezone or "auto"
        return await self._request_json(
            settings.open_meteo_forecast_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "timezone": normalized_timezone,
                "current": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "apparent_temperature",
                        "is_day",
                        "precipitation",
                        "weather_code",
                        "wind_speed_10m",
                    ]
                ),
            },
        )

    async def _fetch_live_forecast(self, latitude: float, longitude: float, timezone: Optional[str]) -> dict[str, Any]:
        settings = get_settings()
        normalized_timezone = timezone or "auto"
        return await self._request_json(
            settings.open_meteo_forecast_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "timezone": normalized_timezone,
                "daily": ",".join(
                    [
                        "weather_code",
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_probability_max",
                    ]
                ),
                "forecast_days": 7,
            },
        )

    def _deserialize_forecast_days(self, forecast_json: str) -> list[dict[str, Any]]:
        try:
            payload = json.loads(forecast_json)
        except (TypeError, ValueError):
            return []
        return payload if isinstance(payload, list) else []

    def _is_forecast_snapshot_stale(self, fetched_at: datetime, ttl_seconds: int) -> bool:
        return datetime.now(dt_timezone.utc) - fetched_at > timedelta(seconds=ttl_seconds)

    def _is_forecast_snapshot_servable(self, fetched_at: datetime, stale_ttl_seconds: int) -> bool:
        return datetime.now(dt_timezone.utc) - fetched_at <= timedelta(seconds=stale_ttl_seconds)

    async def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        return response.json()

    async def _get_or_fetch_json(
        self,
        cache_key: str,
        ttl_seconds: int,
        stale_ttl_seconds: int,
        fetcher: Callable[[], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        now = time.monotonic()
        cached_entry = self._get_cache_entry(cache_key)
        if cached_entry and cached_entry.expires_at > now:
            return cached_entry.value

        created_task = False
        with _cache_lock:
            cached_entry = _response_cache.get(cache_key)
            if cached_entry and cached_entry.expires_at > now:
                return cached_entry.value
            task = _inflight_requests.get(cache_key)
            if task is None:
                task = asyncio.create_task(fetcher())
                _inflight_requests[cache_key] = task
                created_task = True

        try:
            payload = await task
        except httpx.HTTPStatusError as exc:
            stale_entry = self._get_cache_entry(cache_key)
            if exc.response.status_code == 429:
                if stale_entry and stale_entry.stale_until > time.monotonic():
                    return stale_entry.value
                raise UpstreamRateLimitError(self._parse_retry_after_seconds(exc.response)) from exc
            if stale_entry and stale_entry.stale_until > time.monotonic():
                return stale_entry.value
            raise
        except Exception:
            stale_entry = self._get_cache_entry(cache_key)
            if stale_entry and stale_entry.stale_until > time.monotonic():
                return stale_entry.value
            raise
        finally:
            if created_task:
                with _cache_lock:
                    if _inflight_requests.get(cache_key) is task:
                        _inflight_requests.pop(cache_key, None)

        self._set_cache_entry(
            cache_key,
            payload,
            expires_at=time.monotonic() + ttl_seconds,
            stale_until=time.monotonic() + ttl_seconds + stale_ttl_seconds,
        )
        return payload

    def _get_cache_entry(self, cache_key: str) -> CacheEntry | None:
        with _cache_lock:
            return _response_cache.get(cache_key)

    def _set_cache_entry(self, cache_key: str, value: dict[str, Any], expires_at: float, stale_until: float) -> None:
        with _cache_lock:
            _response_cache[cache_key] = CacheEntry(value=value, expires_at=expires_at, stale_until=stale_until)
            self._prune_cache_locked()

    def _prune_cache_locked(self) -> None:
        now = time.monotonic()
        expired_keys = [key for key, entry in _response_cache.items() if entry.stale_until <= now]
        for key in expired_keys:
            _response_cache.pop(key, None)

    def _parse_retry_after_seconds(self, response: httpx.Response) -> int | None:
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return None
        try:
            seconds = int(retry_after)
        except ValueError:
            return None
        return seconds if seconds > 0 else None
