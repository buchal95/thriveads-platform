"""
ThriveAds Platform - Test 1: Add Config Import
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Test 1: Add back config import
try:
    from app.core.config import settings
    CONFIG_IMPORT_SUCCESS = True
    ENVIRONMENT = settings.ENVIRONMENT
    ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS
except Exception as e:
    CONFIG_IMPORT_SUCCESS = False
    CONFIG_ERROR = str(e)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Create FastAPI application
app = FastAPI(
    title="ThriveAds Platform API - Test 1",
    description="Testing config import",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ThriveAds Platform API - Test 1",
        "version": "1.0.0",
        "status": "healthy",
        "test": "config_import"
    }

@app.get("/health")
async def health_check():
    """Health check with config test"""
    result = {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "timestamp": time.time(),
        "message": "ThriveAds Backend Test 1",
        "config_import_success": CONFIG_IMPORT_SUCCESS
    }
    
    if not CONFIG_IMPORT_SUCCESS:
        result["config_error"] = CONFIG_ERROR
    
    return result

@app.get("/debug")
async def debug_info():
    """Debug information"""
    return {
        "test_phase": "1 - Config Import",
        "config_import_success": CONFIG_IMPORT_SUCCESS,
        "config_error": CONFIG_ERROR if not CONFIG_IMPORT_SUCCESS else None,
        "environment_vars": {
            "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else None,
            "META_ACCESS_TOKEN": "***" if os.getenv("META_ACCESS_TOKEN") else None,
            "SECRET_KEY": "***" if os.getenv("SECRET_KEY") else None,
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ThriveAds Test 1 on port {port}")
    print(f"Config import success: {CONFIG_IMPORT_SUCCESS}")
    
    uvicorn.run(
        "main_test1:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
