'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, Calendar, RefreshCw } from 'lucide-react';
import { WeekComparison as WeekComparisonType, MetricChange, MetaAdMetrics } from '../types/meta-ads';
import { formatCurrency, formatROAS, formatNumber, cn } from '../lib/utils';
import { apiService } from '../services/api';

interface WeekComparisonProps {
  className?: string;
}

interface MetricCardProps {
  label: string;
  change: MetricChange;
  format: 'currency' | 'number' | 'roas' | 'percentage';
  icon?: React.ReactNode;
}

function MetricCard({ label, change, format, icon }: MetricCardProps) {
  const formatValue = (value: number) => {
    switch (format) {
      case 'currency':
        return formatCurrency(value);
      case 'roas':
        return formatROAS(value);
      case 'number':
        return formatNumber(value);
      case 'percentage':
        return `${value.toFixed(2)}%`;
      default:
        return value.toLocaleString();
    }
  };

  const getTrendIcon = () => {
    switch (change.trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  const getTrendColor = () => {
    switch (change.trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  const getBackgroundColor = () => {
    switch (change.trend) {
      case 'up':
        return 'bg-green-50 border-green-200';
      case 'down':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={cn('p-4 rounded-lg border transition-all duration-200', getBackgroundColor())}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium text-gray-600">{label}</div>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      
      <div className="text-2xl font-bold text-gray-900 mb-2">
        {formatValue(change.current)}
      </div>
      
      <div className={cn('flex items-center gap-1 text-sm font-medium', getTrendColor())}>
        {getTrendIcon()}
        <span>
          {change.percentage_change > 0 ? '+' : ''}{change.percentage_change.toFixed(1)}%
        </span>
      </div>
      
      <div className="text-xs text-gray-500 mt-1">
        {format === 'currency' ? formatCurrency(Math.abs(change.absolute_change)) : 
         format === 'roas' ? formatROAS(Math.abs(change.absolute_change)) :
         formatNumber(Math.abs(change.absolute_change))} vs minulý týden
      </div>
    </div>
  );
}

export function WeekComparison({ className }: WeekComparisonProps) {
  const [comparison, setComparison] = useState<WeekComparisonType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getWeekComparison();

      if (response.error) {
        throw new Error(response.error);
      }

      // Convert API response to component format
      const apiData = response.data!;
      const convertedData: WeekComparisonType = {
        current_week: {
          date_range: { since: '', until: '' }, // API doesn't provide this
          summary: apiData.current_week.metrics as MetaAdMetrics
        },
        previous_week: {
          date_range: { since: '', until: '' }, // API doesn't provide this
          summary: apiData.previous_week.metrics as MetaAdMetrics
        },
        changes: {
          spend: {
            current: apiData.current_week.metrics.spend,
            previous: apiData.previous_week.metrics.spend,
            absolute_change: apiData.current_week.metrics.spend - apiData.previous_week.metrics.spend,
            percentage_change: apiData.metrics_comparison.spend_change,
            trend: apiData.metrics_comparison.spend_change > 0 ? 'up' : apiData.metrics_comparison.spend_change < 0 ? 'down' : 'neutral'
          },
          impressions: {
            current: apiData.current_week.metrics.impressions,
            previous: apiData.previous_week.metrics.impressions,
            absolute_change: apiData.current_week.metrics.impressions - apiData.previous_week.metrics.impressions,
            percentage_change: apiData.metrics_comparison.impressions_change,
            trend: apiData.metrics_comparison.impressions_change > 0 ? 'up' : apiData.metrics_comparison.impressions_change < 0 ? 'down' : 'neutral'
          },
          clicks: {
            current: apiData.current_week.metrics.clicks,
            previous: apiData.previous_week.metrics.clicks,
            absolute_change: apiData.current_week.metrics.clicks - apiData.previous_week.metrics.clicks,
            percentage_change: apiData.metrics_comparison.clicks_change,
            trend: apiData.metrics_comparison.clicks_change > 0 ? 'up' : apiData.metrics_comparison.clicks_change < 0 ? 'down' : 'neutral'
          },
          conversions: {
            current: apiData.current_week.metrics.conversions,
            previous: apiData.previous_week.metrics.conversions,
            absolute_change: apiData.current_week.metrics.conversions - apiData.previous_week.metrics.conversions,
            percentage_change: apiData.metrics_comparison.conversions_change,
            trend: apiData.metrics_comparison.conversions_change > 0 ? 'up' : apiData.metrics_comparison.conversions_change < 0 ? 'down' : 'neutral'
          },
          roas: {
            current: apiData.current_week.metrics.roas,
            previous: apiData.previous_week.metrics.roas,
            absolute_change: apiData.current_week.metrics.roas - apiData.previous_week.metrics.roas,
            percentage_change: apiData.metrics_comparison.roas_change,
            trend: apiData.metrics_comparison.roas_change > 0 ? 'up' : apiData.metrics_comparison.roas_change < 0 ? 'down' : 'neutral'
          },
          roas_7d_click: {
            current: apiData.current_week.metrics.roas, // Use same as roas since API doesn't separate
            previous: apiData.previous_week.metrics.roas,
            absolute_change: apiData.current_week.metrics.roas - apiData.previous_week.metrics.roas,
            percentage_change: apiData.metrics_comparison.roas_change,
            trend: apiData.metrics_comparison.roas_change > 0 ? 'up' : apiData.metrics_comparison.roas_change < 0 ? 'down' : 'neutral'
          }
        }
      };

      setComparison(convertedData);
    } catch (err) {
      console.error('Failed to fetch week comparison:', err);
      setError(err instanceof Error ? err.message : 'Failed to load comparison');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, []);

  const formatDateRange = (dateRange: { since: string; until: string }) => {
    const since = new Date(dateRange.since);
    const until = new Date(dateRange.until);
    
    const formatDate = (date: Date) => {
      return `${date.getDate()}.${date.getMonth() + 1}`;
    };
    
    return `${formatDate(since)} - ${formatDate(until)}`;
  };

  if (loading) {
    return (
      <div className={cn('bg-white rounded-xl p-6 shadow-sm border border-gray-200', className)}>
        <div className="flex items-center gap-2 mb-6">
          <Calendar className="w-5 h-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900">Porovnání týdnů</h3>
          <RefreshCw className="w-4 h-4 animate-spin text-gray-400 ml-auto" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('bg-white rounded-xl p-6 shadow-sm border border-gray-200', className)}>
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900">Porovnání týdnů</h3>
        </div>
        <div className="text-center py-8">
          <div className="bg-red-100 text-red-700 p-4 rounded-lg mb-4">
            <p className="font-medium">Chyba při načítání porovnání</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
          <button 
            onClick={fetchComparison}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Zkusit znovu
          </button>
        </div>
      </div>
    );
  }

  if (!comparison) {
    return (
      <div className={cn('bg-white rounded-xl p-6 shadow-sm border border-gray-200', className)}>
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="w-5 h-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900">Porovnání týdnů</h3>
        </div>
        <div className="text-center py-8 text-gray-500">
          <p>Žádná data pro porovnání</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('bg-white rounded-xl shadow-sm border border-gray-200', className)}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900">
              Porovnání týdnů
            </h3>
          </div>
          <button 
            onClick={fetchComparison}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Obnovit data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        <div className="text-sm text-gray-600 mt-1">
          <span className="font-medium">Aktuální týden:</span> {formatDateRange(comparison.current_week.date_range)} vs{' '}
          <span className="font-medium">Minulý týden:</span> {formatDateRange(comparison.previous_week.date_range)}
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Celkové náklady"
            change={comparison.changes.spend}
            format="currency"
          />
          <MetricCard
            label="ROAS (Default)"
            change={comparison.changes.roas}
            format="roas"
          />
          <MetricCard
            label="Konverze"
            change={comparison.changes.conversions}
            format="number"
          />
          <MetricCard
            label="Zobrazení"
            change={comparison.changes.impressions}
            format="number"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            label="Kliky"
            change={comparison.changes.clicks}
            format="number"
          />
          <MetricCard
            label="ROAS (7d klik)"
            change={comparison.changes.roas_7d_click}
            format="roas"
          />
        </div>

        {/* Summary insights */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Týdenní přehled</h4>
          <div className="text-sm text-blue-800 space-y-1">
            {comparison.changes.roas.trend === 'up' && (
              <p>✅ ROAS se zlepšil o {comparison.changes.roas.percentage_change.toFixed(1)}% - kampaně jsou efektivnější</p>
            )}
            {comparison.changes.conversions.trend === 'up' && (
              <p>✅ Počet konverzí vzrostl o {comparison.changes.conversions.percentage_change.toFixed(1)}%</p>
            )}
            {comparison.changes.spend.trend === 'down' && (
              <p>💰 Náklady klesly o {Math.abs(comparison.changes.spend.percentage_change).toFixed(1)}% při zachování výkonu</p>
            )}
            {comparison.changes.spend.trend === 'up' && comparison.changes.roas.trend === 'up' && (
              <p>📈 Vyšší investice přinesly lepší výsledky - dobrá škálovatelnost</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
