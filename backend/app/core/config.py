"""
Configuration settings for the Galactic Empire application
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:galactic_empire_dev@postgres:5432/galactic_empire")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://:galactic_empire_redis@redis:6379/0")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:13000").split(",")
    
    # Game settings
    game_name: str = "Galactic Empire"
    game_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
