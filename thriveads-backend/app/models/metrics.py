"""
Metrics database model for storing performance data
"""

from sqlalchemy import Column, String, DateTime, Integer, Numeric, Date, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class AdMetrics(Base):
    """Model for storing daily ad performance metrics"""
    
    __tablename__ = "ad_metrics"
    
    # Composite primary key
    id = Column(String, primary_key=True)  # Generated: ad_id + date
    ad_id = Column(String, ForeignKey("ads.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(10, 2), default=0)
    
    # Calculated metrics
    ctr = Column(Numeric(5, 4), default=0)  # Click-through rate
    cpc = Column(Numeric(10, 2), default=0)  # Cost per click
    cpm = Column(Numeric(10, 2), default=0)  # Cost per mille
    roas = Column(Numeric(10, 4), default=0)  # Return on ad spend
    frequency = Column(Numeric(5, 2), default=0)
    
    # Attribution model used
    attribution = Column(String, default="default")
    
    # Currency
    currency = Column(String, default="CZK")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ad = relationship("Ad")
    
    def __repr__(self):
        return f"<AdMetrics(ad_id={self.ad_id}, date={self.date}, roas={self.roas})>"


class CampaignMetrics(Base):
    """Model for storing daily campaign performance metrics"""
    
    __tablename__ = "campaign_metrics"
    
    # Composite primary key
    id = Column(String, primary_key=True)  # Generated: campaign_id + date
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Performance metrics (aggregated from ads)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(10, 2), default=0)
    
    # Calculated metrics
    ctr = Column(Numeric(5, 4), default=0)
    cpc = Column(Numeric(10, 2), default=0)
    cpm = Column(Numeric(10, 2), default=0)
    roas = Column(Numeric(10, 4), default=0)
    frequency = Column(Numeric(5, 2), default=0)
    
    # Attribution model used
    attribution = Column(String, default="default")
    
    # Currency
    currency = Column(String, default="CZK")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign")
    
    def __repr__(self):
        return f"<CampaignMetrics(campaign_id={self.campaign_id}, date={self.date}, roas={self.roas})>"


class WeeklyAdMetrics(Base):
    """Model for storing weekly aggregated ad performance metrics"""

    __tablename__ = "weekly_ad_metrics"

    # Composite primary key
    id = Column(String, primary_key=True)  # Generated: ad_id + week_start_date
    ad_id = Column(String, ForeignKey("ads.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)  # Monday of the week
    week_end_date = Column(Date, nullable=False)    # Sunday of the week

    # Aggregated performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(12, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(12, 2), default=0)

    # Calculated metrics
    ctr = Column(Numeric(5, 4), default=0)
    cpc = Column(Numeric(10, 2), default=0)
    cpm = Column(Numeric(10, 2), default=0)
    roas = Column(Numeric(10, 4), default=0)
    frequency = Column(Numeric(5, 2), default=0)

    # Attribution model used
    attribution = Column(String, default="default")

    # Currency
    currency = Column(String, default="CZK")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ad = relationship("Ad")

    def __repr__(self):
        return f"<WeeklyAdMetrics(ad_id={self.ad_id}, week={self.week_start_date}, roas={self.roas})>"


class MonthlyAdMetrics(Base):
    """Model for storing monthly aggregated ad performance metrics"""

    __tablename__ = "monthly_ad_metrics"

    # Composite primary key
    id = Column(String, primary_key=True)  # Generated: ad_id + year + month
    ad_id = Column(String, ForeignKey("ads.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    month_start_date = Column(Date, nullable=False)  # First day of month
    month_end_date = Column(Date, nullable=False)    # Last day of month

    # Aggregated performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(12, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(12, 2), default=0)

    # Calculated metrics
    ctr = Column(Numeric(5, 4), default=0)
    cpc = Column(Numeric(10, 2), default=0)
    cpm = Column(Numeric(10, 2), default=0)
    roas = Column(Numeric(10, 4), default=0)
    frequency = Column(Numeric(5, 2), default=0)

    # Attribution model used
    attribution = Column(String, default="default")

    # Currency
    currency = Column(String, default="CZK")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ad = relationship("Ad")

    def __repr__(self):
        return f"<MonthlyAdMetrics(ad_id={self.ad_id}, month={self.year}-{self.month:02d}, roas={self.roas})>"


class WeeklyCampaignMetrics(Base):
    """Model for storing weekly aggregated campaign performance metrics"""

    __tablename__ = "weekly_campaign_metrics"

    # Composite primary key
    id = Column(String, primary_key=True)  # Generated: campaign_id + week_start_date
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    week_start_date = Column(Date, nullable=False)  # Monday of the week
    week_end_date = Column(Date, nullable=False)    # Sunday of the week

    # Aggregated performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(12, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(12, 2), default=0)

    # Calculated metrics
    ctr = Column(Numeric(5, 4), default=0)
    cpc = Column(Numeric(10, 2), default=0)
    cpm = Column(Numeric(10, 2), default=0)
    roas = Column(Numeric(10, 4), default=0)
    frequency = Column(Numeric(5, 2), default=0)

    # Attribution model used
    attribution = Column(String, default="default")

    # Currency
    currency = Column(String, default="CZK")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign")

    def __repr__(self):
        return f"<WeeklyCampaignMetrics(campaign_id={self.campaign_id}, week={self.week_start_date}, roas={self.roas})>"


class MonthlyCampaignMetrics(Base):
    """Model for storing monthly aggregated campaign performance metrics"""

    __tablename__ = "monthly_campaign_metrics"

    # Composite primary key
    id = Column(String, primary_key=True)  # Generated: campaign_id + year + month
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    month_start_date = Column(Date, nullable=False)  # First day of month
    month_end_date = Column(Date, nullable=False)    # Last day of month

    # Aggregated performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(12, 2), default=0)
    conversions = Column(Integer, default=0)
    conversion_value = Column(Numeric(12, 2), default=0)

    # Calculated metrics
    ctr = Column(Numeric(5, 4), default=0)
    cpc = Column(Numeric(10, 2), default=0)
    cpm = Column(Numeric(10, 2), default=0)
    roas = Column(Numeric(10, 4), default=0)
    frequency = Column(Numeric(5, 2), default=0)

    # Attribution model used
    attribution = Column(String, default="default")

    # Currency
    currency = Column(String, default="CZK")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign")

    def __repr__(self):
        return f"<MonthlyCampaignMetrics(campaign_id={self.campaign_id}, month={self.year}-{self.month:02d}, roas={self.roas})>"


class DataSyncLog(Base):
    """Model for tracking data synchronization from Meta API"""

    __tablename__ = "data_sync_log"

    id = Column(String, primary_key=True)  # UUID
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)

    # Sync details
    sync_type = Column(String, nullable=False)  # 'daily', 'weekly', 'monthly', 'backfill'
    sync_date = Column(Date, nullable=False)    # Date being synced
    status = Column(String, nullable=False)     # 'pending', 'running', 'completed', 'failed'

    # Meta API details
    attribution = Column(String, default="default")
    records_processed = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    client = relationship("Client")

    def __repr__(self):
        return f"<DataSyncLog(client_id={self.client_id}, date={self.sync_date}, status={self.status})>"


# Database indexes for performance optimization
Index('idx_ad_metrics_ad_date', AdMetrics.ad_id, AdMetrics.date)
Index('idx_ad_metrics_date_roas', AdMetrics.date, AdMetrics.roas.desc())
Index('idx_campaign_metrics_campaign_date', CampaignMetrics.campaign_id, CampaignMetrics.date)
Index('idx_weekly_ad_metrics_ad_week', WeeklyAdMetrics.ad_id, WeeklyAdMetrics.week_start_date)
Index('idx_weekly_ad_metrics_week_roas', WeeklyAdMetrics.week_start_date, WeeklyAdMetrics.roas.desc())
Index('idx_monthly_ad_metrics_ad_month', MonthlyAdMetrics.ad_id, MonthlyAdMetrics.year, MonthlyAdMetrics.month)
Index('idx_monthly_ad_metrics_month_roas', MonthlyAdMetrics.year, MonthlyAdMetrics.month, MonthlyAdMetrics.roas.desc())
Index('idx_weekly_campaign_metrics_campaign_week', WeeklyCampaignMetrics.campaign_id, WeeklyCampaignMetrics.week_start_date)
Index('idx_monthly_campaign_metrics_campaign_month', MonthlyCampaignMetrics.campaign_id, MonthlyCampaignMetrics.year, MonthlyCampaignMetrics.month)
Index('idx_data_sync_log_client_date', DataSyncLog.client_id, DataSyncLog.sync_date)
Index('idx_data_sync_log_status', DataSyncLog.status)
