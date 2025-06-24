"""
ThriveAds Platform - Fixed Version
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import fixed config
from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title="ThriveAds Platform API",
    description="Meta advertising analytics platform backend",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configure CORS with fixed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ThriveAds Platform API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Simple health check for Railway"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "message": "ThriveAds Backend is running"
    }

@app.get("/debug")
async def debug_info():
    """Debug information"""
    return {
        "status": "operational",
        "config": {
            "environment": settings.ENVIRONMENT,
            "allowed_origins": settings.get_allowed_origins,
            "database_url_set": bool(settings.DATABASE_URL and settings.DATABASE_URL != "postgresql://localhost/thriveads"),
            "meta_token_set": bool(settings.META_ACCESS_TOKEN),
            "secret_key_set": bool(settings.SECRET_KEY and settings.SECRET_KEY != "your-secret-key-change-in-production"),
        }
    }

# Basic API endpoints
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "endpoints": [
            "/",
            "/health", 
            "/debug",
            "/api/v1/status"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ThriveAds Platform on port {port}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Allowed origins: {settings.get_allowed_origins}")
    
    uvicorn.run(
        "main_fixed:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "development"
    )
