"""
Tests for DataSyncService
"""

import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from app.services.data_sync_service import DataSyncService
from app.models.ad import Ad
from app.models.campaign import Campaign
from app.models.metrics import AdMetrics, CampaignMetrics, DataSyncLog


class TestDataSyncService:
    """Test cases for DataSyncService"""

    @pytest.fixture
    def data_sync_service(self, db_session):
        """Create DataSyncService instance with test database."""
        return DataSyncService(db_session)

    @pytest.fixture
    def mock_meta_service(self):
        """Mock MetaService for testing."""
        mock_service = Mock()
        mock_service.get_ads_data = AsyncMock()
        mock_service.get_campaigns_data = AsyncMock()
        mock_service.get_daily_metrics = AsyncMock()
        return mock_service

    @pytest.fixture
    def setup_test_client(self, db_session, sample_client):
        """Set up test client in database."""
        db_session.add(sample_client)
        db_session.commit()
        return sample_client

    @pytest.mark.asyncio
    async def test_sync_daily_data_success(self, data_sync_service, setup_test_client, mock_meta_service):
        """Test successful daily data sync."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        # Mock Meta API responses
        mock_ads_data = [
            {
                'id': 'ad_123',
                'name': 'Test Ad',
                'status': 'ACTIVE',
                'campaign_id': 'campaign_123',
                'adset_id': 'adset_123'
            }
        ]
        
        mock_campaigns_data = [
            {
                'id': 'campaign_123',
                'name': 'Test Campaign',
                'status': 'ACTIVE',
                'objective': 'CONVERSIONS'
            }
        ]
        
        mock_metrics_data = [
            {
                'ad_id': 'ad_123',
                'date': sync_date.strftime('%Y-%m-%d'),
                'impressions': 1000,
                'clicks': 50,
                'spend': 100.00,
                'conversions': 5,
                'conversion_value': 500.00,
                'ctr': 5.0,
                'cpc': 2.0,
                'cpm': 100.0,
                'roas': 5.0,
                'frequency': 1.2,
                'currency': 'CZK'
            }
        ]
        
        mock_meta_service.get_ads_data.return_value = mock_ads_data
        mock_meta_service.get_campaigns_data.return_value = mock_campaigns_data
        mock_meta_service.get_daily_metrics.return_value = mock_metrics_data
        
        with patch('app.services.data_sync_service.MetaService', return_value=mock_meta_service):
            result = await data_sync_service.sync_daily_data(client_id, sync_date)
        
        assert result['status'] == 'completed'
        assert result['ads_synced'] > 0
        assert result['campaigns_synced'] > 0
        assert result['metrics_synced'] > 0
        
        # Verify data was saved to database
        ad = data_sync_service.db.query(Ad).filter(Ad.id == 'ad_123').first()
        assert ad is not None
        assert ad.name == 'Test Ad'
        
        campaign = data_sync_service.db.query(Campaign).filter(Campaign.id == 'campaign_123').first()
        assert campaign is not None
        assert campaign.name == 'Test Campaign'
        
        metrics = data_sync_service.db.query(AdMetrics).filter(
            AdMetrics.ad_id == 'ad_123',
            AdMetrics.date == sync_date
        ).first()
        assert metrics is not None
        assert metrics.impressions == 1000
        assert metrics.roas == Decimal('5.0')

    @pytest.mark.asyncio
    async def test_sync_daily_data_creates_sync_log(self, data_sync_service, setup_test_client, mock_meta_service):
        """Test that sync creates proper sync log."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        mock_meta_service.get_ads_data.return_value = []
        mock_meta_service.get_campaigns_data.return_value = []
        mock_meta_service.get_daily_metrics.return_value = []
        
        with patch('app.services.data_sync_service.MetaService', return_value=mock_meta_service):
            await data_sync_service.sync_daily_data(client_id, sync_date)
        
        sync_log = data_sync_service.db.query(DataSyncLog).filter(
            DataSyncLog.client_id == client_id,
            DataSyncLog.sync_type == "daily",
            DataSyncLog.sync_date == sync_date
        ).first()
        
        assert sync_log is not None
        assert sync_log.status == "completed"
        assert sync_log.started_at is not None
        assert sync_log.completed_at is not None

    @pytest.mark.asyncio
    async def test_sync_ads_data_updates_existing(self, data_sync_service, setup_test_client):
        """Test that sync updates existing ads."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        # Create existing ad
        existing_ad = Ad(
            id="ad_123",
            name="Old Name",
            client_id=client_id,
            status="PAUSED"
        )
        data_sync_service.db.add(existing_ad)
        data_sync_service.db.commit()
        
        # Mock updated ad data
        mock_ads_data = [
            {
                'id': 'ad_123',
                'name': 'Updated Name',
                'status': 'ACTIVE',
                'campaign_id': 'campaign_123',
                'adset_id': 'adset_123'
            }
        ]
        
        with patch.object(data_sync_service, '_get_meta_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_ads_data = AsyncMock(return_value=mock_ads_data)
            mock_get_service.return_value = mock_service
            
            ads_synced = await data_sync_service._sync_ads_data(client_id, sync_date)
        
        # Should update existing ad, not create new one
        assert ads_synced == 0  # No new ads created
        
        updated_ad = data_sync_service.db.query(Ad).filter(Ad.id == 'ad_123').first()
        assert updated_ad.name == 'Updated Name'
        assert updated_ad.status == 'ACTIVE'

    @pytest.mark.asyncio
    async def test_sync_daily_metrics_calculates_roas(self, data_sync_service, setup_test_client):
        """Test that sync correctly calculates ROAS."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        mock_metrics_data = [
            {
                'ad_id': 'ad_123',
                'date': sync_date.strftime('%Y-%m-%d'),
                'impressions': 1000,
                'clicks': 50,
                'spend': 100.00,
                'conversions': 5,
                'conversion_value': 300.00,  # ROAS should be 3.0
                'ctr': 5.0,
                'cpc': 2.0,
                'cpm': 100.0,
                'frequency': 1.2,
                'currency': 'CZK'
            }
        ]
        
        with patch.object(data_sync_service, '_get_meta_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_daily_metrics = AsyncMock(return_value=mock_metrics_data)
            mock_get_service.return_value = mock_service
            
            metrics_synced = await data_sync_service._sync_daily_metrics(client_id, sync_date)
        
        assert metrics_synced > 0
        
        metrics = data_sync_service.db.query(AdMetrics).filter(
            AdMetrics.ad_id == 'ad_123',
            AdMetrics.date == sync_date
        ).first()
        
        assert metrics is not None
        assert float(metrics.roas) == 3.0  # 300 / 100

    @pytest.mark.asyncio
    async def test_sync_handles_zero_spend(self, data_sync_service, setup_test_client):
        """Test that sync handles zero spend correctly."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        mock_metrics_data = [
            {
                'ad_id': 'ad_123',
                'date': sync_date.strftime('%Y-%m-%d'),
                'impressions': 1000,
                'clicks': 0,
                'spend': 0.00,  # Zero spend
                'conversions': 0,
                'conversion_value': 0.00,
                'ctr': 0.0,
                'cpc': 0.0,
                'cpm': 0.0,
                'frequency': 1.0,
                'currency': 'CZK'
            }
        ]
        
        with patch.object(data_sync_service, '_get_meta_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_daily_metrics = AsyncMock(return_value=mock_metrics_data)
            mock_get_service.return_value = mock_service
            
            metrics_synced = await data_sync_service._sync_daily_metrics(client_id, sync_date)
        
        assert metrics_synced > 0
        
        metrics = data_sync_service.db.query(AdMetrics).filter(
            AdMetrics.ad_id == 'ad_123',
            AdMetrics.date == sync_date
        ).first()
        
        assert metrics is not None
        assert float(metrics.roas) == 0.0  # Should handle division by zero

    @pytest.mark.asyncio
    async def test_sync_historical_data(self, data_sync_service, setup_test_client, mock_meta_service):
        """Test historical data sync for date range."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        mock_meta_service.get_ads_data.return_value = []
        mock_meta_service.get_campaigns_data.return_value = []
        mock_meta_service.get_daily_metrics.return_value = []
        
        with patch('app.services.data_sync_service.MetaService', return_value=mock_meta_service):
            result = await data_sync_service.sync_historical_data(client_id, start_date, end_date)
        
        expected_days = (end_date - start_date).days + 1
        assert result['total_days'] == expected_days
        assert result['successful_days'] == expected_days
        assert result['failed_days'] == 0

    @pytest.mark.asyncio
    async def test_sync_error_handling(self, data_sync_service, setup_test_client):
        """Test error handling in sync service."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        with patch.object(data_sync_service, '_get_meta_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_ads_data = AsyncMock(side_effect=Exception("API Error"))
            mock_get_service.return_value = mock_service
            
            with pytest.raises(Exception):
                await data_sync_service.sync_daily_data(client_id, sync_date)
        
        # Check that sync log shows error
        sync_log = data_sync_service.db.query(DataSyncLog).filter(
            DataSyncLog.client_id == client_id,
            DataSyncLog.sync_type == "daily",
            DataSyncLog.sync_date == sync_date
        ).first()
        
        if sync_log:
            assert sync_log.status == "error"

    def test_data_sync_service_initialization(self, db_session):
        """Test DataSyncService initialization."""
        service = DataSyncService(db_session)
        assert service.db == db_session

    @pytest.mark.asyncio
    async def test_sync_with_different_currencies(self, data_sync_service, setup_test_client):
        """Test sync with different currencies."""
        client_id = "513010266454814"
        sync_date = date.today() - timedelta(days=1)
        
        mock_metrics_data = [
            {
                'ad_id': 'ad_123',
                'date': sync_date.strftime('%Y-%m-%d'),
                'impressions': 1000,
                'clicks': 50,
                'spend': 100.00,
                'conversions': 5,
                'conversion_value': 500.00,
                'ctr': 5.0,
                'cpc': 2.0,
                'cpm': 100.0,
                'frequency': 1.2,
                'currency': 'USD'  # Different currency
            }
        ]
        
        with patch.object(data_sync_service, '_get_meta_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_daily_metrics = AsyncMock(return_value=mock_metrics_data)
            mock_get_service.return_value = mock_service
            
            metrics_synced = await data_sync_service._sync_daily_metrics(client_id, sync_date)
        
        assert metrics_synced > 0
        
        metrics = data_sync_service.db.query(AdMetrics).filter(
            AdMetrics.ad_id == 'ad_123',
            AdMetrics.date == sync_date
        ).first()
        
        assert metrics is not None
        assert metrics.currency == 'USD'
