"""
Performance monitoring and benchmarking endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.performance_monitor import PerformanceMonitor

router = APIRouter()


@router.get("/summary")
async def get_performance_summary(
    hours: int = Query(24, description="Hours to look back for performance data"),
    db: Session = Depends(get_db)
):
    """
    Get performance summary for the specified time period
    """
    try:
        monitor = PerformanceMonitor(db)
        summary = monitor.get_performance_summary(hours=hours)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance summary: {str(e)}")


@router.get("/database-analysis")
async def get_database_analysis(
    db: Session = Depends(get_db)
):
    """
    Analyze database performance and get optimization recommendations
    """
    try:
        monitor = PerformanceMonitor(db)
        analysis = monitor.analyze_database_performance()
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing database: {str(e)}")


@router.post("/benchmark/queries")
async def benchmark_queries(
    db: Session = Depends(get_db)
):
    """
    Run query performance benchmarks
    """
    try:
        monitor = PerformanceMonitor(db)
        benchmarks = monitor.benchmark_query_performance()
        return {
            "message": "Query benchmarks completed",
            "benchmarks": benchmarks,
            "recommendations": _get_query_recommendations(benchmarks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running query benchmarks: {str(e)}")


@router.post("/benchmark/aggregation")
async def benchmark_aggregation(
    client_id: str = Query(..., description="Client ID to benchmark"),
    weeks: int = Query(4, description="Number of weeks to test"),
    db: Session = Depends(get_db)
):
    """
    Run aggregation performance benchmarks
    """
    try:
        monitor = PerformanceMonitor(db)
        benchmarks = monitor.benchmark_aggregation_performance(client_id, weeks)
        return {
            "message": "Aggregation benchmarks completed",
            "client_id": client_id,
            "weeks_tested": weeks,
            "benchmarks": benchmarks,
            "recommendations": _get_aggregation_recommendations(benchmarks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running aggregation benchmarks: {str(e)}")


@router.get("/metrics/export")
async def export_performance_metrics(
    format: str = Query("json", description="Export format (json)"),
    db: Session = Depends(get_db)
):
    """
    Export performance metrics data
    """
    try:
        monitor = PerformanceMonitor(db)
        exported_data = monitor.export_metrics(format=format)
        return exported_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")


@router.delete("/metrics/cleanup")
async def cleanup_old_metrics(
    hours: int = Query(24, description="Keep metrics newer than this many hours"),
    db: Session = Depends(get_db)
):
    """
    Clean up old performance metrics
    """
    try:
        monitor = PerformanceMonitor(db)
        monitor.clear_metrics(older_than_hours=hours)
        return {
            "message": "Performance metrics cleaned up",
            "kept_metrics_newer_than_hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up metrics: {str(e)}")


@router.get("/health")
async def get_performance_health(
    db: Session = Depends(get_db)
):
    """
    Get overall performance health status
    """
    try:
        monitor = PerformanceMonitor(db)
        
        # Get recent performance summary
        summary = monitor.get_performance_summary(hours=1)
        
        # Get database analysis
        db_analysis = monitor.analyze_database_performance()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if "performance_stats" in summary:
            stats = summary["performance_stats"]
            
            # Check for performance issues
            if stats.get("avg_duration_seconds", 0) > 5.0:
                health_status = "warning"
                issues.append("Average operation duration is high (>5 seconds)")
            
            if stats.get("max_duration_seconds", 0) > 30.0:
                health_status = "critical"
                issues.append("Maximum operation duration is very high (>30 seconds)")
            
            if stats.get("avg_memory_usage_mb", 0) > 500:
                health_status = "warning"
                issues.append("High memory usage detected (>500MB)")
        
        # Check database size
        if "table_statistics" in db_analysis:
            total_size_mb = sum(
                table.get("size_mb", 0) 
                for table in db_analysis["table_statistics"].values()
                if isinstance(table, dict)
            )
            
            if total_size_mb > 1000:  # 1GB
                if health_status == "healthy":
                    health_status = "warning"
                issues.append(f"Database size is large ({total_size_mb:.1f}MB)")
        
        return {
            "status": health_status,
            "issues": issues,
            "summary": summary,
            "database_analysis": db_analysis,
            "recommendations": _get_health_recommendations(health_status, issues)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking performance health: {str(e)}")


def _get_query_recommendations(benchmarks: dict) -> list:
    """Generate query optimization recommendations"""
    recommendations = []
    
    for query_name, stats in benchmarks.items():
        duration = stats.get("duration_seconds", 0)
        
        if duration > 1.0:
            recommendations.append({
                "query": query_name,
                "issue": f"Slow query ({duration:.2f}s)",
                "recommendation": "Consider adding indexes or optimizing query structure"
            })
        
        if query_name == "complex_join" and duration > 0.5:
            recommendations.append({
                "query": query_name,
                "issue": "Complex join is slow",
                "recommendation": "Consider denormalizing data or using aggregated tables"
            })
    
    return recommendations


def _get_aggregation_recommendations(benchmarks: dict) -> list:
    """Generate aggregation optimization recommendations"""
    recommendations = []
    
    for week_key, stats in benchmarks.items():
        records_per_second = stats.get("records_per_second", 0)
        daily_records = stats.get("daily_records", 0)
        
        if records_per_second < 1000 and daily_records > 10000:
            recommendations.append({
                "week": week_key,
                "issue": f"Low aggregation performance ({records_per_second:.0f} records/sec)",
                "recommendation": "Consider batch processing or pre-aggregation strategies"
            })
    
    return recommendations


def _get_health_recommendations(status: str, issues: list) -> list:
    """Generate health-based recommendations"""
    recommendations = []
    
    if status == "critical":
        recommendations.append({
            "priority": "high",
            "action": "Immediate investigation required",
            "description": "Critical performance issues detected"
        })
    
    if status == "warning":
        recommendations.append({
            "priority": "medium",
            "action": "Monitor and optimize",
            "description": "Performance degradation detected"
        })
    
    for issue in issues:
        if "duration" in issue.lower():
            recommendations.append({
                "priority": "medium",
                "action": "Optimize slow operations",
                "description": "Add caching, optimize queries, or increase resources"
            })
        
        if "memory" in issue.lower():
            recommendations.append({
                "priority": "medium",
                "action": "Optimize memory usage",
                "description": "Review data processing patterns and implement pagination"
            })
        
        if "database size" in issue.lower():
            recommendations.append({
                "priority": "low",
                "action": "Database maintenance",
                "description": "Consider archiving old data or optimizing storage"
            })
    
    return recommendations
