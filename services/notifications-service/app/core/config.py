from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    app_name:str="MiGaraje Notifications Service"
    database_url:str="sqlite:///./notifications.db"
    internal_api_key:str=""
    planning_service_url:str="http://localhost:8002"
    vehicles_service_url:str="http://localhost:8000"
    gateway_service_url:str="http://localhost:8090"
    smtp_host:str=""
    smtp_port:int=587
    smtp_user:str=""
    smtp_password:str=""
    smtp_from:str=""
    notification_interval_seconds:int=3600
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
