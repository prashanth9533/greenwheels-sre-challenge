import app.persistence.models  # noqa: F401
from app.persistence.database import Base, engine


def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("Greenwheels database tables created successfully.")


if __name__ == "__main__":
    initialize_database()