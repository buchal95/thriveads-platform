import { ClientDashboardData, CampaignData, DailyMetrics, WeeklyMetrics } from '../types/meta-ads';

// Mock campaign data
const mockCampaigns: CampaignData[] = [
  {
    id: 'camp_001',
    name: '🎯 Black Friday Sale 2024',
    status: 'ACTIVE',
    objective: 'CONVERSIONS',
    created_time: '2024-11-01T00:00:00Z',
    updated_time: '2024-11-25T12:00:00Z',
    metrics: {
      spend: 3245.50,
      cpc: 1.38,
      cpm: 12.45,
      cpp: 8.90,
      impressions: 456789,
      reach: 234567,
      frequency: 1.95,
      clicks: 2341,
      link_clicks: 2156,
      ctr: 0.0051,
      purchases: {
        default: {
          count: 187,
          value: 15576.00 // 187 * average order value ~83€
        },
        '7d_click': {
          count: 142, // Lower count for 7d_click only (no view-through)
          value: 11836.00 // 142 * average order value ~83€
        }
      },
      conversions: 187,
      conversion_rate: 0.087,
      cost_per_conversion: 17.35,
      roas: 4.8,
      roas_7d_click: 3.6, // Lower ROAS for 7d_click attribution
      return_on_ad_spend: 4.8,
      post_engagement: 3456,
      engagement_rate: 0.0076,
      quality_ranking: 'ABOVE_AVERAGE',
      engagement_rate_ranking: 'ABOVE_AVERAGE'
    }
  },
  {
    id: 'camp_002',
    name: '🛍️ Product Launch Campaign',
    status: 'ACTIVE',
    objective: 'CONVERSIONS',
    created_time: '2024-10-15T00:00:00Z',
    updated_time: '2024-11-25T12:00:00Z',
    metrics: {
      spend: 2890.25,
      cpc: 1.45,
      cpm: 11.20,
      cpp: 7.65,
      impressions: 389456,
      reach: 198765,
      frequency: 1.96,
      clicks: 1987,
      link_clicks: 1823,
      ctr: 0.0051,
      purchases: {
        default: {
          count: 142,
          value: 11278.00 // 142 * ~79€ average order value
        },
        '7d_click': {
          count: 108, // Lower for 7d_click only
          value: 8532.00 // 108 * ~79€ average order value
        }
      },
      conversions: 142,
      conversion_rate: 0.078,
      cost_per_conversion: 20.35,
      roas: 3.9,
      roas_7d_click: 2.95, // Lower ROAS for 7d_click attribution
      return_on_ad_spend: 3.9,
      post_engagement: 2876,
      engagement_rate: 0.0074,
      quality_ranking: 'AVERAGE',
      engagement_rate_ranking: 'ABOVE_AVERAGE'
    }
  },
  {
    id: 'camp_003',
    name: '📱 Mobile App Install',
    status: 'ACTIVE',
    objective: 'APP_INSTALLS',
    created_time: '2024-11-10T00:00:00Z',
    updated_time: '2024-11-25T12:00:00Z',
    metrics: {
      spend: 1567.80,
      cpc: 1.27,
      cpm: 9.85,
      cpp: 6.45,
      impressions: 234567,
      reach: 156789,
      frequency: 1.50,
      clicks: 1234,
      link_clicks: 1156,
      ctr: 0.0053,
      purchases: {
        default: {
          count: 89,
          value: 8152.00 // 89 * ~91€ average order value
        },
        '7d_click': {
          count: 76, // Lower for 7d_click only
          value: 6916.00 // 76 * ~91€ average order value
        }
      },
      conversions: 89,
      conversion_rate: 0.077,
      cost_per_conversion: 17.62,
      roas: 5.2,
      roas_7d_click: 4.4, // Lower ROAS for 7d_click attribution
      return_on_ad_spend: 5.2,
      post_engagement: 1876,
      engagement_rate: 0.0080,
      quality_ranking: 'ABOVE_AVERAGE',
      engagement_rate_ranking: 'AVERAGE'
    }
  }
];

