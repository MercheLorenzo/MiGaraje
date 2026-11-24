from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "MiGaraje API Gateway"
    database_url: str = "sqlite:///./gateway.db"
    jwt_secret: str = "CHANGE_ME_BEFORE_PUBLIC_DEPLOYMENT"
    internal_api_key: str = ""
    vehicles_service_url: str = "http://localhost:8000"
    maintenance_service_url: str = "http://localhost:8001"
    planning_service_url: str = "http://localhost:8002"
    statistics_service_url: str = "http://localhost:8003"
    notifications_service_url: str = "http://localhost:8004"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
