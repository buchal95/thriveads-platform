"""
ThriveAds Platform - Simplified Main for Railway
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Simple settings without complex imports
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Create FastAPI application
app = FastAPI(
    title="ThriveAds Platform API",
    description="Meta advertising analytics platform backend",
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
        "message": "ThriveAds Platform API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Simple health check for Railway"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "timestamp": time.time(),
        "message": "ThriveAds Backend is running",
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "meta_token_set": bool(os.getenv("META_ACCESS_TOKEN"))
    }

# Basic API endpoints for testing
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "endpoints": [
            "/",
            "/health",
            "/api/v1/status"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable (Railway sets this) or default to 8000
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ThriveAds Platform on port {port}")
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development"
    )
