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
        
        # Fetch conversion funnel data from Meta API
        meta_service = MetaService()
        funnel_data = await meta_service.get_conversion_funnel(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )

        # Return structured response that matches frontend expectations
        return {
            "status": "success",
            "period": period,
            "client_id": client_id,
            "funnel_data": {
                "impressions": funnel_data.get("funnel_stages", [{}])[0].get("count", 0) if funnel_data.get("funnel_stages") else 0,
                "clicks": funnel_data.get("funnel_stages", [{}])[1].get("count", 0) if len(funnel_data.get("funnel_stages", [])) > 1 else 0,
                "conversions": funnel_data.get("funnel_stages", [{}])[-1].get("count", 0) if funnel_data.get("funnel_stages") else 0,
                "conversion_rate": funnel_data.get("funnel_stages", [{}])[-1].get("conversion_rate", 0) if funnel_data.get("funnel_stages") else 0,
                "cost_per_conversion": 0  # Calculate if needed
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching funnel data: {str(e)}")


@router.get("/week-on-week")
async def get_week_on_week_comparison(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    complete_weeks: bool = Query(False, description="Use complete weeks only (last week vs week before)"),
    db: Session = Depends(get_db)
):
    """
    Get week-on-week metric comparisons

    Compares current week vs previous week performance, or if complete_weeks=true,
    compares last complete week vs the week before that
    """
    try:
        # Calculate current and previous week ranges
        today = datetime.now().date()
        days_since_monday = today.weekday()

        if complete_weeks:
            # Use last complete week vs week before that
            # Last complete week (Monday to Sunday)
            last_monday = today - timedelta(days=days_since_monday + 7)
            current_week_start = last_monday
            current_week_end = last_monday + timedelta(days=6)  # Sunday

            # Week before last complete week (Monday to Sunday)
            previous_week_start = current_week_start - timedelta(days=7)
            previous_week_end = current_week_start - timedelta(days=1)
        else:
            # Current week (Monday to today or Sunday if week is complete)
            current_week_start = today - timedelta(days=days_since_monday)
            current_week_end = today

            # Previous week (Monday to Sunday)
            previous_week_start = current_week_start - timedelta(days=7)
            previous_week_end = current_week_start - timedelta(days=1)
        
        # Fetch week-on-week comparison data
        meta_service = MetaService()
        comparison_data = await meta_service.get_week_on_week_comparison(
            client_id=client_id,
            current_week_start=current_week_start,
            current_week_end=current_week_end,
            previous_week_start=previous_week_start,
            previous_week_end=previous_week_end
        )

        return comparison_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching week-on-week data: {str(e)}")


@router.get("/daily-breakdown")
async def get_daily_breakdown(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    period: str = Query("last_week", description="Time period: last_week, last_month"),
    db: Session = Depends(get_db)
):
    """
    Get daily breakdown metrics for charts

    Returns daily metrics data for the specified period to power
    daily trend charts in the frontend.
    """
    try:
        # Calculate date range based on period
        end_date = datetime.now().date()

        if period == "last_week":
            # Get last 7 days
            start_date = end_date - timedelta(days=7)
        elif period == "last_month":
            # Get last 30 days
            start_date = end_date - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period. Use 'last_week' or 'last_month'")

        # Fetch daily breakdown data from Meta API
        meta_service = MetaService()
        daily_data = await meta_service.get_daily_breakdown(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )

        # Return structured response that matches frontend expectations
        return {
            "status": "success",
            "period": period,
            "client_id": client_id,
            "daily_data": daily_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching daily breakdown: {str(e)}")


@router.get("/weekly-breakdown")
async def get_weekly_breakdown(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    weeks: int = Query(4, description="Number of weeks to fetch (default: 4, max: 12)"),
    db: Session = Depends(get_db)
):
    """
    Get weekly breakdown metrics for charts

    Returns weekly metrics data to power weekly trend charts in the frontend.
    """
    try:
        # Limit weeks to prevent timeouts
        weeks = min(weeks, 12)

        # Calculate date range (weeks * 7 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks)

        # Fetch weekly breakdown data from Meta API
        meta_service = MetaService()
        weekly_data = await meta_service.get_weekly_breakdown(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            weeks=weeks
        )

        return weekly_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weekly breakdown: {str(e)}")
