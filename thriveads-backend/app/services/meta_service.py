"""
Meta Marketing API service for fetching advertising data
"""

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adsinsights import AdsInsights
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import structlog

from app.core.config import settings
from app.schemas.ad import AdPerformance, AdMetrics

logger = structlog.get_logger()


class MetaService:
    """Service for interacting with Meta Marketing API"""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize Meta API service"""
        self.access_token = access_token or settings.META_ACCESS_TOKEN
        self.api_version = settings.META_API_VERSION

        # Initialize Facebook Ads API with just access token
        FacebookAdsApi.init(
            access_token=self.access_token,
            api_version=self.api_version
        )
    
    async def get_top_performing_ads(
        self,
        client_id: str,
        start_date: date,
        end_date: date,
        attribution: str = "default",
        limit: int = 10
    ) -> List[AdPerformance]:
        """
        Get top performing ads for a client based on ROAS
        
        Args:
            client_id: Meta ad account ID
            start_date: Start date for the period
            end_date: End date for the period
            attribution: Attribution model (default, 7d_click)
            limit: Number of top ads to return
        
        Returns:
            List of top performing ads with metrics
        """
        try:
            # Get ad account
            ad_account = AdAccount(f"act_{client_id}")
            
            # Define insights parameters based on attribution model
            insights_params = {
                'time_range': {
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                },
                'level': 'ad',
                'breakdowns': [],
                'limit': limit * 2,  # Fetch more to account for filtering
            }
            
            # Set attribution window based on parameter
            if attribution == "7d_click":
                insights_params['action_attribution_windows'] = ['7d_click']
            
            # Define metrics to fetch
            insights_fields = [
                'ad_id',
                'ad_name',
                'campaign_name',
                'adset_name',
                'impressions',
                'clicks',
                'spend',
                'actions',
                'action_values',
                'ctr',
                'cpc',
                'cpm',
                'frequency',
                'account_currency'
            ]
            
            # Fetch ads with insights
            ads_insights = ad_account.get_insights(
                fields=insights_fields,
                params=insights_params
            )
            
            # Process and rank ads by ROAS
            top_ads = []
            for insight in ads_insights:
                try:
                    ad_performance = self._process_ad_insight(insight, attribution)
                    if ad_performance and ad_performance.metrics.roas > 0:
                        top_ads.append(ad_performance)
                except Exception as e:
                    logger.warning(f"Error processing ad insight: {e}")
                    continue
            
            # Sort by ROAS and return top performers
            top_ads.sort(key=lambda x: x.metrics.roas, reverse=True)
            return top_ads[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching top performing ads: {e}")
            raise

    def _process_ad_insight(self, insight: Dict[str, Any], attribution: str) -> Optional[AdPerformance]:
        """Process a single ad insight into AdPerformance object"""
        try:
            # Extract basic ad information
            ad_id = insight.get('ad_id')
            ad_name = insight.get('ad_name', '')
            campaign_name = insight.get('campaign_name', '')
            adset_name = insight.get('adset_name', '')

            # Extract metrics
            impressions = int(insight.get('impressions', 0))
            clicks = int(insight.get('clicks', 0))
            spend = Decimal(str(insight.get('spend', 0)))
            ctr = float(insight.get('ctr', 0))
            cpc = Decimal(str(insight.get('cpc', 0)))
            cpm = Decimal(str(insight.get('cpm', 0)))
            frequency = float(insight.get('frequency', 0))

            # Extract conversions and conversion value
            conversions = 0
            conversion_value = Decimal('0')

            actions = insight.get('actions', [])
            action_values = insight.get('action_values', [])

            # Sum up purchase conversions
            for action in actions:
                if action.get('action_type') == 'purchase':
                    conversions += int(action.get('value', 0))

            # Sum up purchase values
            for action_value in action_values:
                if action_value.get('action_type') == 'purchase':
                    conversion_value += Decimal(str(action_value.get('value', 0)))

            # Calculate ROAS
            roas = float(conversion_value / spend) if spend > 0 else 0

            # Create metrics object
            metrics = AdMetrics(
                impressions=impressions,
                clicks=clicks,
                spend=spend,
                conversions=conversions,
                conversion_value=conversion_value,
                ctr=ctr,
                cpc=cpc,
                cpm=cpm,
                roas=roas,
                frequency=frequency
            )

            # Generate Facebook URL (simplified - would need actual post ID in production)
            facebook_url = f"https://www.facebook.com/ads/manager/reporting/view?act={insight.get('account_id', '')}&selected_report_id={ad_id}"

            return AdPerformance(
                id=ad_id,
                name=ad_name,
                status=insight.get('ad_delivery_info', {}).get('delivery_status', 'unknown'),
                campaign_name=campaign_name,
                adset_name=adset_name,
                facebook_url=facebook_url,
                metrics=metrics,
                currency=insight.get('account_currency', 'CZK'),
                attribution=attribution
            )

        except Exception as e:
            logger.error(f"Error processing ad insight: {e}")
            return None

    async def get_ad_performance_history(
        self,
        ad_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get historical performance data for a specific ad"""
        try:
            ad = Ad(ad_id)

            insights_params = {
                'time_range': {
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                },
                'time_increment': 1,  # Daily data
                'level': 'ad',
            }

            insights_fields = [
                'date_start',
                'impressions',
                'clicks',
                'spend',
                'actions',
                'action_values',
                'ctr',
                'cpc',
                'cpm',
            ]

            insights = ad.get_insights(
                fields=insights_fields,
                params=insights_params
            )

            performance_history = []
            for insight in insights:
                performance_history.append({
                    'date': insight.get('date_start'),
                    'metrics': self._extract_metrics_from_insight(insight)
                })

            return performance_history

        except Exception as e:
            logger.error(f"Error fetching ad performance history: {e}")
            raise

    def _extract_metrics_from_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from a single insight"""
        # Extract conversions and conversion value
        conversions = 0
        conversion_value = Decimal('0')

        actions = insight.get('actions', [])
        action_values = insight.get('action_values', [])

        for action in actions:
            if action.get('action_type') == 'purchase':
                conversions += int(action.get('value', 0))

        for action_value in action_values:
            if action_value.get('action_type') == 'purchase':
                conversion_value += Decimal(str(action_value.get('value', 0)))

        spend = Decimal(str(insight.get('spend', 0)))
        roas = float(conversion_value / spend) if spend > 0 else 0

        return {
            'impressions': int(insight.get('impressions', 0)),
            'clicks': int(insight.get('clicks', 0)),
            'spend': spend,
            'conversions': conversions,
            'conversion_value': conversion_value,
            'ctr': float(insight.get('ctr', 0)),
            'cpc': Decimal(str(insight.get('cpc', 0))),
            'cpm': Decimal(str(insight.get('cpm', 0))),
            'roas': roas,
        }
