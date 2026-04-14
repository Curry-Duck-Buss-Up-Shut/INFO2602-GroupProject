from typing import Any, Optional

import httpx

from app.config import get_settings


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


class WeatherService:
    async def search_city(self, query: str, count: int = 6) -> list[dict[str, Any]]:
        if not query.strip():
            return []

        settings = get_settings()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                settings.open_meteo_geocoding_url,
                params={"name": query, "count": count, "language": "en", "format": "json"},
            )
            response.raise_for_status()
        payload = response.json()
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
        data = await self._fetch_weather(latitude, longitude, timezone)
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
        data = await self._fetch_weather(latitude, longitude, timezone)
        daily = data.get("daily", {})
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
        return {"forecast": forecast_days}

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

    async def _fetch_weather(self, latitude: float, longitude: float, timezone: Optional[str]) -> dict[str, Any]:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                settings.open_meteo_forecast_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone or "auto",
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
            response.raise_for_status()
        return response.json()
