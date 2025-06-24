"""
Tests for PerformanceMonitor
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.services.performance_monitor import PerformanceMonitor, PerformanceMetrics
from app.models.metrics import AdMetrics
from tests.conftest import generate_daily_metrics


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor"""

    @pytest.fixture
    def performance_monitor(self, db_session):
        """Create PerformanceMonitor instance with test database."""
        return PerformanceMonitor(db_session)

    @pytest.fixture
    def setup_performance_data(self, db_session, sample_client, sample_ad):
        """Set up test data for performance testing."""
        db_session.add(sample_client)
        db_session.add(sample_ad)
        
        # Add metrics for multiple weeks
        all_metrics = []
        for week in range(4):
            week_metrics = generate_daily_metrics("ad_123", days=7)
            for metric in week_metrics:
                # Adjust dates for different weeks
                metric.date = metric.date - timedelta(days=week * 7)
                metric.id = f"{metric.ad_id}_{metric.date.strftime('%Y%m%d')}"
                all_metrics.append(metric)
        
        for metric in all_metrics:
            db_session.add(metric)
        
        db_session.commit()
        return all_metrics

    def test_monitor_operation_context_manager(self, performance_monitor):
        """Test the monitor_operation context manager."""
        operation_name = "test_operation"
        
        with performance_monitor.monitor_operation(operation_name, records_count=100):
            # Simulate some work
            time.sleep(0.1)
        
        # Check that metrics were recorded
        assert len(performance_monitor.metrics_history) == 1
        
        metric = performance_monitor.metrics_history[0]
        assert metric.operation == operation_name
        assert metric.records_processed == 100
        assert metric.duration_seconds >= 0.1
        assert isinstance(metric.timestamp, datetime)

    def test_monitor_operation_with_exception(self, performance_monitor):
        """Test that metrics are recorded even when exceptions occur."""
        operation_name = "failing_operation"
        
        with pytest.raises(ValueError):
            with performance_monitor.monitor_operation(operation_name):
                raise ValueError("Test exception")
        
        # Metrics should still be recorded
        assert len(performance_monitor.metrics_history) == 1
        assert performance_monitor.metrics_history[0].operation == operation_name

    def test_benchmark_aggregation_performance(self, performance_monitor, setup_performance_data):
        """Test aggregation performance benchmarking."""
        client_id = "513010266454814"
        weeks_to_test = 2
        
        results = performance_monitor.benchmark_aggregation_performance(client_id, weeks_to_test)
        
        assert len(results) == weeks_to_test
        
        for week_key, week_data in results.items():
            assert "daily_records" in week_data
            assert "aggregated_ads" in week_data
            assert "query_duration" in week_data
            assert "records_per_second" in week_data
            
            assert isinstance(week_data["daily_records"], int)
            assert isinstance(week_data["query_duration"], float)
            assert week_data["query_duration"] >= 0

    def test_benchmark_query_performance(self, performance_monitor, setup_performance_data):
        """Test query performance benchmarking."""
        benchmarks = performance_monitor.benchmark_query_performance()
        
        expected_benchmarks = ["top_performing_ads", "weekly_aggregation", "complex_join"]
        
        for benchmark_name in expected_benchmarks:
            assert benchmark_name in benchmarks
            
            benchmark_data = benchmarks[benchmark_name]
            assert "duration_seconds" in benchmark_data
            assert "query_type" in benchmark_data
            assert isinstance(benchmark_data["duration_seconds"], float)
            assert benchmark_data["duration_seconds"] >= 0

    def test_analyze_database_performance(self, performance_monitor, setup_performance_data):
        """Test database performance analysis."""
        analysis = performance_monitor.analyze_database_performance()
        
        assert "table_statistics" in analysis
        assert "index_recommendations" in analysis
        
        # Check table statistics
        table_stats = analysis["table_statistics"]
        assert "ad_metrics" in table_stats
        
        if "ad_metrics" in table_stats and "error" not in table_stats["ad_metrics"]:
            ad_metrics_stats = table_stats["ad_metrics"]
            assert "row_count" in ad_metrics_stats
            assert "size_bytes" in ad_metrics_stats
            assert "size_mb" in ad_metrics_stats
            assert isinstance(ad_metrics_stats["row_count"], int)

    def test_get_performance_summary_empty(self, performance_monitor):
        """Test performance summary with no data."""
        summary = performance_monitor.get_performance_summary(hours=24)
        
        assert "message" in summary
        assert "No performance data available" in summary["message"]

    def test_get_performance_summary_with_data(self, performance_monitor):
        """Test performance summary with data."""
        # Add some test metrics
        test_metrics = [
            PerformanceMetrics(
                operation="test_op_1",
                duration_seconds=1.0,
                memory_usage_mb=50.0,
                cpu_percent=25.0,
                records_processed=100,
                timestamp=datetime.utcnow()
            ),
            PerformanceMetrics(
                operation="test_op_2",
                duration_seconds=2.0,
                memory_usage_mb=75.0,
                cpu_percent=35.0,
                records_processed=200,
                timestamp=datetime.utcnow()
            ),
            PerformanceMetrics(
                operation="test_op_1",
                duration_seconds=1.5,
                memory_usage_mb=60.0,
                cpu_percent=30.0,
                records_processed=150,
                timestamp=datetime.utcnow()
            )
        ]
        
        performance_monitor.metrics_history.extend(test_metrics)
        
        summary = performance_monitor.get_performance_summary(hours=24)
        
        assert "total_operations" in summary
        assert summary["total_operations"] == 3
        
        assert "performance_stats" in summary
        stats = summary["performance_stats"]
        assert "avg_duration_seconds" in stats
        assert "max_duration_seconds" in stats
        assert "min_duration_seconds" in stats
        
        assert stats["avg_duration_seconds"] == 1.5  # (1.0 + 2.0 + 1.5) / 3
        assert stats["max_duration_seconds"] == 2.0
        assert stats["min_duration_seconds"] == 1.0
        
        assert "operations_by_type" in summary
        ops_by_type = summary["operations_by_type"]
        assert "test_op_1" in ops_by_type
        assert "test_op_2" in ops_by_type
        
        assert ops_by_type["test_op_1"]["count"] == 2
        assert ops_by_type["test_op_2"]["count"] == 1

    def test_export_metrics(self, performance_monitor):
        """Test metrics export functionality."""
        # Add test data
        test_metric = PerformanceMetrics(
            operation="test_export",
            duration_seconds=1.0,
            memory_usage_mb=50.0,
            cpu_percent=25.0,
            records_processed=100,
            timestamp=datetime.utcnow()
        )
        performance_monitor.metrics_history.append(test_metric)
        
        exported = performance_monitor.export_metrics(format="json")
        
        assert "performance_metrics" in exported
        assert "query_metrics" in exported
        assert "export_timestamp" in exported
        
        assert len(exported["performance_metrics"]) == 1
        assert exported["performance_metrics"][0]["operation"] == "test_export"

    def test_export_metrics_invalid_format(self, performance_monitor):
        """Test export with invalid format."""
        with pytest.raises(ValueError):
            performance_monitor.export_metrics(format="invalid")

    def test_clear_metrics(self, performance_monitor):
        """Test clearing old metrics."""
        # Add metrics with different timestamps
        old_metric = PerformanceMetrics(
            operation="old_op",
            duration_seconds=1.0,
            memory_usage_mb=50.0,
            cpu_percent=25.0,
            records_processed=100,
            timestamp=datetime.utcnow() - timedelta(hours=25)  # Older than 24 hours
        )
        
        new_metric = PerformanceMetrics(
            operation="new_op",
            duration_seconds=1.0,
            memory_usage_mb=50.0,
            cpu_percent=25.0,
            records_processed=100,
            timestamp=datetime.utcnow()  # Recent
        )
        
        performance_monitor.metrics_history.extend([old_metric, new_metric])
        
        # Clear metrics older than 24 hours
        performance_monitor.clear_metrics(older_than_hours=24)
        
        # Only new metric should remain
        assert len(performance_monitor.metrics_history) == 1
        assert performance_monitor.metrics_history[0].operation == "new_op"

    @patch('psutil.Process')
    @patch('psutil.cpu_percent')
    def test_monitor_operation_resource_tracking(self, mock_cpu, mock_process, performance_monitor):
        """Test that resource usage is properly tracked."""
        # Mock process memory info
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB in bytes
        mock_process.return_value.memory_info.return_value = mock_memory_info
        
        # Mock CPU usage
        mock_cpu.return_value = 50.0
        
        with performance_monitor.monitor_operation("resource_test"):
            pass
        
        assert len(performance_monitor.metrics_history) == 1
        metric = performance_monitor.metrics_history[0]
        
        # Memory should be tracked (difference might be 0 in this mock)
        assert isinstance(metric.memory_usage_mb, float)
        assert isinstance(metric.cpu_percent, float)

    def test_performance_monitor_initialization(self, db_session):
        """Test PerformanceMonitor initialization."""
        monitor = PerformanceMonitor(db_session)
        assert monitor.db == db_session
        assert monitor.metrics_history == []
        assert monitor.query_metrics == []

    def test_multiple_operations_tracking(self, performance_monitor):
        """Test tracking multiple operations."""
        operations = ["op1", "op2", "op3"]
        
        for op in operations:
            with performance_monitor.monitor_operation(op, records_count=50):
                time.sleep(0.01)  # Small delay
        
        assert len(performance_monitor.metrics_history) == 3
        
        recorded_ops = [m.operation for m in performance_monitor.metrics_history]
        assert set(recorded_ops) == set(operations)
        
        # All should have processed 50 records
        for metric in performance_monitor.metrics_history:
            assert metric.records_processed == 50
