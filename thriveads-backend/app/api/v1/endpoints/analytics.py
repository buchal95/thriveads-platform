"""
Advanced analytics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.services.advanced_analytics_service import AdvancedAnalyticsService
from app.services.data_validation_service import DataValidationService
from app.services.data_retention_service import DataRetentionService

router = APIRouter()


@router.get("/trend-analysis")
async def get_trend_analysis(
    client_id: str = Query(..., description="Client ID"),
    metric: str = Query("spend", description="Metric to analyze (spend, roas, conversions, etc.)"),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get trend analysis for a specific metric over time
    """
    try:
        analytics_service = AdvancedAnalyticsService(db)
        result = analytics_service.calculate_trend_analysis(client_id, metric, days)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating trend analysis: {str(e)}")


@router.get("/seasonal-patterns")
async def get_seasonal_patterns(
    client_id: str = Query(..., description="Client ID"),
    metric: str = Query("spend", description="Metric to analyze"),
    months: int = Query(12, description="Number of months to analyze"),
    db: Session = Depends(get_db)
):
    """
    Analyze seasonal patterns in the data
    """
    try:
        analytics_service = AdvancedAnalyticsService(db)
        result = analytics_service.calculate_seasonal_patterns(client_id, metric, months)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing seasonal patterns: {str(e)}")


@router.get("/attribution-comparison")
async def get_attribution_comparison(
    client_id: str = Query(..., description="Client ID"),
    start_date: date = Query(..., description="Start date for comparison"),
    end_date: date = Query(..., description="End date for comparison"),
    db: Session = Depends(get_db)
):
    """
    Compare performance across different attribution models
    """
    try:
        analytics_service = AdvancedAnalyticsService(db)
        result = analytics_service.calculate_attribution_comparison(client_id, start_date, end_date)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing attributions: {str(e)}")


@router.get("/efficiency-metrics")
async def get_efficiency_metrics(
    client_id: str = Query(..., description="Client ID"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: Session = Depends(get_db)
):
    """
    Calculate advanced efficiency metrics
    """
    try:
        analytics_service = AdvancedAnalyticsService(db)
        result = analytics_service.calculate_efficiency_metrics(client_id, start_date, end_date)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating efficiency metrics: {str(e)}")


@router.get("/cohort-analysis")
async def get_cohort_analysis(
    client_id: str = Query(..., description="Client ID"),
    start_date: date = Query(..., description="Start date for cohort analysis"),
    cohort_type: str = Query("weekly", description="Cohort type (weekly or monthly)"),
    db: Session = Depends(get_db)
):
    """
    Calculate cohort analysis for ad performance over time
    """
    try:
        if cohort_type not in ['weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="Cohort type must be 'weekly' or 'monthly'")
        
        analytics_service = AdvancedAnalyticsService(db)
        result = analytics_service.calculate_cohort_analysis(client_id, start_date, cohort_type)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating cohort analysis: {str(e)}")


@router.get("/data-quality")
async def get_data_quality(
    client_id: str = Query(..., description="Client ID"),
    days_back: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get data quality score and analysis
    """
    try:
        validation_service = DataValidationService(db)
        result = validation_service.get_data_quality_score(client_id, days_back)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing data quality: {str(e)}")


@router.get("/data-anomalies")
async def get_data_anomalies(
    client_id: str = Query(..., description="Client ID"),
    days_back: int = Query(30, description="Days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Detect anomalies in recent data
    """
    try:
        validation_service = DataValidationService(db)
        result = validation_service.detect_data_anomalies(client_id, days_back)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting anomalies: {str(e)}")


@router.get("/aggregation-validation")
async def validate_aggregation(
    client_id: str = Query(..., description="Client ID"),
    week_start: date = Query(..., description="Week start date (Monday)"),
    db: Session = Depends(get_db)
):
    """
    Validate that weekly aggregations match sum of daily data
    """
    try:
        # Validate that week_start is a Monday
        if week_start.weekday() != 0:
            raise HTTPException(status_code=400, detail="Week start must be a Monday")
        
        validation_service = DataValidationService(db)
        result = validation_service.validate_aggregation_consistency(client_id, week_start)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating aggregation: {str(e)}")


@router.get("/data-usage")
async def get_data_usage(
    client_id: Optional[str] = Query(None, description="Client ID (optional)"),
    db: Session = Depends(get_db)
):
    """
    Analyze current data usage and storage requirements
    """
    try:
        retention_service = DataRetentionService(db)
        result = retention_service.analyze_data_usage(client_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing data usage: {str(e)}")


@router.get("/retention-policy")
async def get_retention_policy(
    db: Session = Depends(get_db)
):
    """
    Get the current data retention policy
    """
    try:
        retention_service = DataRetentionService(db)
        result = retention_service.get_retention_policy()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting retention policy: {str(e)}")


@router.get("/archival-candidates")
async def get_archival_candidates(
    db: Session = Depends(get_db)
):
    """
    Identify data that should be archived based on retention policy
    """
    try:
        retention_service = DataRetentionService(db)
        result = retention_service.identify_archival_candidates()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying archival candidates: {str(e)}")


@router.post("/archive-data")
async def archive_data(
    data_type: str = Query(..., description="Type of data to archive"),
    dry_run: bool = Query(True, description="If true, only simulate archival"),
    db: Session = Depends(get_db)
):
    """
    Archive old data based on retention policy
    """
    try:
        retention_service = DataRetentionService(db)
        result = retention_service.archive_old_data(data_type, dry_run)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error archiving data: {str(e)}")


@router.delete("/cleanup-old-data")
async def cleanup_old_data(
    data_type: str = Query(..., description="Type of data to clean up"),
    dry_run: bool = Query(True, description="If true, only simulate cleanup"),
    db: Session = Depends(get_db)
):
    """
    Clean up (delete) very old data that exceeds retention policy
    """
    try:
        retention_service = DataRetentionService(db)
        result = retention_service.cleanup_old_data(data_type, dry_run)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up data: {str(e)}")


@router.get("/aggregation-status")
async def get_aggregation_status(
    client_id: str = Query(..., description="Client ID"),
    days_back: int = Query(30, description="Days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get status of aggregations for the past N days
    """
    try:
        from app.services.aggregation_service import AggregationService
        aggregation_service = AggregationService(db)
        result = aggregation_service.get_aggregation_status(client_id, days_back)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting aggregation status: {str(e)}")


@router.post("/validate-and-aggregate")
async def validate_and_aggregate_weekly(
    client_id: str = Query(..., description="Client ID"),
    week_start: date = Query(..., description="Week start date (Monday)"),
    db: Session = Depends(get_db)
):
    """
    Validate data quality and then perform weekly aggregation
    """
    try:
        # Validate that week_start is a Monday
        if week_start.weekday() != 0:
            raise HTTPException(status_code=400, detail="Week start must be a Monday")
        
        from app.services.aggregation_service import AggregationService
        aggregation_service = AggregationService(db)
        result = await aggregation_service.validate_and_aggregate_weekly(client_id, week_start)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in validated aggregation: {str(e)}")
