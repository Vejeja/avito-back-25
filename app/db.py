from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings

DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"{settings.postgres_server}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
