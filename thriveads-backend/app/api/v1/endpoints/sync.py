"""
Data synchronization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date, timedelta
import asyncio

from app.core.database import get_db
from app.services.data_sync_service import DataSyncService
from app.services.aggregation_service import AggregationService
from app.services.backfill_service import BackfillService

router = APIRouter()

# Global backfill progress tracker
_backfill_progress = None


@router.post("/daily")
async def sync_daily_data(
    background_tasks: BackgroundTasks,
    client_id: str = Query(..., description="Client Meta ad account ID"),
    sync_date: Optional[date] = Query(None, description="Date to sync (defaults to yesterday)"),
    db: Session = Depends(get_db)
):
    """
    Sync daily data for a specific client and date
    
    This endpoint triggers a background task to sync data from Meta API
    """
    try:
        if not sync_date:
            # Default to yesterday
            sync_date = (datetime.now() - timedelta(days=1)).date()
        
        # Start background sync
        data_sync_service = DataSyncService(db)
        background_tasks.add_task(
            data_sync_service.sync_daily_data,
            client_id,
            sync_date
        )
        
        return {
            "message": "Daily data sync started",
            "client_id": client_id,
            "sync_date": sync_date.isoformat(),
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting daily sync: {str(e)}")


@router.post("/historical")
async def sync_historical_data(
    background_tasks: BackgroundTasks,
    client_id: str = Query(..., description="Client Meta ad account ID"),
    start_date: date = Query(..., description="Start date for historical sync"),
    end_date: date = Query(..., description="End date for historical sync"),
    db: Session = Depends(get_db)
):
    """
    Sync historical data for a date range
    
    This endpoint triggers a background task to sync historical data from Meta API
    """
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        if (end_date - start_date).days > 90:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
        
        # Start background sync
        data_sync_service = DataSyncService(db)
        background_tasks.add_task(
            data_sync_service.sync_historical_data,
            client_id,
            start_date,
            end_date
        )
        
        return {
            "message": "Historical data sync started",
            "client_id": client_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": (end_date - start_date).days + 1,
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting historical sync: {str(e)}")


@router.post("/aggregate/weekly")
async def aggregate_weekly_data(
    background_tasks: BackgroundTasks,
    client_id: str = Query(..., description="Client Meta ad account ID"),
    week_start: date = Query(..., description="Monday of the week to aggregate"),
    db: Session = Depends(get_db)
):
    """
    Aggregate daily data into weekly summaries
    
    This endpoint triggers weekly data aggregation for performance optimization
    """
    try:
        # Validate that week_start is a Monday
        if week_start.weekday() != 0:
            raise HTTPException(status_code=400, detail="Week start must be a Monday")
        
        # Start background aggregation
        aggregation_service = AggregationService(db)
        background_tasks.add_task(
            aggregation_service.aggregate_weekly_metrics,
            client_id,
            week_start
        )
        
        return {
            "message": "Weekly aggregation started",
            "client_id": client_id,
            "week_start": week_start.isoformat(),
            "week_end": (week_start + timedelta(days=6)).isoformat(),
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting weekly aggregation: {str(e)}")


@router.post("/aggregate/monthly")
async def aggregate_monthly_data(
    background_tasks: BackgroundTasks,
    client_id: str = Query(..., description="Client Meta ad account ID"),
    year: int = Query(..., description="Year to aggregate"),
    month: int = Query(..., description="Month to aggregate (1-12)"),
    db: Session = Depends(get_db)
):
    """
    Aggregate daily data into monthly summaries
    
    This endpoint triggers monthly data aggregation for performance optimization
    """
    try:
        # Validate month
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        # Start background aggregation
        aggregation_service = AggregationService(db)
        background_tasks.add_task(
            aggregation_service.aggregate_monthly_metrics,
            client_id,
            year,
            month
        )
        
        return {
            "message": "Monthly aggregation started",
            "client_id": client_id,
            "year": year,
            "month": month,
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting monthly aggregation: {str(e)}")


@router.get("/status")
async def get_sync_status(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    limit: int = Query(10, description="Number of recent sync logs to return"),
    db: Session = Depends(get_db)
):
    """
    Get synchronization status and recent sync logs
    """
    try:
        from app.models.metrics import DataSyncLog
        
        # Get recent sync logs
        recent_syncs = (
            db.query(DataSyncLog)
            .filter(DataSyncLog.client_id == client_id)
            .order_by(DataSyncLog.created_at.desc())
            .limit(limit)
            .all()
        )
        
        sync_logs = []
        for sync in recent_syncs:
            sync_logs.append({
                "id": sync.id,
                "sync_type": sync.sync_type,
                "sync_date": sync.sync_date.isoformat(),
                "status": sync.status,
                "records_processed": sync.records_processed,
                "error_message": sync.error_message,
                "started_at": sync.started_at.isoformat() if sync.started_at else None,
                "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                "duration_seconds": (
                    (sync.completed_at - sync.started_at).total_seconds()
                    if sync.started_at and sync.completed_at
                    else None
                )
            })
        
        # Get summary statistics
        from sqlalchemy import func
        
        total_syncs = db.query(func.count(DataSyncLog.id)).filter(
            DataSyncLog.client_id == client_id
        ).scalar()
        
        successful_syncs = db.query(func.count(DataSyncLog.id)).filter(
            DataSyncLog.client_id == client_id,
            DataSyncLog.status == "completed"
        ).scalar()
        
        failed_syncs = db.query(func.count(DataSyncLog.id)).filter(
            DataSyncLog.client_id == client_id,
            DataSyncLog.status == "failed"
        ).scalar()
        
        return {
            "client_id": client_id,
            "summary": {
                "total_syncs": total_syncs,
                "successful_syncs": successful_syncs,
                "failed_syncs": failed_syncs,
                "success_rate": (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            },
            "recent_syncs": sync_logs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sync status: {str(e)}")


@router.delete("/logs")
async def cleanup_old_logs(
    client_id: str = Query(..., description="Client Meta ad account ID"),
    days_to_keep: int = Query(30, description="Number of days of logs to keep"),
    db: Session = Depends(get_db)
):
    """
    Clean up old sync logs to manage database size
    """
    try:
        from app.models.metrics import DataSyncLog
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        deleted_count = (
            db.query(DataSyncLog)
            .filter(
                DataSyncLog.client_id == client_id,
                DataSyncLog.created_at < cutoff_date
            )
            .delete()
        )
        
        db.commit()
        
        return {
            "message": "Old sync logs cleaned up",
            "client_id": client_id,
            "deleted_logs": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up logs: {str(e)}")


# Smart Backfill Endpoints for Day-by-Day Historical Data

@router.post("/backfill/2025")
async def start_2025_backfill(
    background_tasks: BackgroundTasks,
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    force_refresh: bool = Query(False, description="Force refresh existing data"),
    delay_seconds: float = Query(1.0, description="Delay between days (seconds)"),
    db: Session = Depends(get_db)
):
    """
    Start systematic backfill of ALL 2025 data, day by day

    This process will:
    - Fetch data one day at a time (fast and reliable)
    - Store with daily granularity for advanced analytics
    - Skip days that already have data (unless force_refresh=True)
    - Run in background and can take 24+ hours to complete
    - Provide real-time progress updates
    """
    global _backfill_progress

    try:
        # Check if backfill is already running
        if _backfill_progress and _backfill_progress.get_status()["status"] == "running":
            return {
                "message": "Backfill already in progress",
                "status": "already_running",
                "progress": _backfill_progress.get_status()
            }

        # Define 2025 date range (up to yesterday)
        start_date = date(2025, 1, 1)
        yesterday = date.today() - timedelta(days=1)
        end_date = min(date(2025, 12, 31), yesterday)  # Don't go beyond yesterday

        total_days = (end_date - start_date).days + 1

        # Start background backfill
        backfill_service = BackfillService(client_id)

        async def run_backfill():
            global _backfill_progress
            _backfill_progress = await backfill_service.backfill_date_range(
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh,
                delay_between_days=delay_seconds
            )

        background_tasks.add_task(run_backfill)

        return {
            "message": "2025 backfill started successfully",
            "status": "started",
            "client_id": client_id,
            "date_range": {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "total_days": total_days
            },
            "settings": {
                "force_refresh": force_refresh,
                "delay_seconds": delay_seconds
            },
            "estimated_duration": f"{total_days * delay_seconds / 3600:.1f} hours",
            "note": "Use GET /api/v1/sync/backfill/status to monitor progress"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting backfill: {str(e)}")


@router.get("/backfill/status")
async def get_backfill_status():
    """
    Get real-time status of the backfill process
    """
    global _backfill_progress

    if not _backfill_progress:
        return {
            "status": "not_started",
            "message": "No backfill process has been started yet"
        }

    return _backfill_progress.get_status()


@router.post("/backfill/custom")
async def start_custom_backfill(
    background_tasks: BackgroundTasks,
    start_date: date = Query(..., description="Start date for backfill"),
    end_date: date = Query(..., description="End date for backfill"),
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    force_refresh: bool = Query(False, description="Force refresh existing data"),
    delay_seconds: float = Query(1.0, description="Delay between days (seconds)"),
    db: Session = Depends(get_db)
):
    """
    Start custom date range backfill, day by day

    For smaller date ranges or specific periods
    """
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before end date")

        total_days = (end_date - start_date).days + 1
        if total_days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")

        # Start background backfill
        backfill_service = BackfillService(client_id)

        async def run_custom_backfill():
            await backfill_service.backfill_date_range(
                start_date=start_date,
                end_date=end_date,
                force_refresh=force_refresh,
                delay_between_days=delay_seconds
            )

        background_tasks.add_task(run_custom_backfill)

        return {
            "message": "Custom backfill started successfully",
            "status": "started",
            "client_id": client_id,
            "date_range": {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "total_days": total_days
            },
            "settings": {
                "force_refresh": force_refresh,
                "delay_seconds": delay_seconds
            },
            "estimated_duration": f"{total_days * delay_seconds / 3600:.1f} hours"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting custom backfill: {str(e)}")


@router.post("/backfill/single-day")
async def backfill_single_day(
    target_date: date = Query(..., description="Date to backfill"),
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    force_refresh: bool = Query(False, description="Force refresh existing data"),
    db: Session = Depends(get_db)
):
    """
    Backfill data for a single day (for testing or fixing specific dates)
    """
    try:
        backfill_service = BackfillService(client_id)
        result = await backfill_service.backfill_single_day(db, target_date, force_refresh)

        return {
            "message": f"Single day backfill completed for {target_date}",
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error backfilling single day: {str(e)}")


@router.post("/populate-database")
async def populate_database_with_working_data(
    client_id: str = Query("513010266454814", description="Client Meta ad account ID"),
    days: int = Query(7, description="Number of recent days to populate"),
    db: Session = Depends(get_db)
):
    """
    Populate database using the working Meta API methods

    This uses the same API calls that work in /campaigns/2025-data endpoint
    """
    try:
        from app.services.meta_service import MetaService
        from app.models.campaign import Campaign
        from app.models.client import Client
        from datetime import datetime, timedelta

        meta_service = MetaService()

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Ensure client exists
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            client = Client(
                id=client_id,
                name="Mimilátky - Notie s.r.o.",
                currency="CZK",
                meta_ad_account_id=client_id
            )
            db.add(client)
            db.commit()

        # Get campaigns data using the working method
        campaigns_data = await meta_service.get_campaigns_with_metrics(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            active_only=True
        )

        campaigns_stored = 0
        for campaign_data in campaigns_data:
            # Store campaign in database
            existing_campaign = db.query(Campaign).filter(Campaign.id == campaign_data['campaign_id']).first()

            if not existing_campaign:
                new_campaign = Campaign(
                    id=campaign_data['campaign_id'],
                    name=campaign_data['campaign_name'],
                    status=campaign_data.get('status', 'ACTIVE'),
                    objective=campaign_data.get('objective', 'CONVERSIONS'),
                    client_id=client_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_campaign)
                campaigns_stored += 1

        db.commit()

        return {
            "message": "Database populated successfully using working Meta API methods",
            "client_id": client_id,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "campaigns_found": len(campaigns_data),
            "campaigns_stored": campaigns_stored,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating database: {str(e)}")
