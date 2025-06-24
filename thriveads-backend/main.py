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


@app.post("/sync-yesterday")
async def sync_yesterday_data():
    """Manually trigger sync for yesterday's data"""
    try:
        from datetime import date, timedelta
        from app.services.meta_service import MetaService

        if not settings.META_ACCESS_TOKEN:
            return {
                "status": "error",
                "message": "META_ACCESS_TOKEN not configured"
            }

        yesterday = date.today() - timedelta(days=1)
        meta_service = MetaService()

        # Get yesterday's campaigns data
        campaigns_data = await meta_service.get_campaigns_with_metrics(
            client_id=settings.DEFAULT_CLIENT_ID,
            start_date=yesterday,
            end_date=yesterday
        )

        # Get yesterday's ads data
        ads_data = await meta_service.get_ads_with_metrics(
            client_id=settings.DEFAULT_CLIENT_ID,
            start_date=yesterday,
            end_date=yesterday
        )

        return {
            "status": "success",
            "message": f"Successfully synced data for {yesterday}",
            "date": str(yesterday),
            "campaigns_count": len(campaigns_data),
            "ads_count": len(ads_data),
            "campaigns_data": campaigns_data[:5],  # Show first 5 for preview
            "ads_data": ads_data[:5]  # Show first 5 for preview
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to sync yesterday's data: {str(e)}"
        }


@app.post("/start-daily-sync")
async def start_daily_sync():
    """Start automated daily sync at 6:00 AM"""
    try:
        from app.services.scheduler_service import scheduler_service

        scheduler_service.start_scheduler()

        return {
            "status": "success",
            "message": "Daily sync scheduler started",
            "schedule": "Every day at 6:00 AM",
            "next_sync": "Tomorrow at 6:00 AM (syncs yesterday's data)"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to start scheduler: {str(e)}"
        }


@app.post("/stop-daily-sync")
async def stop_daily_sync():
    """Stop automated daily sync"""
    try:
        from app.services.scheduler_service import scheduler_service

        scheduler_service.stop_scheduler()

        return {
            "status": "success",
            "message": "Daily sync scheduler stopped"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to stop scheduler: {str(e)}"
        }


@app.get("/sync-status")
async def get_sync_status():
    """Get current sync scheduler status"""
    try:
        from app.services.scheduler_service import scheduler_service

        status = scheduler_service.get_scheduler_status()

        return {
            "status": "success",
            "scheduler": status,
            "instructions": {
                "start_sync": "POST /start-daily-sync",
                "stop_sync": "POST /stop-daily-sync",
                "manual_sync": "POST /sync-yesterday"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get sync status: {str(e)}"
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
