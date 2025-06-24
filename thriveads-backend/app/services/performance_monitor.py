"""
Performance monitoring and benchmarking service
"""

import time
import psutil
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from dataclasses import dataclass, asdict

from app.models.metrics import AdMetrics, CampaignMetrics, WeeklyAdMetrics, MonthlyCampaignMetrics

logger = structlog.get_logger()


@dataclass
class PerformanceMetrics:
    """Performance metrics data class"""
    operation: str
    duration_seconds: float
    memory_usage_mb: float
    cpu_percent: float
    records_processed: int
    timestamp: datetime
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class DatabaseQueryMetrics:
    """Database query performance metrics"""
    query_type: str
    table_name: str
    duration_seconds: float
    rows_affected: int
    execution_plan: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class PerformanceMonitor:
    """Service for monitoring and benchmarking performance"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics_history: List[PerformanceMetrics] = []
        self.query_metrics: List[DatabaseQueryMetrics] = []
    
    @contextmanager
    def monitor_operation(self, operation_name: str, records_count: int = 0):
        """Context manager for monitoring operation performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        start_cpu = psutil.cpu_percent()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            duration = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = (start_cpu + end_cpu) / 2
            
            metrics = PerformanceMetrics(
                operation=operation_name,
                duration_seconds=duration,
                memory_usage_mb=memory_usage,
                cpu_percent=cpu_usage,
                records_processed=records_count,
                timestamp=datetime.utcnow()
            )
            
            self.metrics_history.append(metrics)
            
            logger.info(
                "Performance metrics recorded",
                operation=operation_name,
                duration_seconds=duration,
                memory_usage_mb=memory_usage,
                cpu_percent=cpu_usage,
                records_processed=records_count
            )
    
    def benchmark_aggregation_performance(self, client_id: str, weeks_to_test: int = 4) -> Dict[str, Any]:
        """Benchmark aggregation performance with different data sizes"""
        results = {}
        
        # Test weekly aggregation performance
        for week_offset in range(weeks_to_test):
            week_start = datetime.now().date() - timedelta(days=(week_offset + 1) * 7)
            
            with self.monitor_operation(f"weekly_aggregation_week_{week_offset}"):
                # Count records that would be aggregated
                daily_records = self.db.query(func.count(AdMetrics.id)).filter(
                    AdMetrics.date >= week_start,
                    AdMetrics.date <= week_start + timedelta(days=6)
                ).scalar()
                
                # Simulate aggregation query performance
                start_time = time.time()
                aggregation_query = self.db.query(
                    AdMetrics.ad_id,
                    func.sum(AdMetrics.impressions).label('total_impressions'),
                    func.sum(AdMetrics.clicks).label('total_clicks'),
                    func.sum(AdMetrics.spend).label('total_spend'),
                    func.sum(AdMetrics.conversions).label('total_conversions'),
                    func.sum(AdMetrics.conversion_value).label('total_conversion_value')
                ).filter(
                    AdMetrics.date >= week_start,
                    AdMetrics.date <= week_start + timedelta(days=6)
                ).group_by(AdMetrics.ad_id).all()
                
                query_duration = time.time() - start_time
                
                results[f"week_{week_offset}"] = {
                    "daily_records": daily_records,
                    "aggregated_ads": len(aggregation_query),
                    "query_duration": query_duration,
                    "records_per_second": daily_records / query_duration if query_duration > 0 else 0
                }
        
        return results
    
    def benchmark_query_performance(self) -> Dict[str, Any]:
        """Benchmark common query patterns"""
        benchmarks = {}
        
        # Test 1: Top performing ads query
        with self.monitor_operation("top_performing_ads_query"):
            start_time = time.time()
            top_ads_query = self.db.query(AdMetrics).filter(
                AdMetrics.date >= datetime.now().date() - timedelta(days=7)
            ).order_by(AdMetrics.roas.desc()).limit(10).all()
            duration = time.time() - start_time
            
            benchmarks["top_performing_ads"] = {
                "duration_seconds": duration,
                "records_returned": len(top_ads_query),
                "query_type": "SELECT with ORDER BY and LIMIT"
            }
        
        # Test 2: Weekly aggregation query
        with self.monitor_operation("weekly_aggregation_query"):
            start_time = time.time()
            week_start = datetime.now().date() - timedelta(days=7)
            weekly_agg = self.db.query(
                func.sum(AdMetrics.impressions),
                func.sum(AdMetrics.clicks),
                func.sum(AdMetrics.spend),
                func.avg(AdMetrics.roas)
            ).filter(
                AdMetrics.date >= week_start,
                AdMetrics.date <= week_start + timedelta(days=6)
            ).first()
            duration = time.time() - start_time
            
            benchmarks["weekly_aggregation"] = {
                "duration_seconds": duration,
                "query_type": "Aggregation with GROUP BY"
            }
        
        # Test 3: Complex join query
        with self.monitor_operation("complex_join_query"):
            start_time = time.time()
            join_query = self.db.query(AdMetrics, CampaignMetrics).join(
                CampaignMetrics,
                AdMetrics.date == CampaignMetrics.date
            ).filter(
                AdMetrics.date >= datetime.now().date() - timedelta(days=7)
            ).limit(100).all()
            duration = time.time() - start_time
            
            benchmarks["complex_join"] = {
                "duration_seconds": duration,
                "records_returned": len(join_query),
                "query_type": "JOIN with multiple tables"
            }
        
        return benchmarks
    
    def analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database performance and suggest optimizations"""
        analysis = {}
        
        # Check table sizes
        table_stats = {}
        tables = ['ad_metrics', 'campaign_metrics', 'weekly_ad_metrics', 'monthly_campaign_metrics']
        
        for table in tables:
            try:
                count_query = text(f"SELECT COUNT(*) FROM {table}")
                count = self.db.execute(count_query).scalar()
                
                # Get table size (SQLite specific)
                size_query = text(f"SELECT page_count * page_size as size FROM pragma_page_count('{table}'), pragma_page_size")
                try:
                    size = self.db.execute(size_query).scalar() or 0
                except:
                    size = 0
                
                table_stats[table] = {
                    "row_count": count,
                    "size_bytes": size,
                    "size_mb": size / 1024 / 1024 if size else 0
                }
            except Exception as e:
                logger.warning(f"Could not analyze table {table}: {e}")
                table_stats[table] = {"error": str(e)}
        
        analysis["table_statistics"] = table_stats
        
        # Check for missing indexes (basic check)
        index_recommendations = []
        
        # Check if we have indexes on commonly queried columns
        common_queries = [
            ("ad_metrics", "date", "Frequently filtered by date"),
            ("ad_metrics", "ad_id", "Frequently grouped by ad_id"),
            ("ad_metrics", "roas", "Frequently ordered by ROAS"),
            ("campaign_metrics", "date", "Frequently filtered by date"),
            ("campaign_metrics", "campaign_id", "Frequently grouped by campaign_id")
        ]
        
        for table, column, reason in common_queries:
            # This is a simplified check - in production you'd query PRAGMA index_list
            index_recommendations.append({
                "table": table,
                "column": column,
                "reason": reason,
                "suggested_index": f"CREATE INDEX idx_{table}_{column} ON {table}({column})"
            })
        
        analysis["index_recommendations"] = index_recommendations
        
        return analysis
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No performance data available for the specified period"}
        
        # Calculate statistics
        durations = [m.duration_seconds for m in recent_metrics]
        memory_usage = [m.memory_usage_mb for m in recent_metrics]
        cpu_usage = [m.cpu_percent for m in recent_metrics]
        
        summary = {
            "period_hours": hours,
            "total_operations": len(recent_metrics),
            "performance_stats": {
                "avg_duration_seconds": sum(durations) / len(durations),
                "max_duration_seconds": max(durations),
                "min_duration_seconds": min(durations),
                "avg_memory_usage_mb": sum(memory_usage) / len(memory_usage),
                "max_memory_usage_mb": max(memory_usage),
                "avg_cpu_percent": sum(cpu_usage) / len(cpu_usage),
                "max_cpu_percent": max(cpu_usage)
            },
            "operations_by_type": {}
        }
        
        # Group by operation type
        operations = {}
        for metric in recent_metrics:
            if metric.operation not in operations:
                operations[metric.operation] = []
            operations[metric.operation].append(metric)
        
        for op_name, op_metrics in operations.items():
            op_durations = [m.duration_seconds for m in op_metrics]
            summary["operations_by_type"][op_name] = {
                "count": len(op_metrics),
                "avg_duration": sum(op_durations) / len(op_durations),
                "max_duration": max(op_durations),
                "total_records_processed": sum(m.records_processed for m in op_metrics)
            }
        
        return summary
    
    def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """Export performance metrics in specified format"""
        if format == "json":
            return {
                "performance_metrics": [asdict(m) for m in self.metrics_history],
                "query_metrics": [asdict(m) for m in self.query_metrics],
                "export_timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_metrics(self, older_than_hours: int = 24):
        """Clear old metrics to prevent memory buildup"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        self.query_metrics = [
            m for m in self.query_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        logger.info(
            "Performance metrics cleared",
            cutoff_hours=older_than_hours,
            remaining_performance_metrics=len(self.metrics_history),
            remaining_query_metrics=len(self.query_metrics)
        )
