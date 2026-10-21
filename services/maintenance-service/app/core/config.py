from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MiGaraje Maintenance Service"
    database_url: str = "sqlite:///./maintenance.db"
    vehicles_service_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
