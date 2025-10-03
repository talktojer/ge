"""
Configuration settings for the Galactic Empire application
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://postgres:galactic_empire_dev@postgres:5432/galactic_empire"
    
    # Redis
    redis_url: str = "redis://:galactic_empire_redis@redis:6379/0"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    # Environment
    environment: str = "development"
    
    # CORS
    cors_origins: str = "http://localhost:13000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Game settings
    game_name: str = "Galactic Empire"
    game_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Ignore environment variables for CORS_ORIGINS to avoid parsing issues
        env_ignore_empty = True

# Global settings instance
settings = Settings()
