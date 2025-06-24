"""
Tests for MetaService
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from app.services.meta_service import MetaService
from app.schemas.ad import AdPerformance


class TestMetaService:
    """Test cases for MetaService"""

    @pytest.fixture
    def meta_service(self):
        """Create MetaService instance."""
        return MetaService()

    @pytest.fixture
    def mock_ad_account(self):
        """Mock Facebook AdAccount."""
        mock_account = Mock()
        mock_account.get_insights = Mock()
        return mock_account

    @pytest.fixture
    def mock_insights_data(self):
        """Mock Meta API insights response."""
        return [
            {
                'ad_id': 'ad_123',
                'ad_name': 'Test Ad',
                'campaign_name': 'Test Campaign',
                'adset_name': 'Test AdSet',
                'impressions': '1000',
                'clicks': '50',
                'spend': '100.00',
                'actions': [
                    {'action_type': 'purchase', 'value': '5'}
                ],
                'action_values': [
                    {'action_type': 'purchase', 'value': '500.00'}
                ],
                'ctr': '5.0',
                'cpc': '2.0',
                'cpm': '100.0',
                'frequency': '1.2',
                'account_currency': 'CZK'
            }
        ]

    @pytest.mark.asyncio
    async def test_get_top_performing_ads_success(self, meta_service, mock_insights_data):
        """Test successful retrieval of top performing ads."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.return_value = mock_insights_data
            mock_ad_account_class.return_value = mock_account
            
            result = await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=10
            )
        
        assert len(result) == 1
        ad_performance = result[0]
        
        assert ad_performance.ad_id == 'ad_123'
        assert ad_performance.ad_name == 'Test Ad'
        assert ad_performance.campaign_name == 'Test Campaign'
        assert ad_performance.metrics.impressions == 1000
        assert ad_performance.metrics.clicks == 50
        assert float(ad_performance.metrics.spend) == 100.00
        assert ad_performance.metrics.conversions == 5
        assert float(ad_performance.metrics.conversion_value) == 500.00
        assert float(ad_performance.metrics.roas) == 5.0
        assert ad_performance.currency == 'CZK'

    @pytest.mark.asyncio
    async def test_get_top_performing_ads_with_7d_attribution(self, meta_service, mock_insights_data):
        """Test top performing ads with 7d click attribution."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.return_value = mock_insights_data
            mock_ad_account_class.return_value = mock_account
            
            await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="7d_click",
                limit=10
            )
        
        # Verify that the correct attribution window was set
        call_args = mock_account.get_insights.call_args
        params = call_args[1]['params']
        assert params['action_attribution_windows'] == ['7d_click']

    @pytest.mark.asyncio
    async def test_get_top_performing_ads_sorts_by_roas(self, meta_service):
        """Test that ads are sorted by ROAS in descending order."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        mock_insights_data = [
            {
                'ad_id': 'ad_low_roas',
                'ad_name': 'Low ROAS Ad',
                'campaign_name': 'Test Campaign',
                'adset_name': 'Test AdSet',
                'impressions': '1000',
                'clicks': '50',
                'spend': '100.00',
                'actions': [{'action_type': 'purchase', 'value': '2'}],
                'action_values': [{'action_type': 'purchase', 'value': '200.00'}],
                'ctr': '5.0', 'cpc': '2.0', 'cpm': '100.0', 'frequency': '1.2',
                'account_currency': 'CZK'
            },
            {
                'ad_id': 'ad_high_roas',
                'ad_name': 'High ROAS Ad',
                'campaign_name': 'Test Campaign',
                'adset_name': 'Test AdSet',
                'impressions': '1000',
                'clicks': '50',
                'spend': '100.00',
                'actions': [{'action_type': 'purchase', 'value': '10'}],
                'action_values': [{'action_type': 'purchase', 'value': '1000.00'}],
                'ctr': '5.0', 'cpc': '2.0', 'cpm': '100.0', 'frequency': '1.2',
                'account_currency': 'CZK'
            }
        ]
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.return_value = mock_insights_data
            mock_ad_account_class.return_value = mock_account
            
            result = await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=10
            )
        
        assert len(result) == 2
        # Should be sorted by ROAS descending
        assert result[0].ad_id == 'ad_high_roas'
        assert result[1].ad_id == 'ad_low_roas'
        assert float(result[0].metrics.roas) > float(result[1].metrics.roas)

    @pytest.mark.asyncio
    async def test_get_top_performing_ads_handles_no_conversions(self, meta_service):
        """Test handling of ads with no conversions."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        mock_insights_data = [
            {
                'ad_id': 'ad_no_conversions',
                'ad_name': 'No Conversions Ad',
                'campaign_name': 'Test Campaign',
                'adset_name': 'Test AdSet',
                'impressions': '1000',
                'clicks': '50',
                'spend': '100.00',
                'actions': [],  # No actions
                'action_values': [],  # No action values
                'ctr': '5.0',
                'cpc': '2.0',
                'cpm': '100.0',
                'frequency': '1.2',
                'account_currency': 'CZK'
            }
        ]
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.return_value = mock_insights_data
            mock_ad_account_class.return_value = mock_account
            
            result = await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=10
            )
        
        assert len(result) == 1
        ad_performance = result[0]
        assert ad_performance.metrics.conversions == 0
        assert float(ad_performance.metrics.conversion_value) == 0.0
        assert float(ad_performance.metrics.roas) == 0.0

    @pytest.mark.asyncio
    async def test_get_top_performing_ads_handles_zero_spend(self, meta_service):
        """Test handling of ads with zero spend."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        mock_insights_data = [
            {
                'ad_id': 'ad_zero_spend',
                'ad_name': 'Zero Spend Ad',
                'campaign_name': 'Test Campaign',
                'adset_name': 'Test AdSet',
                'impressions': '1000',
                'clicks': '0',
                'spend': '0.00',  # Zero spend
                'actions': [{'action_type': 'purchase', 'value': '5'}],
                'action_values': [{'action_type': 'purchase', 'value': '500.00'}],
                'ctr': '0.0',
                'cpc': '0.0',
                'cpm': '0.0',
                'frequency': '1.0',
                'account_currency': 'CZK'
            }
        ]
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.return_value = mock_insights_data
            mock_ad_account_class.return_value = mock_account
            
            result = await meta_service.get_top_performing_ads(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                attribution="default",
                limit=10
            )
        
        assert len(result) == 1
        ad_performance = result[0]
        assert float(ad_performance.metrics.spend) == 0.0
        assert float(ad_performance.metrics.roas) == 0.0  # Should handle division by zero

    @pytest.mark.asyncio
    async def test_get_conversion_funnel(self, meta_service):
        """Test conversion funnel data retrieval."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        mock_insights_data = [
            {
                'impressions': '10000',
                'clicks': '500',
                'actions': [
                    {'action_type': 'landing_page_view', 'value': '400'},
                    {'action_type': 'add_to_cart', 'value': '100'},
                    {'action_type': 'purchase', 'value': '25'}
                ]
            }
        ]
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.return_value = mock_insights_data
            mock_ad_account_class.return_value = mock_account
            
            result = await meta_service.get_conversion_funnel(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date
            )
        
        assert 'funnel_stages' in result
        stages = result['funnel_stages']
        
        # Check that all funnel stages are present
        stage_names = [stage['name'] for stage in stages]
        assert 'Impressions' in stage_names
        assert 'Clicks' in stage_names
        assert 'Landing Page Views' in stage_names
        assert 'Add to Cart' in stage_names
        assert 'Purchase' in stage_names
        
        # Check conversion rates are calculated
        for stage in stages:
            assert 'count' in stage
            assert 'conversion_rate' in stage

    @pytest.mark.asyncio
    async def test_get_week_on_week_comparison(self, meta_service):
        """Test week-on-week comparison data."""
        client_id = "513010266454814"
        current_week_start = date.today() - timedelta(days=7)
        current_week_end = date.today() - timedelta(days=1)
        previous_week_start = current_week_start - timedelta(days=7)
        previous_week_end = current_week_start - timedelta(days=1)
        
        # Mock current week data
        current_week_data = [
            {
                'impressions': '5000',
                'clicks': '250',
                'spend': '500.00',
                'actions': [{'action_type': 'purchase', 'value': '25'}],
                'action_values': [{'action_type': 'purchase', 'value': '2500.00'}]
            }
        ]
        
        # Mock previous week data
        previous_week_data = [
            {
                'impressions': '4000',
                'clicks': '200',
                'spend': '400.00',
                'actions': [{'action_type': 'purchase', 'value': '20'}],
                'action_values': [{'action_type': 'purchase', 'value': '2000.00'}]
            }
        ]
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            # Return different data based on call order
            mock_account.get_insights.side_effect = [current_week_data, previous_week_data]
            mock_ad_account_class.return_value = mock_account
            
            result = await meta_service.get_week_on_week_comparison(
                client_id=client_id,
                current_week_start=current_week_start,
                current_week_end=current_week_end,
                previous_week_start=previous_week_start,
                previous_week_end=previous_week_end
            )
        
        assert 'current_week' in result
        assert 'previous_week' in result
        assert 'comparison' in result
        
        # Check that percentage changes are calculated
        comparison = result['comparison']
        assert 'impressions_change' in comparison
        assert 'clicks_change' in comparison
        assert 'spend_change' in comparison
        assert 'conversions_change' in comparison
        assert 'roas_change' in comparison

    @pytest.mark.asyncio
    async def test_get_ad_performance_history(self, meta_service):
        """Test ad performance history retrieval."""
        ad_id = "ad_123"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        mock_insights_data = [
            {
                'date_start': (start_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                'impressions': str(1000 + i * 100),
                'clicks': str(50 + i * 5),
                'spend': str(100.00 + i * 10),
                'actions': [{'action_type': 'purchase', 'value': str(5 + i)}],
                'action_values': [{'action_type': 'purchase', 'value': str(500.00 + i * 50)}],
                'ctr': '5.0',
                'cpc': '2.0',
                'cpm': '100.0'
            }
            for i in range(7)
        ]
        
        with patch('app.services.meta_service.Ad') as mock_ad_class:
            mock_ad = Mock()
            mock_ad.get_insights.return_value = mock_insights_data
            mock_ad_class.return_value = mock_ad
            
            result = await meta_service.get_ad_performance_history(
                ad_id=ad_id,
                start_date=start_date,
                end_date=end_date
            )
        
        assert len(result) == 7
        for i, daily_data in enumerate(result):
            assert 'date' in daily_data
            assert 'metrics' in daily_data
            expected_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            assert daily_data['date'] == expected_date

    def test_meta_service_initialization(self):
        """Test MetaService initialization."""
        service = MetaService()
        assert service is not None

    @pytest.mark.asyncio
    async def test_api_error_handling(self, meta_service):
        """Test handling of Meta API errors."""
        client_id = "513010266454814"
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)
        
        with patch('app.services.meta_service.AdAccount') as mock_ad_account_class:
            mock_account = Mock()
            mock_account.get_insights.side_effect = Exception("API Error")
            mock_ad_account_class.return_value = mock_account
            
            with pytest.raises(Exception):
                await meta_service.get_top_performing_ads(
                    client_id=client_id,
                    start_date=start_date,
                    end_date=end_date,
                    attribution="default",
                    limit=10
                )
