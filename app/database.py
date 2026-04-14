import logging
from contextlib import contextmanager
from sqlmodel import SQLModel, Session, create_engine
from app.config import get_settings
from app.models import *  

logger = logging.getLogger(__name__)

settings = get_settings()
engine_kwargs = {
    "echo": settings.env.lower() in ["dev", "development", "test", "testing", "staging"],
}

if settings.database_uri.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_additional_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
        }
    )

engine = create_engine(settings.database_uri, **engine_kwargs)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def initialize_database():
    create_db_and_tables()
    from app.services.seed_service import seed_defaults

    with Session(engine) as session:
        seed_defaults(session)

def drop_all():
    SQLModel.metadata.drop_all(bind=engine)
    
def _session_generator():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

def get_session():
    yield from _session_generator()

@contextmanager
def get_cli_session():
    yield from _session_generator()
