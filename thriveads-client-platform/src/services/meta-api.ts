import { AttributionWindow, ClientDashboardData, CampaignData, DailyMetrics, MetaAdMetrics, PurchaseConversions } from '@/types/meta-ads';
import { ClientConfig } from '@/config/clients';

// Meta API Configuration
interface MetaAPIConfig {
  accessToken: string;
  apiVersion: string;
  adAccountId: string;
  clientConfig: ClientConfig;
}

// Meta API Response Types
interface MetaInsightsResponse {
  data: Array<{
    date_start: string;
    date_stop: string;
    impressions: string;
    reach: string;
    frequency: string;
    clicks: string;
    ctr: string;
    spend: string;
    cpc: string;
    cpm: string;
    cpp: string;
    actions?: Array<{
      action_type: string;
      value: string;
      '1d_click'?: string;
      '7d_click'?: string;
      'default'?: string;
    }>;
    action_values?: Array<{
      action_type: string;
      value: string;
      '1d_click'?: string;
      '7d_click'?: string;
      'default'?: string;
    }>;
    video_play_actions?: Array<{
      action_type: string;
      value: string;
    }>;
    quality_ranking?: string;
    engagement_rate_ranking?: string;
  }>;
  paging?: {
    cursors: {
      before: string;
      after: string;
    };
    next?: string;
  };
}

export class MetaAPIService {
  private config: MetaAPIConfig;
  private baseURL: string;

  constructor(config: MetaAPIConfig) {
    this.config = config;
    this.baseURL = `https://graph.facebook.com/${config.apiVersion}`;
  }

