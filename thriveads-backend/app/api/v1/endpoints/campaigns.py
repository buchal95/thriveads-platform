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
        
        # TODO: Implement get_top_performing_campaigns in MetaService
        # This would be similar to get_top_performing_ads but aggregated at campaign level
        
        return {
            "message": "Top performing campaigns endpoint - to be implemented",
            "client_id": client_id,
            "period": period,
            "attribution": attribution,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching campaigns: {str(e)}")


@router.get("/{campaign_id}")
async def get_campaign_details(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific campaign"""
    # TODO: Implement campaign details fetching
    return {
        "message": "Campaign details endpoint - to be implemented",
        "campaign_id": campaign_id
    }
