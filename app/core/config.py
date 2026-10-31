from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SubLedger API"
    environment: str = "development"
    database_url: str = "sqlite:///./subledger.db"
    api_v1_prefix: str = "/api/v1"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
