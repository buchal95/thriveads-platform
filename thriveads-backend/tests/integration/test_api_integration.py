"""
Integration tests for API endpoints with real data
"""

import pytest
import os
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.models.client import Client


# Skip integration tests if no Meta API credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("META_ACCESS_TOKEN") or not os.getenv("META_AD_ACCOUNT_ID"),
    reason="Meta API credentials not available"
)


@pytest.fixture
def integration_test_client(db_session):
    """Create a test client with real Meta credentials for integration testing."""
    # Create client with real credentials
    client = Client(
        id=os.getenv("META_AD_ACCOUNT_ID", "513010266454814"),
        name="Integration Test Client",
        meta_ad_account_id=os.getenv("META_AD_ACCOUNT_ID", "513010266454814"),
        meta_access_token=os.getenv("META_ACCESS_TOKEN"),
        currency="CZK",
        timezone="Europe/Prague",
        is_active=True
    )
    db_session.add(client)
    db_session.commit()
    return client


class TestAPIIntegration:
    """Integration tests for API endpoints with real Meta data"""

    @pytest.mark.integration
    def test_top_performing_ads_endpoint_integration(self, client, integration_test_client):
        """Test top performing ads endpoint with real data."""
        response = client.get(
            "/api/v1/ads/top-performing",
            params={
                "client_id": integration_test_client.id,
                "period": "last_week",
                "attribution": "default",
                "limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Validate response structure for each ad
        for ad_data in data:
            assert "id" in ad_data
            assert "name" in ad_data
            assert "status" in ad_data
            assert "campaign_name" in ad_data
            assert "metrics" in ad_data
            assert "currency" in ad_data
            
            # Validate metrics structure
            metrics = ad_data["metrics"]
            assert "impressions" in metrics
            assert "clicks" in metrics
            assert "spend" in metrics
            assert "conversions" in metrics
            assert "conversion_value" in metrics
            assert "roas" in metrics
            assert "ctr" in metrics
            assert "cpc" in metrics
            assert "cpm" in metrics
            assert "frequency" in metrics
            
            # Validate data types and ranges
            assert isinstance(metrics["impressions"], int)
            assert metrics["impressions"] >= 0
            assert isinstance(metrics["clicks"], int)
            assert metrics["clicks"] >= 0
            assert float(metrics["spend"]) >= 0
            assert isinstance(metrics["conversions"], int)
            assert metrics["conversions"] >= 0
            assert float(metrics["conversion_value"]) >= 0
            assert float(metrics["roas"]) >= 0

    @pytest.mark.integration
    def test_top_performing_ads_different_periods(self, client, integration_test_client):
        """Test top performing ads with different time periods."""
        periods = ["last_week", "last_month"]
        
        for period in periods:
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": integration_test_client.id,
                    "period": period,
                    "attribution": "default",
                    "limit": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.integration
    def test_top_performing_ads_attribution_switching(self, client, integration_test_client):
        """Test top performing ads with different attribution models."""
        attributions = ["default", "7d_click"]
        
        for attribution in attributions:
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": integration_test_client.id,
                    "period": "last_week",
                    "attribution": attribution,
                    "limit": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.integration
    def test_conversion_funnel_endpoint_integration(self, client, integration_test_client):
        """Test conversion funnel endpoint with real data."""
        response = client.get(
            "/api/v1/metrics/funnel",
            params={
                "client_id": integration_test_client.id,
                "period": "last_week"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "funnel_stages" in data
        assert isinstance(data["funnel_stages"], list)
        
        # Validate funnel stages structure
        for stage in data["funnel_stages"]:
            assert "name" in stage
            assert "count" in stage
            assert "conversion_rate" in stage
            assert isinstance(stage["count"], int)
            assert isinstance(stage["conversion_rate"], (int, float))
            assert 0 <= stage["conversion_rate"] <= 100

    @pytest.mark.integration
    def test_week_on_week_comparison_endpoint_integration(self, client, integration_test_client):
        """Test week-on-week comparison endpoint with real data."""
        response = client.get(
            "/api/v1/metrics/week-on-week",
            params={"client_id": integration_test_client.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "current_week" in data
        assert "previous_week" in data
        
        # Check for comparison data (might be named differently)
        assert "metrics_comparison" in data or "comparison" in data
        
        # Validate week data structure
        for week_key in ["current_week", "previous_week"]:
            week_data = data[week_key]
            assert "metrics" in week_data
            metrics = week_data["metrics"]
            
            # Validate metrics
            required_metrics = ["impressions", "clicks", "spend", "conversions"]
            for metric in required_metrics:
                assert metric in metrics
                assert isinstance(metrics[metric], (int, float))
                assert metrics[metric] >= 0

    @pytest.mark.integration
    def test_daily_sync_endpoint_integration(self, client, integration_test_client):
        """Test daily sync endpoint with real client."""
        response = client.post(
            "/api/v1/sync/daily",
            params={"client_id": integration_test_client.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "client_id" in data
        assert "sync_date" in data
        assert "status" in data
        assert data["status"] == "started"
        assert data["client_id"] == integration_test_client.id

    @pytest.mark.integration
    def test_weekly_aggregation_endpoint_integration(self, client, integration_test_client):
        """Test weekly aggregation endpoint."""
        # Get last Monday
        today = date.today()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        
        response = client.post(
            "/api/v1/sync/aggregate/weekly",
            params={
                "client_id": integration_test_client.id,
                "week_start": last_monday.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "client_id" in data
        assert "week_start" in data
        assert "week_end" in data
        assert "status" in data
        assert data["status"] == "started"

    @pytest.mark.integration
    def test_monthly_aggregation_endpoint_integration(self, client, integration_test_client):
        """Test monthly aggregation endpoint."""
        # Use last month
        today = date.today()
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1
        
        response = client.post(
            "/api/v1/sync/aggregate/monthly",
            params={
                "client_id": integration_test_client.id,
                "year": year,
                "month": month
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "client_id" in data
        assert "year" in data
        assert "month" in data
        assert "status" in data
        assert data["status"] == "started"

    @pytest.mark.integration
    def test_sync_status_endpoint_integration(self, client, integration_test_client):
        """Test sync status endpoint."""
        response = client.get(
            "/api/v1/sync/status",
            params={"client_id": integration_test_client.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "client_id" in data
        assert "summary" in data
        assert "recent_syncs" in data
        
        # Validate summary structure
        summary = data["summary"]
        assert "total_syncs" in summary
        assert "successful_syncs" in summary
        assert "failed_syncs" in summary
        assert "success_rate" in summary
        
        # Validate recent syncs structure
        recent_syncs = data["recent_syncs"]
        assert isinstance(recent_syncs, list)

    @pytest.mark.integration
    def test_error_handling_invalid_client_id(self, client):
        """Test error handling with invalid client ID."""
        invalid_client_id = "999999999999999"
        
        response = client.get(
            "/api/v1/ads/top-performing",
            params={
                "client_id": invalid_client_id,
                "period": "last_week",
                "attribution": "default",
                "limit": 5
            }
        )
        
        # Should handle the error gracefully
        assert response.status_code in [400, 404, 500]

    @pytest.mark.integration
    def test_rate_limiting_behavior(self, client, integration_test_client):
        """Test behavior under multiple rapid requests."""
        # Make multiple requests rapidly
        responses = []
        for i in range(5):
            response = client.get(
                "/api/v1/ads/top-performing",
                params={
                    "client_id": integration_test_client.id,
                    "period": "last_week",
                    "attribution": "default",
                    "limit": 3
                }
            )
            responses.append(response)
        
        # All requests should either succeed or fail gracefully
        for response in responses:
            assert response.status_code in [200, 429, 500]  # 429 = Too Many Requests

    @pytest.mark.integration
    def test_data_consistency_across_endpoints(self, client, integration_test_client):
        """Test data consistency across different endpoints."""
        # Get top performing ads
        ads_response = client.get(
            "/api/v1/ads/top-performing",
            params={
                "client_id": integration_test_client.id,
                "period": "last_week",
                "attribution": "default",
                "limit": 5
            }
        )
        
        # Get week-on-week comparison
        comparison_response = client.get(
            "/api/v1/metrics/week-on-week",
            params={"client_id": integration_test_client.id}
        )
        
        # Get conversion funnel
        funnel_response = client.get(
            "/api/v1/metrics/funnel",
            params={
                "client_id": integration_test_client.id,
                "period": "last_week"
            }
        )
        
        # All should succeed
        assert ads_response.status_code == 200
        assert comparison_response.status_code == 200
        assert funnel_response.status_code == 200
        
        # Currency should be consistent across endpoints
        ads_data = ads_response.json()
        comparison_data = comparison_response.json()
        
        if ads_data and "currency" in ads_data[0]:
            ads_currency = ads_data[0]["currency"]
            if "currency" in comparison_data:
                assert comparison_data["currency"] == ads_currency
