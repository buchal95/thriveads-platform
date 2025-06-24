"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://localhost/thriveads"
    
    # Meta API Configuration
    META_ACCESS_TOKEN: str = ""
    META_API_VERSION: str = "v18.0"  # Latest stable version

    # Optional Meta App credentials (not needed for basic API access)
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js dev server
        "https://thriveads-platform.vercel.app",  # Production frontend
    ]
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Data refresh intervals (in minutes)
    DATA_REFRESH_INTERVAL: int = 60  # 1 hour
    
    # Client configuration
    DEFAULT_CLIENT_ID: str = "513010266454814"  # Mimilátky CZ
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)


# Create settings instance
settings = Settings()
