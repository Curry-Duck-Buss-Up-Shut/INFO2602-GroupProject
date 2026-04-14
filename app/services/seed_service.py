import csv
from datetime import date, datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.models.disaster_event import DisasterEvent
from app.models.weather_game_snapshot import WeatherGameSnapshot
from app.repositories.weather_game_snapshot import WeatherGameSnapshotRepository
from app.repositories.user import UserRepository
from app.schemas.user import AdminCreate, RegularUserCreate
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
    snapshots = _load_weather_game_snapshots_from_csv()
    if snapshots:
        repo.replace_all(snapshots)


def _load_weather_game_snapshots_from_csv() -> list[WeatherGameSnapshot]:
    csv_path = _resolve_weather_game_csv_path()
    if not csv_path.exists():
        return []

    snapshots: list[WeatherGameSnapshot] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader, start=1):
            snapshot = _build_weather_game_snapshot_from_csv_row(row, index)
            if snapshot is not None:
                snapshots.append(snapshot)
    return snapshots


def _resolve_weather_game_csv_path() -> Path:
    configured_path = Path(get_settings().weather_game_csv_path)
    if configured_path.is_absolute():
        return configured_path
    return Path(__file__).resolve().parents[2] / configured_path


def _build_weather_game_snapshot_from_csv_row(row: dict[str, str], index: int) -> WeatherGameSnapshot | None:
    city_name = (row.get("capital_city") or "").strip() or (row.get("country") or "").strip()
    country_name = (row.get("country") or "").strip()
    temperature_raw = (row.get("avg_temp_c") or "").strip()
    timezone_name = (row.get("timezone") or "").strip() or _extract_primary_timezone(row.get("all_country_timezones", ""))

    if not city_name or not country_name or not temperature_raw:
        return None

    try:
        temperature = round(float(temperature_raw), 2)
    except ValueError:
        return None

    apparent_temperature = temperature
    humidity = 55
    wind_speed = 8.0
    precipitation = 0.0
    weather_code = _weather_code_for_temperature(temperature)
    weather_label = "Average temperature"
    source_name = (row.get("temperature_source") or "").strip() or "gameinfo.csv"

    return WeatherGameSnapshot(
        city_name=city_name,
        country_name=country_name,
        latitude=float(index),
        longitude=0.0,
        timezone_name=timezone_name or "auto",
        temperature=temperature,
        apparent_temperature=apparent_temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        precipitation=precipitation,
        weather_code=weather_code,
        weather_label=weather_label,
        is_day=True,
        source_name=source_name,
        updated_at=datetime.now(timezone.utc),
    )


def _extract_primary_timezone(raw_value: str) -> str:
    return (raw_value or "").split("|", maxsplit=1)[0].strip()


def _weather_code_for_temperature(temperature: float) -> int:
    if temperature <= 0:
        return 71
    if temperature <= 10:
        return 3
    if temperature <= 20:
        return 2
    if temperature <= 28:
        return 1
    return 0
