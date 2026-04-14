import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as dt_timezone
from threading import Lock
from typing import Any, Awaitable, Callable, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.config import get_settings
from app.repositories.weather_current_snapshot import WeatherCurrentSnapshotRepository
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
_upstream_request_lock = asyncio.Lock()
_next_upstream_request_at = 0.0


class WeatherService:
    def __init__(
        self,
        forecast_repo: WeatherForecastSnapshotRepository | None = None,
        current_snapshot_repo: WeatherCurrentSnapshotRepository | None = None,
    ):
        self.forecast_repo = forecast_repo
        self.current_snapshot_repo = current_snapshot_repo

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
        normalized_location = self._normalize_weather_location(latitude, longitude, timezone)
        snapshot = None
        snapshot_payload = None
        cache_key = self._build_current_weather_cache_key(**normalized_location)

        if self.current_snapshot_repo:
            snapshot = self.current_snapshot_repo.get_snapshot(
                normalized_location["latitude"],
                normalized_location["longitude"],
                normalized_location["timezone"],
            )
            snapshot_payload = self._deserialize_current_snapshot(snapshot.weather_json) if snapshot else None
            if snapshot_payload and not self._is_current_snapshot_stale(
                snapshot.fetched_at,
                settings.weather_current_snapshot_ttl_seconds,
            ):
                return snapshot_payload
        try:
            data = await self._get_or_fetch_json(
                cache_key=cache_key,
                ttl_seconds=settings.weather_cache_ttl_seconds,
                stale_ttl_seconds=settings.weather_stale_ttl_seconds,
                fetcher=lambda: self._fetch_live_current_weather(**normalized_location),
            )
        except Exception as primary_error:
            try:
                data = await self._get_or_fetch_json(
                    cache_key=f"{cache_key}:met-no",
                    ttl_seconds=settings.weather_cache_ttl_seconds,
                    stale_ttl_seconds=settings.weather_stale_ttl_seconds,
                    fetcher=lambda: self._fetch_met_no_current_weather(**normalized_location),
                )
                self._cache_current_weather_fallback_payload(cache_key, data)
            except Exception:
                if snapshot_payload and snapshot and self._is_current_snapshot_servable(
                    snapshot.fetched_at,
                    settings.weather_current_snapshot_stale_ttl_seconds,
                ):
                    return snapshot_payload
                if isinstance(primary_error, UpstreamRateLimitError):
                    raise primary_error
                if isinstance(primary_error, httpx.HTTPStatusError) and primary_error.response.status_code == 429:
                    raise UpstreamRateLimitError(self._parse_retry_after_seconds(primary_error.response)) from primary_error
                raise primary_error

        formatted_payload = self._format_current_weather_payload(data)
        if self.current_snapshot_repo:
            self.current_snapshot_repo.upsert_snapshot(
                latitude=normalized_location["latitude"],
                longitude=normalized_location["longitude"],
                timezone_name=normalized_location["timezone"],
                weather_json=json.dumps(formatted_payload),
                fetched_at=datetime.now(dt_timezone.utc),
            )
        return formatted_payload

    async def get_current_weather_batch(self, locations: list[dict[str, Any]]) -> list[dict[str, Any] | None]:
        if not locations:
            return []

        settings = get_settings()
        normalized_locations = [
            self._normalize_weather_location(
                location["latitude"],
                location["longitude"],
                location.get("timezone", "auto"),
            )
            for location in locations
        ]
        now = time.monotonic()
        results: list[dict[str, Any] | None] = [None] * len(normalized_locations)
        stale_entries: dict[int, CacheEntry] = {}
        stale_snapshot_payloads: dict[int, dict[str, Any]] = {}
        uncached_locations: list[dict[str, Any]] = []
        uncached_indices: list[int] = []

        for index, location in enumerate(normalized_locations):
            cache_key = self._build_current_weather_cache_key(**location)
            cached_entry = self._get_cache_entry(cache_key)
            if cached_entry and cached_entry.expires_at > now:
                results[index] = self._format_current_weather_payload(cached_entry.value)
                continue
            if self.current_snapshot_repo:
                snapshot = self.current_snapshot_repo.get_snapshot(
                    location["latitude"],
                    location["longitude"],
                    location["timezone"],
                )
                snapshot_payload = self._deserialize_current_snapshot(snapshot.weather_json) if snapshot else None
                if snapshot_payload and not self._is_current_snapshot_stale(
                    snapshot.fetched_at,
                    settings.weather_current_snapshot_ttl_seconds,
                ):
                    results[index] = snapshot_payload
                    continue
                if snapshot_payload and self._is_current_snapshot_servable(
                    snapshot.fetched_at,
                    settings.weather_current_snapshot_stale_ttl_seconds,
                ):
                    stale_snapshot_payloads[index] = snapshot_payload
            if cached_entry and cached_entry.stale_until > now:
                stale_entries[index] = cached_entry
            uncached_locations.append(location)
            uncached_indices.append(index)

        if not uncached_locations:
            return results

        try:
            payloads = await self._fetch_live_current_weather_batch(uncached_locations)
        except httpx.HTTPStatusError as exc:
            self._apply_stale_batch_results(results, stale_entries, stale_snapshot_payloads, uncached_indices)
            if exc.response.status_code == 429 and not any(result is not None for result in results):
                raise UpstreamRateLimitError(self._parse_retry_after_seconds(exc.response)) from exc
            if any(result is not None for result in results):
                return results
            raise
        except Exception:
            self._apply_stale_batch_results(results, stale_entries, stale_snapshot_payloads, uncached_indices)
            if any(result is not None for result in results):
                return results
            raise

        expires_at = time.monotonic() + settings.weather_cache_ttl_seconds
        stale_until = expires_at + settings.weather_stale_ttl_seconds

        for offset, result_index in enumerate(uncached_indices):
            payload = payloads[offset] if offset < len(payloads) else None
            if isinstance(payload, dict):
                cache_key = self._build_current_weather_cache_key(**normalized_locations[result_index])
                self._set_cache_entry(cache_key, payload, expires_at=expires_at, stale_until=stale_until)
                formatted_payload = self._format_current_weather_payload(payload)
                if self.current_snapshot_repo:
                    self.current_snapshot_repo.upsert_snapshot(
                        latitude=normalized_locations[result_index]["latitude"],
                        longitude=normalized_locations[result_index]["longitude"],
                        timezone_name=normalized_locations[result_index]["timezone"],
                        weather_json=json.dumps(formatted_payload),
                        fetched_at=datetime.now(dt_timezone.utc),
                    )
                results[result_index] = formatted_payload
                continue

            stale_entry = stale_entries.get(result_index)
            if stale_entry:
                results[result_index] = self._format_current_weather_payload(stale_entry.value)
                continue

            snapshot_payload = stale_snapshot_payloads.get(result_index)
            if snapshot_payload:
                results[result_index] = snapshot_payload

        return results

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
            daily = data.get("daily", {})
            forecast_days = self._build_forecast_days(daily)
        except Exception as primary_error:
            try:
                forecast_days = await self._fetch_met_no_forecast(
                    normalized_latitude,
                    normalized_longitude,
                    normalized_timezone,
                )
            except Exception:
                if forecast_days and snapshot and self._is_forecast_snapshot_servable(
                    snapshot.fetched_at,
                    settings.weather_forecast_snapshot_stale_ttl_seconds,
                ):
                    return {"forecast": forecast_days}
                if isinstance(primary_error, UpstreamRateLimitError):
                    raise primary_error
                if isinstance(primary_error, httpx.HTTPStatusError) and primary_error.response.status_code == 429:
                    raise UpstreamRateLimitError(self._parse_retry_after_seconds(primary_error.response)) from primary_error
                raise primary_error

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

    def _normalize_weather_location(self, latitude: float, longitude: float, timezone: str | None) -> dict[str, Any]:
        return {
            "latitude": round(float(latitude), 4),
            "longitude": round(float(longitude), 4),
            "timezone": (timezone or "auto").strip() or "auto",
        }

    def _build_current_weather_cache_key(self, latitude: float, longitude: float, timezone: str) -> str:
        return f"weather-current:{latitude}:{longitude}:{timezone.lower()}"

    def _cache_current_weather_fallback_payload(self, cache_key: str, payload: dict[str, Any]) -> None:
        settings = get_settings()
        expires_at = time.monotonic() + settings.weather_cache_ttl_seconds
        stale_until = expires_at + settings.weather_stale_ttl_seconds
        self._set_cache_entry(cache_key, payload, expires_at=expires_at, stale_until=stale_until)

    def _format_current_weather_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        current = data.get("current", {})
        weather_code = current.get("weather_code")
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
            "weather_code": weather_code,
            "weather_label": WEATHER_CODE_LABELS.get(weather_code, "Unknown"),
        }

    def _apply_stale_batch_results(
        self,
        results: list[dict[str, Any] | None],
        stale_entries: dict[int, CacheEntry],
        stale_snapshot_payloads: dict[int, dict[str, Any]],
        indices: list[int],
    ) -> None:
        for index in indices:
            stale_entry = stale_entries.get(index)
            if stale_entry:
                results[index] = self._format_current_weather_payload(stale_entry.value)
                continue
            snapshot_payload = stale_snapshot_payloads.get(index)
            if snapshot_payload:
                results[index] = snapshot_payload

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

    async def _fetch_live_current_weather_batch(self, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        settings = get_settings()
        payload = await self._request_json(
            settings.open_meteo_forecast_url,
            params={
                "latitude": ",".join(str(location["latitude"]) for location in locations),
                "longitude": ",".join(str(location["longitude"]) for location in locations),
                "timezone": ",".join(location["timezone"] for location in locations),
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
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [payload]
        return []

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

    async def _fetch_met_no_current_weather(self, latitude: float, longitude: float, timezone: Optional[str]) -> dict[str, Any]:
        payload = await self._fetch_met_no_locationforecast(latitude, longitude)
        return self._build_met_no_current_weather_payload(payload, latitude, longitude, timezone or "auto")

    async def _fetch_met_no_forecast(self, latitude: float, longitude: float, timezone: Optional[str]) -> list[dict[str, Any]]:
        payload = await self._fetch_met_no_locationforecast(latitude, longitude)
        return self._build_met_no_forecast_days(payload, timezone or "auto")

    async def _fetch_met_no_locationforecast(self, latitude: float, longitude: float) -> dict[str, Any]:
        settings = get_settings()
        return await self._request_json(
            settings.met_no_locationforecast_url,
            params={"lat": latitude, "lon": longitude},
            headers={"User-Agent": settings.met_no_user_agent},
        )

    def _build_met_no_current_weather_payload(
        self,
        payload: dict[str, Any],
        latitude: float,
        longitude: float,
        timezone: str,
    ) -> dict[str, Any]:
        timeseries = payload.get("properties", {}).get("timeseries", [])
        if not timeseries:
            raise ValueError("MET Norway did not return current weather data.")

        forecast_point = timeseries[0]
        weather_data = forecast_point.get("data", {})
        instant_details = weather_data.get("instant", {}).get("details", {})
        observed_at = self._convert_met_no_time(forecast_point.get("time"), timezone)
        symbol_code = self._get_met_no_symbol_code(weather_data)
        weather_code = self._map_met_no_symbol_code(symbol_code)
        wind_speed = instant_details.get("wind_speed")

        return {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "timezone_abbreviation": observed_at.tzname() or "UTC",
            "current": {
                "time": observed_at.isoformat(),
                "temperature_2m": instant_details.get("air_temperature"),
                "apparent_temperature": instant_details.get("air_temperature"),
                "relative_humidity_2m": instant_details.get("relative_humidity"),
                "wind_speed_10m": round(wind_speed * 3.6, 1) if isinstance(wind_speed, (int, float)) else None,
                "precipitation": self._get_met_no_precipitation_amount(weather_data),
                "is_day": 1 if self._is_day_from_met_no_symbol(symbol_code, observed_at) else 0,
                "weather_code": weather_code,
            },
        }

    def _build_met_no_forecast_days(self, payload: dict[str, Any], timezone: str) -> list[dict[str, Any]]:
        timeseries = payload.get("properties", {}).get("timeseries", [])
        if not timeseries:
            raise ValueError("MET Norway did not return forecast data.")

        grouped_days: dict[str, dict[str, Any]] = {}
        for entry in timeseries:
            weather_data = entry.get("data", {})
            instant_details = weather_data.get("instant", {}).get("details", {})
            local_time = self._convert_met_no_time(entry.get("time"), timezone)
            day_key = local_time.date().isoformat()
            day_bucket = grouped_days.setdefault(
                day_key,
                {
                    "date": day_key,
                    "temperatures": [],
                    "precipitation_probabilities": [],
                    "symbol_code": None,
                    "symbol_distance": None,
                },
            )

            temperature = instant_details.get("air_temperature")
            if isinstance(temperature, (int, float)):
                day_bucket["temperatures"].append(float(temperature))

            precipitation_probability = self._get_met_no_precipitation_probability(weather_data)
            if isinstance(precipitation_probability, (int, float)):
                day_bucket["precipitation_probabilities"].append(int(round(precipitation_probability)))

            symbol_code = self._get_met_no_symbol_code(weather_data)
            if symbol_code:
                distance_to_midday = abs((local_time.hour + (local_time.minute / 60)) - 12)
                if day_bucket["symbol_distance"] is None or distance_to_midday < day_bucket["symbol_distance"]:
                    day_bucket["symbol_code"] = symbol_code
                    day_bucket["symbol_distance"] = distance_to_midday

        forecast_days = []
        for day_key in sorted(grouped_days.keys())[:7]:
            day_bucket = grouped_days[day_key]
            temperatures = day_bucket["temperatures"]
            if not temperatures:
                continue
            weather_code = self._map_met_no_symbol_code(day_bucket["symbol_code"])
            precipitation_values = day_bucket["precipitation_probabilities"]
            forecast_days.append(
                {
                    "date": day_bucket["date"],
                    "weather_code": weather_code,
                    "weather_label": WEATHER_CODE_LABELS.get(weather_code, "Unknown"),
                    "temperature_max": round(max(temperatures), 1),
                    "temperature_min": round(min(temperatures), 1),
                    "precipitation_probability": max(precipitation_values) if precipitation_values else None,
                }
            )
        return forecast_days

    def _convert_met_no_time(self, value: str | None, timezone: str) -> datetime:
        if not value:
            return datetime.now(dt_timezone.utc)
        observed_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return observed_at.astimezone(self._resolve_timezone(timezone))

    def _resolve_timezone(self, timezone: str) -> dt_timezone | ZoneInfo:
        normalized_timezone = (timezone or "").strip()
        if not normalized_timezone or normalized_timezone.lower() == "auto":
            return dt_timezone.utc
        try:
            return ZoneInfo(normalized_timezone)
        except ZoneInfoNotFoundError:
            return dt_timezone.utc

    def _get_met_no_symbol_code(self, weather_data: dict[str, Any]) -> str | None:
        for period in ("next_1_hours", "next_6_hours", "next_12_hours"):
            symbol_code = weather_data.get(period, {}).get("summary", {}).get("symbol_code")
            if symbol_code:
                return str(symbol_code)
        return None

    def _get_met_no_precipitation_amount(self, weather_data: dict[str, Any]) -> float | int:
        for period in ("next_1_hours", "next_6_hours", "next_12_hours"):
            precipitation_amount = weather_data.get(period, {}).get("details", {}).get("precipitation_amount")
            if isinstance(precipitation_amount, (int, float)):
                return precipitation_amount
        return 0

    def _get_met_no_precipitation_probability(self, weather_data: dict[str, Any]) -> float | None:
        for period in ("next_1_hours", "next_6_hours", "next_12_hours"):
            probability = weather_data.get(period, {}).get("details", {}).get("probability_of_precipitation")
            if isinstance(probability, (int, float)):
                return float(probability)
        return None

    def _is_day_from_met_no_symbol(self, symbol_code: str | None, observed_at: datetime) -> bool:
        normalized_symbol = (symbol_code or "").lower()
        if "_night" in normalized_symbol:
            return False
        if "_day" in normalized_symbol:
            return True
        return 6 <= observed_at.hour < 18

    def _map_met_no_symbol_code(self, symbol_code: str | None) -> int:
        normalized_symbol = (symbol_code or "").lower()
        if "thunder" in normalized_symbol:
            return 95
        if "snow" in normalized_symbol or "sleet" in normalized_symbol:
            if "heavy" in normalized_symbol:
                return 75
            if "light" in normalized_symbol:
                return 71
            return 73
        if "rainshowers" in normalized_symbol:
            if "heavy" in normalized_symbol:
                return 81
            return 80
        if "rain" in normalized_symbol:
            if "heavy" in normalized_symbol:
                return 65
            if "light" in normalized_symbol:
                return 61
            return 63
        if "drizzle" in normalized_symbol:
            if "heavy" in normalized_symbol:
                return 55
            if "light" in normalized_symbol:
                return 51
            return 53
        if "fog" in normalized_symbol:
            return 45
        if "partlycloudy" in normalized_symbol:
            return 2
        if "fair" in normalized_symbol:
            return 1
        if "cloudy" in normalized_symbol:
            return 3
        return 0

    def _deserialize_forecast_days(self, forecast_json: str) -> list[dict[str, Any]]:
        try:
            payload = json.loads(forecast_json)
        except (TypeError, ValueError):
            return []
        return payload if isinstance(payload, list) else []

    def _deserialize_current_snapshot(self, weather_json: str) -> dict[str, Any] | None:
        try:
            payload = json.loads(weather_json)
        except (TypeError, ValueError):
            return None
        return payload if isinstance(payload, dict) else None

    def _coerce_utc_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=dt_timezone.utc)
        return value.astimezone(dt_timezone.utc)

    def _is_current_snapshot_stale(self, fetched_at: datetime, ttl_seconds: int) -> bool:
        return datetime.now(dt_timezone.utc) - self._coerce_utc_datetime(fetched_at) > timedelta(seconds=ttl_seconds)

    def _is_current_snapshot_servable(self, fetched_at: datetime, stale_ttl_seconds: int) -> bool:
        return datetime.now(dt_timezone.utc) - self._coerce_utc_datetime(fetched_at) <= timedelta(seconds=stale_ttl_seconds)

    def _is_forecast_snapshot_stale(self, fetched_at: datetime, ttl_seconds: int) -> bool:
        return datetime.now(dt_timezone.utc) - self._coerce_utc_datetime(fetched_at) > timedelta(seconds=ttl_seconds)

    def _is_forecast_snapshot_servable(self, fetched_at: datetime, stale_ttl_seconds: int) -> bool:
        return datetime.now(dt_timezone.utc) - self._coerce_utc_datetime(fetched_at) <= timedelta(seconds=stale_ttl_seconds)

    async def _request_json(
        self,
        url: str,
        params: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        await self._wait_for_upstream_slot()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
        return response.json()

    async def _wait_for_upstream_slot(self) -> None:
        interval_seconds = max(get_settings().weather_upstream_min_interval_ms, 0) / 1000
        if interval_seconds <= 0:
            return

        global _next_upstream_request_at
        async with _upstream_request_lock:
            now = time.monotonic()
            wait_seconds = _next_upstream_request_at - now
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            _next_upstream_request_at = time.monotonic() + interval_seconds

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
