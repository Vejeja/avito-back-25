from pydantic import BaseSettings

class Settings(BaseSettings):
    postgres_server: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"

settings = Settings()
