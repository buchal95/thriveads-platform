"""
Campaign endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.meta_service import MetaService

router = APIRouter()


@router.get("/2025-data")
async def get_2025_campaigns_data(
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    db: Session = Depends(get_db)
):
    """
    Get all campaigns data for 2025 for Mimilátky CZ
    """
    try:
        meta_service = MetaService()

        # Get 2025 data (January 1 to December 31, 2025)
        start_date = datetime(2025, 1, 1).date()
        end_date = datetime(2025, 12, 31).date()

        # Fetch campaigns data from Meta API for 2025 (only campaigns with spend > 0)
        campaigns_2025 = await meta_service.get_campaigns_with_metrics(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            fields=[
                'campaign_id', 'campaign_name', 'status', 'objective',
                'spend', 'impressions', 'clicks', 'conversions',
                'cost_per_result', 'cpm', 'cpc', 'ctr', 'frequency'
            ],
            active_only=True  # Only campaigns with spend > 0 for better performance
        )

        return {
            "status": "success",
            "period": "2025",
            "client_id": client_id,
            "date_range": {
                "start_date": str(start_date),
                "end_date": str(end_date)
            },
            "total_campaigns": len(campaigns_2025),
            "campaigns": campaigns_2025
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching 2025 campaigns data: {str(e)}")


@router.get("/top-performing")
async def get_top_performing_campaigns(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    period: str = Query("last_week", description="Time period: last_week, last_month"),
    attribution: str = Query("default", description="Attribution model: default, 7d_click"),
    limit: int = Query(10, description="Number of top campaigns to return"),
    db: Session = Depends(get_db)
):
    """
    Get top performing campaigns for a client
    
    Similar to ads endpoint but aggregated at campaign level
    """
    try:
        meta_service = MetaService()
        
        # Calculate date range
        end_date = datetime.now().date()
        if period == "last_week":
            days_since_monday = end_date.weekday()
            last_monday = end_date - timedelta(days=days_since_monday + 7)
            start_date = last_monday
            end_date = last_monday + timedelta(days=6)
        elif period == "last_month":
            first_day_current_month = end_date.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            start_date = last_day_previous_month.replace(day=1)
            end_date = last_day_previous_month
        else:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        # Fetch top performing campaigns from Meta API
        top_campaigns = await meta_service.get_top_performing_campaigns(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution=attribution,
            limit=limit
        )

        return top_campaigns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching campaigns: {str(e)}")


@router.get("/{campaign_id}")
async def get_campaign_details(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific campaign"""
    try:
        meta_service = MetaService()

        # Fetch campaign details from Meta API
        campaign_details = await meta_service.get_campaign_details(campaign_id)

        return campaign_details

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching campaign details: {str(e)}")
