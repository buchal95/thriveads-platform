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

router = APIRouter()


@router.get("/2025-data")
async def get_2025_ads_data(
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    db: Session = Depends(get_db)
):
    """
    Get all ads data for 2025 for Mimilátky CZ
    """
    try:
        meta_service = MetaService()

        # Get 2025 data (January 1 to December 31, 2025)
        start_date = datetime(2025, 1, 1).date()
        end_date = datetime(2025, 12, 31).date()

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
            "period": "2025",
            "client_id": client_id,
            "date_range": {
                "start_date": str(start_date),
                "end_date": str(end_date)
            },
            "total_ads": len(ads_2025),
            "ads": ads_2025
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching 2025 ads data: {str(e)}")


@router.get("/top-performing", response_model=List[AdPerformance])
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
        meta_service = MetaService()
        ad_service = AdService(db)
        
        # Calculate date range
        end_date = datetime.now().date()
        if period == "last_week":
            # Get last complete week (Monday to Sunday)
            days_since_monday = end_date.weekday()
            last_monday = end_date - timedelta(days=days_since_monday + 7)
            start_date = last_monday
            end_date = last_monday + timedelta(days=6)
        elif period == "last_month":
            # Get last complete month
            first_day_current_month = end_date.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            start_date = last_day_previous_month.replace(day=1)
            end_date = last_day_previous_month
        else:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        # Fetch top performing ads from Meta API
        top_ads = await meta_service.get_top_performing_ads(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution=attribution,
            limit=limit
        )
        
        return top_ads
        
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
