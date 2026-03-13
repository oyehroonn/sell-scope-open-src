"""Application configuration"""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sellscope:sellscope@localhost:5432/sellscope"
    
    # File-based store (no Postgres/Redis when True). One of CSV or Pandas.
    USE_CSV_STORE: bool = False
    USE_PANDAS_STORE: bool = True  # Main DB as nested pandas; stores full scraped_data per asset
    DATA_DIR: str = "data"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Scraping
    SCRAPE_DELAY_MIN: float = 1.0
    SCRAPE_DELAY_MAX: float = 3.0
    SCRAPE_MAX_CONCURRENT: int = 5
    PROXY_POOL: List[str] = []
    
    # AI
    EMBEDDING_MODEL: str = "sentence-transformers/clip-ViT-B-32"
    EMBEDDING_DIMENSION: int = 512
    
    # Make.com
    MAKE_WEBHOOK_SECRET: str = ""
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
