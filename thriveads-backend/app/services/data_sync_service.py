"""
Data synchronization service for batch processing Meta API data
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import structlog
import uuid

from app.models.metrics import AdMetrics, CampaignMetrics, DataSyncLog
from app.models.ad import Ad
from app.models.campaign import Campaign
from app.models.client import Client
from app.services.meta_service import MetaService
from app.services.aggregation_service import AggregationService

logger = structlog.get_logger()


class DataSyncService:
    """Service for synchronizing data from Meta API to database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.meta_service = MetaService()
        self.aggregation_service = AggregationService(db)
    
    async def sync_daily_data(self, client_id: str, sync_date: date) -> Dict[str, Any]:
        """
        Sync daily data for a specific client and date
        
        Args:
            client_id: Client ID to sync data for
            sync_date: Date to sync data for
        
        Returns:
            Dictionary with sync results
        """
        logger.info(
            "Starting daily data sync",
            client_id=client_id,
            sync_date=sync_date
        )
        
        # Track sync
        sync_log = DataSyncLog(
            id=str(uuid.uuid4()),
            client_id=client_id,
            sync_type="daily",
            sync_date=sync_date,
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            # Sync ads data
            ads_synced = await self._sync_ads_data(client_id, sync_date)
            
            # Sync campaigns data
            campaigns_synced = await self._sync_campaigns_data(client_id, sync_date)
            
            # Sync daily metrics
            metrics_synced = await self._sync_daily_metrics(client_id, sync_date)
            
            total_records = ads_synced + campaigns_synced + metrics_synced
            
            # Update sync log
            sync_log.status = "completed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.records_processed = total_records
            self.db.commit()
            
            logger.info(
                "Daily data sync completed",
                client_id=client_id,
                sync_date=sync_date,
                ads_synced=ads_synced,
                campaigns_synced=campaigns_synced,
                metrics_synced=metrics_synced
            )
            
            return {
                "sync_date": sync_date.isoformat(),
                "ads_synced": ads_synced,
                "campaigns_synced": campaigns_synced,
                "metrics_synced": metrics_synced,
                "total_records": total_records,
                "status": "completed"
            }
            
        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.error(
                "Daily data sync failed",
                client_id=client_id,
                sync_date=sync_date,
                error=str(e)
            )
            raise
    
    async def _sync_ads_data(self, client_id: str, sync_date: date) -> int:
        """Sync ads basic information"""
        try:
            # Get ad account
            from facebook_business.adobjects.adaccount import AdAccount
            ad_account = AdAccount(f"act_{client_id}")
            
            # Fetch ads
            ads = ad_account.get_ads(fields=[
                'id',
                'name', 
                'status',
                'campaign_id',
                'adset_id',
                'creative',
                'created_time',
                'updated_time'
            ])
            
            ads_synced = 0
            for ad_data in ads:
                # Create or update ad record
                existing_ad = self.db.query(Ad).filter(Ad.id == ad_data['id']).first()
                
                if existing_ad:
                    # Update existing ad
                    existing_ad.name = ad_data.get('name', '')
                    existing_ad.status = ad_data.get('status', '')
                    existing_ad.updated_at = datetime.utcnow()
                else:
                    # Create new ad
                    new_ad = Ad(
                        id=ad_data['id'],
                        name=ad_data.get('name', ''),
                        status=ad_data.get('status', ''),
                        client_id=client_id,
                        campaign_id=ad_data.get('campaign_id'),
                        adset_id=ad_data.get('adset_id'),
                        creative_id=ad_data.get('creative', {}).get('id') if ad_data.get('creative') else None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(new_ad)
                    ads_synced += 1
            
            self.db.commit()
            return ads_synced
            
        except Exception as e:
            logger.error(f"Error syncing ads data: {e}")
            raise
    
    async def _sync_campaigns_data(self, client_id: str, sync_date: date) -> int:
        """Sync campaigns basic information"""
        try:
            # Get ad account
            from facebook_business.adobjects.adaccount import AdAccount
            ad_account = AdAccount(f"act_{client_id}")
            
            # Fetch campaigns
            campaigns = ad_account.get_campaigns(fields=[
                'id',
                'name',
                'status',
                'objective',
                'daily_budget',
                'lifetime_budget',
                'created_time',
                'updated_time'
            ])
            
            campaigns_synced = 0
            for campaign_data in campaigns:
                # Create or update campaign record
                existing_campaign = self.db.query(Campaign).filter(Campaign.id == campaign_data['id']).first()
                
                if existing_campaign:
                    # Update existing campaign
                    existing_campaign.name = campaign_data.get('name', '')
                    existing_campaign.status = campaign_data.get('status', '')
                    existing_campaign.objective = campaign_data.get('objective', '')
                    existing_campaign.updated_at = datetime.utcnow()
                else:
                    # Create new campaign
                    new_campaign = Campaign(
                        id=campaign_data['id'],
                        name=campaign_data.get('name', ''),
                        status=campaign_data.get('status', ''),
                        objective=campaign_data.get('objective', ''),
                        client_id=client_id,
                        daily_budget=campaign_data.get('daily_budget'),
                        lifetime_budget=campaign_data.get('lifetime_budget'),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(new_campaign)
                    campaigns_synced += 1
            
            self.db.commit()
            return campaigns_synced
            
        except Exception as e:
            logger.error(f"Error syncing campaigns data: {e}")
            raise
    
    async def _sync_daily_metrics(self, client_id: str, sync_date: date) -> int:
        """Sync daily performance metrics"""
        try:
            # Get ad account
            from facebook_business.adobjects.adaccount import AdAccount
            ad_account = AdAccount(f"act_{client_id}")
            
            # Fetch daily insights for ads
            insights = ad_account.get_insights(
                fields=[
                    'ad_id',
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
                ],
                params={
                    'time_range': {
                        'since': sync_date.strftime('%Y-%m-%d'),
                        'until': sync_date.strftime('%Y-%m-%d')
                    },
                    'level': 'ad',
                    'time_increment': 1
                }
            )
            
            metrics_synced = 0
            for insight in insights:
                # Process and store ad metrics
                ad_id = insight.get('ad_id')
                if not ad_id:
                    continue
                
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
                spend = float(insight.get('spend', 0))
                roas = conversion_value / spend if spend > 0 else 0
                
                # Create or update metrics record
                metrics_id = f"{ad_id}_{sync_date.strftime('%Y%m%d')}"
                existing_metrics = self.db.query(AdMetrics).filter(AdMetrics.id == metrics_id).first()
                
                if existing_metrics:
                    # Update existing metrics
                    existing_metrics.impressions = int(insight.get('impressions', 0))
                    existing_metrics.clicks = int(insight.get('clicks', 0))
                    existing_metrics.spend = spend
                    existing_metrics.conversions = conversions
                    existing_metrics.conversion_value = conversion_value
                    existing_metrics.ctr = float(insight.get('ctr', 0))
                    existing_metrics.cpc = float(insight.get('cpc', 0))
                    existing_metrics.cpm = float(insight.get('cpm', 0))
                    existing_metrics.roas = roas
                    existing_metrics.frequency = float(insight.get('frequency', 0))
                    existing_metrics.updated_at = datetime.utcnow()
                else:
                    # Create new metrics record
                    new_metrics = AdMetrics(
                        id=metrics_id,
                        ad_id=ad_id,
                        date=sync_date,
                        impressions=int(insight.get('impressions', 0)),
                        clicks=int(insight.get('clicks', 0)),
                        spend=spend,
                        conversions=conversions,
                        conversion_value=conversion_value,
                        ctr=float(insight.get('ctr', 0)),
                        cpc=float(insight.get('cpc', 0)),
                        cpm=float(insight.get('cpm', 0)),
                        roas=roas,
                        frequency=float(insight.get('frequency', 0)),
                        currency=insight.get('account_currency', 'CZK'),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    self.db.add(new_metrics)
                    metrics_synced += 1
            
            self.db.commit()
            return metrics_synced
            
        except Exception as e:
            logger.error(f"Error syncing daily metrics: {e}")
            raise
    
    async def sync_historical_data(self, client_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Sync historical data for a date range
        
        Args:
            client_id: Client ID to sync data for
            start_date: Start date for sync
            end_date: End date for sync
        
        Returns:
            Dictionary with sync results
        """
        logger.info(
            "Starting historical data sync",
            client_id=client_id,
            start_date=start_date,
            end_date=end_date
        )
        
        total_days = (end_date - start_date).days + 1
        successful_days = 0
        failed_days = 0
        
        current_date = start_date
        while current_date <= end_date:
            try:
                await self.sync_daily_data(client_id, current_date)
                successful_days += 1
            except Exception as e:
                logger.error(f"Failed to sync data for {current_date}: {e}")
                failed_days += 1
            
            current_date += timedelta(days=1)
        
        logger.info(
            "Historical data sync completed",
            client_id=client_id,
            total_days=total_days,
            successful_days=successful_days,
            failed_days=failed_days
        )
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_days": total_days,
            "successful_days": successful_days,
            "failed_days": failed_days,
            "success_rate": (successful_days / total_days * 100) if total_days > 0 else 0
        }
