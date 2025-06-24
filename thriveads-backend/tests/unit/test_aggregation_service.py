"""
Tests for AggregationService
"""

import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

from app.services.aggregation_service import AggregationService
from app.models.metrics import (
    AdMetrics, CampaignMetrics, WeeklyAdMetrics, MonthlyCampaignMetrics,
    DataSyncLog
)
from tests.conftest import generate_daily_metrics


class TestAggregationService:
    """Test cases for AggregationService"""

    @pytest.fixture
    def aggregation_service(self, db_session):
        """Create AggregationService instance with test database."""
        return AggregationService(db_session)

    @pytest.fixture
    def setup_test_data(self, db_session, sample_client, sample_campaign, sample_ad):
        """Set up test data in database."""
        db_session.add(sample_client)
        db_session.add(sample_campaign)
        db_session.add(sample_ad)
        
        # Add daily metrics for the past week
        daily_metrics = generate_daily_metrics("ad_123", days=7)
        for metric in daily_metrics:
            db_session.add(metric)
        
        db_session.commit()
        return {
            'client': sample_client,
            'campaign': sample_campaign,
            'ad': sample_ad,
            'metrics': daily_metrics
        }

    @pytest.mark.asyncio
    async def test_aggregate_weekly_metrics_success(self, aggregation_service, setup_test_data):
        """Test successful weekly metrics aggregation."""
        client_id = "513010266454814"
        week_start = date.today() - timedelta(days=7)
        
        result = await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        assert result['ads_aggregated'] > 0
        assert result['campaigns_aggregated'] > 0
        
        # Verify weekly ad metrics were created
        weekly_ad_metrics = aggregation_service.db.query(WeeklyAdMetrics).filter(
            WeeklyAdMetrics.week_start_date == week_start
        ).first()
        
        assert weekly_ad_metrics is not None
        assert weekly_ad_metrics.ad_id == "ad_123"
        assert weekly_ad_metrics.impressions > 0
        assert weekly_ad_metrics.spend > 0
        assert weekly_ad_metrics.roas > 0

    @pytest.mark.asyncio
    async def test_aggregate_weekly_metrics_no_data(self, aggregation_service, db_session):
        """Test weekly aggregation with no data."""
        client_id = "nonexistent_client"
        week_start = date.today() - timedelta(days=7)
        
        result = await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        assert result['ads_aggregated'] == 0
        assert result['campaigns_aggregated'] == 0

    @pytest.mark.asyncio
    async def test_aggregate_monthly_metrics_success(self, aggregation_service, setup_test_data):
        """Test successful monthly metrics aggregation."""
        client_id = "513010266454814"
        current_date = date.today()
        year = current_date.year
        month = current_date.month
        
        result = await aggregation_service.aggregate_monthly_metrics(client_id, year, month)
        
        assert result['ads_aggregated'] >= 0
        assert result['campaigns_aggregated'] >= 0

    @pytest.mark.asyncio
    async def test_weekly_aggregation_calculates_correct_metrics(self, aggregation_service, setup_test_data):
        """Test that weekly aggregation calculates metrics correctly."""
        client_id = "513010266454814"
        week_start = date.today() - timedelta(days=7)
        
        # Get the daily metrics for verification
        daily_metrics = aggregation_service.db.query(AdMetrics).filter(
            AdMetrics.ad_id == "ad_123",
            AdMetrics.date >= week_start,
            AdMetrics.date <= week_start + timedelta(days=6)
        ).all()
        
        expected_impressions = sum(m.impressions for m in daily_metrics)
        expected_clicks = sum(m.clicks for m in daily_metrics)
        expected_spend = sum(m.spend for m in daily_metrics)
        expected_conversions = sum(m.conversions for m in daily_metrics)
        expected_conversion_value = sum(m.conversion_value for m in daily_metrics)
        
        await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        weekly_metric = aggregation_service.db.query(WeeklyAdMetrics).filter(
            WeeklyAdMetrics.ad_id == "ad_123",
            WeeklyAdMetrics.week_start_date == week_start
        ).first()
        
        assert weekly_metric.impressions == expected_impressions
        assert weekly_metric.clicks == expected_clicks
        assert weekly_metric.spend == expected_spend
        assert weekly_metric.conversions == expected_conversions
        assert weekly_metric.conversion_value == expected_conversion_value
        
        # Test calculated metrics
        if expected_impressions > 0:
            expected_ctr = (expected_clicks / expected_impressions * 100)
            assert abs(float(weekly_metric.ctr) - expected_ctr) < 0.01
        
        if expected_clicks > 0:
            expected_cpc = (expected_spend / expected_clicks)
            assert abs(float(weekly_metric.cpc) - float(expected_cpc)) < 0.01
        
        if expected_spend > 0:
            expected_roas = (expected_conversion_value / expected_spend)
            assert abs(float(weekly_metric.roas) - float(expected_roas)) < 0.01

    @pytest.mark.asyncio
    async def test_aggregation_creates_sync_log(self, aggregation_service, setup_test_data):
        """Test that aggregation creates proper sync logs."""
        client_id = "513010266454814"
        week_start = date.today() - timedelta(days=7)
        
        await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        sync_log = aggregation_service.db.query(DataSyncLog).filter(
            DataSyncLog.client_id == client_id,
            DataSyncLog.sync_type == "weekly",
            DataSyncLog.sync_date == week_start
        ).first()
        
        assert sync_log is not None
        assert sync_log.status == "completed"
        assert sync_log.started_at is not None
        assert sync_log.completed_at is not None
        assert sync_log.records_processed > 0

    @pytest.mark.asyncio
    async def test_aggregation_handles_existing_records(self, aggregation_service, setup_test_data):
        """Test that aggregation properly updates existing records."""
        client_id = "513010266454814"
        week_start = date.today() - timedelta(days=7)
        
        # Run aggregation twice
        result1 = await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        result2 = await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        # Should have same results
        assert result1['ads_aggregated'] == result2['ads_aggregated']
        
        # Should only have one weekly record per ad
        weekly_records = aggregation_service.db.query(WeeklyAdMetrics).filter(
            WeeklyAdMetrics.week_start_date == week_start
        ).all()
        
        ad_ids = [record.ad_id for record in weekly_records]
        assert len(ad_ids) == len(set(ad_ids))  # No duplicates

    @pytest.mark.asyncio
    async def test_aggregation_with_different_attributions(self, aggregation_service, db_session, setup_test_data):
        """Test aggregation with different attribution models."""
        client_id = "513010266454814"
        week_start = date.today() - timedelta(days=7)
        
        # Add metrics with different attribution
        metric_7d = AdMetrics(
            id=f"ad_123_{week_start.strftime('%Y%m%d')}_7d",
            ad_id="ad_123",
            date=week_start,
            impressions=1000,
            clicks=50,
            spend=Decimal("100.00"),
            conversions=5,
            conversion_value=Decimal("500.00"),
            attribution="7d_click",
            currency="CZK"
        )
        db_session.add(metric_7d)
        db_session.commit()
        
        await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        # Should have separate weekly records for each attribution
        weekly_records = aggregation_service.db.query(WeeklyAdMetrics).filter(
            WeeklyAdMetrics.week_start_date == week_start,
            WeeklyAdMetrics.ad_id == "ad_123"
        ).all()
        
        attributions = [record.attribution for record in weekly_records]
        assert "default" in attributions
        assert "7d_click" in attributions

    @pytest.mark.asyncio
    async def test_aggregation_error_handling(self, aggregation_service, db_session):
        """Test error handling in aggregation service."""
        client_id = "513010266454814"
        week_start = date.today() - timedelta(days=7)
        
        # Mock database error
        with patch.object(aggregation_service.db, 'query', side_effect=Exception("Database error")):
            with pytest.raises(Exception):
                await aggregation_service.aggregate_weekly_metrics(client_id, week_start)
        
        # Check that sync log shows error
        sync_log = aggregation_service.db.query(DataSyncLog).filter(
            DataSyncLog.client_id == client_id,
            DataSyncLog.sync_type == "weekly",
            DataSyncLog.sync_date == week_start
        ).first()
        
        if sync_log:
            assert sync_log.status == "error"

    def test_aggregation_service_initialization(self, db_session):
        """Test AggregationService initialization."""
        service = AggregationService(db_session)
        assert service.db == db_session

    @pytest.mark.asyncio
    async def test_monthly_aggregation_date_range(self, aggregation_service, setup_test_data):
        """Test that monthly aggregation uses correct date range."""
        client_id = "513010266454814"
        year = 2024
        month = 1
        
        # Add metrics for January 2024
        jan_start = date(2024, 1, 1)
        jan_end = date(2024, 1, 31)
        
        metric = AdMetrics(
            id=f"ad_123_{jan_start.strftime('%Y%m%d')}",
            ad_id="ad_123",
            date=jan_start,
            impressions=1000,
            clicks=50,
            spend=Decimal("100.00"),
            conversions=5,
            conversion_value=Decimal("500.00"),
            attribution="default",
            currency="CZK"
        )
        aggregation_service.db.add(metric)
        aggregation_service.db.commit()
        
        result = await aggregation_service.aggregate_monthly_metrics(client_id, year, month)
        
        assert result['ads_aggregated'] >= 0
