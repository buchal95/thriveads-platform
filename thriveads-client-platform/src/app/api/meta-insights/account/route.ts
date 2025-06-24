import { NextRequest, NextResponse } from 'next/server';
import { getCurrentClientConfig } from '../../../../config/clients';
import { AccountInfo } from '../../../../types/meta-ads';

// Meta API service for account information
class MetaAccountAPIService {
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

  async fetchAccountInfo(): Promise<AccountInfo> {
    const url = `${this.baseURL}/act_${this.adAccountId}`;
    
    const queryParams = new URLSearchParams({
      access_token: this.accessToken,
      fields: [
        'id',
        'name',
        'account_id',
        'currency',
        'timezone_name',
        'account_status',
        'business_country_code',
        'created_time',
        'funding_source_details'
      ].join(',')
    });

    console.log('Meta Account API Request URL:', `${url}?${queryParams.toString()}`);

    const response = await fetch(`${url}?${queryParams.toString()}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Meta Account API Error:', response.status, errorText);
      throw new Error(`Meta Account API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Meta Account API Response:', JSON.stringify(data, null, 2));

    return {
      id: data.id,
      name: data.name,
      currency: data.currency,
      timezone_name: data.timezone_name,
      account_status: data.account_status
    };
  }
}

// API Route Handler
export async function GET(request: NextRequest) {
  try {
    console.log('Fetching Meta account information...');

    const metaAccountAPI = new MetaAccountAPIService();
    const accountInfo = await metaAccountAPI.fetchAccountInfo();

    const clientConfig = getCurrentClientConfig();

    const response = {
      client_id: clientConfig.id,
      client_name: clientConfig.name,
      account_info: accountInfo
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Meta Account API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch account information', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
