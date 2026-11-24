from pydantic_settings import BaseSettings,SettingsConfigDict
class Settings(BaseSettings):
    app_name:str="MiGaraje Statistics Service"
    internal_api_key:str=""
    vehicles_service_url:str="http://localhost:8000"
    maintenance_service_url:str="http://localhost:8001"
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
settings=Settings()
