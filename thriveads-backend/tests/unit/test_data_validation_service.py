"""
Tests for DataValidationService
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.services.data_validation_service import DataValidationService
from tests.conftest import generate_daily_metrics


class TestDataValidationService:
    """Test cases for DataValidationService"""

    @pytest.fixture
    def validation_service(self, db_session):
        """Create DataValidationService instance with test database."""
        return DataValidationService(db_session)

    def test_validate_metrics_data_valid(self, validation_service):
        """Test validation with valid metrics data."""
        valid_data = {
            'impressions': 1000,
            'clicks': 50,
            'spend': 100.0,
            'conversions': 5,
            'conversion_value': 500.0,
            'ctr': 5.0,
            'roas': 5.0
        }
        
        is_valid, errors = validation_service.validate_metrics_data(valid_data)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_metrics_data_missing_fields(self, validation_service):
        """Test validation with missing required fields."""
        invalid_data = {
            'impressions': 1000,
            'clicks': 50
            # Missing spend, conversions, conversion_value
        }
        
        is_valid, errors = validation_service.validate_metrics_data(invalid_data)
        
        assert is_valid is False
        assert len(errors) >= 3
        assert any('spend' in error for error in errors)
        assert any('conversions' in error for error in errors)
        assert any('conversion_value' in error for error in errors)

    def test_validate_metrics_data_negative_values(self, validation_service):
        """Test validation with negative values."""
        invalid_data = {
            'impressions': -100,
            'clicks': -10,
            'spend': -50.0,
            'conversions': -2,
            'conversion_value': -100.0
        }
        
        is_valid, errors = validation_service.validate_metrics_data(invalid_data)
        
        assert is_valid is False
        assert len(errors) >= 5
        assert any('negative' in error.lower() for error in errors)

    def test_validate_metrics_data_logical_inconsistencies(self, validation_service):
        """Test validation with logical inconsistencies."""
        invalid_data = {
            'impressions': 100,
            'clicks': 200,  # More clicks than impressions
            'spend': 50.0,
            'conversions': 300,  # More conversions than clicks
            'conversion_value': 500.0
        }
        
        is_valid, errors = validation_service.validate_metrics_data(invalid_data)
        
        assert is_valid is False
        assert any('clicks cannot exceed impressions' in error.lower() for error in errors)
        assert any('conversions cannot exceed clicks' in error.lower() for error in errors)

    def test_validate_metrics_data_ctr_consistency(self, validation_service):
        """Test CTR consistency validation."""
        invalid_data = {
            'impressions': 1000,
            'clicks': 50,
            'spend': 100.0,
            'conversions': 5,
            'conversion_value': 500.0,
            'ctr': 10.0  # Should be 5.0 based on clicks/impressions
        }
        
        is_valid, errors = validation_service.validate_metrics_data(invalid_data)
        
        assert is_valid is False
        assert any('ctr inconsistent' in error.lower() for error in errors)

    def test_validate_metrics_data_roas_consistency(self, validation_service):
        """Test ROAS consistency validation."""
        invalid_data = {
            'impressions': 1000,
            'clicks': 50,
            'spend': 100.0,
            'conversions': 5,
            'conversion_value': 500.0,
            'roas': 10.0  # Should be 5.0 based on conversion_value/spend
        }
        
        is_valid, errors = validation_service.validate_metrics_data(invalid_data)
        
        assert is_valid is False
        assert any('roas inconsistent' in error.lower() for error in errors)

    def test_detect_data_anomalies_no_data(self, validation_service):
        """Test anomaly detection with no data."""
        client_id = "test_client"
        
        anomalies = validation_service.detect_data_anomalies(client_id, days_back=30)
        
        assert 'missing_data' in anomalies
        assert len(anomalies['missing_data']) > 0
        assert any(anomaly['type'] == 'no_recent_data' for anomaly in anomalies['missing_data'])

    def test_detect_data_anomalies_with_data(self, validation_service, db_session, sample_ad):
        """Test anomaly detection with sample data."""
        db_session.add(sample_ad)
        
        # Add some test metrics with anomalies
        test_date = date.today() - timedelta(days=1)
        
        # Normal metric
        normal_metric = generate_daily_metrics("ad_123", days=1)[0]
        normal_metric.date = test_date
        normal_metric.id = f"ad_123_{test_date.strftime('%Y%m%d')}"
        db_session.add(normal_metric)
        
        # Anomalous metric (clicks > impressions)
        anomalous_metric = generate_daily_metrics("ad_123", days=1)[0]
        anomalous_metric.date = test_date - timedelta(days=1)
        anomalous_metric.id = f"ad_123_{(test_date - timedelta(days=1)).strftime('%Y%m%d')}"
        anomalous_metric.clicks = 2000  # More than impressions
        anomalous_metric.impressions = 1000
        db_session.add(anomalous_metric)
        
        db_session.commit()
        
        client_id = "513010266454814"
        anomalies = validation_service.detect_data_anomalies(client_id, days_back=30)
        
        assert 'inconsistencies' in anomalies
        # Should detect clicks > impressions anomaly
        clicks_anomalies = [a for a in anomalies['inconsistencies'] 
                          if a.get('type') == 'clicks_exceed_impressions']
        assert len(clicks_anomalies) > 0

    def test_validate_aggregation_consistency_no_data(self, validation_service):
        """Test aggregation consistency validation with no data."""
        client_id = "test_client"
        week_start = date.today() - timedelta(days=7)
        
        result = validation_service.validate_aggregation_consistency(client_id, week_start)
        
        assert 'is_consistent' in result
        assert 'daily_count' in result
        assert 'weekly_count' in result
        assert result['daily_count'] == 0
        assert result['weekly_count'] == 0

    def test_get_data_quality_score_no_anomalies(self, validation_service):
        """Test data quality score with no anomalies."""
        client_id = "test_client"
        
        # Mock the detect_data_anomalies method to return no anomalies
        def mock_detect_anomalies(client_id, days_back):
            return {
                'outliers': [],
                'missing_data': [],
                'inconsistencies': [],
                'suspicious_patterns': []
            }
        
        validation_service.detect_data_anomalies = mock_detect_anomalies
        
        result = validation_service.get_data_quality_score(client_id, days_back=30)
        
        assert result['score'] == 100
        assert result['quality_level'] == 'excellent'
        assert result['total_anomalies'] == 0

    def test_get_data_quality_score_with_anomalies(self, validation_service):
        """Test data quality score with various anomalies."""
        client_id = "test_client"
        
        # Mock the detect_data_anomalies method to return anomalies
        def mock_detect_anomalies(client_id, days_back):
            return {
                'outliers': [{'severity': 'high'}, {'severity': 'medium'}],
                'missing_data': [{'severity': 'medium'}],
                'inconsistencies': [{'severity': 'high'}],
                'suspicious_patterns': [{'severity': 'low'}]
            }
        
        validation_service.detect_data_anomalies = mock_detect_anomalies
        
        result = validation_service.get_data_quality_score(client_id, days_back=30)
        
        # Score should be reduced: 100 - (2*10 + 2*5 + 1*1) = 100 - 31 = 69
        assert result['score'] == 69
        assert result['quality_level'] == 'fair'
        assert result['total_anomalies'] == 5
        assert result['anomaly_breakdown']['high_severity'] == 2
        assert result['anomaly_breakdown']['medium_severity'] == 2
        assert result['anomaly_breakdown']['low_severity'] == 1

    def test_get_quality_recommendations(self, validation_service):
        """Test quality recommendations generation."""
        # Test with various anomaly types
        anomalies = {
            'missing_data': [{'type': 'missing_daily_data'}],
            'inconsistencies': [{'type': 'data_mismatch'}],
            'outliers': [{'type': 'high_spend'}],
            'suspicious_patterns': [{'type': 'zero_roas_with_spend'}]
        }
        
        recommendations = validation_service._get_quality_recommendations(anomalies)
        
        assert len(recommendations) >= 4
        assert any('automated daily data sync' in rec.lower() for rec in recommendations)
        assert any('data validation rules' in rec.lower() for rec in recommendations)
        assert any('outlier detection alerts' in rec.lower() for rec in recommendations)
        assert any('zero roas' in rec.lower() for rec in recommendations)

    def test_get_quality_recommendations_no_issues(self, validation_service):
        """Test quality recommendations with no issues."""
        anomalies = {
            'missing_data': [],
            'inconsistencies': [],
            'outliers': [],
            'suspicious_patterns': []
        }
        
        recommendations = validation_service._get_quality_recommendations(anomalies)
        
        assert len(recommendations) == 1
        assert 'excellent' in recommendations[0].lower()

    def test_data_validation_service_initialization(self, db_session):
        """Test DataValidationService initialization."""
        service = DataValidationService(db_session)
        assert service.db == db_session
