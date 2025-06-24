import { NextRequest, NextResponse } from 'next/server';
import { getCurrentClientConfig } from '@/config/clients';
import { getLastMonday, getLastSunday } from '@/lib/utils';
import { WeekComparison, MetricChange } from '@/types/meta-ads';

// Meta API service for week-on-week comparison
class MetaComparisonAPIService {
  private accessToken: string;
  private adAccountId: string;
  private apiVersion: string;
  private baseURL: string;

  constructor() {
    this.accessToken = process.env.META_ACCESS_TOKEN || '';
    this.adAccountId = process.env.META_AD_ACCOUNT_ID || '';
    this.apiVersion = process.env.META_API_VERSION || 'v21.0';
    this.baseURL = `https://graph.facebook.com/${this.apiVersion}`;

    if (!this.accessToken || !this.adAccountId) {
      throw new Error('Meta API credentials not configured');
    }
  }

  async fetchInsights(dateRange: { since: string; until: string }) {
    const url = `${this.baseURL}/act_${this.adAccountId}/insights`;
    
    const queryParams = new URLSearchParams({
      access_token: this.accessToken,
      level: 'account',
      time_range: JSON.stringify({
        since: dateRange.since,
        until: dateRange.until
      }),
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
        'actions',
        'action_values',
        'video_play_actions',
        'quality_ranking',
        'engagement_rate_ranking'
      ].join(','),
      action_attribution_windows: ['default', '7d_click'].join(','),
      limit: '100'
    });

    const response = await fetch(`${url}?${queryParams.toString()}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Meta Comparison API Error:', response.status, errorText);
      throw new Error(`Meta Comparison API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  // Extract purchase conversions with proper attribution
  private extractPurchaseConversions(actions?: Array<any>, actionValues?: Array<any>) {
    const purchaseAction = actions?.find(action => action.action_type === 'purchase');
    const purchaseValue = actionValues?.find(action => action.action_type === 'purchase');

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

  // Convert Meta API response to our internal metrics format
  convertToMetrics(data: any) {
    const purchases = this.extractPurchaseConversions(data.actions, data.action_values);
    const spend = parseFloat(data.spend || '0');

    const roasDefault = spend > 0 ? purchases.default.value / spend : 0;
    const roas7dClick = spend > 0 ? purchases['7d_click'].value / spend : 0;

    return {
      spend,
      cpc: parseFloat(data.cpc || '0'),
      cpm: parseFloat(data.cpm || '0'),
      cpp: parseFloat(data.cpp || '0'),
      impressions: parseInt(data.impressions || '0'),
      reach: parseInt(data.reach || '0'),
      frequency: parseFloat(data.frequency || '0'),
      clicks: parseInt(data.clicks || '0'),
      link_clicks: parseInt(data.link_clicks || '0'),
      ctr: parseFloat(data.ctr || '0'),
      purchases,
      conversions: purchases.default.count,
      conversion_rate: parseInt(data.clicks || '0') > 0 ? purchases.default.count / parseInt(data.clicks) : 0,
      cost_per_conversion: purchases.default.count > 0 ? spend / purchases.default.count : 0,
      roas: roasDefault,
      roas_7d_click: roas7dClick,
      return_on_ad_spend: roasDefault,
      post_engagement: 0,
      engagement_rate: 0,
      video_play_actions: data.video_play_actions?.[0]?.value ? parseInt(data.video_play_actions[0].value) : undefined,
      quality_ranking: data.quality_ranking as any,
      engagement_rate_ranking: data.engagement_rate_ranking as any
    };
  }

  // Calculate metric change
  private calculateChange(current: number, previous: number): MetricChange {
    const absolute_change = current - previous;
    const percentage_change = previous > 0 ? (absolute_change / previous) * 100 : 0;
    
    let trend: 'up' | 'down' | 'neutral' = 'neutral';
    if (Math.abs(percentage_change) > 0.1) { // Only consider significant changes
      trend = percentage_change > 0 ? 'up' : 'down';
    }

    return {
      current,
      previous,
      absolute_change,
      percentage_change,
      trend
    };
  }

  // Get week ranges
  private getWeekRanges() {
    const now = new Date();
    
    // Current week (last Monday to last Sunday)
    const currentWeekStart = getLastMonday(now);
    const currentWeekEnd = getLastSunday(now);
    
    // Previous week
    const previousWeekStart = new Date(currentWeekStart);
    previousWeekStart.setDate(previousWeekStart.getDate() - 7);
    const previousWeekEnd = new Date(currentWeekEnd);
    previousWeekEnd.setDate(previousWeekEnd.getDate() - 7);
    
    return {
      currentWeek: {
        since: currentWeekStart.toISOString().split('T')[0],
        until: currentWeekEnd.toISOString().split('T')[0]
      },
      previousWeek: {
        since: previousWeekStart.toISOString().split('T')[0],
        until: previousWeekEnd.toISOString().split('T')[0]
      }
    };
  }

  // Get week-on-week comparison
  async getWeekComparison(): Promise<WeekComparison> {
    const { currentWeek, previousWeek } = this.getWeekRanges();

    console.log('Fetching week comparison:', { currentWeek, previousWeek });

    // Fetch data for both weeks
    const [currentData, previousData] = await Promise.all([
      this.fetchInsights(currentWeek),
      this.fetchInsights(previousWeek)
    ]);

    // Convert to metrics
    const currentMetrics = currentData.data.length > 0 ? this.convertToMetrics(currentData.data[0]) : null;
    const previousMetrics = previousData.data.length > 0 ? this.convertToMetrics(previousData.data[0]) : null;

    if (!currentMetrics || !previousMetrics) {
      throw new Error('Insufficient data for week comparison');
    }

    // Calculate changes
    const changes = {
      spend: this.calculateChange(currentMetrics.spend, previousMetrics.spend),
      impressions: this.calculateChange(currentMetrics.impressions, previousMetrics.impressions),
      clicks: this.calculateChange(currentMetrics.clicks, previousMetrics.clicks),
      conversions: this.calculateChange(currentMetrics.conversions, previousMetrics.conversions),
      roas: this.calculateChange(currentMetrics.roas, previousMetrics.roas),
      roas_7d_click: this.calculateChange(currentMetrics.roas_7d_click, previousMetrics.roas_7d_click)
    };

    return {
      current_week: {
        date_range: currentWeek,
        summary: currentMetrics
      },
      previous_week: {
        date_range: previousWeek,
        summary: previousMetrics
      },
      changes
    };
  }
}

// API Route Handler
export async function GET(request: NextRequest) {
  try {
    console.log('Fetching week-on-week comparison...');

    const metaComparisonAPI = new MetaComparisonAPIService();
    const comparison = await metaComparisonAPI.getWeekComparison();

    const clientConfig = getCurrentClientConfig();

    const response = {
      client_id: clientConfig.id,
      client_name: clientConfig.name,
      comparison
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Meta Comparison API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch week comparison', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
