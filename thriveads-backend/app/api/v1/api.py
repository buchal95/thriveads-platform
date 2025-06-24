"""
API v1 router configuration
"""

from fastapi import APIRouter

from .endpoints import campaigns, ads, metrics, clients, sync, performance, analytics
from . import monitoring

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    clients.router,
    prefix="/clients",
    tags=["clients"]
)

api_router.include_router(
    campaigns.router,
    prefix="/campaigns",
    tags=["campaigns"]
)

api_router.include_router(
    ads.router,
    prefix="/ads",
    tags=["ads"]
)

api_router.include_router(
    metrics.router,
    prefix="/metrics",
    tags=["metrics"]
)

api_router.include_router(
    sync.router,
    prefix="/sync",
    tags=["data-sync"]
)

api_router.include_router(
    performance.router,
    prefix="/performance",
    tags=["performance"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["advanced-analytics"]
)

api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)
