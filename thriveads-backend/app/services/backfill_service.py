"""
Smart Backfill Service for Historical Data

This service systematically downloads historical Meta API data day-by-day
to build a complete database for advanced analytics while respecting
Railway Pro resource limits.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_session_local
from app.services.meta_service import MetaService
from app.models.campaign import Campaign
from app.models.ad import Ad
from app.models.metrics import CampaignMetrics, AdMetrics
from app.models.client import Client

logger = logging.getLogger(__name__)


class BackfillProgress:
    """Track backfill progress"""
    def __init__(self, db: Session):
        self.db = db
        self.start_time = datetime.now()
        self.days_completed = 0
        self.days_total = 0
        self.current_date = None
        self.errors = []
        
    def update(self, current_date: date, completed: int, total: int):
        self.current_date = current_date
        self.days_completed = completed
        self.days_total = total
        
    def add_error(self, date_str: str, error: str):
        self.errors.append(f"{date_str}: {error}")
        
    def get_status(self) -> Dict[str, Any]:
        elapsed = datetime.now() - self.start_time
        progress_pct = (self.days_completed / self.days_total * 100) if self.days_total > 0 else 0
        
        # Estimate remaining time
        if self.days_completed > 0:
            avg_time_per_day = elapsed.total_seconds() / self.days_completed
            remaining_days = self.days_total - self.days_completed
            estimated_remaining = timedelta(seconds=avg_time_per_day * remaining_days)
        else:
            estimated_remaining = None
            
        return {
            "status": "running" if self.days_completed < self.days_total else "completed",
            "progress": {
                "completed_days": self.days_completed,
                "total_days": self.days_total,
                "percentage": round(progress_pct, 1),
                "current_date": str(self.current_date) if self.current_date else None
            },
            "timing": {
                "started_at": self.start_time.isoformat(),
                "elapsed": str(elapsed).split('.')[0],  # Remove microseconds
                "estimated_remaining": str(estimated_remaining).split('.')[0] if estimated_remaining else None
            },
            "errors": self.errors[-10:],  # Last 10 errors
            "error_count": len(self.errors)
        }


class BackfillService:
    """Service for systematic historical data backfill"""
    
    def __init__(self, client_id: str = "513010266454814"):
        self.client_id = client_id
        self.meta_service = MetaService()
        
    async def check_existing_data(self, db: Session, target_date: date) -> Dict[str, bool]:
        """Check what data already exists for a specific date"""
        
        # Check if we have campaign metrics for this date
        # Use join instead of relationship navigation
        campaign_metrics_exist = db.query(CampaignMetrics).join(Campaign).filter(
            and_(
                CampaignMetrics.date == target_date,
                Campaign.client_id == self.client_id
            )
        ).first() is not None
        
        # Check if we have ad metrics for this date
        # Use join instead of relationship navigation
        ad_metrics_exist = db.query(AdMetrics).join(Ad).join(Campaign).filter(
            and_(
                AdMetrics.date == target_date,
                Campaign.client_id == self.client_id
            )
        ).first() is not None
        
        return {
            "campaigns": campaign_metrics_exist,
            "ads": ad_metrics_exist,
            "complete": campaign_metrics_exist and ad_metrics_exist
        }
    
    async def backfill_single_day(
        self, 
        db: Session, 
        target_date: date,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Backfill data for a single day"""
        
        try:
            # Check if data already exists
            existing = await self.check_existing_data(db, target_date)
            if existing["complete"] and not force_refresh:
                return {
                    "date": str(target_date),
                    "status": "skipped",
                    "reason": "Data already exists",
                    "campaigns": 0,
                    "ads": 0
                }
            
            logger.info(f"Backfilling data for {target_date}")
            
            # Fetch campaigns data for this day
            campaigns_data = await self.meta_service.get_campaigns_with_metrics(
                client_id=self.client_id,
                start_date=target_date,
                end_date=target_date,  # Same day for daily granularity
                active_only=True
            )
            
            # Fetch ads data for this day
            ads_data = await self.meta_service.get_ads_with_metrics(
                client_id=self.client_id,
                start_date=target_date,
                end_date=target_date,  # Same day for daily granularity
                active_only=True
            )
            
            # Store campaigns data
            campaigns_stored = 0
            for campaign_data in campaigns_data:
                if campaign_data.get('spend', 0) > 0:  # Only store campaigns with spend
                    await self._store_campaign_data(db, campaign_data, target_date)
                    campaigns_stored += 1
            
            # Store ads data
            ads_stored = 0
            for ad_data in ads_data:
                if ad_data.get('spend', 0) > 0:  # Only store ads with spend
                    await self._store_ad_data(db, ad_data, target_date)
                    ads_stored += 1
            
            db.commit()
            
            return {
                "date": str(target_date),
                "status": "success",
                "campaigns": campaigns_stored,
                "ads": ads_stored,
                "total_spend": sum(c.get('spend', 0) for c in campaigns_data)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error backfilling {target_date}: {e}")
            return {
                "date": str(target_date),
                "status": "error",
                "error": str(e),
                "campaigns": 0,
                "ads": 0
            }
    
    async def _store_campaign_data(self, db: Session, campaign_data: Dict, target_date: date):
        """Store campaign data in database"""
        
        # Get or create client
        client = db.query(Client).filter(Client.meta_ad_account_id == self.client_id).first()
        if not client:
            client = Client(
                id=f"client_{self.client_id}",  # Generate a unique ID
                name="Mimilátky CZ",
                meta_ad_account_id=self.client_id,
                currency="CZK"
            )
            db.add(client)
            db.flush()
        
        # Get or create campaign
        campaign = db.query(Campaign).filter(
            and_(
                Campaign.id == campaign_data['campaign_id'],
                Campaign.client_id == client.id
            )
        ).first()

        if not campaign:
            campaign = Campaign(
                id=campaign_data['campaign_id'],
                name=campaign_data['campaign_name'],
                status=campaign_data.get('status', 'UNKNOWN'),
                objective=campaign_data.get('objective', 'UNKNOWN'),
                client_id=client.id
            )
            db.add(campaign)
            db.flush()
        
        # Delete existing metrics for this date (if force refresh)
        db.query(CampaignMetrics).filter(
            and_(
                CampaignMetrics.campaign_id == campaign.id,
                CampaignMetrics.date == target_date
            )
        ).delete()
        
        # Create new metrics
        metrics = CampaignMetrics(
            campaign_id=campaign.id,
            date=target_date,
            spend=campaign_data.get('spend', 0),
            impressions=campaign_data.get('impressions', 0),
            clicks=campaign_data.get('clicks', 0),
            conversions=campaign_data.get('conversions', 0),
            cpm=campaign_data.get('cpm', 0),
            cpc=campaign_data.get('cpc', 0),
            ctr=campaign_data.get('ctr', 0),
            frequency=campaign_data.get('frequency', 0)
        )
        db.add(metrics)
    
    async def _store_ad_data(self, db: Session, ad_data: Dict, target_date: date):
        """Store ad data in database"""
        
        # Get campaign (should exist from campaign backfill)
        campaign = db.query(Campaign).filter(
            Campaign.id == ad_data['campaign_id']
        ).first()
        
        if not campaign:
            logger.warning(f"Campaign {ad_data['campaign_id']} not found for ad {ad_data['ad_id']}")
            return
        
        # Get or create ad
        ad = db.query(Ad).filter(
            Ad.id == ad_data['ad_id']
        ).first()

        if not ad:
            ad = Ad(
                id=ad_data['ad_id'],
                name=ad_data['ad_name'],
                status=ad_data.get('status', 'UNKNOWN'),
                campaign_id=campaign.id,
                client_id=campaign.client_id  # Add client_id
            )
            db.add(ad)
            db.flush()
        
        # Delete existing metrics for this date (if force refresh)
        db.query(AdMetrics).filter(
            and_(
                AdMetrics.ad_id == ad.id,
                AdMetrics.date == target_date
            )
        ).delete()
        
        # Create new metrics
        metrics = AdMetrics(
            ad_id=ad.id,
            date=target_date,
            spend=ad_data.get('spend', 0),
            impressions=ad_data.get('impressions', 0),
            clicks=ad_data.get('clicks', 0),
            conversions=ad_data.get('conversions', 0),
            link_clicks=ad_data.get('link_clicks', 0),
            cpm=ad_data.get('cpm', 0),
            cpc=ad_data.get('cpc', 0),
            ctr=ad_data.get('ctr', 0),
            frequency=ad_data.get('frequency', 0),
            reach=ad_data.get('reach', 0)
        )
        db.add(metrics)
    
    async def backfill_date_range(
        self,
        start_date: date,
        end_date: date,
        force_refresh: bool = False,
        delay_between_days: float = 1.0
    ) -> BackfillProgress:
        """Backfill data for a date range, day by day"""
        
        db = get_session_local()
        
        try:
            # Calculate total days
            total_days = (end_date - start_date).days + 1
            progress = BackfillProgress(db)
            progress.update(start_date, 0, total_days)
            
            current_date = start_date
            completed = 0
            
            while current_date <= end_date:
                try:
                    # Backfill this day
                    result = await self.backfill_single_day(db, current_date, force_refresh)
                    
                    completed += 1
                    progress.update(current_date, completed, total_days)
                    
                    if result["status"] == "error":
                        progress.add_error(str(current_date), result.get("error", "Unknown error"))
                    
                    logger.info(f"Day {completed}/{total_days}: {result}")
                    
                    # Small delay to be nice to Meta API and Railway
                    if delay_between_days > 0:
                        await asyncio.sleep(delay_between_days)
                    
                except Exception as e:
                    progress.add_error(str(current_date), str(e))
                    logger.error(f"Failed to process {current_date}: {e}")
                
                current_date += timedelta(days=1)
            
            return progress
            
        finally:
            db.close()
