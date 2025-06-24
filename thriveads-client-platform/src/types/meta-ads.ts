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
  metrics: MetaAdMetrics;
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
    geo_locations?: any;
  };
  metrics: MetaAdMetrics;
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
    object_story_spec?: any;
  };
  facebook_url: string; // Direct link to Facebook ad
  metrics: MetaAdMetrics;
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
    summary: MetaAdMetrics;
  };
  previous_week: {
    date_range: DateRange;
    summary: MetaAdMetrics;
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

export interface DailyMetrics {
  date: string;
  metrics: MetaAdMetrics;
}

export interface WeeklyMetrics {
  week_start: string;
  week_end: string;
  metrics: MetaAdMetrics;
}

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
    summary: MetaAdMetrics;
    campaigns: CampaignData[];
    daily_breakdown: DailyMetrics[];
  };
  
  last_month: {
    date_range: {
      since: string;
      until: string;
    };
    summary: MetaAdMetrics;
    campaigns: CampaignData[];
    weekly_breakdown: WeeklyMetrics[];
  };
}

export interface MetricChange {
  value: number;
  percentage: number;
  trend: 'up' | 'down' | 'neutral';
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
