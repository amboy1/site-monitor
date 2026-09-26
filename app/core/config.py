import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically locate project root directory and load .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    # App Settings
    APP_ENV: str = os.getenv("APP_ENV", "production")
    APP_NAME: str = os.getenv("APP_NAME", "Site Monitor Service")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))

    # Security & JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", 
        "change-me-to-a-super-secret-64-char-min-random-string"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Database Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@db:5432/site_monitor"
    )

    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # CORS Settings
    CORS_ORIGINS: list[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "").split(",") 
        if origin.strip()
    ]

    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
