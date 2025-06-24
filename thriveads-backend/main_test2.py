"""
ThriveAds Platform - Test 2: Simplified Config
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Test 2: Create simplified config without pydantic
class SimpleSettings:
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/thriveads")
        self.META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
        self.META_API_VERSION = os.getenv("META_API_VERSION", "v23.0")
        self.SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DEFAULT_CLIENT_ID = os.getenv("DEFAULT_CLIENT_ID", "513010266454814")
        
        # CORS origins
        origins_str = os.getenv("ALLOWED_ORIGINS", "*")
        if origins_str == "*":
            self.ALLOWED_ORIGINS = ["*"]
        else:
            self.ALLOWED_ORIGINS = origins_str.split(",")

# Test both approaches
SIMPLE_CONFIG_SUCCESS = True
PYDANTIC_CONFIG_SUCCESS = True
SIMPLE_CONFIG_ERROR = None
PYDANTIC_CONFIG_ERROR = None

# Try simple config
try:
    simple_settings = SimpleSettings()
    SIMPLE_CONFIG_SUCCESS = True
except Exception as e:
    SIMPLE_CONFIG_SUCCESS = False
    SIMPLE_CONFIG_ERROR = str(e)

# Try pydantic config
try:
    from app.core.config import settings as pydantic_settings
    PYDANTIC_CONFIG_SUCCESS = True
    settings = pydantic_settings
except Exception as e:
    PYDANTIC_CONFIG_SUCCESS = False
    PYDANTIC_CONFIG_ERROR = str(e)
    settings = simple_settings

# Create FastAPI application
app = FastAPI(
    title="ThriveAds Platform API - Test 2",
    description="Testing config approaches",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ThriveAds Platform API - Test 2",
        "version": "1.0.0",
        "status": "healthy",
        "test": "config_comparison"
    }

@app.get("/health")
async def health_check():
    """Health check with config test"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "message": "ThriveAds Backend Test 2",
        "simple_config_success": SIMPLE_CONFIG_SUCCESS,
        "pydantic_config_success": PYDANTIC_CONFIG_SUCCESS
    }

@app.get("/debug")
async def debug_info():
    """Debug information"""
    return {
        "test_phase": "2 - Config Comparison",
        "simple_config": {
            "success": SIMPLE_CONFIG_SUCCESS,
            "error": SIMPLE_CONFIG_ERROR
        },
        "pydantic_config": {
            "success": PYDANTIC_CONFIG_SUCCESS,
            "error": PYDANTIC_CONFIG_ERROR
        },
        "current_settings": {
            "environment": settings.ENVIRONMENT,
            "database_url_set": bool(settings.DATABASE_URL and settings.DATABASE_URL != "postgresql://localhost/thriveads"),
            "meta_token_set": bool(settings.META_ACCESS_TOKEN),
            "secret_key_set": bool(settings.SECRET_KEY and settings.SECRET_KEY != "default-secret-key"),
            "allowed_origins": settings.ALLOWED_ORIGINS
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ThriveAds Test 2 on port {port}")
    print(f"Simple config success: {SIMPLE_CONFIG_SUCCESS}")
    print(f"Pydantic config success: {PYDANTIC_CONFIG_SUCCESS}")
    
    uvicorn.run(
        "main_test2:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
