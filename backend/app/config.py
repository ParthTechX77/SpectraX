import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    app_name: str = "SpectraX"
    app_version: str = "0.1.0"
    environment: str = "development"

    database_url: str = (
        "postgresql+asyncpg://spectrax:spectrax@localhost:5432/spectrax"
    )

    redis_url: str = "redis://localhost:6379/0"

    storage_path: str = "./storage"

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()