// Mock daily metrics for last week
const mockDailyMetrics: DailyMetrics[] = [
  {
    date: '2024-11-18',
    metrics: {
      spend: 1123.45,
      cpc: 1.35,
      cpm: 11.20,
      cpp: 7.80,
      impressions: 156789,
      reach: 89456,
      frequency: 1.75,
      clicks: 832,
      link_clicks: 765,
      ctr: 0.0053,
      conversions: 67,
      conversion_rate: 0.088,
      cost_per_conversion: 16.77,
      roas: 4.5,
      roas_7d_click: 4.2,
      return_on_ad_spend: 4.5,
      purchases: {
        default: { count: 67, value: 5055.25 },
        '7d_click': { count: 63, value: 4716.60 }
      },
      post_engagement: 1234,
      engagement_rate: 0.0079
    }
  },
  {
    date: '2024-11-19',
    metrics: {
      spend: 1087.23,
      cpc: 1.42,
      cpm: 12.10,
      cpp: 8.20,
      impressions: 145678,
      reach: 87654,
      frequency: 1.66,
      clicks: 765,
      link_clicks: 698,
      ctr: 0.0053,
      conversions: 58,
      conversion_rate: 0.083,
      cost_per_conversion: 18.75,
      roas: 4.2,
      roas_7d_click: 3.9,
      return_on_ad_spend: 4.2,
      purchases: {
        default: { count: 58, value: 4347.50 },
        '7d_click': { count: 54, value: 4050.00 }
      },
      post_engagement: 1156,
      engagement_rate: 0.0079
    }
  }
  // Add more days as needed...
];

// Mock weekly metrics for last month
const mockWeeklyMetrics: WeeklyMetrics[] = [
  {
    week_start: '2024-10-28',
    week_end: '2024-11-03',
    metrics: {
      spend: 6789.45,
      cpc: 1.38,
      cpm: 11.85,
      cpp: 8.10,
      impressions: 987654,
      reach: 456789,
      frequency: 2.16,
      clicks: 4912,
      link_clicks: 4523,
      ctr: 0.0050,
      conversions: 342,
      conversion_rate: 0.076,
      cost_per_conversion: 19.85,
      roas: 4.1,
      roas_7d_click: 3.7,
      return_on_ad_spend: 4.1,
      purchases: {
        default: { count: 342, value: 25620.00 },
        '7d_click': { count: 318, value: 23850.00 }
      },
      post_engagement: 7654,
      engagement_rate: 0.0078
    }
  }
  // Add more weeks as needed...
];

// Main mock dashboard data
export const mockClientData: ClientDashboardData = {
  client_id: 'client_001',
  client_name: 'Protein & Co',
  ad_account_id: 'act_123456789',
  last_updated: '2024-11-25T14:30:00Z',
  
  last_week: {
    date_range: {
      since: '2024-11-18',
      until: '2024-11-24'
    },
    summary: {
      spend: 7703.55,
      cpc: 1.39,
      cpm: 11.50,
      cpp: 7.95,
      impressions: 1080812,
      reach: 543210,
      frequency: 1.99,
      clicks: 5562,
      link_clicks: 5135,
      ctr: 0.0051,
      purchases: {
        default: {
          count: 418,
          value: 35006.00 // Sum of all campaigns default attribution
        },
        '7d_click': {
          count: 326, // Lower total for 7d_click only
          value: 27284.00 // Sum of all campaigns 7d_click attribution
        }
      },
      conversions: 418,
      conversion_rate: 0.081,
      cost_per_conversion: 18.43,
      roas: 4.3,
      roas_7d_click: 3.5, // Lower ROAS for 7d_click attribution
      return_on_ad_spend: 4.3,
      post_engagement: 8208,
      engagement_rate: 0.0076
    },
    campaigns: mockCampaigns,
    daily_breakdown: mockDailyMetrics
  },
  
  last_month: {
    date_range: {
      since: '2024-10-01',
      until: '2024-10-31'
    },
    summary: {
      spend: 28456.78,
      cpc: 1.42,
      cpm: 12.20,
      cpp: 8.45,
      impressions: 3987654,
      reach: 1876543,
      frequency: 2.13,
      clicks: 20045,
      link_clicks: 18234,
      ctr: 0.0050,
      purchases: {
        default: {
          count: 1456,
          value: 116648.00 // 1456 * ~80€ average order value
        },
        '7d_click': {
          count: 1134, // Lower for 7d_click only
          value: 90720.00 // 1134 * ~80€ average order value
        }
      },
      conversions: 1456,
      conversion_rate: 0.080,
      cost_per_conversion: 19.54,
      roas: 4.1,
      roas_7d_click: 3.2, // Lower ROAS for 7d_click attribution
      return_on_ad_spend: 4.1,
      post_engagement: 29876,
      engagement_rate: 0.0075
    },
    campaigns: mockCampaigns,
    weekly_breakdown: mockWeeklyMetrics
  }
};
