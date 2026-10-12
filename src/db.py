import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base

DEFAULT_DB_PATH = os.environ.get("CRM_DB_PATH", "crm.db")


def get_engine(db_path: str = DEFAULT_DB_PATH):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
