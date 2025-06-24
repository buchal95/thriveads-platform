'use client';

import { useState, useEffect } from 'react';
import { User, Bell, Settings, RefreshCw } from 'lucide-react';
import { TimePeriod, ClientDashboardData } from '@/types/meta-ads';
import { mockClientData } from '@/data/mock-data';
import { TimePeriodSelector, DateRangeDisplay } from '@/components/TimePeriodSelector';
import { SpendCard, ImpressionsCard, ROASCard, ConversionsCard } from '@/components/MetricCard';
import { SpendTrendChart, WeeklySpendTrendChart, CampaignPerformanceChart, ROASComparisonChart, MetricsOverview } from '@/components/Charts';
import { CampaignTable } from '@/components/CampaignTable';
import { AttributionComparison } from '@/components/AttributionComparison';
import { BestPerformingAds } from '@/components/BestPerformingAds';
import { WeekComparison } from '@/components/WeekComparison';
import { formatROAS } from '../lib/utils';
import { apiService } from '@/services/api';

export default function Dashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('last_week');
  const [dashboardData, setDashboardData] = useState<ClientDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Client-safe date formatter to avoid hydration issues
  const formatLastUpdated = (dateString: string) => {
    // Use a consistent format that works the same on server and client
    const date = new Date(dateString);
    // Use UTC to ensure consistency between server and client
    const day = date.getUTCDate();
    const month = date.getUTCMonth() + 1;
    const year = date.getUTCFullYear();
    const hours = date.getUTCHours();
    const minutes = date.getUTCMinutes();
    return `${day}. ${month}. ${year} ${hours}:${minutes.toString().padStart(2, '0')} UTC`;
  };

  // Fetch real Meta API data
  const fetchMetaData = async (period: TimePeriod) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getDashboardData(period);

      if (response.error) {
        throw new Error(response.error);
      }

      const data = response.data;

      // Transform API response to match our ClientDashboardData structure
      const transformedData: ClientDashboardData = {
        client_id: data.client_id,
        client_name: data.client_name,
        ad_account_id: data.ad_account_id,
        last_updated: data.last_updated,
        last_week: period === 'last_week' ? {
          date_range: data.date_range,
          summary: data.summary,
          campaigns: data.campaigns,
          daily_breakdown: data.daily_breakdown
        } : mockClientData.last_week, // Use mock for other period
        last_month: period === 'last_month' ? {
          date_range: data.date_range,
          summary: data.summary,
          campaigns: data.campaigns,
          weekly_breakdown: [] // Would need separate API call
        } : mockClientData.last_month // Use mock for other period
      };

      setDashboardData(transformedData);
    } catch (err) {
      console.error('Failed to fetch Meta data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
      // Fallback to mock data on error
      setDashboardData(mockClientData);
    } finally {
      setLoading(false);
    }
  };

  // Set client-side flag to prevent hydration issues
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Load data on component mount and period change
  useEffect(() => {
    fetchMetaData(selectedPeriod);
  }, [selectedPeriod]);

  // Keyboard shortcuts (client-side only)
  useEffect(() => {
    // Only add event listeners on the client side
    if (typeof window === 'undefined') return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + R to refresh
      if ((event.metaKey || event.ctrlKey) && event.key === 'r') {
        event.preventDefault();
        fetchMetaData(selectedPeriod);
      }
      // 1 for last week, 2 for last month
      if (event.key === '1' && !event.metaKey && !event.ctrlKey && !event.altKey) {
        setSelectedPeriod('last_week');
      }
      if (event.key === '2' && !event.metaKey && !event.ctrlKey && !event.altKey) {
        setSelectedPeriod('last_month');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedPeriod]);

  // Use real data if available, fallback to mock
  const clientData = dashboardData || mockClientData;

  // Get data based on selected period
  const currentData = selectedPeriod === 'last_week'
    ? clientData.last_week
    : clientData.last_month;

  // Mock previous period data for comparison (simplified)
  const previousData = {
    spend: currentData.summary.spend * 0.85, // 15% less than current
    impressions: currentData.summary.impressions * 0.92, // 8% less than current
    roas: currentData.summary.roas * 0.88, // 12% less than current
    conversions: currentData.summary.conversions * 0.77 // 23% less than current
  };

  // Handle loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header Skeleton */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <div className="text-2xl font-bold text-blue-600">ThriveAds</div>
                <div className="ml-4 text-sm text-gray-500">Klientský dashboard</div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-32 h-8 bg-gray-200 rounded-lg animate-pulse"></div>
                <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Skeleton */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <div className="w-64 h-8 bg-gray-200 rounded-lg animate-pulse mb-2"></div>
            <div className="w-96 h-4 bg-gray-100 rounded animate-pulse"></div>
          </div>

          {/* Metric Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-2xl p-8 border border-gray-200 animate-pulse">
                <div className="w-24 h-4 bg-gray-200 rounded mb-4"></div>
                <div className="w-32 h-10 bg-gray-300 rounded mb-3"></div>
                <div className="w-20 h-4 bg-gray-100 rounded"></div>
              </div>
            ))}
          </div>

          {/* Charts Skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-2xl p-8 border border-gray-200 animate-pulse">
                <div className="w-48 h-6 bg-gray-200 rounded mb-6"></div>
                <div className="h-80 bg-gray-100 rounded-xl"></div>
              </div>
            ))}
          </div>

          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600 font-medium">Načítání dat z Meta API...</p>
            <p className="text-gray-500 text-sm mt-1">Může to trvat několik sekund</p>
          </div>
        </main>
      </div>
    );
  }

  // Handle error state
  if (error && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <div className="text-2xl font-bold text-blue-600">ThriveAds</div>
                <div className="ml-4 text-sm text-gray-500">Klientský dashboard</div>
              </div>
            </div>
          </div>
        </header>

        {/* Error Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Chyba při načítání dat
            </h1>

            <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
              <p className="text-red-800 font-medium mb-2">Nepodařilo se načíst data z Meta API</p>
              <p className="text-red-700 text-sm">{error}</p>
            </div>

            <div className="space-y-4">
              <button
                onClick={() => fetchMetaData(selectedPeriod)}
                className="btn-primary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Načítání...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Zkusit znovu
                  </>
                )}
              </button>

              <p className="text-gray-600 text-sm">
                Pokud problém přetrvává, kontaktujte podporu nebo zkuste obnovit stránku.
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                ThriveAds
              </div>
              <div className="hidden sm:block ml-4 text-sm text-gray-500">
                Klientský dashboard
              </div>
            </div>

            {/* Time Period Selector & Actions */}
            <div className="flex items-center gap-2 sm:gap-4">
              <div className="hidden md:block">
                <TimePeriodSelector
                  selectedPeriod={selectedPeriod}
                  onPeriodChange={setSelectedPeriod}
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1 sm:gap-2">
                <button
                  onClick={() => fetchMetaData(selectedPeriod)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl transition-all duration-200"
                  title="Obnovit data (Cmd+R)"
                  disabled={loading}
                >
                  <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
                </button>
                <button
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl transition-all duration-200"
                  title="Oznámení"
                >
                  <Bell className="w-5 h-5" />
                </button>
                <button
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl transition-all duration-200"
                  title="Nastavení"
                >
                  <Settings className="w-5 h-5" />
                </button>

                {/* User Profile */}
                <div className="flex items-center gap-3 pl-3 ml-2 border-l border-gray-200">
                  <div className="hidden sm:block text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {clientData.client_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      Klientský účet
                    </div>
                  </div>
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-sm">
                    <User className="w-4 h-4 text-white" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Time Period Selector */}
          <div className="md:hidden pb-4">
            <TimePeriodSelector
              selectedPeriod={selectedPeriod}
              onPeriodChange={setSelectedPeriod}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">
                Vítejte zpět, {clientData.client_name}
              </h1>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-gray-600">
                <DateRangeDisplay
                  since={currentData.date_range.since}
                  until={currentData.date_range.until}
                />
                <span className="hidden sm:inline">•</span>
                <span>
                  Naposledy aktualizováno: {formatLastUpdated(clientData.last_updated)}
                </span>
                {error && (
                  <>
                    <span className="hidden sm:inline">•</span>
                    <span className="text-orange-600 font-medium">
                      ⚠️ Používají se záložní data
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex items-center gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {formatROAS(currentData.summary.roas)}
                </div>
                <div className="text-gray-500">ROAS</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {currentData.summary.conversions.toLocaleString()}
                </div>
                <div className="text-gray-500">Konverze</div>
              </div>
            </div>
          </div>
        </div>

        {/* Week-on-Week Comparison */}
        <WeekComparison className="mb-8" />

        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <SpendCard
            current={currentData.summary.spend}
            previous={previousData.spend}
          />
          <ImpressionsCard
            current={currentData.summary.impressions}
            previous={previousData.impressions}
          />
          <ROASCard
            current={currentData.summary.roas}
            previous={previousData.roas}
          />
          <ConversionsCard
            current={currentData.summary.conversions}
            previous={previousData.conversions}
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {selectedPeriod === 'last_week' && currentData.daily_breakdown && (
            <SpendTrendChart data={currentData.daily_breakdown} />
          )}
          {selectedPeriod === 'last_month' && currentData.weekly_breakdown && (
            <WeeklySpendTrendChart data={currentData.weekly_breakdown} />
          )}
          <CampaignPerformanceChart campaigns={currentData.campaigns} />
          <ROASComparisonChart campaigns={currentData.campaigns} />
          <MetricsOverview
            data={{
              impressions: currentData.summary.impressions,
              clicks: currentData.summary.clicks,
              conversions: currentData.summary.conversions
            }}
          />
        </div>

        {/* Best Performing Ads */}
        <BestPerformingAds className="mb-8" />

        {/* Attribution Comparison */}
        <AttributionComparison
          purchases={{
            default: { count: currentData.summary.conversions, value: currentData.summary.conversion_value },
            '7d_click': { count: currentData.summary.conversions, value: currentData.summary.conversion_value }
          }}
          spend={currentData.summary.spend}
          roasDefault={currentData.summary.roas}
          roas7dClick={currentData.summary.roas}
          className="mb-8"
        />

        {/* Campaign Table */}
        <CampaignTable campaigns={currentData.campaigns} />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Keyboard Shortcuts */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Klávesové zkratky</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Obnovit data</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Cmd+R</kbd>
                </div>
                <div className="flex justify-between">
                  <span>Minulý týden</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">1</kbd>
                </div>
                <div className="flex justify-between">
                  <span>Minulý měsíc</span>
                  <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">2</kbd>
                </div>
              </div>
            </div>

            {/* Data Info */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Informace o datech</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div>Meta Ad Account: {clientData.ad_account_id}</div>
                <div>Časové pásmo: Europe/Prague</div>
                <div>Měna: CZK</div>
                <div>API verze: v23.0</div>
              </div>
            </div>

            {/* Support */}
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Podpora</h3>
              <div className="space-y-2 text-sm text-gray-600">
                <div>
                  <a href="mailto:support@thriveads.com" className="text-blue-600 hover:text-blue-700">
                    support@thriveads.com
                  </a>
                </div>
                <div>
                  <a href="https://docs.thriveads.com" className="text-blue-600 hover:text-blue-700">
                    Dokumentace
                  </a>
                </div>
                <div className="text-xs text-gray-500 mt-4">
                  © 2024 ThriveAds. Všechna práva vyhrazena.
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
