"""
Ads performance endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.schemas.ad import Ad, AdPerformance
from app.services.meta_service import MetaService
from app.services.ad_service import AdService
from app.services.database_service import DatabaseService

router = APIRouter()


@router.get("/2025-data")
async def get_2025_ads_data(
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    days: int = Query(30, description="Number of days to fetch (default: 30, max: 90)"),
    db: Session = Depends(get_db)
):
    """
    Get recent ads data for 2025 for Mimilátky CZ
    Optimized for Railway Pro - fetches last N days instead of full year
    """
    try:
        meta_service = MetaService()

        # Limit days to prevent timeouts (max 90 days)
        days = min(days, 90)

        # Get recent data (last N days from today)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Fetch ads data from Meta API for 2025 (only ads with spend > 0)
        ads_2025 = await meta_service.get_ads_with_metrics(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            fields=[
                'ad_id', 'ad_name', 'status', 'campaign_id', 'campaign_name',
                'spend', 'impressions', 'clicks', 'conversions', 'link_clicks',
                'cost_per_result', 'cpm', 'cpc', 'ctr', 'frequency',
                'video_views', 'video_view_rate', 'reach'
            ],
            active_only=True  # Only ads with spend > 0 for better performance
        )

        return {
            "status": "success",
            "period": f"Last {days} days",
            "client_id": client_id,
            "date_range": {
                "start_date": str(start_date),
                "end_date": str(end_date)
            },
            "total_ads": len(ads_2025),
            "ads": ads_2025,
            "note": "Optimized for Railway Pro - use smaller date ranges for better performance"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching 2025 ads data: {str(e)}")


@router.get("/top-performing")
async def get_top_performing_ads(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    period: str = Query("last_week", description="Time period: last_week, last_month"),
    attribution: str = Query("default", description="Attribution model: default, 7d_click"),
    limit: int = Query(10, description="Number of top ads to return"),
    db: Session = Depends(get_db)
):
    """
    Get top performing ads for a client
    
    Returns the best performing ads based on ROAS (Return on Ad Spend)
    with clickable Facebook feed URLs and performance metrics.
    """
    try:
        db_service = DatabaseService(db)

        # Calculate date range
        end_date = datetime.now().date()
        if period == "last_week":
            # Use last 7 days (same as 2025-data endpoint for consistency)
            start_date = end_date - timedelta(days=7)
        elif period == "last_month":
            # Use last 30 days
            start_date = end_date - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")

        # Get top performing ads from database
        top_ads = db_service.get_top_performing_ads(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution=attribution,
            limit=limit
        )

        # Return structured response that matches frontend expectations
        return {
            "status": "success",
            "period": period,
            "client_id": client_id,
            "attribution": attribution,
            "total_ads": len(top_ads),
            "ads": top_ads
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ads: {str(e)}")


@router.get("/{ad_id}", response_model=Ad)
async def get_ad_details(
    ad_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific ad"""
    ad_service = AdService(db)
    ad = await ad_service.get_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    return ad


@router.get("/{ad_id}/performance")
async def get_ad_performance_history(
    ad_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Get performance history for a specific ad"""
    try:
        meta_service = MetaService()
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        performance_data = await meta_service.get_ad_performance_history(
            ad_id=ad_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return performance_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ad performance: {str(e)}")
