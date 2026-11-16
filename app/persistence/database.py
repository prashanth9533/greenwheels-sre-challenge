
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load database settings from the project root .env file.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured in the .env file")

# Create the PostgreSQL database engine.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# Create database sessions.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Base class for database models.
class Base(DeclarativeBase):
    pass


# Dependency for safely opening and closing database sessions.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
