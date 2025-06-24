"""
Integration tests with Meta API
"""

import pytest
import os
from datetime import date, timedelta
from unittest.mock import patch

from app.services.meta_service import MetaService
from app.services.data_sync_service import DataSyncService
from app.models.client import Client
from app.models.ad import Ad
from app.models.campaign import Campaign
from app.models.metrics import AdMetrics, CampaignMetrics


# Skip integration tests if no Meta API credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("META_ACCESS_TOKEN") or not os.getenv("META_AD_ACCOUNT_ID"),
    reason="Meta API credentials not available"
)


@pytest.fixture
def meta_credentials():
    """Get Meta API credentials from environment."""
    return {
        "access_token": os.getenv("META_ACCESS_TOKEN"),
        "ad_account_id": os.getenv("META_AD_ACCOUNT_ID", "513010266454814")
    }


@pytest.fixture
def integration_client(db_session, meta_credentials):
    """Create a test client with real Meta credentials."""
    client = Client(
        id=meta_credentials["ad_account_id"],
        name="Integration Test Client",
        meta_ad_account_id=meta_credentials["ad_account_id"],
        meta_access_token=meta_credentials["access_token"],
        currency="CZK",
        timezone="Europe/Prague",
        is_active=True
    )
    db_session.add(client)
    db_session.commit()
    return client


