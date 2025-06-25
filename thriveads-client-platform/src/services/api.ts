/**
 * API Service for ThriveAds Platform
 * Handles all communication with the Railway backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://thriveads-platform-production.up.railway.app';
const CLIENT_ID = '513010266454814'; // Mimilátky CZ

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface CampaignMetrics {
  impressions: number;
  clicks: number;
  spend: number;
  conversions: number;
  conversion_value: number;
  ctr: number;
  cpc: number;
  cpm: number;
  roas: number;
  frequency: number;
}

export interface Campaign {
  id: string;
  name: string;
  status: string;
  metrics: CampaignMetrics;
  currency: string;
  attribution: string;
}

export interface AdMetrics extends CampaignMetrics {
  reach?: number;
  link_clicks?: number;
}

export interface Ad {
  id: string;
  name: string;
  status: string;
  metrics: AdMetrics;
  currency: string;
  attribution: string;
  facebook_url?: string;
}

export interface ConversionFunnelStage {
  stage: string;
  count: number;
  conversion_rate?: number;
}

export interface ConversionFunnel {
  stages: ConversionFunnelStage[];
  total_impressions: number;
  total_conversions: number;
  overall_conversion_rate: number;
}

export interface WeekComparison {
  client_id: string;
  current_week: {
    start_date: string;
    end_date: string;
    metrics: {
      spend: number;
      roas: number;
      conversions: number;
      ctr: number;
      impressions: number;
      clicks: number;
    };
  };
  previous_week: {
    start_date: string;
    end_date: string;
    metrics: {
      spend: number;
      roas: number;
      conversions: number;
      ctr: number;
      impressions: number;
      clicks: number;
    };
  };
  metrics_comparison: {
    spend_change: number;
    roas_change: number;
    conversions_change: number;
    ctr_change: number;
    impressions_change: number;
    clicks_change: number;
  };
  currency: string;
}

export interface DashboardData {
  client_id: string;
  client_name: string;
  ad_account_id: string;
  last_updated: string;
  period: string;
  date_range: {
    since: string;
    until: string;
  };
  summary: CampaignMetrics;
  campaigns: CampaignData[];
  daily_breakdown?: DailyMetrics[];
  weekly_breakdown?: WeeklyMetrics[];
  week_comparison?: WeekComparison;
}

export interface DailyMetrics {
  date: string;
  metrics: CampaignMetrics;
}

export interface WeeklyMetrics {
  week_start: string;
  week_end: string;
  metrics: CampaignMetrics;
}

class ApiService {
  private baseUrl: string;
  private clientId: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.clientId = CLIENT_ID;
  }

  private async makeRequest<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      console.log(`Making API request to: ${url}`);
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.detail || data.error || `HTTP ${response.status}`,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      console.error('API request failed:', error);
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  /**
   * Get top performing campaigns
   */
  async getTopCampaigns(
    period: 'last_week' | 'last_month' = 'last_week',
    attribution: 'default' | '7d_click' = 'default',
    limit: number = 10
  ): Promise<ApiResponse<Campaign[]>> {
    const params = new URLSearchParams({
      client_id: this.clientId,
      period,
      attribution,
      limit: limit.toString(),
    });

    return this.makeRequest<Campaign[]>(`/api/v1/campaigns/top-performing?${params}`);
  }

  /**
   * Get top performing ads
   */
  async getTopAds(
    period: 'last_week' | 'last_month' = 'last_week',
    attribution: 'default' | '7d_click' = 'default',
    limit: number = 10
  ): Promise<ApiResponse<Ad[]>> {
    const params = new URLSearchParams({
      client_id: this.clientId,
      period,
      attribution,
      limit: limit.toString(),
    });

    return this.makeRequest<Ad[]>(`/api/v1/ads/top-performing?${params}`);
  }

  /**
   * Get conversion funnel data
   */
  async getConversionFunnel(
    period: 'last_week' | 'last_month' = 'last_week'
  ): Promise<ApiResponse<ConversionFunnel>> {
    const params = new URLSearchParams({
      client_id: this.clientId,
      period,
    });

    return this.makeRequest<ConversionFunnel>(`/api/v1/metrics/funnel?${params}`);
  }

  /**
   * Get week-on-week comparison
   */
  async getWeekComparison(): Promise<ApiResponse<WeekComparison>> {
    const params = new URLSearchParams({
      client_id: this.clientId,
    });

    return this.makeRequest<WeekComparison>(`/api/v1/metrics/week-on-week?${params}`);
  }

  /**
   * Get dashboard data (account summary + campaigns)
   */
  async getDashboardData(
    period: 'last_week' | 'last_month' = 'last_week'
  ): Promise<ApiResponse<DashboardData>> {
    // For now, we'll combine multiple API calls to get dashboard data
    // In the future, the backend could provide a single dashboard endpoint

    try {
      console.log('Starting getDashboardData for period:', period);

      // Fetch all required data in parallel
      const campaignsPromise = this.getTopCampaigns(period, 'default', 20);
      const weekComparisonPromise = this.getWeekComparison();

      // Get breakdown data based on period
      let breakdownPromise: Promise<ApiResponse<DailyMetrics[]>> | Promise<ApiResponse<WeeklyMetrics[]>>;
      if (period === 'last_week') {
        breakdownPromise = this.getDailyBreakdown(period);
      } else {
        breakdownPromise = this.getWeeklyBreakdown(4);
      }

      const [campaignsResponse, weekComparisonResponse, breakdownResponse] = await Promise.all([
        campaignsPromise,
        weekComparisonPromise,
        breakdownPromise
      ]);

      console.log('API responses received:', {
        campaigns: campaignsResponse.status,
        weekComparison: weekComparisonResponse.status,
        breakdown: breakdownResponse.status
      });

      if (campaignsResponse.error) {
        console.error('Campaigns error:', campaignsResponse.error);
        return campaignsResponse;
      }

      if (weekComparisonResponse.error) {
        console.error('Week comparison error:', weekComparisonResponse.error);
        return weekComparisonResponse;
      }

      if (breakdownResponse.error) {
        console.error('Breakdown error:', breakdownResponse.error);
        return breakdownResponse;
      }

      const campaigns = campaignsResponse.data || [];
      const weekComparison = weekComparisonResponse.data!;
      const breakdownData = breakdownResponse.data || [];

      // Calculate summary metrics from campaigns
      const summary = campaigns.reduce((acc, campaign) => {
        acc.spend += campaign.metrics.spend;
        acc.impressions += campaign.metrics.impressions;
        acc.clicks += campaign.metrics.clicks;
        acc.conversions += campaign.metrics.conversions;
        acc.conversion_value += campaign.metrics.conversion_value;
        return acc;
      }, {
        spend: 0,
        impressions: 0,
        clicks: 0,
        conversions: 0,
        conversion_value: 0,
        ctr: 0,
        cpc: 0,
        cpm: 0,
        roas: 0,
        roas_7d_click: 0
      });

      // Calculate derived metrics
      if (summary.impressions > 0) {
        summary.ctr = (summary.clicks / summary.impressions) * 100;
        summary.cpm = (summary.spend / summary.impressions) * 1000;
      }
      if (summary.clicks > 0) {
        summary.cpc = summary.spend / summary.clicks;
      }
      if (summary.spend > 0) {
        summary.roas = summary.conversion_value / summary.spend;
        summary.roas_7d_click = summary.roas; // Same for now
      }

      const dashboardData = {
        client_id: this.clientId,
        client_name: 'Mimilátky CZ',
        ad_account_id: this.clientId,
        last_updated: new Date().toISOString(),
        period,
        date_range: {
          since: weekComparison.current_week.start_date || '',
          until: weekComparison.current_week.end_date || ''
        },
        summary,
        campaigns,
        // Include breakdown data based on period
        ...(period === 'last_week'
          ? { daily_breakdown: breakdownData as DailyMetrics[] }
          : { weekly_breakdown: breakdownData as WeeklyMetrics[] }
        )
      };

      console.log('Dashboard data assembled successfully:', {
        campaigns: campaigns.length,
        summary: summary,
        dateRange: dashboardData.date_range
      });

      return {
        data: dashboardData,
        status: 200
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Failed to fetch dashboard data',
        status: 500
      };
    }
  }

  /**
   * Get daily breakdown data for charts
   */
  async getDailyBreakdown(
    period: 'last_week' | 'last_month' = 'last_week'
  ): Promise<ApiResponse<DailyMetrics[]>> {
    const params = new URLSearchParams({
      client_id: this.clientId,
      period,
    });

    return this.makeRequest<DailyMetrics[]>(`/api/v1/metrics/daily-breakdown?${params}`);
  }

  /**
   * Get weekly breakdown data for charts
   */
  async getWeeklyBreakdown(
    weeks: number = 4
  ): Promise<ApiResponse<WeeklyMetrics[]>> {
    const params = new URLSearchParams({
      client_id: this.clientId,
      weeks: weeks.toString(),
    });

    return this.makeRequest<WeeklyMetrics[]>(`/api/v1/metrics/weekly-breakdown?${params}`);
  }

  /**
   * Get client information
   */
  async getClientInfo(): Promise<ApiResponse<{ id: string; name: string; currency: string }>> {
    return this.makeRequest<{ id: string; name: string; currency: string }>(`/api/v1/clients/${this.clientId}`);
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<ApiResponse<{ status: string; message: string }>> {
    return this.makeRequest<{ status: string; message: string }>('/health');
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
