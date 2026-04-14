from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app.config import get_settings
from app.models.disaster_event import DisasterEvent
from app.models.weather_game_snapshot import WeatherGameSnapshot
from app.repositories.weather_game_snapshot import WeatherGameSnapshotRepository
from app.repositories.user import UserRepository
from app.schemas.user import AdminCreate, RegularUserCreate
from app.services.weather_service import WEATHER_CODE_LABELS
from app.utilities.security import encrypt_password


def seed_defaults(db: Session) -> None:
    settings = get_settings()
    user_repo = UserRepository(db)

    if not user_repo.get_by_username(settings.seeded_user_username):
        user_repo.create(
            RegularUserCreate(
                username=settings.seeded_user_username,
                email=settings.seeded_user_email,
                password=settings.seeded_user_password,
            ),
            password_hash=encrypt_password(settings.seeded_user_password),
        )

    if not user_repo.get_by_username(settings.seeded_admin_username):
        user_repo.create(
            AdminCreate(
                username=settings.seeded_admin_username,
                email=settings.seeded_admin_email,
                password=settings.seeded_admin_password,
            ),
            password_hash=encrypt_password(settings.seeded_admin_password),
        )

    existing_event = db.exec(select(DisasterEvent)).first()
    if existing_event:
        return

    bob = user_repo.get_by_username(settings.seeded_user_username)
    seed_events = [
        DisasterEvent(
            title="Tropical Wave Monitoring in Trinidad",
            country="Trinidad and Tobago",
            region="Port of Spain",
            category="Storm",
            event_date=date(2026, 4, 3),
            severity="Moderate",
            short_summary="Local agencies are tracking heavy rain bands and isolated flash-flood risk for low-lying communities.",
            latitude=10.6603,
            longitude=-61.5089,
            source_name="Office of Disaster Preparedness",
            source_url="https://odpm.gov.tt/",
            created_by=bob.id if bob else None,
        ),
        DisasterEvent(
            title="Saharan Dust Advisory for Eastern Caribbean",
            country="Barbados",
            region="Bridgetown",
            category="Air Quality",
            event_date=date(2026, 4, 1),
            severity="Low",
            short_summary="A dust plume is expected to reduce visibility and affect persons with respiratory conditions over the next 48 hours.",
            latitude=13.0975,
            longitude=-59.6167,
            source_name="Caribbean Weather Desk",
            created_by=bob.id if bob else None,
        ),
        DisasterEvent(
            title="Riverine Flood Recovery Operations",
            country="Guyana",
            region="Georgetown",
            category="Flood",
            event_date=date(2026, 3, 28),
            severity="High",
            short_summary="Response teams continue damage assessments and relief distribution after multi-day flood impacts in affected communities.",
            latitude=6.8013,
            longitude=-58.1551,
            source_name="StormScope Desk",
            created_by=bob.id if bob else None,
        ),
    ]
    db.add_all(seed_events)
    db.commit()


