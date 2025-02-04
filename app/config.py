from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    app_env: str = "development"
    api_rate_limit: str | None = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()