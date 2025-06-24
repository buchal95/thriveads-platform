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
    """Manually trigger sync for yesterday's data and store in database"""
    try:
        from datetime import date, timedelta
        from app.services.meta_service import MetaService
        from app.core.database import get_session_local
        from app.models.campaign import Campaign
        from app.models.ad import Ad
        from app.models.metrics import CampaignMetrics, AdMetrics
        from app.models.client import Client

        if not settings.META_ACCESS_TOKEN:
            return {
                "status": "error",
                "message": "META_ACCESS_TOKEN not configured"
            }

        yesterday = date.today() - timedelta(days=1)
        meta_service = MetaService()

        # Get database session
        SessionLocal = get_session_local()
        db = SessionLocal()

        try:
            # Ensure client exists
            client = db.query(Client).filter(Client.id == settings.DEFAULT_CLIENT_ID).first()
            if not client:
                client = Client(
                    id=settings.DEFAULT_CLIENT_ID,
                    name="Mimilátky - Notie s.r.o.",
                    currency="CZK"
                )
                db.add(client)
                db.commit()

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

            campaigns_stored = 0
            ads_stored = 0
            campaign_metrics_stored = 0
            ad_metrics_stored = 0

            # Store campaigns and metrics
            for campaign_data in campaigns_data:
                # Store/update campaign
                campaign = db.query(Campaign).filter(Campaign.id == campaign_data['campaign_id']).first()
                if not campaign:
                    campaign = Campaign(
                        id=campaign_data['campaign_id'],
                        name=campaign_data['campaign_name'],
                        status=campaign_data['status'],
                        objective=campaign_data.get('objective'),
                        client_id=settings.DEFAULT_CLIENT_ID
                    )
                    db.add(campaign)
                    campaigns_stored += 1
                else:
                    campaign.name = campaign_data['campaign_name']
                    campaign.status = campaign_data['status']
                    campaign.objective = campaign_data.get('objective')

                # Store campaign metrics for yesterday
                metrics_id = f"{campaign_data['campaign_id']}_{yesterday}"
                campaign_metrics = db.query(CampaignMetrics).filter(CampaignMetrics.id == metrics_id).first()
                if not campaign_metrics:
                    campaign_metrics = CampaignMetrics(
                        id=metrics_id,
                        campaign_id=campaign_data['campaign_id'],
                        date=yesterday,
                        impressions=campaign_data.get('impressions', 0),
                        clicks=campaign_data.get('clicks', 0),
                        spend=campaign_data.get('spend', 0),
                        conversions=campaign_data.get('conversions', 0),
                        ctr=campaign_data.get('ctr', 0),
                        cpc=campaign_data.get('cpc', 0),
                        cpm=campaign_data.get('cpm', 0),
                        frequency=campaign_data.get('frequency', 0),
                        currency="CZK"
                    )
                    db.add(campaign_metrics)
                    campaign_metrics_stored += 1
                else:
                    # Update existing metrics
                    campaign_metrics.impressions = campaign_data.get('impressions', 0)
                    campaign_metrics.clicks = campaign_data.get('clicks', 0)
                    campaign_metrics.spend = campaign_data.get('spend', 0)
                    campaign_metrics.conversions = campaign_data.get('conversions', 0)
                    campaign_metrics.ctr = campaign_data.get('ctr', 0)
                    campaign_metrics.cpc = campaign_data.get('cpc', 0)
                    campaign_metrics.cpm = campaign_data.get('cpm', 0)
                    campaign_metrics.frequency = campaign_data.get('frequency', 0)

            # Store ads and metrics
            for ad_data in ads_data:
                # Store/update ad
                ad = db.query(Ad).filter(Ad.id == ad_data['ad_id']).first()
                if not ad:
                    ad = Ad(
                        id=ad_data['ad_id'],
                        name=ad_data['ad_name'],
                        status=ad_data['status'],
                        campaign_id=ad_data['campaign_id'],
                        client_id=settings.DEFAULT_CLIENT_ID
                    )
                    db.add(ad)
                    ads_stored += 1
                else:
                    ad.name = ad_data['ad_name']
                    ad.status = ad_data['status']

                # Store ad metrics for yesterday
                metrics_id = f"{ad_data['ad_id']}_{yesterday}"
                ad_metrics = db.query(AdMetrics).filter(AdMetrics.id == metrics_id).first()
                if not ad_metrics:
                    ad_metrics = AdMetrics(
                        id=metrics_id,
                        ad_id=ad_data['ad_id'],
                        date=yesterday,
                        impressions=ad_data.get('impressions', 0),
                        clicks=ad_data.get('clicks', 0),
                        spend=ad_data.get('spend', 0),
                        conversions=ad_data.get('conversions', 0),
                        ctr=ad_data.get('ctr', 0),
                        cpc=ad_data.get('cpc', 0),
                        cpm=ad_data.get('cpm', 0),
                        frequency=ad_data.get('frequency', 0),
                        currency="CZK"
                    )
                    db.add(ad_metrics)
                    ad_metrics_stored += 1
                else:
                    # Update existing metrics
                    ad_metrics.impressions = ad_data.get('impressions', 0)
                    ad_metrics.clicks = ad_data.get('clicks', 0)
                    ad_metrics.spend = ad_data.get('spend', 0)
                    ad_metrics.conversions = ad_data.get('conversions', 0)
                    ad_metrics.ctr = ad_data.get('ctr', 0)
                    ad_metrics.cpc = ad_data.get('cpc', 0)
                    ad_metrics.cpm = ad_data.get('cpm', 0)
                    ad_metrics.frequency = ad_data.get('frequency', 0)

            # Commit all changes
            db.commit()

            return {
                "status": "success",
                "message": f"Successfully synced and stored data for {yesterday}",
                "date": str(yesterday),
                "stored_in_database": {
                    "campaigns_stored": campaigns_stored,
                    "ads_stored": ads_stored,
                    "campaign_metrics_stored": campaign_metrics_stored,
                    "ad_metrics_stored": ad_metrics_stored
                },
                "totals": {
                    "campaigns_count": len(campaigns_data),
                    "ads_count": len(ads_data)
                },
                "preview": {
                    "campaigns_data": campaigns_data[:3],  # Show first 3 for preview
                    "ads_data": ads_data[:3]  # Show first 3 for preview
                }
            }

        finally:
            db.close()

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


