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
    
    async def get_campaigns_with_metrics(
        self,
        client_id: str,
        start_date: date,
        end_date: date,
        fields: List[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get campaigns with metrics for a date range"""
        try:
            if fields is None:
                fields = [
                    'campaign_id', 'campaign_name', 'status', 'objective',
                    'spend', 'impressions', 'clicks', 'conversions',
                    'cost_per_result', 'cpm', 'cpc', 'ctr', 'frequency'
                ]

            account = AdAccount(f"act_{client_id}")

            # Use insights API directly for better performance when active_only=True
            if active_only:
                # Get insights directly with spend filtering - much more efficient
                insights = account.get_insights(
                    fields=[
                        'campaign_id', 'campaign_name', 'spend', 'impressions',
                        'clicks', 'actions', 'cpm', 'cpc', 'ctr', 'frequency'
                    ],
                    params={
                        'time_range': {
                            'since': start_date.strftime('%Y-%m-%d'),
                            'until': end_date.strftime('%Y-%m-%d')
                        },
                        'level': 'campaign',
                        'filtering': [
                            {
                                'field': 'spend',
                                'operator': 'GREATER_THAN',
                                'value': 0
                            }
                        ]
                    }
                )

                campaigns_data = []
                for insight in insights:
                    # Extract conversions from actions
                    actions = insight.get('actions', [])
                    conversions = sum(int(action['value']) for action in actions
                                    if action['action_type'] in ['purchase', 'complete_registration'])

                    campaign_data = {
                        'campaign_id': insight.get('campaign_id'),
                        'campaign_name': insight.get('campaign_name'),
                        'status': 'ACTIVE',  # Campaigns with spend are active
                        'objective': 'CONVERSIONS',  # Default objective
                        'spend': float(insight.get('spend', 0)),
                        'impressions': int(insight.get('impressions', 0)),
                        'clicks': int(insight.get('clicks', 0)),
                        'conversions': conversions,
                        'cost_per_result': 0,  # Calculate if needed
                        'cpm': float(insight.get('cpm', 0)),
                        'cpc': float(insight.get('cpc', 0)),
                        'ctr': float(insight.get('ctr', 0)),
                        'frequency': float(insight.get('frequency', 0))
                    }
                    campaigns_data.append(campaign_data)

                return campaigns_data

            else:
                # Get all campaigns first, then filter by spend if needed
                campaigns = account.get_campaigns(
                    fields=['id', 'name', 'status', 'objective']
                )

                # If active_only, we'll filter by spend during insights processing
                # This is more reliable than trying to filter campaigns directly

            campaigns_data = []
            for campaign in campaigns:
                # Get insights for each campaign
                insights = campaign.get_insights(
                    fields=[
                        'spend', 'impressions', 'clicks', 'actions',
                        'cost_per_action_type', 'cpm', 'cpc', 'ctr', 'frequency'
                    ],
                    params={
                        'time_range': {
                            'since': start_date.strftime('%Y-%m-%d'),
                            'until': end_date.strftime('%Y-%m-%d')
                        }
                    }
                )

                campaign_data = {
                    'campaign_id': campaign['id'],
                    'campaign_name': campaign['name'],
                    'status': campaign['status'],
                    'objective': campaign.get('objective', 'Unknown'),
                    'spend': 0,
                    'impressions': 0,
                    'clicks': 0,
                    'conversions': 0,
                    'cost_per_result': 0,
                    'cpm': 0,
                    'cpc': 0,
                    'ctr': 0,
                    'frequency': 0
                }

                # Process insights
                total_spend = 0
                for insight in insights:
                    spend = float(insight.get('spend', 0))
                    total_spend += spend

                    campaign_data.update({
                        'spend': spend,
                        'impressions': int(insight.get('impressions', 0)),
                        'clicks': int(insight.get('clicks', 0)),
                        'cpm': float(insight.get('cpm', 0)),
                        'cpc': float(insight.get('cpc', 0)),
                        'ctr': float(insight.get('ctr', 0)),
                        'frequency': float(insight.get('frequency', 0))
                    })

                    # Extract conversions from actions
                    actions = insight.get('actions', [])
                    conversions = sum(int(action['value']) for action in actions
                                    if action['action_type'] in ['purchase', 'complete_registration'])
                    campaign_data['conversions'] = conversions

                # Only include campaigns with spend > 0 if active_only is True
                if not active_only or total_spend > 0:
                    campaigns_data.append(campaign_data)

            return campaigns_data

        except Exception as e:
            logger.error(f"Error fetching campaigns with metrics: {e}")
            raise

    async def get_ads_with_metrics(
        self,
        client_id: str,
        start_date: date,
        end_date: date,
        fields: List[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get ads with metrics for a date range"""
        try:
            if fields is None:
                fields = [
                    'ad_id', 'ad_name', 'status', 'campaign_id', 'campaign_name',
                    'spend', 'impressions', 'clicks', 'conversions', 'link_clicks',
                    'cost_per_result', 'cpm', 'cpc', 'ctr', 'frequency',
                    'video_views', 'video_view_rate', 'reach'
                ]

            account = AdAccount(f"act_{client_id}")

            # Use insights API directly for better performance when active_only=True
            if active_only:
                # Get insights directly with spend filtering - much more efficient
                insights = account.get_insights(
                    fields=[
                        'ad_id', 'ad_name', 'campaign_id', 'campaign_name', 'spend',
                        'impressions', 'clicks', 'actions', 'cpm', 'cpc', 'ctr',
                        'frequency', 'video_views', 'video_view_rate', 'reach'
                    ],
                    params={
                        'time_range': {
                            'since': start_date.strftime('%Y-%m-%d'),
                            'until': end_date.strftime('%Y-%m-%d')
                        },
                        'level': 'ad',
                        'filtering': [
                            {
                                'field': 'spend',
                                'operator': 'GREATER_THAN',
                                'value': 0
                            }
                        ]
                    }
                )

                ads_data = []
                for insight in insights:
                    # Extract conversions and link clicks from actions
                    actions = insight.get('actions', [])
                    conversions = sum(int(action['value']) for action in actions
                                    if action['action_type'] in ['purchase', 'complete_registration'])
                    link_clicks = sum(int(action['value']) for action in actions
                                    if action['action_type'] == 'link_click')

                    ad_data = {
                        'ad_id': insight.get('ad_id'),
                        'ad_name': insight.get('ad_name'),
                        'status': 'ACTIVE',  # Ads with spend are active
                        'campaign_id': insight.get('campaign_id'),
                        'campaign_name': insight.get('campaign_name'),
                        'spend': float(insight.get('spend', 0)),
                        'impressions': int(insight.get('impressions', 0)),
                        'clicks': int(insight.get('clicks', 0)),
                        'conversions': conversions,
                        'link_clicks': link_clicks,
                        'cost_per_result': 0,  # Calculate if needed
                        'cpm': float(insight.get('cpm', 0)),
                        'cpc': float(insight.get('cpc', 0)),
                        'ctr': float(insight.get('ctr', 0)),
                        'frequency': float(insight.get('frequency', 0)),
                        'video_views': int(insight.get('video_views', 0)),
                        'video_view_rate': float(insight.get('video_view_rate', 0)),
                        'reach': int(insight.get('reach', 0))
                    }
                    ads_data.append(ad_data)

                return ads_data

            else:
                # Get all ads first, then filter by spend if needed
                ads = account.get_ads(
                    fields=['id', 'name', 'status', 'campaign_id']
                )

                # If active_only, we'll filter by spend during insights processing
                # This is more reliable than trying to filter ads directly

            ads_data = []
            for ad in ads:
                # Get campaign name
                campaign = Campaign(ad['campaign_id'])
                campaign_info = campaign.api_get(fields=['name'])

                # Get insights for each ad
                insights = ad.get_insights(
                    fields=[
                        'spend', 'impressions', 'clicks', 'actions',
                        'cost_per_action_type', 'cpm', 'cpc', 'ctr', 'frequency',
                        'video_views', 'video_view_rate', 'reach'
                    ],
                    params={
                        'time_range': {
                            'since': start_date.strftime('%Y-%m-%d'),
                            'until': end_date.strftime('%Y-%m-%d')
                        }
                    }
                )

                ad_data = {
                    'ad_id': ad['id'],
                    'ad_name': ad['name'],
                    'status': ad['status'],
                    'campaign_id': ad['campaign_id'],
                    'campaign_name': campaign_info.get('name', 'Unknown'),
                    'spend': 0,
                    'impressions': 0,
                    'clicks': 0,
                    'conversions': 0,
                    'link_clicks': 0,
                    'cost_per_result': 0,
                    'cpm': 0,
                    'cpc': 0,
                    'ctr': 0,
                    'frequency': 0,
                    'video_views': 0,
                    'video_view_rate': 0,
                    'reach': 0
                }

                # Process insights
                total_spend = 0
                for insight in insights:
                    spend = float(insight.get('spend', 0))
                    total_spend += spend

                    ad_data.update({
                        'spend': spend,
                        'impressions': int(insight.get('impressions', 0)),
                        'clicks': int(insight.get('clicks', 0)),
                        'cpm': float(insight.get('cpm', 0)),
                        'cpc': float(insight.get('cpc', 0)),
                        'ctr': float(insight.get('ctr', 0)),
                        'frequency': float(insight.get('frequency', 0)),
                        'video_views': int(insight.get('video_views', 0)),
                        'video_view_rate': float(insight.get('video_view_rate', 0)),
                        'reach': int(insight.get('reach', 0))
                    })

                    # Extract conversions and link clicks from actions
                    actions = insight.get('actions', [])
                    conversions = sum(int(action['value']) for action in actions
                                    if action['action_type'] in ['purchase', 'complete_registration'])
                    link_clicks = sum(int(action['value']) for action in actions
                                    if action['action_type'] == 'link_click')

                    ad_data['conversions'] = conversions
                    ad_data['link_clicks'] = link_clicks

                # Only include ads with spend > 0 if active_only is True
                if not active_only or total_spend > 0:
                    ads_data.append(ad_data)

            return ads_data

        except Exception as e:
            logger.error(f"Error fetching ads with metrics: {e}")
            raise

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
                'filtering': [
                    {
                        'field': 'spend',
                        'operator': 'GREATER_THAN',
                        'value': 0  # Only ads with spend > 0
                    }
                ]
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

            # Generate Facebook URL for ads manager
            facebook_url = f"https://www.facebook.com/ads/manager/reporting/view?act={client_id}&selected_report_id={ad_id}"

            # Try to get preview URL from creative
            preview_url = None
            try:
                ad = Ad(ad_id)
                ad_data = ad.api_get(fields=['creative'])
                if ad_data.get('creative'):
                    creative_id = ad_data['creative']['id']
                    from facebook_business.adobjects.adcreative import AdCreative
                    creative = AdCreative(creative_id)
                    creative_data = creative.api_get(fields=['thumbnail_url'])
                    preview_url = creative_data.get('thumbnail_url')
            except Exception as e:
                logger.warning(f"Could not fetch preview URL for ad {ad_id}: {e}")

            return AdPerformance(
                id=ad_id,
                name=ad_name,
                status=insight.get('ad_delivery_info', {}).get('delivery_status', 'unknown'),
                campaign_name=campaign_name,
                adset_name=adset_name,
                preview_url=preview_url,
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

    async def get_top_performing_campaigns(
        self,
        client_id: str,
        start_date: date,
        end_date: date,
        attribution: str = "default",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top performing campaigns for a client based on ROAS

        Args:
            client_id: Meta ad account ID
            start_date: Start date for the period
            end_date: End date for the period
            attribution: Attribution model (default, 7d_click)
            limit: Number of top campaigns to return

        Returns:
            List of top performing campaigns with metrics
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
                'level': 'campaign',
                'breakdowns': [],
                'limit': limit * 2,  # Fetch more to account for filtering
                'filtering': [
                    {
                        'field': 'spend',
                        'operator': 'GREATER_THAN',
                        'value': 0  # Only campaigns with spend > 0
                    }
                ]
            }

            # Set attribution window based on parameter
            if attribution == "7d_click":
                insights_params['action_attribution_windows'] = ['7d_click']

            # Define metrics to fetch
            insights_fields = [
                'campaign_id',
                'campaign_name',
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

            # Fetch campaigns with insights
            campaigns_insights = ad_account.get_insights(
                fields=insights_fields,
                params=insights_params
            )

            # Process and rank campaigns by ROAS
            top_campaigns = []
            for insight in campaigns_insights:
                try:
                    campaign_performance = self._process_campaign_insight(insight, attribution)
                    if campaign_performance and campaign_performance.get('metrics', {}).get('roas', 0) > 0:
                        top_campaigns.append(campaign_performance)
                except Exception as e:
                    logger.warning(f"Error processing campaign insight: {e}")
                    continue

            # Sort by ROAS and return top performers
            top_campaigns.sort(key=lambda x: x.get('metrics', {}).get('roas', 0), reverse=True)
            return top_campaigns[:limit]

        except Exception as e:
            logger.error(f"Error fetching top performing campaigns: {e}")
            raise

    def _process_campaign_insight(self, insight: Dict[str, Any], attribution: str) -> Optional[Dict[str, Any]]:
        """Process a single campaign insight into campaign performance object"""
        try:
            # Extract basic campaign information
            campaign_id = insight.get('campaign_id')
            campaign_name = insight.get('campaign_name', '')

            # Extract metrics
            impressions = int(insight.get('impressions', 0))
            clicks = int(insight.get('clicks', 0))
            spend = float(insight.get('spend', 0))
            ctr = float(insight.get('ctr', 0))
            cpc = float(insight.get('cpc', 0))
            cpm = float(insight.get('cpm', 0))
            frequency = float(insight.get('frequency', 0))

            # Extract conversions and conversion value
            conversions = 0
            conversion_value = 0.0

            actions = insight.get('actions', [])
            action_values = insight.get('action_values', [])

            # Sum up purchase conversions
            for action in actions:
                if action.get('action_type') == 'purchase':
                    conversions += int(action.get('value', 0))

            # Sum up purchase values
            for action_value in action_values:
                if action_value.get('action_type') == 'purchase':
                    conversion_value += float(action_value.get('value', 0))

            # Calculate ROAS
            roas = conversion_value / spend if spend > 0 else 0

            return {
                "id": campaign_id,
                "name": campaign_name,
                "status": "active",  # Would need separate API call for actual status
                "metrics": {
                    "impressions": impressions,
                    "clicks": clicks,
                    "spend": spend,
                    "conversions": conversions,
                    "conversion_value": conversion_value,
                    "ctr": ctr,
                    "cpc": cpc,
                    "cpm": cpm,
                    "roas": roas,
                    "frequency": frequency
                },
                "currency": insight.get('account_currency', 'CZK'),
                "attribution": attribution
            }

        except Exception as e:
            logger.error(f"Error processing campaign insight: {e}")
            return None

    async def get_campaign_details(self, campaign_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific campaign"""
        try:
            campaign = Campaign(campaign_id)

            # Fetch campaign basic info
            campaign_data = campaign.api_get(fields=[
                'id',
                'name',
                'status',
                'objective',
                'daily_budget',
                'lifetime_budget',
                'created_time',
                'updated_time'
            ])

            return {
                "id": campaign_data.get('id'),
                "name": campaign_data.get('name'),
                "status": campaign_data.get('status'),
                "objective": campaign_data.get('objective'),
                "daily_budget": campaign_data.get('daily_budget'),
                "lifetime_budget": campaign_data.get('lifetime_budget'),
                "created_time": campaign_data.get('created_time'),
                "updated_time": campaign_data.get('updated_time')
            }

        except Exception as e:
            logger.error(f"Error fetching campaign details: {e}")
            raise

    async def get_conversion_funnel(
        self,
        client_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get conversion funnel data for visualization

        Returns funnel stages with conversion rates:
        - Impressions
        - Clicks
        - Landing Page Views
        - Add to Cart
        - Purchase
        """
        try:
            # Get ad account
            ad_account = AdAccount(f"act_{client_id}")

            # Define insights parameters
            insights_params = {
                'time_range': {
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                },
                'level': 'account',
                'breakdowns': [],
            }

            # Define metrics to fetch including all funnel actions
            insights_fields = [
                'impressions',
                'clicks',
                'actions',
                'account_currency'
            ]

            # Fetch account insights
            insights = ad_account.get_insights(
                fields=insights_fields,
                params=insights_params
            )

            # Process funnel data
            if insights:
                insight = insights[0]  # Account level has single result

                impressions = int(insight.get('impressions', 0))
                clicks = int(insight.get('clicks', 0))

                # Extract different action types
                actions = insight.get('actions', [])
                landing_page_views = 0
                add_to_cart = 0
                purchases = 0

                for action in actions:
                    action_type = action.get('action_type')
                    value = int(action.get('value', 0))

                    if action_type == 'landing_page_view':
                        landing_page_views += value
                    elif action_type == 'add_to_cart':
                        add_to_cart += value
                    elif action_type == 'purchase':
                        purchases += value

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
                    "currency": insight.get('account_currency', 'CZK')
                }
            else:
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

        except Exception as e:
            logger.error(f"Error fetching conversion funnel: {e}")
            raise

    async def get_week_on_week_comparison(
        self,
        client_id: str,
        current_week_start: date,
        current_week_end: date,
        previous_week_start: date,
        previous_week_end: date
    ) -> Dict[str, Any]:
        """
        Get week-on-week metric comparisons

        Compares current week vs previous week performance
        """
        try:
            # Get ad account
            ad_account = AdAccount(f"act_{client_id}")

            # Fetch current week metrics
            current_week_insights = ad_account.get_insights(
                fields=[
                    'impressions',
                    'clicks',
                    'spend',
                    'actions',
                    'action_values',
                    'ctr',
                    'account_currency'
                ],
                params={
                    'time_range': {
                        'since': current_week_start.strftime('%Y-%m-%d'),
                        'until': current_week_end.strftime('%Y-%m-%d')
                    },
                    'level': 'account'
                }
            )

            # Fetch previous week metrics
            previous_week_insights = ad_account.get_insights(
                fields=[
                    'impressions',
                    'clicks',
                    'spend',
                    'actions',
                    'action_values',
                    'ctr',
                    'account_currency'
                ],
                params={
                    'time_range': {
                        'since': previous_week_start.strftime('%Y-%m-%d'),
                        'until': previous_week_end.strftime('%Y-%m-%d')
                    },
                    'level': 'account'
                }
            )

            # Process current week data
            current_metrics = self._extract_week_metrics(current_week_insights[0] if current_week_insights else {})
            previous_metrics = self._extract_week_metrics(previous_week_insights[0] if previous_week_insights else {})

            # Calculate percentage changes
            metrics_comparison = {}
            for metric in ['spend', 'roas', 'conversions', 'ctr', 'impressions', 'clicks']:
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
                "currency": current_week_insights[0].get('account_currency', 'CZK') if current_week_insights else 'CZK'
            }

        except Exception as e:
            logger.error(f"Error fetching week-on-week comparison: {e}")
            raise

    def _extract_week_metrics(self, insight: Dict[str, Any]) -> Dict[str, float]:
        """Extract metrics from a weekly insight"""
        if not insight:
            return {
                'spend': 0.0,
                'roas': 0.0,
                'conversions': 0,
                'ctr': 0.0,
                'impressions': 0,
                'clicks': 0
            }

        # Extract basic metrics
        impressions = int(insight.get('impressions', 0))
        clicks = int(insight.get('clicks', 0))
        spend = float(insight.get('spend', 0))
        ctr = float(insight.get('ctr', 0))

        # Extract conversions and conversion value
        conversions = 0
        conversion_value = 0.0

        actions = insight.get('actions', [])
        action_values = insight.get('action_values', [])

        for action in actions:
            if action.get('action_type') == 'purchase':
                conversions += int(action.get('value', 0))

        for action_value in action_values:
            if action_value.get('action_type') == 'purchase':
                conversion_value += float(action_value.get('value', 0))

        # Calculate ROAS
        roas = conversion_value / spend if spend > 0 else 0.0

        return {
            'spend': spend,
            'roas': roas,
            'conversions': conversions,
            'ctr': ctr,
            'impressions': impressions,
            'clicks': clicks
        }