def seed_weather_game_snapshots(db: Session) -> None:
    repo = WeatherGameSnapshotRepository(db)
    if repo.has_snapshots():
        return

    seed_cities = [
        {"city_name": "Port of Spain", "country_name": "Trinidad and Tobago", "latitude": 10.6603, "longitude": -61.5089, "timezone_name": "America/Port_of_Spain"},
        {"city_name": "Kingston", "country_name": "Jamaica", "latitude": 17.9712, "longitude": -76.7936, "timezone_name": "America/Jamaica"},
        {"city_name": "Miami", "country_name": "United States", "latitude": 25.7617, "longitude": -80.1918, "timezone_name": "America/New_York"},
        {"city_name": "Lima", "country_name": "Peru", "latitude": -12.0464, "longitude": -77.0428, "timezone_name": "America/Lima"},
        {"city_name": "Mexico City", "country_name": "Mexico", "latitude": 19.4326, "longitude": -99.1332, "timezone_name": "America/Mexico_City"},
        {"city_name": "Sao Paulo", "country_name": "Brazil", "latitude": -23.5505, "longitude": -46.6333, "timezone_name": "America/Sao_Paulo"},
        {"city_name": "Buenos Aires", "country_name": "Argentina", "latitude": -34.6037, "longitude": -58.3816, "timezone_name": "America/Argentina/Buenos_Aires"},
        {"city_name": "Reykjavik", "country_name": "Iceland", "latitude": 64.1466, "longitude": -21.9426, "timezone_name": "Atlantic/Reykjavik"},
        {"city_name": "London", "country_name": "United Kingdom", "latitude": 51.5072, "longitude": -0.1276, "timezone_name": "Europe/London"},
        {"city_name": "Cairo", "country_name": "Egypt", "latitude": 30.0444, "longitude": 31.2357, "timezone_name": "Africa/Cairo"},
        {"city_name": "Mumbai", "country_name": "India", "latitude": 19.0760, "longitude": 72.8777, "timezone_name": "Asia/Kolkata"},
        {"city_name": "Singapore", "country_name": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "timezone_name": "Asia/Singapore"},
        {"city_name": "Tokyo", "country_name": "Japan", "latitude": 35.6762, "longitude": 139.6503, "timezone_name": "Asia/Tokyo"},
        {"city_name": "Sydney", "country_name": "Australia", "latitude": -33.8688, "longitude": 151.2093, "timezone_name": "Australia/Sydney"},
        {"city_name": "Ottawa", "country_name": "Canada", "latitude": 45.4215, "longitude": -75.6972, "timezone_name": "America/Toronto"},
        {"city_name": "Paris", "country_name": "France", "latitude": 48.8566, "longitude": 2.3522, "timezone_name": "Europe/Paris"},
        {"city_name": "Berlin", "country_name": "Germany", "latitude": 52.5200, "longitude": 13.4050, "timezone_name": "Europe/Berlin"},
        {"city_name": "Nairobi", "country_name": "Kenya", "latitude": -1.2921, "longitude": 36.8219, "timezone_name": "Africa/Nairobi"},
        {"city_name": "Dubai", "country_name": "United Arab Emirates", "latitude": 25.2048, "longitude": 55.2708, "timezone_name": "Asia/Dubai"},
        {"city_name": "Bangkok", "country_name": "Thailand", "latitude": 13.7563, "longitude": 100.5018, "timezone_name": "Asia/Bangkok"},
        {"city_name": "Jakarta", "country_name": "Indonesia", "latitude": -6.2088, "longitude": 106.8456, "timezone_name": "Asia/Jakarta"},
        {"city_name": "Seoul", "country_name": "South Korea", "latitude": 37.5665, "longitude": 126.9780, "timezone_name": "Asia/Seoul"},
        {"city_name": "Auckland", "country_name": "New Zealand", "latitude": -36.8509, "longitude": 174.7645, "timezone_name": "Pacific/Auckland"},
        {"city_name": "Santiago", "country_name": "Chile", "latitude": -33.4489, "longitude": -70.6693, "timezone_name": "America/Santiago"},
        {"city_name": "Bogota", "country_name": "Colombia", "latitude": 4.7110, "longitude": -74.0721, "timezone_name": "America/Bogota"},
        {"city_name": "Caracas", "country_name": "Venezuela", "latitude": 10.4806, "longitude": -66.9036, "timezone_name": "America/Caracas"},
        {"city_name": "Panama City", "country_name": "Panama", "latitude": 8.9824, "longitude": -79.5199, "timezone_name": "America/Panama"},
        {"city_name": "Bridgetown", "country_name": "Barbados", "latitude": 13.0975, "longitude": -59.6165, "timezone_name": "America/Barbados"},
    ]

    snapshots = [_build_weather_game_snapshot(seed_city) for seed_city in seed_cities]
    repo.replace_all(snapshots)


def _build_weather_game_snapshot(city: dict[str, object]) -> WeatherGameSnapshot:
    city_name = str(city["city_name"])
    country_name = str(city["country_name"])
    latitude = float(city["latitude"])
    longitude = float(city["longitude"])
    timezone_name = str(city["timezone_name"])

    signature = sum(ord(character) for character in f"{city_name}:{country_name}")
    latitude_penalty = min(abs(latitude), 60.0) * 0.32
    longitude_adjustment = ((abs(longitude) % 18) - 9) * 0.18
    signature_adjustment = ((signature % 13) - 6) * 0.55
    temperature = round(max(-4.0, min(37.5, 31.5 - latitude_penalty + longitude_adjustment + signature_adjustment)), 1)

    humidity = max(38, min(96, 54 + (signature % 42)))
    wind_speed = round(6 + (signature % 25) * 0.9, 1)
    precipitation = round(((signature // 7) % 16) * 0.3, 1)
    apparent_temperature = round(temperature + ((humidity - 60) / 14) - (wind_speed / 20), 1)

    if precipitation >= 3.6:
        weather_code = 65
    elif precipitation >= 1.8:
        weather_code = 63
    elif humidity >= 88:
        weather_code = 3
    elif humidity >= 76:
        weather_code = 2
    elif temperature <= 2:
        weather_code = 71
    else:
        weather_code = 1 if humidity >= 60 else 0

    return WeatherGameSnapshot(
        city_name=city_name,
        country_name=country_name,
        latitude=latitude,
        longitude=longitude,
        timezone_name=timezone_name,
        temperature=temperature,
        apparent_temperature=apparent_temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        precipitation=precipitation,
        weather_code=weather_code,
        weather_label=WEATHER_CODE_LABELS.get(weather_code, "Unknown"),
        is_day=(signature % 2 == 0),
        updated_at=datetime.now(timezone.utc),
    )
