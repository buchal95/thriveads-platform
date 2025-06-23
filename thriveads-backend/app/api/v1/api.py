"""
API v1 router configuration
"""

from fastapi import APIRouter

from .endpoints import campaigns, ads, metrics, clients

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
