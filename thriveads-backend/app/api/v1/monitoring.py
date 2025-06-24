"""
Monitoring and health check endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import time
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.config import settings
from app.core.monitoring import get_monitor
from app.services.meta_service import MetaService

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint"""
    monitor = get_monitor()
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database health check
    try:
        db_start = time.time()
        result = db.execute(text("SELECT 1 as test, NOW() as db_time"))
        row = result.fetchone()
        db_duration = time.time() - db_start
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_duration * 1000, 2),
            "server_time": str(row.db_time) if row else None
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Meta API configuration check
    if settings.META_ACCESS_TOKEN:
        health_status["checks"]["meta_api"] = {
            "status": "configured",
            "has_token": True,
            "api_version": settings.META_API_VERSION
        }
    else:
        health_status["checks"]["meta_api"] = {
            "status": "not_configured",
            "has_token": False
        }
    
    # System metrics
    try:
        system_metrics = monitor.get_system_metrics()
        health_status["checks"]["system"] = {
            "status": "healthy",
            **system_metrics
        }
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Application metrics
    app_metrics = monitor.get_application_metrics()
    health_status["checks"]["application"] = {
        "status": "healthy",
        **app_metrics
    }
    
    # Overall response time
    total_duration = time.time() - start_time
    health_status["response_time_ms"] = round(total_duration * 1000, 2)
    
    return health_status


@router.get("/metrics")
async def get_metrics():
    """Get detailed application metrics"""
    monitor = get_monitor()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": monitor.get_system_metrics(),
        "application": monitor.get_application_metrics(),
        "environment": settings.ENVIRONMENT
    }


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Simple status endpoint for load balancers"""
    try:
        # Quick database ping
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/meta-api/test")
async def test_meta_api():
    """Test Meta API connectivity"""
    if not settings.META_ACCESS_TOKEN:
        raise HTTPException(
            status_code=400, 
            detail="Meta API token not configured"
        )
    
    try:
        meta_service = MetaService()
        start_time = time.time()
        
        # Test API call - get account info
        account_info = meta_service.get_account_info(settings.DEFAULT_CLIENT_ID)
        duration = time.time() - start_time
        
        return {
            "status": "success",
            "response_time_ms": round(duration * 1000, 2),
            "account_id": account_info.get("id"),
            "account_name": account_info.get("name"),
            "currency": account_info.get("currency"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/database/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    try:
        stats = {}
        
        # Get table row counts
        tables = ["campaigns", "ads", "ad_metrics", "campaign_metrics"]
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                row = result.fetchone()
                stats[f"{table}_count"] = row.count if row else 0
            except Exception:
                stats[f"{table}_count"] = "error"
        
        # Get recent data info
        try:
            result = db.execute(text("""
                SELECT 
                    MAX(date) as latest_date,
                    MIN(date) as earliest_date,
                    COUNT(DISTINCT date) as unique_dates
                FROM ad_metrics
            """))
            row = result.fetchone()
            if row:
                stats["data_range"] = {
                    "latest_date": str(row.latest_date) if row.latest_date else None,
                    "earliest_date": str(row.earliest_date) if row.earliest_date else None,
                    "unique_dates": row.unique_dates
                }
        except Exception:
            stats["data_range"] = "error"
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database stats: {str(e)}"
        )


@router.get("/performance/summary")
async def get_performance_summary():
    """Get performance summary for monitoring dashboard"""
    monitor = get_monitor()
    
    # Get system metrics
    system_metrics = monitor.get_system_metrics()
    app_metrics = monitor.get_application_metrics()
    
    # Calculate health score based on various factors
    health_score = 100
    
    # Deduct points for high resource usage
    if system_metrics.get("memory", {}).get("percent_used", 0) > 80:
        health_score -= 20
    if system_metrics.get("cpu", {}).get("percent_used", 0) > 80:
        health_score -= 20
    if app_metrics.get("error_rate", 0) > 5:
        health_score -= 30
    
    health_score = max(0, health_score)
    
    return {
        "health_score": health_score,
        "status": "healthy" if health_score > 70 else "warning" if health_score > 40 else "critical",
        "uptime_hours": round(app_metrics.get("uptime_seconds", 0) / 3600, 2),
        "total_requests": app_metrics.get("request_count", 0),
        "error_rate": app_metrics.get("error_rate", 0),
        "memory_usage": system_metrics.get("memory", {}).get("percent_used", 0),
        "cpu_usage": system_metrics.get("cpu", {}).get("percent_used", 0),
        "timestamp": datetime.utcnow().isoformat()
    }
