from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    gemini_api_key: str
    base_api_url: str = "https://dpppa-sulutprov.support"  # Base URL saja
    app_env: str = "development"
    api_rate_limit: Optional[str] = None
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    session_ttl: int = 86400  # 24 hours in seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()