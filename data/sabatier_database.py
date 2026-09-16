import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SABATIER_DATABASE_URL = os.getenv(
    "SABATIER_DATABASE_URL",
    "postgresql+psycopg://postgres:labs@localhost:5434/sabatier",
)

engine = create_engine(SABATIER_DATABASE_URL)
SabatierSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass

def get_sabatier_session():
    with SabatierSession() as session:
        yield session
