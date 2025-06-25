// Meta Ads data types based on Meta Marketing API

// Attribution window types for Meta API
export type AttributionWindow =
  | '1d_view'
  | '7d_view'
  | '28d_view'
  | '1d_click'
  | '7d_click'
  | '28d_click'
  | '1d_ev'
  | 'dda'
  | 'default';

// Purchase conversion metrics with attribution windows
export interface PurchaseConversions {
  // Default attribution (7d_click + 1d_view)
  default: {
    value: number;
    count: number;
  };
  // 7-day click attribution only
  '7d_click': {
    value: number;
    count: number;
  };
}

export interface MetaAdMetrics {
  // Financial metrics
  spend: number;
  cpc: number;
  cpm: number;
  cpp: number;

  // Performance metrics
  impressions: number;
  reach: number;
  frequency: number;
  clicks: number;
  link_clicks: number;
  ctr: number;

  // Conversion metrics with attribution windows
  purchases: PurchaseConversions;
  conversions: number; // Total conversions (default attribution)
  conversion_rate: number;
  cost_per_conversion: number;
  roas: number; // Based on default attribution
  roas_7d_click: number; // Based on 7d_click attribution only
  return_on_ad_spend: number;

  // Engagement metrics
  post_engagement: number;
  engagement_rate: number;

  // Video metrics (optional)
  video_play_actions?: number;
  video_view_rate?: number;
  video_avg_time_watched_actions?: number;

  // Quality metrics
  quality_ranking?: 'ABOVE_AVERAGE' | 'AVERAGE' | 'BELOW_AVERAGE';
  engagement_rate_ranking?: 'ABOVE_AVERAGE' | 'AVERAGE' | 'BELOW_AVERAGE';
}

export interface CampaignData {
  id: string;
  name: string;
  status: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  objective: string;
  created_time: string;
  updated_time: string;
  metrics: CampaignMetrics;
}

export interface AdSetData {
  id: string;
  name: string;
  campaign_id: string;
  status: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  targeting?: {
    age_min?: number;
    age_max?: number;
    genders?: number[];
    geo_locations?: {
      countries?: string[];
      regions?: Array<{ key: string; name: string }>;
      cities?: Array<{ key: string; name: string; region_id?: string }>;
    };
  };
  metrics: CampaignMetrics;
}

export interface AdData {
  id: string;
  name: string;
  adset_id: string;
  adset_name: string;
  campaign_id: string;
  campaign_name: string;
  status: 'ACTIVE' | 'PAUSED' | 'DELETED' | 'ARCHIVED';
  creative?: {
    title?: string;
    body?: string;
    image_url?: string;
    thumbnail_url?: string;
    video_url?: string;
    object_story_spec?: {
      page_id?: string;
      instagram_actor_id?: string;
      link_data?: {
        link?: string;
        message?: string;
        name?: string;
        description?: string;
        picture?: string;
      };
    };
  };
  facebook_url: string; // Direct link to Facebook ad
  metrics: CampaignMetrics;
}

// Week-on-week comparison types
export interface MetricChange {
  current: number;
  previous: number;
  absolute_change: number;
  percentage_change: number;
  trend: 'up' | 'down' | 'neutral';
}

export interface WeekComparison {
  current_week: {
    date_range: DateRange;
    summary: CampaignMetrics;
  };
  previous_week: {
    date_range: DateRange;
    summary: CampaignMetrics;
  };
  changes: {
    spend: MetricChange;
    impressions: MetricChange;
    clicks: MetricChange;
    conversions: MetricChange;
    roas: MetricChange;
    roas_7d_click: MetricChange;
  };
}

// Account information
export interface AccountInfo {
  id: string;
  name: string;
  currency: string;
  timezone_name: string;
  account_status: number;
}

// Import types from api service to avoid duplication
import { CampaignMetrics, DailyMetrics, WeeklyMetrics } from '../services/api';

export interface ClientDashboardData {
  client_id: string;
  client_name: string;
  ad_account_id: string;
  last_updated: string;

  // Time period data
  last_week: {
    date_range: {
      since: string;
      until: string;
    };
    summary: CampaignMetrics;
    campaigns: CampaignData[];
    daily_breakdown: DailyMetrics[];
  };

  last_month: {
    date_range: {
      since: string;
      until: string;
    };
    summary: CampaignMetrics;
    campaigns: CampaignData[];
    weekly_breakdown: WeeklyMetrics[];
  };
}



export interface MetricCardData {
  label: string;
  value: string;
  change: MetricChange;
  icon?: string;
}

// Time period options
export type TimePeriod = 'last_week' | 'last_month';

export interface DateRange {
  since: string;
  until: string;
}
