"""
ThriveAds Platform - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting ThriveAds Platform API")

    # Initialize database (only if DATABASE_URL is properly configured)
    try:
        if settings.DATABASE_URL != "postgresql://localhost/thriveads":
            await init_db()
        else:
            logger.info("Skipping database initialization - using default DATABASE_URL")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    yield

    logger.info("Shutting down ThriveAds Platform API")


# Create FastAPI application
app = FastAPI(
    title="ThriveAds Platform API",
    description="Meta advertising analytics platform backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ThriveAds Platform API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Simple health check for Railway"""
    import time
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "message": "ThriveAds Backend is running"
    }


@app.get("/test-meta-api")
async def test_meta_api():
    """Test Meta API connection"""
    try:
        from app.services.meta_service import MetaService

        if not settings.META_ACCESS_TOKEN:
            return {
                "status": "error",
                "message": "META_ACCESS_TOKEN not configured",
                "instructions": "Please set META_ACCESS_TOKEN in Railway environment variables"
            }

        meta_service = MetaService()

        # Test basic API connection by getting account info
        from facebook_business.api import FacebookAdsApi
        from facebook_business.adobjects.adaccount import AdAccount

        FacebookAdsApi.init(
            access_token=settings.META_ACCESS_TOKEN,
            api_version=settings.META_API_VERSION
        )

        account = AdAccount(f"act_{settings.DEFAULT_CLIENT_ID}")
        account_info = account.api_get(fields=['name', 'currency', 'account_status'])

        return {
            "status": "success",
            "message": "Meta API connection successful",
            "account_info": {
                "account_id": settings.DEFAULT_CLIENT_ID,
                "account_name": account_info.get('name'),
                "currency": account_info.get('currency'),
                "account_status": account_info.get('account_status')
            },
            "api_version": settings.META_API_VERSION,
            "ready_for_2025_data": True
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Meta API connection failed: {str(e)}",
            "instructions": "Please check your META_ACCESS_TOKEN and ensure it has proper permissions"
        }


if __name__ == "__main__":
    import uvicorn
    import os

    # Get port from environment variable (Railway sets this) or default to 8000
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "development"
    )
