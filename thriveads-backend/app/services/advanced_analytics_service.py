"""
Advanced analytics service for complex calculations and insights
"""

import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import statistics
import numpy as np

from app.models.metrics import AdMetrics, CampaignMetrics, WeeklyAdMetrics, MonthlyCampaignMetrics
from app.models.ad import Ad
from app.models.campaign import Campaign

logger = structlog.get_logger()


class AdvancedAnalyticsService:
    """Service for advanced analytics calculations and insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_trend_analysis(self, client_id: str, metric: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate trend analysis for a specific metric over time
        
        Args:
            client_id: Client ID
            metric: Metric to analyze (spend, roas, conversions, etc.)
            days: Number of days to analyze
        
        Returns:
            Trend analysis with direction, strength, and predictions
        """
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        # Get daily aggregated data
        daily_data = self.db.query(
            AdMetrics.date,
            func.sum(getattr(AdMetrics, metric)).label('value')
        ).filter(
            and_(
                AdMetrics.date >= start_date,
                AdMetrics.date <= end_date
            )
        ).group_by(AdMetrics.date).order_by(AdMetrics.date).all()
        
        if len(daily_data) < 7:
            return {
                'trend': 'insufficient_data',
                'message': 'Not enough data for trend analysis'
            }
        
        # Extract values and dates
        dates = [d.date for d in daily_data]
        values = [float(d.value) if d.value else 0 for d in daily_data]
        
        # Calculate trend using linear regression
        x = list(range(len(values)))
        slope, intercept = np.polyfit(x, values, 1)
        
        # Calculate trend strength (R-squared)
        y_pred = [slope * i + intercept for i in x]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(len(values)))
        ss_tot = sum((values[i] - statistics.mean(values)) ** 2 for i in range(len(values)))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction and strength
        if abs(slope) < 0.01:
            trend_direction = 'stable'
        elif slope > 0:
            trend_direction = 'increasing'
        else:
            trend_direction = 'decreasing'
        
        if r_squared > 0.7:
            trend_strength = 'strong'
        elif r_squared > 0.4:
            trend_strength = 'moderate'
        else:
            trend_strength = 'weak'
        
        # Calculate percentage change
        if len(values) >= 2:
            first_week_avg = statistics.mean(values[:7])
            last_week_avg = statistics.mean(values[-7:])
            percent_change = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg != 0 else 0
        else:
            percent_change = 0
        
        # Predict next 7 days
        predictions = []
        for i in range(len(values), len(values) + 7):
            predicted_value = slope * i + intercept
            predictions.append(max(0, predicted_value))  # Ensure non-negative
        
        return {
            'metric': metric,
            'period_days': days,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'r_squared': round(r_squared, 3),
            'slope': round(slope, 4),
            'percent_change': round(percent_change, 2),
            'current_value': values[-1] if values else 0,
            'average_value': round(statistics.mean(values), 2) if values else 0,
            'predictions_7_days': [round(p, 2) for p in predictions],
            'data_points': len(values)
        }
    
    def calculate_cohort_analysis(self, client_id: str, start_date: date, cohort_type: str = 'weekly') -> Dict[str, Any]:
        """
        Calculate cohort analysis for ad performance over time
        
        Args:
            client_id: Client ID
            start_date: Start date for cohort analysis
            cohort_type: 'weekly' or 'monthly'
        
        Returns:
            Cohort analysis data
        """
        if cohort_type == 'weekly':
            period_days = 7
            periods = 12  # 12 weeks
        else:
            period_days = 30
            periods = 6   # 6 months
        
        cohorts = []
        
        for period in range(periods):
            cohort_start = start_date + timedelta(days=period * period_days)
            cohort_end = cohort_start + timedelta(days=period_days - 1)
            
            # Get ads that started in this cohort period
            cohort_ads = self.db.query(Ad.id).filter(
                and_(
                    Ad.created_at >= cohort_start,
                    Ad.created_at <= cohort_end
                )
            ).all()
            
            if not cohort_ads:
                continue
            
            ad_ids = [ad.id for ad in cohort_ads]
            
            # Calculate performance for each subsequent period
            performance_periods = []
            for perf_period in range(periods - period):
                perf_start = cohort_start + timedelta(days=perf_period * period_days)
                perf_end = perf_start + timedelta(days=period_days - 1)
                
                metrics = self.db.query(
                    func.sum(AdMetrics.spend).label('total_spend'),
                    func.sum(AdMetrics.conversions).label('total_conversions'),
                    func.sum(AdMetrics.conversion_value).label('total_conversion_value'),
                    func.avg(AdMetrics.roas).label('avg_roas')
                ).filter(
                    and_(
                        AdMetrics.ad_id.in_(ad_ids),
                        AdMetrics.date >= perf_start,
                        AdMetrics.date <= perf_end
                    )
                ).first()
                
                performance_periods.append({
                    'period': perf_period,
                    'start_date': perf_start.isoformat(),
                    'end_date': perf_end.isoformat(),
                    'total_spend': float(metrics.total_spend) if metrics.total_spend else 0,
                    'total_conversions': int(metrics.total_conversions) if metrics.total_conversions else 0,
                    'total_conversion_value': float(metrics.total_conversion_value) if metrics.total_conversion_value else 0,
                    'avg_roas': float(metrics.avg_roas) if metrics.avg_roas else 0
                })
            
            cohorts.append({
                'cohort_period': period,
                'cohort_start': cohort_start.isoformat(),
                'cohort_end': cohort_end.isoformat(),
                'ad_count': len(ad_ids),
                'performance': performance_periods
            })
        
        return {
            'cohort_type': cohort_type,
            'start_date': start_date.isoformat(),
            'cohorts': cohorts
        }
    
    def calculate_attribution_comparison(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Compare performance across different attribution models
        """
        attributions = ['default', '7d_click']
        comparison = {}
        
        for attribution in attributions:
            metrics = self.db.query(
                func.sum(AdMetrics.impressions).label('total_impressions'),
                func.sum(AdMetrics.clicks).label('total_clicks'),
                func.sum(AdMetrics.spend).label('total_spend'),
                func.sum(AdMetrics.conversions).label('total_conversions'),
                func.sum(AdMetrics.conversion_value).label('total_conversion_value'),
                func.avg(AdMetrics.roas).label('avg_roas'),
                func.avg(AdMetrics.ctr).label('avg_ctr')
            ).filter(
                and_(
                    AdMetrics.date >= start_date,
                    AdMetrics.date <= end_date,
                    AdMetrics.attribution == attribution
                )
            ).first()
            
            comparison[attribution] = {
                'impressions': int(metrics.total_impressions) if metrics.total_impressions else 0,
                'clicks': int(metrics.total_clicks) if metrics.total_clicks else 0,
                'spend': float(metrics.total_spend) if metrics.total_spend else 0,
                'conversions': int(metrics.total_conversions) if metrics.total_conversions else 0,
                'conversion_value': float(metrics.total_conversion_value) if metrics.total_conversion_value else 0,
                'avg_roas': float(metrics.avg_roas) if metrics.avg_roas else 0,
                'avg_ctr': float(metrics.avg_ctr) if metrics.avg_ctr else 0
            }
        
        # Calculate differences
        if 'default' in comparison and '7d_click' in comparison:
            default_data = comparison['default']
            seven_day_data = comparison['7d_click']
            
            differences = {}
            for metric in ['conversions', 'conversion_value', 'avg_roas']:
                default_val = default_data[metric]
                seven_day_val = seven_day_data[metric]
                
                if default_val != 0:
                    diff_percent = ((seven_day_val - default_val) / default_val) * 100
                else:
                    diff_percent = 100 if seven_day_val > 0 else 0
                
                differences[f'{metric}_difference_percent'] = round(diff_percent, 2)
            
            comparison['attribution_impact'] = differences
        
        return comparison
    
    def calculate_seasonal_patterns(self, client_id: str, metric: str = 'spend', months: int = 12) -> Dict[str, Any]:
        """
        Analyze seasonal patterns in the data
        """
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=months * 30)
        
        # Get daily data
        daily_data = self.db.query(
            AdMetrics.date,
            func.sum(getattr(AdMetrics, metric)).label('value')
        ).filter(
            and_(
                AdMetrics.date >= start_date,
                AdMetrics.date <= end_date
            )
        ).group_by(AdMetrics.date).order_by(AdMetrics.date).all()
        
        if len(daily_data) < 30:
            return {'error': 'Insufficient data for seasonal analysis'}
        
        # Group by day of week
        day_of_week_data = {}
        for d in daily_data:
            dow = d.date.weekday()  # 0 = Monday, 6 = Sunday
            if dow not in day_of_week_data:
                day_of_week_data[dow] = []
            day_of_week_data[dow].append(float(d.value) if d.value else 0)
        
        day_of_week_avg = {}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for dow in range(7):
            if dow in day_of_week_data:
                day_of_week_avg[day_names[dow]] = round(statistics.mean(day_of_week_data[dow]), 2)
            else:
                day_of_week_avg[day_names[dow]] = 0
        
        # Group by month
        month_data = {}
        for d in daily_data:
            month = d.date.month
            if month not in month_data:
                month_data[month] = []
            month_data[month].append(float(d.value) if d.value else 0)
        
        month_avg = {}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for month in range(1, 13):
            if month in month_data:
                month_avg[month_names[month-1]] = round(statistics.mean(month_data[month]), 2)
            else:
                month_avg[month_names[month-1]] = 0
        
        # Find best and worst performing days/months
        best_day = max(day_of_week_avg, key=day_of_week_avg.get)
        worst_day = min(day_of_week_avg, key=day_of_week_avg.get)
        best_month = max(month_avg, key=month_avg.get)
        worst_month = min(month_avg, key=month_avg.get)
        
        return {
            'metric': metric,
            'analysis_period_months': months,
            'day_of_week_patterns': day_of_week_avg,
            'monthly_patterns': month_avg,
            'insights': {
                'best_day_of_week': best_day,
                'worst_day_of_week': worst_day,
                'best_month': best_month,
                'worst_month': worst_month,
                'day_variation_percent': round(
                    ((day_of_week_avg[best_day] - day_of_week_avg[worst_day]) / 
                     day_of_week_avg[worst_day] * 100) if day_of_week_avg[worst_day] > 0 else 0, 2
                ),
                'month_variation_percent': round(
                    ((month_avg[best_month] - month_avg[worst_month]) / 
                     month_avg[worst_month] * 100) if month_avg[worst_month] > 0 else 0, 2
                )
            }
        }
    
    def calculate_efficiency_metrics(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Calculate advanced efficiency metrics
        """
        # Get all metrics for the period
        metrics = self.db.query(AdMetrics).filter(
            and_(
                AdMetrics.date >= start_date,
                AdMetrics.date <= end_date
            )
        ).all()
        
        if not metrics:
            return {'error': 'No data available for the specified period'}
        
        # Calculate efficiency metrics
        total_spend = sum(float(m.spend) for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        total_conversion_value = sum(float(m.conversion_value) for m in metrics)
        total_impressions = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        
        # Cost per acquisition (CPA)
        cpa = total_spend / total_conversions if total_conversions > 0 else 0
        
        # Return on ad spend (ROAS)
        roas = total_conversion_value / total_spend if total_spend > 0 else 0
        
        # Click-through rate (CTR)
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        # Conversion rate
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        # Cost per click (CPC)
        cpc = total_spend / total_clicks if total_clicks > 0 else 0
        
        # Cost per mille (CPM)
        cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        
        # Efficiency score (custom metric combining multiple factors)
        # Higher ROAS, lower CPA, higher conversion rate = better efficiency
        efficiency_score = 0
        if roas > 0:
            efficiency_score += min(roas * 10, 50)  # Max 50 points for ROAS
        if cpa > 0:
            efficiency_score += max(0, 30 - cpa)  # Max 30 points for low CPA
        if conversion_rate > 0:
            efficiency_score += min(conversion_rate * 2, 20)  # Max 20 points for conversion rate
        
        efficiency_score = min(100, efficiency_score)  # Cap at 100
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'totals': {
                'spend': round(total_spend, 2),
                'conversions': total_conversions,
                'conversion_value': round(total_conversion_value, 2),
                'impressions': total_impressions,
                'clicks': total_clicks
            },
            'efficiency_metrics': {
                'cpa': round(cpa, 2),
                'roas': round(roas, 2),
                'ctr': round(ctr, 2),
                'conversion_rate': round(conversion_rate, 2),
                'cpc': round(cpc, 2),
                'cpm': round(cpm, 2),
                'efficiency_score': round(efficiency_score, 1)
            },
            'benchmarks': {
                'excellent_roas': 4.0,
                'good_roas': 2.0,
                'excellent_ctr': 2.0,
                'good_ctr': 1.0,
                'excellent_conversion_rate': 5.0,
                'good_conversion_rate': 2.0
            }
        }
