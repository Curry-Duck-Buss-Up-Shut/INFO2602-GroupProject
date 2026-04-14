from datetime import date

import typer
from sqlalchemy import inspect
from sqlmodel import Session, select

from app.database import create_db_and_tables, drop_all, engine, get_cli_session
from app.models import DisasterEvent, User
from app.schemas.user import AdminCreate, RegularUserCreate
from app.services.disaster_service import NASA_EXTERNAL_SOURCE
from app.utilities.security import encrypt_password

cli = typer.Typer(help="StormScope maintenance commands.")


@cli.callback()
def main():
    """StormScope maintenance commands."""
    return None


def _load_preserved_nasa_records() -> tuple[list[dict], dict[int, str]]:
    inspector = inspect(engine)
    if not inspector.has_table(User.__table__.name) or not inspector.has_table(DisasterEvent.__table__.name):
        return [], {}

    with get_cli_session() as db:
        users = db.exec(select(User)).all()
        user_id_to_username = {user.id: user.username for user in users if user.id is not None}
        nasa_records = []

        for event in db.exec(select(DisasterEvent).where(DisasterEvent.external_source == NASA_EXTERNAL_SOURCE)).all():
            event_data = event.model_dump()
            event_data.pop("id", None)
            nasa_records.append(event_data)

    return nasa_records, user_id_to_username


def _restore_preserved_nasa_records(
    db: Session,
    nasa_records: list[dict],
    old_usernames_by_id: dict[int, str],
    new_user_ids_by_username: dict[str, int],
) -> int:
    restored_records = []

    for record in nasa_records:
        old_created_by = record.get("created_by")
        created_by = None
        if old_created_by is not None:
            old_username = old_usernames_by_id.get(old_created_by)
            if old_username:
                created_by = new_user_ids_by_username.get(old_username)

        restored_records.append(DisasterEvent(**{**record, "created_by": created_by}))

    if not restored_records:
        return 0

    db.add_all(restored_records)
    db.commit()
    return len(restored_records)


@cli.command("initialize")
def initialize():
    """Drop all tables, recreate them, and seed demo data."""
    preserved_nasa_records, old_usernames_by_id = _load_preserved_nasa_records()

    # Reset the schema first so this command behaves like a full local bootstrap.
    drop_all()
    create_db_and_tables()

    with get_cli_session() as db:  # Get a connection to the database.
        # Keep the main demo accounts the website already expects, plus a couple of extra users.
        bob = RegularUserCreate(username="bob", email="bob@example.com", password="bobpass")
        bob_db = User(
            username=bob.username,
            email=bob.email,
            password_hash=encrypt_password(bob.password),
            role=bob.role,
        )
        rick = RegularUserCreate(username="rick", email="rick@mail.com", password="rickpass")
        rick_db = User(
            username=rick.username,
            email=rick.email,
            password_hash=encrypt_password(rick.password),
            role=rick.role,
        )
        sally = RegularUserCreate(username="sally", email="sally@mail.com", password="sallypass")
        sally_db = User(
            username=sally.username,
            email=sally.email,
            password_hash=encrypt_password(sally.password),
            role=sally.role,
        )
        stormadmin = AdminCreate(
            username="stormadmin",
            email="stormadmin@example.com",
            password="adminpass",
        )
        stormadmin_db = User(
            username=stormadmin.username,
            email=stormadmin.email,
            password_hash=encrypt_password(stormadmin.password),
            role=stormadmin.role,
        )

        db.add_all([bob_db, rick_db, sally_db, stormadmin_db])  # Save all demo users at once.
        db.commit()
        db.refresh(bob_db)
        db.refresh(rick_db)
        db.refresh(sally_db)
        db.refresh(stormadmin_db)

        # StormScope does not have todos, so seed the disaster timeline entries the site expects.
        db.add_all(
            [
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
                    created_by=bob_db.id,
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
                    created_by=bob_db.id,
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
                    created_by=bob_db.id,
                ),
            ]
        )
        db.commit()

        restored_nasa_count = _restore_preserved_nasa_records(
            db,
            preserved_nasa_records,
            old_usernames_by_id,
            {
                bob_db.username: bob_db.id,
                rick_db.username: rick_db.id,
                sally_db.username: sally_db.id,
                stormadmin_db.username: stormadmin_db.id,
            },
        )

    print(f"Database initialized. Preserved {restored_nasa_count} NASA record(s).")


if __name__ == "__main__":
    cli()