@app.post("/init-database")
async def init_database():
    """Initialize database tables"""
    try:
        from app.core.database import engine, Base
        from app.models import campaign, ad, client, metrics  # Import all models

        # Create all tables
        Base.metadata.create_all(bind=engine)

        return {
            "status": "success",
            "message": "Database tables created successfully",
            "tables_created": [
                "clients",
                "campaigns",
                "ads",
                "ad_metrics",
                "campaign_metrics",
                "weekly_ad_metrics",
                "monthly_ad_metrics",
                "weekly_campaign_metrics",
                "monthly_campaign_metrics",
                "data_sync_log"
            ]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize database: {str(e)}"
        }


@app.get("/database-status")
async def get_database_status():
    """Check database connection and table status"""
    try:
        from app.core.database import get_session_local
        from app.models.client import Client
        from app.models.campaign import Campaign
        from app.models.ad import Ad
        from app.models.metrics import CampaignMetrics, AdMetrics

        SessionLocal = get_session_local()
        db = SessionLocal()

        try:
            # Test database connection
            clients_count = db.query(Client).count()
            campaigns_count = db.query(Campaign).count()
            ads_count = db.query(Ad).count()
            campaign_metrics_count = db.query(CampaignMetrics).count()
            ad_metrics_count = db.query(AdMetrics).count()

            return {
                "status": "success",
                "message": "Database connection successful",
                "table_counts": {
                    "clients": clients_count,
                    "campaigns": campaigns_count,
                    "ads": ads_count,
                    "campaign_metrics": campaign_metrics_count,
                    "ad_metrics": ad_metrics_count
                },
                "database_ready": True
            }

        finally:
            db.close()

    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
            "database_ready": False
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
