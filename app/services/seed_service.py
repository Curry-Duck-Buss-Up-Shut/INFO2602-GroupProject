from datetime import date

from sqlmodel import Session, select

from app.config import get_settings
from app.models.disaster_event import DisasterEvent
from app.models.user import User
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
