"""
Database Service for querying stored Meta API data

This service provides methods to query the database for analytics data
instead of making live Meta API calls.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.campaign import Campaign
from app.models.ad import Ad
from app.models.metrics import CampaignMetrics, AdMetrics
from app.models.client import Client

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for querying stored analytics data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_top_performing_ads(
        self,
        client_id: str,
        start_date: date,
        end_date: date,
        attribution: str = "default",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top performing ads from database"""
        
        # Query ads with aggregated metrics for the date range
        query = (
            self.db.query(
                Ad.id,
                Ad.name,
                Ad.status,
                Campaign.name.label('campaign_name'),
                func.sum(AdMetrics.spend).label('total_spend'),
                func.sum(AdMetrics.impressions).label('total_impressions'),
                func.sum(AdMetrics.clicks).label('total_clicks'),
                func.sum(AdMetrics.conversions).label('total_conversions'),
                func.sum(AdMetrics.conversion_value).label('total_conversion_value'),
                func.avg(AdMetrics.ctr).label('avg_ctr'),
                func.avg(AdMetrics.cpc).label('avg_cpc'),
                func.avg(AdMetrics.cpm).label('avg_cpm'),
                func.avg(AdMetrics.frequency).label('avg_frequency')
            )
            .join(AdMetrics, Ad.id == AdMetrics.ad_id)
            .join(Campaign, Ad.campaign_id == Campaign.id)
            .filter(
                and_(
                    Campaign.client_id == f"client_{client_id}",
                    AdMetrics.date >= start_date,
                    AdMetrics.date <= end_date,
                    AdMetrics.attribution == attribution
                )
            )
            .group_by(Ad.id, Ad.name, Ad.status, Campaign.name)
            .having(func.sum(AdMetrics.spend) > 0)
        )
        
        results = query.all()
        
        # Convert to list of dicts and calculate ROAS
        ads = []
        for result in results:
            spend = float(result.total_spend or 0)
            conversion_value = float(result.total_conversion_value or 0)
            roas = conversion_value / spend if spend > 0 else 0
            
            ad_data = {
                "id": result.id,
                "name": result.name,
                "status": result.status or "ACTIVE",
                "campaign_name": result.campaign_name,
                "facebook_url": f"https://www.facebook.com/ads/library/?id={result.id}&search_type=all&media_type=all",
                "metrics": {
                    "impressions": int(result.total_impressions or 0),
                    "clicks": int(result.total_clicks or 0),
                    "spend": spend,
                    "conversions": int(result.total_conversions or 0),
                    "ctr": float(result.avg_ctr or 0),
                    "cpc": float(result.avg_cpc or 0),
                    "cpm": float(result.avg_cpm or 0),
                    "roas": roas,
                    "frequency": float(result.avg_frequency or 0)
                },
                "currency": "CZK",
                "attribution": attribution
            }
            ads.append(ad_data)
        
        # Sort by ROAS and return top performers
        ads.sort(key=lambda x: x["metrics"]["roas"], reverse=True)
        return ads[:limit]
    
    def get_top_performing_campaigns(
        self,
        client_id: str,
        start_date: date,
        end_date: date,
        attribution: str = "default",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top performing campaigns from database"""
        
        # Query campaigns with aggregated metrics for the date range
        query = (
            self.db.query(
                Campaign.id,
                Campaign.name,
                Campaign.status,
                func.sum(CampaignMetrics.spend).label('total_spend'),
                func.sum(CampaignMetrics.impressions).label('total_impressions'),
                func.sum(CampaignMetrics.clicks).label('total_clicks'),
                func.sum(CampaignMetrics.conversions).label('total_conversions'),
                func.sum(CampaignMetrics.conversion_value).label('total_conversion_value'),
                func.avg(CampaignMetrics.ctr).label('avg_ctr'),
                func.avg(CampaignMetrics.cpc).label('avg_cpc'),
                func.avg(CampaignMetrics.cpm).label('avg_cpm'),
                func.avg(CampaignMetrics.frequency).label('avg_frequency')
            )
            .join(CampaignMetrics, Campaign.id == CampaignMetrics.campaign_id)
            .filter(
                and_(
                    Campaign.client_id == f"client_{client_id}",
                    CampaignMetrics.date >= start_date,
                    CampaignMetrics.date <= end_date,
                    CampaignMetrics.attribution == attribution
                )
            )
            .group_by(Campaign.id, Campaign.name, Campaign.status)
            .having(func.sum(CampaignMetrics.spend) > 0)
        )
        
        results = query.all()
        
        # Convert to list of dicts and calculate ROAS
        campaigns = []
        for result in results:
            spend = float(result.total_spend or 0)
            conversion_value = float(result.total_conversion_value or 0)
            roas = conversion_value / spend if spend > 0 else 0
            
            campaign_data = {
                "id": result.id,
                "name": result.name,
                "status": result.status or "active",
                "metrics": {
                    "impressions": int(result.total_impressions or 0),
                    "clicks": int(result.total_clicks or 0),
                    "spend": spend,
                    "conversions": int(result.total_conversions or 0),
                    "conversion_value": conversion_value,
                    "ctr": float(result.avg_ctr or 0),
                    "cpc": float(result.avg_cpc or 0),
                    "cpm": float(result.avg_cpm or 0),
                    "roas": roas,
                    "frequency": float(result.avg_frequency or 0)
                },
                "currency": "CZK",
                "attribution": attribution
            }
            campaigns.append(campaign_data)
        
        # Sort by ROAS and return top performers
        campaigns.sort(key=lambda x: x["metrics"]["roas"], reverse=True)
        return campaigns[:limit]
    
    def get_week_on_week_comparison(
        self,
        client_id: str,
        current_week_start: date,
        current_week_end: date,
        previous_week_start: date,
        previous_week_end: date
    ) -> Dict[str, Any]:
        """Get week-on-week comparison from database"""
        
        # Get current week metrics (aggregated across all campaigns)
        current_week_query = (
            self.db.query(
                func.sum(CampaignMetrics.spend).label('spend'),
                func.sum(CampaignMetrics.impressions).label('impressions'),
                func.sum(CampaignMetrics.clicks).label('clicks'),
                func.sum(CampaignMetrics.conversions).label('conversions'),
                func.sum(CampaignMetrics.conversion_value).label('conversion_value'),
                func.avg(CampaignMetrics.ctr).label('ctr'),
                func.avg(CampaignMetrics.cpc).label('cpc'),
                func.avg(CampaignMetrics.cpm).label('cpm'),
                func.avg(CampaignMetrics.frequency).label('frequency')
            )
            .join(Campaign, CampaignMetrics.campaign_id == Campaign.id)
            .filter(
                and_(
                    Campaign.client_id == f"client_{client_id}",
                    CampaignMetrics.date >= current_week_start,
                    CampaignMetrics.date <= current_week_end
                )
            )
        ).first()
        
        # Get previous week metrics
        previous_week_query = (
            self.db.query(
                func.sum(CampaignMetrics.spend).label('spend'),
                func.sum(CampaignMetrics.impressions).label('impressions'),
                func.sum(CampaignMetrics.clicks).label('clicks'),
                func.sum(CampaignMetrics.conversions).label('conversions'),
                func.sum(CampaignMetrics.conversion_value).label('conversion_value'),
                func.avg(CampaignMetrics.ctr).label('ctr'),
                func.avg(CampaignMetrics.cpc).label('cpc'),
                func.avg(CampaignMetrics.cpm).label('cpm'),
                func.avg(CampaignMetrics.frequency).label('frequency')
            )
            .join(Campaign, CampaignMetrics.campaign_id == Campaign.id)
            .filter(
                and_(
                    Campaign.client_id == f"client_{client_id}",
                    CampaignMetrics.date >= previous_week_start,
                    CampaignMetrics.date <= previous_week_end
                )
            )
        ).first()
        
        # Extract metrics
        def extract_metrics(result):
            if not result or not result.spend:
                return {
                    'spend': 0, 'roas': 0, 'conversions': 0, 'ctr': 0,
                    'cpc': 0, 'cpm': 0, 'frequency': 0, 'impressions': 0,
                    'clicks': 0, 'reach': 0
                }
            
            spend = float(result.spend or 0)
            conversion_value = float(result.conversion_value or 0)
            impressions = int(result.impressions or 0)
            roas = conversion_value / spend if spend > 0 else 0
            
            return {
                'spend': spend,
                'roas': roas,
                'conversions': int(result.conversions or 0),
                'ctr': float(result.ctr or 0),
                'cpc': float(result.cpc or 0),
                'cpm': float(result.cpm or 0),
                'frequency': float(result.frequency or 0),
                'impressions': impressions,
                'clicks': int(result.clicks or 0),
                'reach': int(impressions / max(result.frequency or 1, 1))  # Estimate reach
            }
        
        current_metrics = extract_metrics(current_week_query)
        previous_metrics = extract_metrics(previous_week_query)
        
        # Calculate percentage changes
        metrics_comparison = {}
        for metric in ['spend', 'roas', 'conversions', 'ctr', 'cpc', 'cpm', 'frequency', 'impressions', 'clicks', 'reach']:
            current_value = current_metrics.get(metric, 0)
            previous_value = previous_metrics.get(metric, 0)
            
            if previous_value > 0:
                change = ((current_value - previous_value) / previous_value) * 100
            else:
                change = 100.0 if current_value > 0 else 0.0
            
            metrics_comparison[f"{metric}_change"] = round(change, 2)
        
        return {
            "client_id": client_id,
            "current_week": {
                "start_date": current_week_start.isoformat(),
                "end_date": current_week_end.isoformat(),
                "metrics": current_metrics
            },
            "previous_week": {
                "start_date": previous_week_start.isoformat(),
                "end_date": previous_week_end.isoformat(),
                "metrics": previous_metrics
            },
            "metrics_comparison": metrics_comparison,
            "currency": "CZK"
        }

    def get_conversion_funnel(
        self,
        client_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get conversion funnel data from database"""

        # Aggregate metrics across all campaigns for the period
        result = (
            self.db.query(
                func.sum(CampaignMetrics.impressions).label('impressions'),
                func.sum(CampaignMetrics.clicks).label('clicks'),
                func.sum(CampaignMetrics.conversions).label('conversions')
            )
            .join(Campaign, CampaignMetrics.campaign_id == Campaign.id)
            .filter(
                and_(
                    Campaign.client_id == f"client_{client_id}",
                    CampaignMetrics.date >= start_date,
                    CampaignMetrics.date <= end_date
                )
            )
        ).first()

        if not result or not result.impressions:
            # Return empty funnel if no data
            return {
                "client_id": client_id,
                "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
                "funnel_stages": [
                    {"stage": "Impressions", "count": 0, "conversion_rate": 100.0},
                    {"stage": "Clicks", "count": 0, "conversion_rate": 0.0},
                    {"stage": "Landing Page Views", "count": 0, "conversion_rate": 0.0},
                    {"stage": "Add to Cart", "count": 0, "conversion_rate": 0.0},
                    {"stage": "Purchase", "count": 0, "conversion_rate": 0.0}
                ],
                "currency": "CZK"
            }

        impressions = int(result.impressions or 0)
        clicks = int(result.clicks or 0)
        purchases = int(result.conversions or 0)

        # Estimate intermediate funnel stages (these would need more detailed tracking)
        landing_page_views = int(clicks * 0.85)  # Estimate 85% of clicks reach landing page
        add_to_cart = int(purchases * 1.8)  # Estimate add-to-cart is ~1.8x purchases

        # Calculate conversion rates
        funnel_stages = [
            {
                "stage": "Impressions",
                "count": impressions,
                "conversion_rate": 100.0
            },
            {
                "stage": "Clicks",
                "count": clicks,
                "conversion_rate": (clicks / impressions * 100) if impressions > 0 else 0
            },
            {
                "stage": "Landing Page Views",
                "count": landing_page_views,
                "conversion_rate": (landing_page_views / clicks * 100) if clicks > 0 else 0
            },
            {
                "stage": "Add to Cart",
                "count": add_to_cart,
                "conversion_rate": (add_to_cart / landing_page_views * 100) if landing_page_views > 0 else 0
            },
            {
                "stage": "Purchase",
                "count": purchases,
                "conversion_rate": (purchases / add_to_cart * 100) if add_to_cart > 0 else 0
            }
        ]

        return {
            "client_id": client_id,
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "funnel_stages": funnel_stages,
            "currency": "CZK"
        }

    def get_daily_breakdown(
        self,
        client_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get daily breakdown metrics from database"""

        # Query daily aggregated metrics
        query = (
            self.db.query(
                CampaignMetrics.date,
                func.sum(CampaignMetrics.spend).label('spend'),
                func.sum(CampaignMetrics.impressions).label('impressions'),
                func.sum(CampaignMetrics.clicks).label('clicks'),
                func.sum(CampaignMetrics.conversions).label('conversions'),
                func.sum(CampaignMetrics.conversion_value).label('conversion_value'),
                func.avg(CampaignMetrics.ctr).label('ctr'),
                func.avg(CampaignMetrics.cpc).label('cpc'),
                func.avg(CampaignMetrics.cpm).label('cpm'),
                func.avg(CampaignMetrics.frequency).label('frequency')
            )
            .join(Campaign, CampaignMetrics.campaign_id == Campaign.id)
            .filter(
                and_(
                    Campaign.client_id == f"client_{client_id}",
                    CampaignMetrics.date >= start_date,
                    CampaignMetrics.date <= end_date
                )
            )
            .group_by(CampaignMetrics.date)
            .order_by(CampaignMetrics.date)
        )

        results = query.all()

        # Convert to list of dicts
        daily_data = []
        for result in results:
            spend = float(result.spend or 0)
            conversion_value = float(result.conversion_value or 0)
            roas = conversion_value / spend if spend > 0 else 0

            daily_data.append({
                "date": result.date.isoformat(),
                "metrics": {
                    "spend": spend,
                    "impressions": int(result.impressions or 0),
                    "clicks": int(result.clicks or 0),
                    "conversions": int(result.conversions or 0),
                    "conversion_value": conversion_value,
                    "ctr": float(result.ctr or 0),
                    "cpc": float(result.cpc or 0),
                    "cpm": float(result.cpm or 0),
                    "roas": roas,
                    "frequency": float(result.frequency or 0)
                }
            })

        return daily_data
