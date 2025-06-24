"""
Tests for API endpoints
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.schemas.ad import AdPerformance, AdMetrics as AdMetricsSchema


class TestAdsEndpoints:
    """Test cases for ads API endpoints"""

    def test_get_top_performing_ads_success(self, client):
        """Test successful retrieval of top performing ads."""
        mock_ad_performance = AdPerformance(
            id="ad_123",
            name="Test Ad",
            status="ACTIVE",
            campaign_name="Test Campaign",
            adset_name="Test AdSet",
            metrics=AdMetricsSchema(
                impressions=1000,
                clicks=50,
                spend=100.00,
                conversions=5,
                conversion_value=500.00,
                ctr=5.0,
                cpc=2.0,
                cpm=100.0,
                roas=5.0,
                frequency=1.2
            ),
            currency="CZK",
            facebook_url="https://facebook.com/ad_123"
        )
        
        with patch('app.api.v1.endpoints.ads.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_top_performing_ads = AsyncMock(return_value=[mock_ad_performance])
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": "513010266454814",
                    "period": "last_week",
                    "attribution": "default",
                    "limit": 10
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        ad_data = data[0]
        assert ad_data["id"] == "ad_123"
        assert ad_data["name"] == "Test Ad"
        assert ad_data["metrics"]["impressions"] == 1000
        assert ad_data["metrics"]["roas"] == 5.0
        assert ad_data["currency"] == "CZK"

    def test_get_top_performing_ads_with_7d_attribution(self, client):
        """Test top performing ads with 7d click attribution."""
        with patch('app.api.v1.endpoints.ads.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_top_performing_ads = AsyncMock(return_value=[])
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": "513010266454814",
                    "period": "last_week",
                    "attribution": "7d_click",
                    "limit": 10
                }
            )
        
        assert response.status_code == 200
        
        # Verify that the service was called with correct attribution
        mock_service.get_top_performing_ads.assert_called_once()
        call_args = mock_service.get_top_performing_ads.call_args
        assert call_args[1]['attribution'] == '7d_click'

    def test_get_top_performing_ads_last_month(self, client):
        """Test top performing ads for last month period."""
        with patch('app.api.v1.endpoints.ads.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_top_performing_ads = AsyncMock(return_value=[])
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": "513010266454814",
                    "period": "last_month",
                    "attribution": "default",
                    "limit": 10
                }
            )
        
        assert response.status_code == 200
        
        # Verify that the service was called with correct date range
        mock_service.get_top_performing_ads.assert_called_once()
        call_args = mock_service.get_top_performing_ads.call_args
        start_date = call_args[1]['start_date']
        end_date = call_args[1]['end_date']
        
        # Should be previous month's date range
        today = date.today()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        expected_start = last_day_previous_month.replace(day=1)
        
        assert start_date == expected_start
        assert end_date == last_day_previous_month

    def test_get_top_performing_ads_missing_client_id(self, client):
        """Test top performing ads endpoint without client_id."""
        response = client.get("/api/v1/ads/top-performing")
        assert response.status_code == 422  # Validation error

    def test_get_top_performing_ads_invalid_period(self, client):
        """Test top performing ads with invalid period."""
        response = client.get(
            "/api/v1/ads/top-performing",
            params={
                "client_id": "513010266454814",
                "period": "invalid_period"
            }
        )
        assert response.status_code == 400

    def test_get_top_performing_ads_api_error(self, client):
        """Test handling of API errors."""
        with patch('app.api.v1.endpoints.ads.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_top_performing_ads = AsyncMock(side_effect=Exception("API Error"))
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": "513010266454814",
                    "period": "last_week"
                }
            )
        
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]

    def test_get_ad_performance_history(self, client):
        """Test ad performance history endpoint."""
        mock_history_data = [
            {
                'date': '2024-01-01',
                'metrics': {
                    'impressions': 1000,
                    'clicks': 50,
                    'spend': 100.00,
                    'conversions': 5,
                    'conversion_value': 500.00,
                    'roas': 5.0
                }
            }
        ]
        
        with patch('app.api.v1.endpoints.ads.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_ad_performance_history = AsyncMock(return_value=mock_history_data)
            mock_meta_service_class.return_value = mock_service
            
            response = client.get("/api/v1/ads/ad_123/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['date'] == '2024-01-01'
        assert data[0]['metrics']['impressions'] == 1000


class TestMetricsEndpoints:
    """Test cases for metrics API endpoints"""

    def test_get_conversion_funnel_last_week(self, client):
        """Test conversion funnel for last week."""
        mock_funnel_data = {
            'funnel_stages': [
                {'name': 'Impressions', 'count': 10000, 'conversion_rate': 100.0},
                {'name': 'Clicks', 'count': 500, 'conversion_rate': 5.0},
                {'name': 'Purchase', 'count': 25, 'conversion_rate': 5.0}
            ],
            'period': 'last_week'
        }
        
        with patch('app.api.v1.endpoints.metrics.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_conversion_funnel = AsyncMock(return_value=mock_funnel_data)
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/metrics/funnel",
                params={
                    "client_id": "513010266454814",
                    "period": "last_week"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert 'funnel_stages' in data
        assert len(data['funnel_stages']) == 3
        assert data['funnel_stages'][0]['name'] == 'Impressions'

    def test_get_conversion_funnel_last_month(self, client):
        """Test conversion funnel for last month."""
        with patch('app.api.v1.endpoints.metrics.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_conversion_funnel = AsyncMock(return_value={})
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/metrics/funnel",
                params={
                    "client_id": "513010266454814",
                    "period": "last_month"
                }
            )
        
        assert response.status_code == 200
        
        # Verify correct date range was calculated
        mock_service.get_conversion_funnel.assert_called_once()
        call_args = mock_service.get_conversion_funnel.call_args
        start_date = call_args[1]['start_date']
        end_date = call_args[1]['end_date']
        
        # Should be previous month's date range
        today = date.today()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        expected_start = last_day_previous_month.replace(day=1)
        
        assert start_date == expected_start
        assert end_date == last_day_previous_month

    def test_get_conversion_funnel_invalid_period(self, client):
        """Test conversion funnel with invalid period."""
        response = client.get(
            "/api/v1/metrics/funnel",
            params={
                "client_id": "513010266454814",
                "period": "invalid_period"
            }
        )
        assert response.status_code == 400

    def test_get_week_on_week_comparison(self, client):
        """Test week-on-week comparison endpoint."""
        mock_comparison_data = {
            'current_week': {
                'impressions': 5000,
                'clicks': 250,
                'spend': 500.00,
                'conversions': 25,
                'roas': 5.0
            },
            'previous_week': {
                'impressions': 4000,
                'clicks': 200,
                'spend': 400.00,
                'conversions': 20,
                'roas': 5.0
            },
            'comparison': {
                'impressions_change': 25.0,
                'clicks_change': 25.0,
                'spend_change': 25.0,
                'conversions_change': 25.0,
                'roas_change': 0.0
            }
        }
        
        with patch('app.api.v1.endpoints.metrics.MetaService') as mock_meta_service_class:
            mock_service = Mock()
            mock_service.get_week_on_week_comparison = AsyncMock(return_value=mock_comparison_data)
            mock_meta_service_class.return_value = mock_service
            
            response = client.get(
                "/api/v1/metrics/week-on-week",
                params={"client_id": "513010266454814"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert 'current_week' in data
        assert 'previous_week' in data
        assert 'comparison' in data
        assert data['comparison']['impressions_change'] == 25.0

    def test_get_week_on_week_comparison_missing_client_id(self, client):
        """Test week-on-week comparison without client_id."""
        response = client.get("/api/v1/metrics/week-on-week")
        assert response.status_code == 422  # Validation error


class TestSyncEndpoints:
    """Test cases for sync API endpoints"""

    def test_sync_daily_data(self, client):
        """Test daily data sync endpoint."""
        with patch('app.api.v1.endpoints.sync.DataSyncService') as mock_sync_service_class:
            mock_service = Mock()
            mock_service.sync_daily_data = AsyncMock(return_value={
                'status': 'completed',
                'ads_synced': 10,
                'campaigns_synced': 5,
                'metrics_synced': 50
            })
            mock_sync_service_class.return_value = mock_service
            
            response = client.post(
                "/api/v1/sync/daily",
                params={"client_id": "513010266454814"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Daily data sync started'
        assert data['client_id'] == '513010266454814'

    def test_sync_weekly_aggregation(self, client):
        """Test weekly aggregation endpoint."""
        week_start = date.today() - timedelta(days=7)
        # Ensure it's a Monday
        while week_start.weekday() != 0:
            week_start -= timedelta(days=1)
        
        response = client.post(
            "/api/v1/sync/aggregate/weekly",
            params={
                "client_id": "513010266454814",
                "week_start": week_start.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Weekly aggregation started'
        assert data['client_id'] == '513010266454814'

    def test_sync_weekly_aggregation_invalid_day(self, client):
        """Test weekly aggregation with non-Monday start date."""
        # Use a Tuesday
        week_start = date.today() - timedelta(days=6)
        while week_start.weekday() != 1:  # Tuesday
            week_start -= timedelta(days=1)
        
        response = client.post(
            "/api/v1/sync/aggregate/weekly",
            params={
                "client_id": "513010266454814",
                "week_start": week_start.isoformat()
            }
        )
        
        assert response.status_code == 400
        assert "Week start must be a Monday" in response.json()["detail"]

    def test_sync_monthly_aggregation(self, client):
        """Test monthly aggregation endpoint."""
        response = client.post(
            "/api/v1/sync/aggregate/monthly",
            params={
                "client_id": "513010266454814",
                "year": 2024,
                "month": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == 'Monthly aggregation started'
        assert data['client_id'] == '513010266454814'
        assert data['year'] == 2024
        assert data['month'] == 1

    def test_sync_monthly_aggregation_invalid_month(self, client):
        """Test monthly aggregation with invalid month."""
        response = client.post(
            "/api/v1/sync/aggregate/monthly",
            params={
                "client_id": "513010266454814",
                "year": 2024,
                "month": 13  # Invalid month
            }
        )
        
        assert response.status_code == 400
        assert "Month must be between 1 and 12" in response.json()["detail"]
