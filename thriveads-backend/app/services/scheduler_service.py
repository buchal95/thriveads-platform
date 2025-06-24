"""
Scheduler service for automated daily data sync
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any
import schedule
import time
import threading

from app.core.config import settings
from app.services.meta_service import MetaService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling automated data sync tasks"""
    
    def __init__(self):
        self.meta_service = MetaService()
        self.is_running = False
        self.scheduler_thread = None
    
    async def sync_yesterday_data_job(self) -> Dict[str, Any]:
        """Job to sync yesterday's data - runs daily"""
        try:
            yesterday = date.today() - timedelta(days=1)
            
            logger.info(f"Starting automated sync for {yesterday}")
            
            # Get yesterday's campaigns data
            campaigns_data = await self.meta_service.get_campaigns_with_metrics(
                client_id=settings.DEFAULT_CLIENT_ID,
                start_date=yesterday,
                end_date=yesterday
            )
            
            # Get yesterday's ads data
            ads_data = await self.meta_service.get_ads_with_metrics(
                client_id=settings.DEFAULT_CLIENT_ID,
                start_date=yesterday,
                end_date=yesterday
            )
            
            # TODO: Store in database (implement when database models are ready)
            
            result = {
                "status": "success",
                "date": str(yesterday),
                "campaigns_synced": len(campaigns_data),
                "ads_synced": len(ads_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Automated sync completed for {yesterday}", **result)
            return result
            
        except Exception as e:
            logger.error(f"Automated sync failed for {yesterday}: {e}")
            return {
                "status": "error",
                "date": str(yesterday),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_async_job(self, job_func):
        """Helper to run async jobs in scheduler"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(job_func())
            logger.info("Scheduled job completed", result=result)
        except Exception as e:
            logger.error(f"Scheduled job failed: {e}")
        finally:
            loop.close()
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Schedule daily sync at 6:00 AM (after Meta API data is available)
        schedule.every().day.at("06:00").do(
            self.run_async_job,
            self.sync_yesterday_data_job
        )

        # Schedule weekly summary (optional)
        schedule.every().monday.at("07:00").do(
            self.run_async_job,
            self.weekly_summary_job
        )

        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("Scheduler started - Daily sync at 6:00 AM, Weekly summary on Mondays at 7:00 AM")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    async def weekly_summary_job(self) -> Dict[str, Any]:
        """Weekly summary job - runs every Monday"""
        try:
            # Get last week's data summary
            end_date = date.today() - timedelta(days=1)  # Yesterday
            start_date = end_date - timedelta(days=7)    # Last 7 days
            
            logger.info(f"Generating weekly summary for {start_date} to {end_date}")
            
            # Get week's campaigns data
            campaigns_data = await self.meta_service.get_campaigns_with_metrics(
                client_id=settings.DEFAULT_CLIENT_ID,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate summary metrics
            total_spend = sum(float(c.get('spend', 0)) for c in campaigns_data)
            total_impressions = sum(int(c.get('impressions', 0)) for c in campaigns_data)
            total_clicks = sum(int(c.get('clicks', 0)) for c in campaigns_data)
            total_conversions = sum(int(c.get('conversions', 0)) for c in campaigns_data)
            
            result = {
                "status": "success",
                "period": "weekly",
                "date_range": {
                    "start_date": str(start_date),
                    "end_date": str(end_date)
                },
                "summary": {
                    "total_spend": total_spend,
                    "total_impressions": total_impressions,
                    "total_clicks": total_clicks,
                    "total_conversions": total_conversions,
                    "average_cpc": total_spend / total_clicks if total_clicks > 0 else 0,
                    "conversion_rate": (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
                },
                "campaigns_count": len(campaigns_data),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Weekly summary generated", **result)
            return result
            
        except Exception as e:
            logger.error(f"Weekly summary failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "scheduled_jobs": len(schedule.jobs),
            "next_run": str(schedule.next_run()) if schedule.jobs else None,
            "jobs": [
                {
                    "job": str(job.job_func),
                    "next_run": str(job.next_run),
                    "interval": str(job.interval)
                }
                for job in schedule.jobs
            ]
        }


# Global scheduler instance
scheduler_service = SchedulerService()
