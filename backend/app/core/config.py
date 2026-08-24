from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://gridiron:gridiron@db:5432/gridiron"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    starting_capital: int = 1_000_000
    training_slots_per_day: int = 3
    training_duration_hours: int = 18

    class Config:
        env_file = ".env"


settings = Settings()
