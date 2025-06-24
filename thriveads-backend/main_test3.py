"""
ThriveAds Platform - Test 3: Add Database Imports
"""

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import config (we know this works from Test 2)
from app.core.config import settings

# Test 3: Add database imports
DATABASE_IMPORT_SUCCESS = True
DATABASE_ERROR = None

try:
    from app.core.database import init_db, get_db, engine
    DATABASE_IMPORT_SUCCESS = True
except Exception as e:
    DATABASE_IMPORT_SUCCESS = False
    DATABASE_ERROR = str(e)

# Test database models import
MODELS_IMPORT_SUCCESS = True
MODELS_ERROR = None

try:
    from app.models import client, campaign, ad, metrics
    MODELS_IMPORT_SUCCESS = True
except Exception as e:
    MODELS_IMPORT_SUCCESS = False
    MODELS_ERROR = str(e)

# Create FastAPI application
app = FastAPI(
    title="ThriveAds Platform API - Test 3",
    description="Testing database imports",
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
        "message": "ThriveAds Platform API - Test 3",
        "version": "1.0.0",
        "status": "healthy",
        "test": "database_imports"
    }

@app.get("/health")
async def health_check():
    """Health check with database import test"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "message": "ThriveAds Backend Test 3",
        "database_import_success": DATABASE_IMPORT_SUCCESS,
        "models_import_success": MODELS_IMPORT_SUCCESS
    }

@app.get("/debug")
async def debug_info():
    """Debug information"""
    return {
        "test_phase": "3 - Database Imports",
        "database_import": {
            "success": DATABASE_IMPORT_SUCCESS,
            "error": DATABASE_ERROR
        },
        "models_import": {
            "success": MODELS_IMPORT_SUCCESS,
            "error": MODELS_ERROR
        },
        "environment_vars": {
            "DATABASE_URL": "***" if settings.DATABASE_URL else None,
            "META_ACCESS_TOKEN": "***" if settings.META_ACCESS_TOKEN else None,
            "SECRET_KEY": "***" if settings.SECRET_KEY else None,
        }
    }

@app.get("/test-db")
async def test_database():
    """Test database connection (if imports work)"""
    if not DATABASE_IMPORT_SUCCESS:
        return {
            "status": "error",
            "message": "Database imports failed",
            "error": DATABASE_ERROR
        }
    
    try:
        # Try to create a simple database connection test
        from sqlalchemy import text
        db = next(get_db())
        result = db.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        
        return {
            "status": "success",
            "message": "Database connection successful",
            "test_result": row[0] if row else None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Database connection failed",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ThriveAds Test 3 on port {port}")
    print(f"Database import success: {DATABASE_IMPORT_SUCCESS}")
    print(f"Models import success: {MODELS_IMPORT_SUCCESS}")
    
    if DATABASE_ERROR:
        print(f"Database error: {DATABASE_ERROR}")
    if MODELS_ERROR:
        print(f"Models error: {MODELS_ERROR}")
    
    uvicorn.run(
        "main_test3:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