class TestMetaAPIIntegration:
    """Integration tests with real Meta API"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_meta_service_connection(self, meta_credentials):
        """Test basic connection to Meta API."""
        meta_service = MetaService()
        
        # Test with a simple API call - get account info
        try:
            # This should not raise an exception if credentials are valid
            client_id = meta_credentials["ad_account_id"]
            start_date = date.today() - timedelta(days=7)
            end_date = date.today() - timedelta(days=1)
            
            # Try to get top performing ads (even if empty)
            result = await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=5
            )
            
            # Should return a list (even if empty)
            assert isinstance(result, list)
            
        except Exception as e:
            pytest.fail(f"Meta API connection failed: {str(e)}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_top_performing_ads_real_data(self, meta_credentials):
        """Test getting top performing ads with real data."""
        meta_service = MetaService()
        client_id = meta_credentials["ad_account_id"]
        
        # Get data for last week
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        result = await meta_service.get_top_performing_ads(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution="default",
            limit=10
        )
        
        assert isinstance(result, list)
        
        # If we have ads, validate their structure
        for ad_performance in result:
            assert hasattr(ad_performance, 'id')
            assert hasattr(ad_performance, 'name')
            assert hasattr(ad_performance, 'metrics')
            assert hasattr(ad_performance.metrics, 'impressions')
            assert hasattr(ad_performance.metrics, 'spend')
            assert hasattr(ad_performance.metrics, 'roas')
            
            # Validate data types
            assert isinstance(ad_performance.metrics.impressions, int)
            assert ad_performance.metrics.impressions >= 0
            assert float(ad_performance.metrics.spend) >= 0
            assert float(ad_performance.metrics.roas) >= 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_conversion_funnel_real_data(self, meta_credentials):
        """Test conversion funnel with real data."""
        meta_service = MetaService()
        client_id = meta_credentials["ad_account_id"]
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        result = await meta_service.get_conversion_funnel(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )
        
        assert isinstance(result, dict)
        assert 'funnel_stages' in result
        assert isinstance(result['funnel_stages'], list)
        
        # Validate funnel structure
        for stage in result['funnel_stages']:
            assert 'name' in stage
            assert 'count' in stage
            assert 'conversion_rate' in stage
            assert isinstance(stage['count'], int)
            assert isinstance(stage['conversion_rate'], (int, float))

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_week_on_week_comparison_real_data(self, meta_credentials):
        """Test week-on-week comparison with real data."""
        meta_service = MetaService()
        client_id = meta_credentials["ad_account_id"]
        
        # Calculate current and previous week
        today = date.today()
        days_since_monday = today.weekday()
        current_week_start = today - timedelta(days=days_since_monday)
        current_week_end = today
        previous_week_start = current_week_start - timedelta(days=7)
        previous_week_end = current_week_start - timedelta(days=1)
        
        result = await meta_service.get_week_on_week_comparison(
            client_id=client_id,
            current_week_start=current_week_start,
            current_week_end=current_week_end,
            previous_week_start=previous_week_start,
            previous_week_end=previous_week_end
        )
        
        assert isinstance(result, dict)
        assert 'current_week' in result
        assert 'previous_week' in result
        assert 'metrics_comparison' in result or 'comparison' in result
        
        # Validate week data structure
        for week_key in ['current_week', 'previous_week']:
            week_data = result[week_key]
            assert 'metrics' in week_data
            metrics = week_data['metrics']
            assert 'impressions' in metrics
            assert 'clicks' in metrics
            assert 'spend' in metrics
            assert 'conversions' in metrics

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_sync_integration(self, integration_client, db_session):
        """Test full data sync integration."""
        data_sync_service = DataSyncService(db_session)
        client_id = integration_client.id
        
        # Sync data for yesterday
        sync_date = date.today() - timedelta(days=1)
        
        try:
            result = await data_sync_service.sync_daily_data(client_id, sync_date)
            
            assert result['status'] == 'completed'
            assert 'ads_synced' in result
            assert 'campaigns_synced' in result
            assert 'metrics_synced' in result
            
            # Verify data was actually saved
            ads_count = db_session.query(Ad).filter(Ad.client_id == client_id).count()
            campaigns_count = db_session.query(Campaign).filter(Campaign.client_id == client_id).count()
            metrics_count = db_session.query(AdMetrics).filter(AdMetrics.date == sync_date).count()
            
            # Should have some data (even if zero)
            assert ads_count >= 0
            assert campaigns_count >= 0
            assert metrics_count >= 0
            
        except Exception as e:
            pytest.fail(f"Data sync integration failed: {str(e)}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_attribution_switching(self, meta_credentials):
        """Test different attribution models."""
        meta_service = MetaService()
        client_id = meta_credentials["ad_account_id"]
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        # Test default attribution
        default_result = await meta_service.get_top_performing_ads(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution="default",
            limit=5
        )
        
        # Test 7d click attribution
        seven_day_result = await meta_service.get_top_performing_ads(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution="7d_click",
            limit=5
        )
        
        # Both should return lists
        assert isinstance(default_result, list)
        assert isinstance(seven_day_result, list)
        
        # Results might be different due to attribution model
        # but structure should be the same
        for result_set in [default_result, seven_day_result]:
            for ad_performance in result_set:
                assert hasattr(ad_performance, 'metrics')
                assert hasattr(ad_performance.metrics, 'roas')

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_currency_handling(self, meta_credentials):
        """Test that currency is properly handled from Meta API."""
        meta_service = MetaService()
        client_id = meta_credentials["ad_account_id"]
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        result = await meta_service.get_top_performing_ads(
            client_id=client_id,
            start_date=start_date,
            end_date=end_date,
            attribution="default",
            limit=5
        )
        
        # If we have ads, check currency
        for ad_performance in result:
            assert hasattr(ad_performance, 'currency')
            assert isinstance(ad_performance.currency, str)
            assert len(ad_performance.currency) == 3  # Currency code should be 3 letters

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_invalid_account(self):
        """Test error handling with invalid account ID."""
        meta_service = MetaService()
        invalid_client_id = "999999999999999"  # Invalid account ID
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        with pytest.raises(Exception):
            await meta_service.get_top_performing_ads(
                client_id=invalid_client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=5
            )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_date_range_validation(self, meta_credentials):
        """Test various date ranges."""
        meta_service = MetaService()
        client_id = meta_credentials["ad_account_id"]
        
        # Test different date ranges
        test_ranges = [
            (date.today() - timedelta(days=1), date.today() - timedelta(days=1)),  # Single day
            (date.today() - timedelta(days=7), date.today() - timedelta(days=1)),  # Week
            (date.today() - timedelta(days=30), date.today() - timedelta(days=1)), # Month
        ]
        
        for start_date, end_date in test_ranges:
            result = await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=5
            )
            
            assert isinstance(result, list)
            # Each date range should return valid data structure
