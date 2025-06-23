import { NextRequest, NextResponse } from 'next/server';
import { getCurrentClientConfig } from '@/config/clients';
import { getLastMonday, getLastSunday, getFirstDayOfLastMonth, getLastDayOfLastMonth } from '@/lib/utils';

// Meta API service for fetching real data
class MetaAPIService {
  private accessToken: string;
  private adAccountId: string;
  private apiVersion: string;
  private baseURL: string;

  constructor() {
    this.accessToken = process.env.META_ACCESS_TOKEN || '';
    this.adAccountId = process.env.META_AD_ACCOUNT_ID || '';
    this.apiVersion = process.env.META_API_VERSION || 'v23.0';
    this.baseURL = `https://graph.facebook.com/${this.apiVersion}`;

    if (!this.accessToken || !this.adAccountId) {
      throw new Error('Meta API credentials not configured');
    }
  }

  async fetchInsights(params: {
    dateRange: { since: string; until: string };
    level: 'account' | 'campaign' | 'adset' | 'ad';
    breakdowns?: string[];
  }) {
    const url = `${this.baseURL}/act_${this.adAccountId}/insights`;
    
    const queryParams = new URLSearchParams({
      access_token: this.accessToken,
      level: params.level,
      time_range: JSON.stringify({
        since: params.dateRange.since,
        until: params.dateRange.until
      }),
      // Essential fields for comprehensive reporting
      fields: [
        'date_start',
        'date_stop',
        'campaign_name',
        'campaign_id',
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

    // Add optional breakdowns
    if (params.breakdowns && params.breakdowns.length > 0) {
      queryParams.append('breakdowns', params.breakdowns.join(','));
    }

    console.log('Meta API Request URL:', `${url}?${queryParams.toString()}`);

    const response = await fetch(`${url}?${queryParams.toString()}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Meta API Error:', response.status, errorText);
      throw new Error(`Meta API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Meta API Response:', JSON.stringify(data, null, 2));
    return data;
  }

  // Extract purchase conversions with proper attribution
  private extractPurchaseConversions(actions?: Array<any>, actionValues?: Array<any>) {
    const purchaseAction = actions?.find(action => action.action_type === 'purchase');
    const purchaseValue = actionValues?.find(action => action.action_type === 'purchase');

    // If no default attribution, use the total value as default
    const defaultCount = purchaseAction?.default ? parseInt(purchaseAction.default) :
                        (purchaseAction?.value ? parseInt(purchaseAction.value) : 0);
    const defaultValue = purchaseValue?.default ? parseFloat(purchaseValue.default) :
                        (purchaseValue?.value ? parseFloat(purchaseValue.value) : 0);

    return {
      default: {
        count: defaultCount,
        value: defaultValue
      },
      '7d_click': {
        count: purchaseAction?.['7d_click'] ? parseInt(purchaseAction['7d_click']) : 0,
        value: purchaseValue?.['7d_click'] ? parseFloat(purchaseValue['7d_click']) : 0
      }
    };
  }

  // Convert Meta API response to our internal format
  convertToMetrics(data: any) {
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
      conversions: purchases.default.count,
      conversion_rate: parseInt(data.clicks || '0') > 0 ? purchases.default.count / parseInt(data.clicks) : 0,
      cost_per_conversion: purchases.default.count > 0 ? spend / purchases.default.count : 0,
      roas: roasDefault,
      roas_7d_click: roas7dClick,
      return_on_ad_spend: roasDefault,
      
      // Engagement metrics
      post_engagement: 0,
      engagement_rate: 0,
      
      // Video metrics
      video_play_actions: data.video_play_actions?.[0]?.value ? parseInt(data.video_play_actions[0].value) : undefined,
      
      // Quality metrics
      quality_ranking: data.quality_ranking as any,
      engagement_rate_ranking: data.engagement_rate_ranking as any
    };
  }
}

// API Route Handler
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || 'last_week';
    
    // Calculate date ranges
    const now = new Date();
    let dateRange;
    
    if (period === 'last_week') {
      dateRange = {
        since: getLastMonday(now).toISOString().split('T')[0],
        until: getLastSunday(now).toISOString().split('T')[0]
      };
    } else {
      dateRange = {
        since: getFirstDayOfLastMonth(now).toISOString().split('T')[0],
        until: getLastDayOfLastMonth(now).toISOString().split('T')[0]
      };
    }

    console.log('Fetching Meta data for period:', period, 'Date range:', dateRange);

    const metaAPI = new MetaAPIService();
    
    // Fetch account-level summary
    const accountData = await metaAPI.fetchInsights({
      dateRange,
      level: 'account'
    });

    // Fetch campaign-level data
    const campaignData = await metaAPI.fetchInsights({
      dateRange,
      level: 'campaign'
    });

    // Fetch daily breakdown for last week
    let dailyData = null;
    if (period === 'last_week') {
      try {
        // For daily breakdown, we need to make separate requests for each day
        const dailyPromises = [];
        const startDate = new Date(dateRange.since);
        const endDate = new Date(dateRange.until);

        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
          const dayString = d.toISOString().split('T')[0];
          dailyPromises.push(
            metaAPI.fetchInsights({
              dateRange: { since: dayString, until: dayString },
              level: 'account'
            })
          );
        }

        const dailyResults = await Promise.all(dailyPromises);
        dailyData = {
          data: dailyResults.map((result, index) => {
            const dayString = new Date(startDate.getTime() + index * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            return {
              date_start: dayString,
              ...(result.data[0] || {})
            };
          }).filter(item => item.impressions) // Only include days with data
        };
      } catch (error) {
        console.error('Error fetching daily data:', error);
        dailyData = { data: [] };
      }
    }

    // Process the data
    const summary = accountData.data.length > 0 ? metaAPI.convertToMetrics(accountData.data[0]) : null;
    
    const campaigns = campaignData.data.map((item: any) => ({
      id: item.campaign_id || `campaign_${Date.now()}_${Math.random()}`,
      name: item.campaign_name || 'Unnamed Campaign',
      status: 'ACTIVE' as const,
      objective: 'CONVERSIONS',
      created_time: new Date().toISOString(),
      updated_time: new Date().toISOString(),
      metrics: metaAPI.convertToMetrics(item)
    }));

    const dailyBreakdown = dailyData ? dailyData.data.map((item: any) => ({
      date: item.date_start,
      metrics: metaAPI.convertToMetrics(item)
    })) : [];

    const clientConfig = getCurrentClientConfig();

    const response = {
      client_id: clientConfig.id,
      client_name: clientConfig.name,
      ad_account_id: clientConfig.metaAdAccountId,
      last_updated: new Date().toISOString(),
      period,
      date_range: dateRange,
      summary,
      campaigns,
      daily_breakdown: dailyBreakdown
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Meta API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch Meta insights', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
