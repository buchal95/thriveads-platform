'use client';

import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { DailyMetrics, WeeklyMetrics, CampaignData } from '@/types/meta-ads';
import { formatCurrency, formatNumber, formatROAS } from '@/lib/utils';

// Daily spend trend chart
interface SpendTrendChartProps {
  data: DailyMetrics[];
  className?: string;
}

// Weekly spend trend chart
interface WeeklySpendTrendChartProps {
  data: WeeklyMetrics[];
  className?: string;
}

export function SpendTrendChart({ data, className }: SpendTrendChartProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const chartData = data.map(item => {
    // Use consistent date formatting to avoid hydration issues
    const date = new Date(item.date);
    const day = date.getUTCDate();
    const month = date.getUTCMonth() + 1;
    return {
      date: `${day}.${month}`,
      spend: item.metrics.spend,
      clicks: item.metrics.clicks,
      conversions: item.metrics.conversions
    };
  });

  return (
    <div className={className}>
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Denní trend nákladů
        </h3>
        <div className="h-80">
          {isClient ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis
                  stroke="#6b7280"
                  fontSize={12}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), 'Náklady']}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="spend"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{ fill: '#2563eb', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#2563eb', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
              <div className="text-gray-500">Načítání grafu...</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function WeeklySpendTrendChart({ data, className }: WeeklySpendTrendChartProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const chartData = data.map(item => {
    // Use consistent date formatting to avoid hydration issues
    const startDate = new Date(item.week_start);
    const endDate = new Date(item.week_end);
    const startDay = startDate.getUTCDate();
    const startMonth = startDate.getUTCMonth() + 1;
    const endDay = endDate.getUTCDate();
    const endMonth = endDate.getUTCMonth() + 1;

    return {
      week: `${startDay}.${startMonth} - ${endDay}.${endMonth}`,
      spend: item.metrics.spend,
      clicks: item.metrics.clicks,
      conversions: item.metrics.conversions
    };
  });

  return (
    <div className={className}>
      <div className="luxury-table">
        <div className="px-8 py-6 border-b border-gray-100">
          <h3 className="text-xl font-bold text-gray-900">
            Týdenní trend nákladů
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Vývoj nákladů za posledních {data.length} týdnů
          </p>
        </div>
        <div className="p-6">
          <div className="h-80">
            {isClient ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ left: 20, right: 20, top: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="week"
                    stroke="#6b7280"
                    fontSize={12}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    stroke="#6b7280"
                    fontSize={12}
                    tickFormatter={(value) => formatCurrency(value)}
                  />
                  <Tooltip
                    formatter={(value: number) => [formatCurrency(value), 'Náklady']}
                    labelStyle={{ color: '#374151' }}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '12px',
                      boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="spend"
                    stroke="url(#spendLineGradient)"
                    strokeWidth={3}
                    dot={{ fill: '#2563eb', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 7, stroke: '#2563eb', strokeWidth: 2 }}
                  />
                  <defs>
                    <linearGradient id="spendLineGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#2563eb" />
                      <stop offset="100%" stopColor="#6366f1" />
                    </linearGradient>
                  </defs>
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
                <div className="text-gray-500">Načítání grafu...</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Campaign performance bar chart
interface CampaignPerformanceChartProps {
  campaigns: CampaignData[];
  className?: string;
}

export function CampaignPerformanceChart({ campaigns, className }: CampaignPerformanceChartProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Add error handling and debugging
  if (!campaigns || campaigns.length === 0) {
    return (
      <div className={className}>
        <div className="luxury-table">
          <div className="px-8 py-6 border-b border-gray-100">
            <h3 className="text-xl font-bold text-gray-900">
              Nejlepší kampaně podle nákladů
            </h3>
            <p className="text-sm text-gray-500 mt-1">Žádná data k zobrazení</p>
          </div>
          <div className="text-center py-16 text-gray-500">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <BarChart3 className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-lg font-medium">Žádné kampaně k zobrazení</p>
            <p className="text-sm mt-1">Zkontrolujte připojení k API nebo časové období</p>
          </div>
        </div>
      </div>
    );
  }

  const chartData = campaigns
    .filter(campaign => campaign.metrics && campaign.metrics.spend > 0) // Filter out campaigns with no spend
    .sort((a, b) => b.metrics.spend - a.metrics.spend)
    .slice(0, 5) // Top 5 campaigns
    .map(campaign => ({
      name: campaign.name.length > 20
        ? campaign.name.substring(0, 20) + '...'
        : campaign.name,
      spend: campaign.metrics.spend,
      roas: campaign.metrics.roas || 0,
      conversions: campaign.metrics.conversions || 0
    }));

  if (chartData.length === 0) {
    return (
      <div className={className}>
        <div className="luxury-table">
          <div className="px-8 py-6 border-b border-gray-100">
            <h3 className="text-xl font-bold text-gray-900">
              Nejlepší kampaně podle nákladů
            </h3>
            <p className="text-sm text-gray-500 mt-1">Žádná data s náklady</p>
          </div>
          <div className="text-center py-16 text-gray-500">
            <p className="text-lg font-medium">Žádné kampaně s náklady</p>
            <p className="text-sm mt-1">Všechny kampaně mají nulové náklady</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="luxury-table">
        <div className="px-8 py-6 border-b border-gray-100">
          <h3 className="text-xl font-bold text-gray-900">
            Nejlepší kampaně podle nákladů
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Top {chartData.length} kampaní s nejvyššími náklady
          </p>
        </div>
        <div className="p-6">
          <div className="h-80">
            {isClient ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="horizontal" margin={{ left: 20, right: 20, top: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    type="number"
                    stroke="#6b7280"
                    fontSize={12}
                    tickFormatter={(value) => formatCurrency(value)}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="#6b7280"
                    fontSize={12}
                    width={140}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === 'spend') return [formatCurrency(value), 'Náklady'];
                      if (name === 'roas') return [formatROAS(value), 'ROAS'];
                      return [value, name];
                    }}
                    labelStyle={{ color: '#374151' }}
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '12px',
                      boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Bar
                    dataKey="spend"
                    fill="url(#spendGradient)"
                    radius={[0, 8, 8, 0]}
                  />
                  <defs>
                    <linearGradient id="spendGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#2563eb" />
                      <stop offset="100%" stopColor="#6366f1" />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
                <div className="text-gray-500">Načítání grafu...</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ROAS comparison chart
interface ROASComparisonChartProps {
  campaigns: CampaignData[];
  className?: string;
}

export function ROASComparisonChart({ campaigns, className }: ROASComparisonChartProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const chartData = campaigns
    .sort((a, b) => b.metrics.roas - a.metrics.roas)
    .slice(0, 5)
    .map(campaign => ({
      name: campaign.name.length > 15
        ? campaign.name.substring(0, 15) + '...'
        : campaign.name,
      roas: campaign.metrics.roas,
      spend: campaign.metrics.spend
    }));

  return (
    <div className={className}>
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          ROAS podle kampaní
        </h3>
        <div className="h-80">
          {isClient ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="name"
                  stroke="#6b7280"
                  fontSize={12}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  stroke="#6b7280"
                  fontSize={12}
                  tickFormatter={(value) => value.toFixed(1) + 'x'}
                />
                <Tooltip
                  formatter={(value: number) => [formatROAS(value), 'ROAS']}
                  labelStyle={{ color: '#374151' }}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Bar
                  dataKey="roas"
                  fill="#10b981"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
              <div className="text-gray-500">Načítání grafu...</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Simple metrics overview pie chart
interface MetricsOverviewProps {
  data: {
    impressions: number;
    clicks: number;
    conversions: number;
  };
  className?: string;
}

export function MetricsOverview({ data, className }: MetricsOverviewProps) {
  // Calculate conversion rates for funnel
  const impressionToClick = data.impressions > 0 ? (data.clicks / data.impressions) * 100 : 0;
  const clickToConversion = data.clicks > 0 ? (data.conversions / data.clicks) * 100 : 0;
  const overallConversionRate = data.impressions > 0 ? (data.conversions / data.impressions) * 100 : 0;

  const funnelData = [
    {
      name: 'Zobrazení',
      value: data.impressions,
      percentage: 100,
      color: '#e5e7eb',
      width: 100
    },
    {
      name: 'Kliky',
      value: data.clicks,
      percentage: impressionToClick,
      color: '#2563eb',
      width: Math.max(impressionToClick, 5) // Minimum width for visibility
    },
    {
      name: 'Konverze',
      value: data.conversions,
      percentage: overallConversionRate,
      color: '#10b981',
      width: Math.max(overallConversionRate, 2) // Minimum width for visibility
    }
  ];

  return (
    <div className={className}>
      <div className="luxury-table">
        <div className="px-8 py-6 border-b border-gray-100">
          <h3 className="text-xl font-bold text-gray-900">
            Přehled konverzního trychtýře
          </h3>
          <p className="text-sm text-gray-500 mt-1">
            Celková konverzní míra: {overallConversionRate.toFixed(3)}%
          </p>
        </div>
        <div className="p-8">
          {/* Funnel Visualization */}
          <div className="space-y-4">
            {funnelData.map((item, index) => (
              <div key={index} className="relative">
                {/* Funnel Step */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full shadow-sm"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm font-semibold text-gray-900">{item.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">
                      {formatNumber(item.value)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.percentage.toFixed(2)}% z celku
                    </div>
                  </div>
                </div>

                {/* Funnel Bar */}
                <div className="relative h-12 bg-gray-100 rounded-xl overflow-hidden">
                  <div
                    className="h-full rounded-xl transition-all duration-500 ease-out shadow-sm"
                    style={{
                      width: `${item.width}%`,
                      background: `linear-gradient(135deg, ${item.color} 0%, ${item.color}dd 100%)`
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-medium text-gray-700">
                      {formatNumber(item.value)}
                    </span>
                  </div>
                </div>

                {/* Conversion Rate Arrow */}
                {index < funnelData.length - 1 && (
                  <div className="flex items-center justify-center mt-3 mb-1">
                    <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 rounded-full border border-blue-200">
                      <span className="text-xs font-medium text-blue-700">
                        {index === 0
                          ? `CTR: ${impressionToClick.toFixed(2)}%`
                          : `CR: ${clickToConversion.toFixed(2)}%`
                        }
                      </span>
                      <svg className="w-3 h-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Summary Stats */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {impressionToClick.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">
                  Click-through Rate
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {clickToConversion.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">
                  Conversion Rate
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {overallConversionRate.toFixed(3)}%
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">
                  Overall CR
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
