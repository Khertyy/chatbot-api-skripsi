from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    app_env: str = "development"
    api_rate_limit: str | None = None
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0
    session_ttl: int = 86400  # 24 hours in seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()