"""
Metrics and analytics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.meta_service import MetaService

router = APIRouter()


@router.get("/funnel")
async def get_conversion_funnel(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    period: str = Query("last_week", description="Time period: last_week, last_month"),
    db: Session = Depends(get_db)
):
    """
    Get conversion funnel data for visualization
    
    Returns funnel stages with conversion rates:
    - Impressions
    - Clicks
    - Landing Page Views
    - Add to Cart
    - Purchase
    """
    try:
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
        
        # TODO: Implement funnel data fetching from Meta API
        # This would aggregate various action types to build the funnel
        
        return {
            "message": "Conversion funnel endpoint - to be implemented",
            "client_id": client_id,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "funnel_stages": [
                {"stage": "Impressions", "count": 0, "conversion_rate": 100.0},
                {"stage": "Clicks", "count": 0, "conversion_rate": 0.0},
                {"stage": "Landing Page Views", "count": 0, "conversion_rate": 0.0},
                {"stage": "Add to Cart", "count": 0, "conversion_rate": 0.0},
                {"stage": "Purchase", "count": 0, "conversion_rate": 0.0}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching funnel data: {str(e)}")


@router.get("/week-on-week")
async def get_week_on_week_comparison(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    db: Session = Depends(get_db)
):
    """
    Get week-on-week metric comparisons
    
    Compares current week vs previous week performance
    """
    try:
        # Calculate current and previous week ranges
        today = datetime.now().date()
        days_since_monday = today.weekday()
        
        # Current week (Monday to today or Sunday if week is complete)
        current_week_start = today - timedelta(days=days_since_monday)
        current_week_end = today
        
        # Previous week (Monday to Sunday)
        previous_week_start = current_week_start - timedelta(days=7)
        previous_week_end = current_week_start - timedelta(days=1)
        
        # TODO: Implement week-on-week comparison logic
        # This would fetch metrics for both periods and calculate percentage changes
        
        return {
            "message": "Week-on-week comparison endpoint - to be implemented",
            "client_id": client_id,
            "current_week": {
                "start_date": current_week_start.isoformat(),
                "end_date": current_week_end.isoformat()
            },
            "previous_week": {
                "start_date": previous_week_start.isoformat(),
                "end_date": previous_week_end.isoformat()
            },
            "metrics_comparison": {
                "spend_change": 0.0,
                "roas_change": 0.0,
                "conversions_change": 0.0,
                "ctr_change": 0.0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching week-on-week data: {str(e)}")