  /**
   * Fetch insights with proper attribution windows for purchases
   * This is the key method that implements correct attribution handling
   */
  async fetchInsights(params: {
    dateRange: { since: string; until: string };
    level: 'account' | 'campaign' | 'adset' | 'ad';
    campaignIds?: string[];
    breakdowns?: string[];
  }): Promise<MetaInsightsResponse> {
    const url = `${this.baseURL}/act_${this.config.adAccountId}/insights`;
    
    // Critical: Include both default and 7d_click attribution windows
    // Default = 7d_click + 1d_view (Meta's standard)
    // 7d_click = Only clicks within 7 days (more conservative)
    const queryParams = new URLSearchParams({
      access_token: this.config.accessToken,
      level: params.level,
      time_range: JSON.stringify({
        since: params.dateRange.since,
        until: params.dateRange.until
      }),
      // Essential fields for comprehensive reporting
      fields: [
        'date_start',
        'date_stop',
        'impressions',
        'reach',
        'frequency', 
        'clicks',
        'ctr',
        'spend',
        'cpc',
        'cpm',
        'cpp',
        'actions', // Contains conversion counts
        'action_values', // Contains conversion values (purchase amounts)
        'video_play_actions',
        'quality_ranking',
        'engagement_rate_ranking'
      ].join(','),
      // CRITICAL: Attribution windows for accurate purchase tracking
      action_attribution_windows: ['default', '7d_click'].join(','),
      limit: '100'
    });

    // Add optional parameters
    if (params.campaignIds && params.campaignIds.length > 0) {
      queryParams.append('filtering', JSON.stringify([{
        field: 'campaign.id',
        operator: 'IN',
        value: params.campaignIds
      }]));
    }

    if (params.breakdowns && params.breakdowns.length > 0) {
      queryParams.append('breakdowns', params.breakdowns.join(','));
    }

    const response = await fetch(`${url}?${queryParams.toString()}`);
    
    if (!response.ok) {
      throw new Error(`Meta API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Process Meta API response and extract purchase conversions with proper attribution
   */
  private extractPurchaseConversions(
    actions?: Array<any>, 
    actionValues?: Array<any>
  ): PurchaseConversions {
    // Find purchase actions and values
    const purchaseAction = actions?.find(action => action.action_type === 'purchase');
    const purchaseValue = actionValues?.find(action => action.action_type === 'purchase');

    return {
      default: {
        count: purchaseAction?.default ? parseInt(purchaseAction.default) : 0,
        value: purchaseValue?.default ? parseFloat(purchaseValue.default) : 0
      },
      '7d_click': {
        count: purchaseAction?.['7d_click'] ? parseInt(purchaseAction['7d_click']) : 0,
        value: purchaseValue?.['7d_click'] ? parseFloat(purchaseValue['7d_click']) : 0
      }
    };
  }

  /**
   * Convert Meta API response to our internal metrics format
   */
  private convertToMetrics(data: any): MetaAdMetrics {
    const purchases = this.extractPurchaseConversions(data.actions, data.action_values);
    const spend = parseFloat(data.spend || '0');

    // Calculate ROAS for both attribution windows
    const roasDefault = spend > 0 ? purchases.default.value / spend : 0;
    const roas7dClick = spend > 0 ? purchases['7d_click'].value / spend : 0;

    return {
      // Financial metrics
      spend,
      cpc: parseFloat(data.cpc || '0'),
      cpm: parseFloat(data.cpm || '0'),
      cpp: parseFloat(data.cpp || '0'),
      
      // Performance metrics
      impressions: parseInt(data.impressions || '0'),
      reach: parseInt(data.reach || '0'),
      frequency: parseFloat(data.frequency || '0'),
      clicks: parseInt(data.clicks || '0'),
      link_clicks: parseInt(data.link_clicks || '0'),
      ctr: parseFloat(data.ctr || '0'),
      
      // Conversion metrics with attribution
      purchases,
      conversions: purchases.default.count, // Use default for general conversions
      conversion_rate: parseInt(data.clicks || '0') > 0 ? purchases.default.count / parseInt(data.clicks) : 0,
      cost_per_conversion: purchases.default.count > 0 ? spend / purchases.default.count : 0,
      roas: roasDefault,
      roas_7d_click: roas7dClick,
      return_on_ad_spend: roasDefault,
      
      // Engagement metrics
      post_engagement: 0, // Would need to be calculated from actions
      engagement_rate: 0, // Would need to be calculated
      
      // Video metrics
      video_play_actions: data.video_play_actions?.[0]?.value ? parseInt(data.video_play_actions[0].value) : undefined,
      
      // Quality metrics
      quality_ranking: data.quality_ranking as any,
      engagement_rate_ranking: data.engagement_rate_ranking as any
    };
  }

  /**
   * Fetch campaign insights for a specific date range
   */
  async fetchCampaignInsights(dateRange: { since: string; until: string }): Promise<CampaignData[]> {
    const response = await this.fetchInsights({
      dateRange,
      level: 'campaign'
    });

    return response.data.map(item => ({
      id: `campaign_${Date.now()}_${Math.random()}`, // Would come from campaign.id in real API
      name: 'Campaign Name', // Would come from campaign.name in real API
      status: 'ACTIVE' as const,
      objective: 'CONVERSIONS',
      created_time: new Date().toISOString(),
      updated_time: new Date().toISOString(),
      metrics: this.convertToMetrics(item)
    }));
  }

  /**
   * Fetch daily breakdown for insights
   */
  async fetchDailyInsights(dateRange: { since: string; until: string }): Promise<DailyMetrics[]> {
    const response = await this.fetchInsights({
      dateRange,
      level: 'account',
      breakdowns: ['date_start']
    });

    return response.data.map(item => ({
      date: item.date_start,
      metrics: this.convertToMetrics(item)
    }));
  }

  /**
   * Fetch account-level summary
   */
  async fetchAccountSummary(dateRange: { since: string; until: string }): Promise<MetaAdMetrics> {
    const response = await this.fetchInsights({
      dateRange,
      level: 'account'
    });

    if (response.data.length === 0) {
      throw new Error('No data returned from Meta API');
    }

    return this.convertToMetrics(response.data[0]);
  }
}

// Factory function to create Meta API service
export function createMetaAPIService(config: MetaAPIConfig): MetaAPIService {
  return new MetaAPIService(config);
}

// Helper function to validate Meta API configuration
export function validateMetaConfig(config: Partial<MetaAPIConfig>): config is MetaAPIConfig {
  return !!(
    config.accessToken &&
    config.apiVersion &&
    config.adAccountId &&
    config.adAccountId.match(/^\d+$/) // Ad account ID should be numeric
  );
}
