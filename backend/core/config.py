import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Account-Auto-Sign"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    DATABASE_URL: str = "sqlite:///./data.db"

    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # Playwright settings
    PLAYWRIGHT_HEADLESS: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# 适配 Hugging Face Spaces：如果 /data 目录存在，则数据库写入 /data
if os.path.isdir("/data"):
    settings.DATABASE_URL = "sqlite:////data/data.db"
