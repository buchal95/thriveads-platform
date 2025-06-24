import { NextRequest, NextResponse } from 'next/server';
import { getCurrentClientConfig } from '@/config/clients';
import { getLastMonday, getLastSunday } from '@/lib/utils';
import { AdData } from '@/types/meta-ads';

// Meta API service for fetching ad-level data
class MetaAdsAPIService {
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

  async fetchAdInsights(dateRange: { since: string; until: string }) {
    const url = `${this.baseURL}/act_${this.adAccountId}/insights`;
    
    const queryParams = new URLSearchParams({
      access_token: this.accessToken,
      level: 'ad',
      time_range: JSON.stringify({
        since: dateRange.since,
        until: dateRange.until
      }),
      // Essential fields for ad-level reporting
      fields: [
        'date_start',
        'date_stop',
        'ad_id',
        'ad_name',
        'adset_id',
        'adset_name',
        'campaign_id',
        'campaign_name',
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
        'action_values', // Contains conversion values
        'video_play_actions',
        'quality_ranking',
        'engagement_rate_ranking'
      ].join(','),
      // Attribution windows for accurate purchase tracking
      action_attribution_windows: ['default', '7d_click'].join(','),
      limit: '100',
      // PERFORMANCE: Only get ads with spend > 0
      filtering: JSON.stringify([{
        field: 'spend',
        operator: 'GREATER_THAN',
        value: 0
      }])
    });

    console.log('Meta Ads API Request URL:', `${url}?${queryParams.toString()}`);

    const response = await fetch(`${url}?${queryParams.toString()}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Meta Ads API Error:', response.status, errorText);
      throw new Error(`Meta Ads API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Meta Ads API Response:', JSON.stringify(data, null, 2));
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
  convertToAdMetrics(data: any) {
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

  // Generate Facebook ad preview URL using Meta API
  async generateFacebookAdURL(adId: string): Promise<string> {
    try {
      // First try to get ad creative to generate preview URL
      const creativeUrl = `${this.baseURL}/${adId}`;
      const creativeParams = new URLSearchParams({
        access_token: this.accessToken,
        fields: 'creative{effective_object_story_id,object_story_id}'
      });

      const creativeResponse = await fetch(`${creativeUrl}?${creativeParams.toString()}`);

      if (creativeResponse.ok) {
        const creativeData = await creativeResponse.json();
        const objectStoryId = creativeData.creative?.effective_object_story_id || creativeData.creative?.object_story_id;

        if (objectStoryId) {
          // Extract page ID and post ID from object story ID (format: pageId_postId)
          const [pageId, postId] = objectStoryId.split('_');
          if (pageId && postId) {
            return `https://www.facebook.com/${pageId}/posts/${postId}`;
          }
        }
      }
    } catch (error) {
      console.warn('Failed to get ad creative for preview URL:', error);
    }

    // Fallback to Ads Manager URL (requires login but works for account owners)
    return `https://www.facebook.com/ads/manager/creation/creative/preview/?ad_id=${adId}`;
  }

  // Convert API response to AdData format
  async convertToAdData(item: any): Promise<AdData> {
    const facebookUrl = await this.generateFacebookAdURL(item.ad_id);

    return {
      id: item.ad_id,
      name: item.ad_name || 'Unnamed Ad',
      adset_id: item.adset_id,
      adset_name: item.adset_name || 'Unnamed AdSet',
      campaign_id: item.campaign_id,
      campaign_name: item.campaign_name || 'Unnamed Campaign',
      status: 'ACTIVE' as const, // We'd need separate API call to get actual status
      facebook_url: facebookUrl,
      metrics: this.convertToAdMetrics(item)
    };
  }

  // Get top performing ads
  async getTopPerformingAds(dateRange: { since: string; until: string }, limit: number = 10): Promise<AdData[]> {
    const response = await this.fetchAdInsights(dateRange);

    // Convert all ads with proper async handling
    const ads = await Promise.all(
      response.data.map((item: any) => this.convertToAdData(item))
    );

    // Filter ads with conversions and sort by ROAS (default attribution)
    const topAds = ads
      .filter((ad: AdData) => ad.metrics.purchases.default.count > 0) // Only ads with conversions
      .sort((a: AdData, b: AdData) => {
        // Primary: ROAS (default attribution)
        if (b.metrics.roas !== a.metrics.roas) {
          return b.metrics.roas - a.metrics.roas;
        }
        // Secondary: Total conversion value
        return b.metrics.purchases.default.value - a.metrics.purchases.default.value;
      })
      .slice(0, limit);

    return topAds;
  }
}

// API Route Handler
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || 'last_week';
    const limit = parseInt(searchParams.get('limit') || '10');
    
    // Calculate date range
    const now = new Date();
    let dateRange;
    
    if (period === 'last_week') {
      dateRange = {
        since: getLastMonday(now).toISOString().split('T')[0],
        until: getLastSunday(now).toISOString().split('T')[0]
      };
    } else {
      // For now, default to last week
      dateRange = {
        since: getLastMonday(now).toISOString().split('T')[0],
        until: getLastSunday(now).toISOString().split('T')[0]
      };
    }

    console.log('Fetching top performing ads for period:', period, 'Date range:', dateRange);

    const metaAdsAPI = new MetaAdsAPIService();
    const topAds = await metaAdsAPI.getTopPerformingAds(dateRange, limit);

    const clientConfig = getCurrentClientConfig();

    const response = {
      client_id: clientConfig.id,
      client_name: clientConfig.name,
      period,
      date_range: dateRange,
      total_ads: topAds.length,
      top_performing_ads: topAds
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Meta Ads API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch top performing ads', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
