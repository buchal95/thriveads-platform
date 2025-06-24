"""
Data validation service for ensuring data quality and consistency
"""

import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.metrics import AdMetrics, CampaignMetrics, WeeklyAdMetrics, MonthlyCampaignMetrics
from app.models.ad import Ad
from app.models.campaign import Campaign

logger = structlog.get_logger()


class DataValidationService:
    """Service for validating and ensuring data quality"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_metrics_data(self, metrics_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate metrics data for consistency and business rules
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields validation
        required_fields = ['impressions', 'clicks', 'spend', 'conversions', 'conversion_value']
        for field in required_fields:
            if field not in metrics_data:
                errors.append(f"Missing required field: {field}")
            elif metrics_data[field] is None:
                errors.append(f"Field {field} cannot be null")
        
        if errors:
            return False, errors
        
        # Data type validation
        try:
            impressions = int(metrics_data['impressions'])
            clicks = int(metrics_data['clicks'])
            spend = float(metrics_data['spend'])
            conversions = int(metrics_data['conversions'])
            conversion_value = float(metrics_data['conversion_value'])
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid data type: {str(e)}")
            return False, errors
        
        # Business logic validation
        if impressions < 0:
            errors.append("Impressions cannot be negative")
        
        if clicks < 0:
            errors.append("Clicks cannot be negative")
        
        if spend < 0:
            errors.append("Spend cannot be negative")
        
        if conversions < 0:
            errors.append("Conversions cannot be negative")
        
        if conversion_value < 0:
            errors.append("Conversion value cannot be negative")
        
        # Logical consistency checks
        if clicks > impressions:
            errors.append("Clicks cannot exceed impressions")
        
        if conversions > clicks:
            errors.append("Conversions cannot exceed clicks")
        
        # CTR validation (if provided)
        if 'ctr' in metrics_data:
            try:
                ctr = float(metrics_data['ctr'])
                if ctr < 0 or ctr > 100:
                    errors.append("CTR must be between 0 and 100")
                
                # Check CTR consistency with impressions/clicks
                if impressions > 0:
                    calculated_ctr = (clicks / impressions) * 100
                    if abs(ctr - calculated_ctr) > 0.1:  # Allow small rounding differences
                        errors.append(f"CTR inconsistent: provided {ctr}, calculated {calculated_ctr:.2f}")
            except (ValueError, TypeError):
                errors.append("Invalid CTR value")
        
        # ROAS validation (if provided)
        if 'roas' in metrics_data:
            try:
                roas = float(metrics_data['roas'])
                if roas < 0:
                    errors.append("ROAS cannot be negative")
                
                # Check ROAS consistency
                if spend > 0:
                    calculated_roas = conversion_value / spend
                    if abs(roas - calculated_roas) > 0.01:  # Allow small rounding differences
                        errors.append(f"ROAS inconsistent: provided {roas}, calculated {calculated_roas:.2f}")
            except (ValueError, TypeError):
                errors.append("Invalid ROAS value")
        
        return len(errors) == 0, errors
    
    def detect_data_anomalies(self, client_id: str, days_back: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect anomalies in recent data
        
        Returns:
            Dictionary of anomaly types and their details
        """
        anomalies = {
            'outliers': [],
            'missing_data': [],
            'inconsistencies': [],
            'suspicious_patterns': []
        }
        
        cutoff_date = date.today() - timedelta(days=days_back)
        
        # Check for outliers in key metrics
        recent_metrics = self.db.query(AdMetrics).filter(
            AdMetrics.date >= cutoff_date
        ).all()
        
        if not recent_metrics:
            anomalies['missing_data'].append({
                'type': 'no_recent_data',
                'message': f'No data found for last {days_back} days',
                'severity': 'high'
            })
            return anomalies
        
        # Calculate statistical thresholds
        spends = [float(m.spend) for m in recent_metrics if m.spend > 0]
        roas_values = [float(m.roas) for m in recent_metrics if m.roas > 0]
        
        if spends:
            avg_spend = sum(spends) / len(spends)
            max_spend = max(spends)
            
            # Check for spend outliers (more than 5x average)
            for metric in recent_metrics:
                if float(metric.spend) > avg_spend * 5:
                    anomalies['outliers'].append({
                        'type': 'high_spend',
                        'ad_id': metric.ad_id,
                        'date': metric.date.isoformat(),
                        'value': float(metric.spend),
                        'threshold': avg_spend * 5,
                        'severity': 'medium'
                    })
        
        if roas_values:
            avg_roas = sum(roas_values) / len(roas_values)
            
            # Check for ROAS outliers
            for metric in recent_metrics:
                if float(metric.roas) > avg_roas * 10:  # Extremely high ROAS
                    anomalies['outliers'].append({
                        'type': 'extremely_high_roas',
                        'ad_id': metric.ad_id,
                        'date': metric.date.isoformat(),
                        'value': float(metric.roas),
                        'threshold': avg_roas * 10,
                        'severity': 'low'  # High ROAS is good, but worth noting
                    })
                elif float(metric.roas) == 0 and float(metric.spend) > 0:
                    anomalies['suspicious_patterns'].append({
                        'type': 'zero_roas_with_spend',
                        'ad_id': metric.ad_id,
                        'date': metric.date.isoformat(),
                        'spend': float(metric.spend),
                        'severity': 'medium'
                    })
        
        # Check for missing daily data
        expected_dates = []
        current_date = cutoff_date
        while current_date <= date.today() - timedelta(days=1):
            expected_dates.append(current_date)
            current_date += timedelta(days=1)
        
        actual_dates = set(m.date for m in recent_metrics)
        missing_dates = [d for d in expected_dates if d not in actual_dates]
        
        for missing_date in missing_dates:
            anomalies['missing_data'].append({
                'type': 'missing_daily_data',
                'date': missing_date.isoformat(),
                'severity': 'medium'
            })
        
        # Check for data inconsistencies
        for metric in recent_metrics:
            if metric.clicks > metric.impressions:
                anomalies['inconsistencies'].append({
                    'type': 'clicks_exceed_impressions',
                    'ad_id': metric.ad_id,
                    'date': metric.date.isoformat(),
                    'clicks': metric.clicks,
                    'impressions': metric.impressions,
                    'severity': 'high'
                })
            
            if metric.conversions > metric.clicks:
                anomalies['inconsistencies'].append({
                    'type': 'conversions_exceed_clicks',
                    'ad_id': metric.ad_id,
                    'date': metric.date.isoformat(),
                    'conversions': metric.conversions,
                    'clicks': metric.clicks,
                    'severity': 'high'
                })
        
        return anomalies
    
    def validate_aggregation_consistency(self, client_id: str, week_start: date) -> Dict[str, Any]:
        """
        Validate that weekly aggregations match sum of daily data
        """
        week_end = week_start + timedelta(days=6)
        
        # Get daily metrics for the week
        daily_metrics = self.db.query(AdMetrics).filter(
            and_(
                AdMetrics.date >= week_start,
                AdMetrics.date <= week_end
            )
        ).all()
        
        # Get weekly aggregations
        weekly_metrics = self.db.query(WeeklyAdMetrics).filter(
            WeeklyAdMetrics.week_start_date == week_start
        ).all()
        
        validation_results = {
            'is_consistent': True,
            'discrepancies': [],
            'daily_count': len(daily_metrics),
            'weekly_count': len(weekly_metrics)
        }
        
        # Group daily metrics by ad_id and attribution
        daily_by_ad = {}
        for metric in daily_metrics:
            key = f"{metric.ad_id}_{metric.attribution}"
            if key not in daily_by_ad:
                daily_by_ad[key] = {
                    'impressions': 0,
                    'clicks': 0,
                    'spend': Decimal('0'),
                    'conversions': 0,
                    'conversion_value': Decimal('0')
                }
            
            daily_by_ad[key]['impressions'] += metric.impressions
            daily_by_ad[key]['clicks'] += metric.clicks
            daily_by_ad[key]['spend'] += metric.spend
            daily_by_ad[key]['conversions'] += metric.conversions
            daily_by_ad[key]['conversion_value'] += metric.conversion_value
        
        # Compare with weekly aggregations
        for weekly_metric in weekly_metrics:
            key = f"{weekly_metric.ad_id}_{weekly_metric.attribution}"
            
            if key not in daily_by_ad:
                validation_results['discrepancies'].append({
                    'type': 'weekly_without_daily',
                    'ad_id': weekly_metric.ad_id,
                    'attribution': weekly_metric.attribution
                })
                validation_results['is_consistent'] = False
                continue
            
            daily_totals = daily_by_ad[key]
            
            # Check each metric
            tolerance = 0.01  # Allow small rounding differences
            
            if abs(weekly_metric.impressions - daily_totals['impressions']) > tolerance:
                validation_results['discrepancies'].append({
                    'type': 'impressions_mismatch',
                    'ad_id': weekly_metric.ad_id,
                    'weekly': weekly_metric.impressions,
                    'daily_sum': daily_totals['impressions']
                })
                validation_results['is_consistent'] = False
            
            if abs(float(weekly_metric.spend) - float(daily_totals['spend'])) > tolerance:
                validation_results['discrepancies'].append({
                    'type': 'spend_mismatch',
                    'ad_id': weekly_metric.ad_id,
                    'weekly': float(weekly_metric.spend),
                    'daily_sum': float(daily_totals['spend'])
                })
                validation_results['is_consistent'] = False
        
        return validation_results
    
    def get_data_quality_score(self, client_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Calculate overall data quality score
        """
        anomalies = self.detect_data_anomalies(client_id, days_back)
        
        # Count anomalies by severity
        high_severity = sum(1 for category in anomalies.values() 
                          for anomaly in category if anomaly.get('severity') == 'high')
        medium_severity = sum(1 for category in anomalies.values() 
                            for anomaly in category if anomaly.get('severity') == 'medium')
        low_severity = sum(1 for category in anomalies.values() 
                         for anomaly in category if anomaly.get('severity') == 'low')
        
        total_anomalies = high_severity + medium_severity + low_severity
        
        # Calculate score (100 - penalty for anomalies)
        penalty = (high_severity * 10) + (medium_severity * 5) + (low_severity * 1)
        score = max(0, 100 - penalty)
        
        # Determine quality level
        if score >= 90:
            quality_level = "excellent"
        elif score >= 75:
            quality_level = "good"
        elif score >= 60:
            quality_level = "fair"
        else:
            quality_level = "poor"
        
        return {
            'score': score,
            'quality_level': quality_level,
            'total_anomalies': total_anomalies,
            'anomaly_breakdown': {
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity
            },
            'recommendations': self._get_quality_recommendations(anomalies)
        }
    
    def _get_quality_recommendations(self, anomalies: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate recommendations based on detected anomalies"""
        recommendations = []
        
        if anomalies['missing_data']:
            recommendations.append("Set up automated daily data sync to prevent missing data")
        
        if anomalies['inconsistencies']:
            recommendations.append("Review data validation rules and Meta API response handling")
        
        if anomalies['outliers']:
            recommendations.append("Implement outlier detection alerts for unusual spending patterns")
        
        if anomalies['suspicious_patterns']:
            recommendations.append("Investigate ads with zero ROAS but positive spend")
        
        if not any(anomalies.values()):
            recommendations.append("Data quality is excellent - maintain current processes")
        
        return recommendations
