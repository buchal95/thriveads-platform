"""
Ad Pydantic schemas
"""

from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class AdBase(BaseModel):
    """Base ad schema"""
    id: str
    name: str
    status: str
    campaign_id: str
    adset_id: str


class Ad(AdBase):
    """Full ad schema"""
    client_id: str
    creative_id: Optional[str] = None
    preview_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AdMetrics(BaseModel):
    """Ad performance metrics"""
    impressions: int
    clicks: int
    spend: Decimal
    conversions: int
    conversion_value: Decimal
    ctr: float  # Click-through rate
    cpc: Decimal  # Cost per click
    cpm: Decimal  # Cost per mille
    roas: float  # Return on ad spend
    frequency: float


class AdPerformance(BaseModel):
    """Ad with performance metrics"""
    # Ad information
    id: str
    name: str
    status: str
    campaign_name: str
    adset_name: str
    
    # Creative information
    preview_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
    creative_body: Optional[str] = None
    creative_title: Optional[str] = None
    
    # Performance metrics
    metrics: AdMetrics
    
    # Comparison metrics (week-on-week)
    previous_period_metrics: Optional[AdMetrics] = None
    metrics_change: Optional[Dict[str, float]] = None  # Percentage changes
    
    # Currency
    currency: str = "CZK"
    
    # Attribution model used
    attribution: str = "default"


class AdPerformanceHistory(BaseModel):
    """Historical performance data for an ad"""
    ad_id: str
    date: datetime
    metrics: AdMetrics
    currency: str = "CZK"


class AdCreate(BaseModel):
    """Schema for creating a new ad"""
    id: str
    name: str
    status: str
    client_id: str
    campaign_id: str
    adset_id: Optional[str] = None
    creative_id: Optional[str] = None
    preview_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None


class AdUpdate(BaseModel):
    """Schema for updating an ad"""
    name: Optional[str] = None
    status: Optional[str] = None
    preview_url: Optional[HttpUrl] = None
    facebook_url: Optional[HttpUrl] = None
