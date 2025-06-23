"""
Data aggregation service for pre-calculating weekly and monthly metrics
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import structlog
import uuid

from app.models.metrics import (
    AdMetrics, CampaignMetrics,
    WeeklyAdMetrics, MonthlyAdMetrics,
    WeeklyCampaignMetrics, MonthlyCampaignMetrics,
    DataSyncLog
)
from app.models.ad import Ad
from app.models.campaign import Campaign

logger = structlog.get_logger()


class AggregationService:
    """Service for aggregating daily metrics into weekly and monthly summaries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def aggregate_weekly_metrics(self, client_id: str, week_start: date) -> Dict[str, int]:
        """
        Aggregate daily metrics into weekly summaries for a specific week
        
        Args:
            client_id: Client ID to aggregate for
            week_start: Monday of the week to aggregate (date)
        
        Returns:
            Dictionary with counts of aggregated records
        """
        week_end = week_start + timedelta(days=6)  # Sunday
        
        logger.info(
            "Starting weekly aggregation",
            client_id=client_id,
            week_start=week_start,
            week_end=week_end
        )
        
        # Track aggregation
        sync_log = DataSyncLog(
            id=str(uuid.uuid4()),
            client_id=client_id,
            sync_type="weekly",
            sync_date=week_start,
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
        
        try:
            ad_count = await self._aggregate_weekly_ad_metrics(client_id, week_start, week_end)
            campaign_count = await self._aggregate_weekly_campaign_metrics(client_id, week_start, week_end)
            
            # Update sync log
            sync_log.status = "completed"
            sync_log.completed_at = datetime.utcnow()
            sync_log.records_processed = ad_count + campaign_count
            self.db.commit()
            
            logger.info(
                "Weekly aggregation completed",
                client_id=client_id,
                week_start=week_start,
                ad_records=ad_count,
                campaign_records=campaign_count
            )
            
            return {
                "ad_records": ad_count,
                "campaign_records": campaign_count,
                "total_records": ad_count + campaign_count
            }
            
        except Exception as e:
            sync_log.status = "failed"
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.error(
                "Weekly aggregation failed",
                client_id=client_id,
                week_start=week_start,
                error=str(e)
            )
            raise
    
    async def _aggregate_weekly_ad_metrics(self, client_id: str, week_start: date, week_end: date) -> int:
        """Aggregate daily ad metrics into weekly summaries"""
        
        # Query to aggregate daily ad metrics for the week
        weekly_aggregates = (
            self.db.query(
                AdMetrics.ad_id,
                func.sum(AdMetrics.impressions).label('impressions'),
                func.sum(AdMetrics.clicks).label('clicks'),
                func.sum(AdMetrics.spend).label('spend'),
                func.sum(AdMetrics.conversions).label('conversions'),
                func.sum(AdMetrics.conversion_value).label('conversion_value'),
                func.avg(AdMetrics.frequency).label('frequency'),
                AdMetrics.attribution,
                AdMetrics.currency
            )
            .join(Ad, AdMetrics.ad_id == Ad.id)
            .filter(
                and_(
                    Ad.client_id == client_id,
                    AdMetrics.date >= week_start,
                    AdMetrics.date <= week_end
                )
            )
            .group_by(AdMetrics.ad_id, AdMetrics.attribution, AdMetrics.currency)
            .all()
        )
        
        records_created = 0
        
        for agg in weekly_aggregates:
            # Calculate derived metrics
            ctr = (agg.clicks / agg.impressions * 100) if agg.impressions > 0 else 0
            cpc = (agg.spend / agg.clicks) if agg.clicks > 0 else 0
            cpm = (agg.spend / agg.impressions * 1000) if agg.impressions > 0 else 0
            roas = (agg.conversion_value / agg.spend) if agg.spend > 0 else 0
            
            # Create or update weekly record
            weekly_id = f"{agg.ad_id}_{week_start.strftime('%Y%m%d')}"
            
            existing = self.db.query(WeeklyAdMetrics).filter(
                WeeklyAdMetrics.id == weekly_id
            ).first()
            
            if existing:
                # Update existing record
                existing.impressions = agg.impressions
                existing.clicks = agg.clicks
                existing.spend = agg.spend
                existing.conversions = agg.conversions
                existing.conversion_value = agg.conversion_value
                existing.ctr = ctr
                existing.cpc = cpc
                existing.cpm = cpm
                existing.roas = roas
                existing.frequency = agg.frequency
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                weekly_record = WeeklyAdMetrics(
                    id=weekly_id,
                    ad_id=agg.ad_id,
                    week_start_date=week_start,
                    week_end_date=week_end,
                    impressions=agg.impressions,
                    clicks=agg.clicks,
                    spend=agg.spend,
                    conversions=agg.conversions,
                    conversion_value=agg.conversion_value,
                    ctr=ctr,
                    cpc=cpc,
                    cpm=cpm,
                    roas=roas,
                    frequency=agg.frequency,
                    attribution=agg.attribution,
                    currency=agg.currency
                )
                self.db.add(weekly_record)
                records_created += 1
        
        self.db.commit()
        return records_created
    
    async def _aggregate_weekly_campaign_metrics(self, client_id: str, week_start: date, week_end: date) -> int:
        """Aggregate daily campaign metrics into weekly summaries"""
        
        # Similar logic to ad metrics but for campaigns
        weekly_aggregates = (
            self.db.query(
                CampaignMetrics.campaign_id,
                func.sum(CampaignMetrics.impressions).label('impressions'),
                func.sum(CampaignMetrics.clicks).label('clicks'),
                func.sum(CampaignMetrics.spend).label('spend'),
                func.sum(CampaignMetrics.conversions).label('conversions'),
                func.sum(CampaignMetrics.conversion_value).label('conversion_value'),
                func.avg(CampaignMetrics.frequency).label('frequency'),
                CampaignMetrics.attribution,
                CampaignMetrics.currency
            )
            .join(Campaign, CampaignMetrics.campaign_id == Campaign.id)
            .filter(
                and_(
                    Campaign.client_id == client_id,
                    CampaignMetrics.date >= week_start,
                    CampaignMetrics.date <= week_end
                )
            )
            .group_by(CampaignMetrics.campaign_id, CampaignMetrics.attribution, CampaignMetrics.currency)
            .all()
        )
        
        records_created = 0
        
        for agg in weekly_aggregates:
            # Calculate derived metrics
            ctr = (agg.clicks / agg.impressions * 100) if agg.impressions > 0 else 0
            cpc = (agg.spend / agg.clicks) if agg.clicks > 0 else 0
            cpm = (agg.spend / agg.impressions * 1000) if agg.impressions > 0 else 0
            roas = (agg.conversion_value / agg.spend) if agg.spend > 0 else 0
            
            # Create or update weekly record
            weekly_id = f"{agg.campaign_id}_{week_start.strftime('%Y%m%d')}"
            
            existing = self.db.query(WeeklyCampaignMetrics).filter(
                WeeklyCampaignMetrics.id == weekly_id
            ).first()
            
            if existing:
                # Update existing record
                existing.impressions = agg.impressions
                existing.clicks = agg.clicks
                existing.spend = agg.spend
                existing.conversions = agg.conversions
                existing.conversion_value = agg.conversion_value
                existing.ctr = ctr
                existing.cpc = cpc
                existing.cpm = cpm
                existing.roas = roas
                existing.frequency = agg.frequency
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                weekly_record = WeeklyCampaignMetrics(
                    id=weekly_id,
                    campaign_id=agg.campaign_id,
                    week_start_date=week_start,
                    week_end_date=week_end,
                    impressions=agg.impressions,
                    clicks=agg.clicks,
                    spend=agg.spend,
                    conversions=agg.conversions,
                    conversion_value=agg.conversion_value,
                    ctr=ctr,
                    cpc=cpc,
                    cpm=cpm,
                    roas=roas,
                    frequency=agg.frequency,
                    attribution=agg.attribution,
                    currency=agg.currency
                )
                self.db.add(weekly_record)
                records_created += 1
        
        self.db.commit()
        return records_created
