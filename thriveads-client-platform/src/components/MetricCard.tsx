import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../lib/utils';

interface MetricChange {
  value: number;
  percentage: number;
  trend: 'up' | 'down' | 'neutral';
}

interface MetricCardProps {
  label: string;
  value: string;
  change: MetricChange;
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({ label, value, change, icon, className }: MetricCardProps) {
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

  return (
    <div className={cn('metric-card', className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="metric-label">{label}</div>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      
      <div className="metric-value">{value}</div>
      
      <div className={cn('metric-change', getTrendColor())}>
        {getTrendIcon()}
        <span className="ml-1">
          {change.percentage > 0 ? '+' : ''}{change.percentage.toFixed(1)}%
        </span>
        <span className="ml-2 text-gray-500 text-xs">
          vs předchozí období
        </span>
      </div>
    </div>
  );
}

// Specialized metric cards for common Meta Ads metrics
interface SpendCardProps {
  current: number;
  previous: number;
  currency?: string;
  className?: string;
}

export function SpendCard({ current, previous, currency = 'CZK', className }: SpendCardProps) {
  const change = {
    value: current - previous,
    percentage: previous > 0 ? ((current - previous) / previous) * 100 : 0,
    trend: current > previous ? 'up' as const : current < previous ? 'down' as const : 'neutral' as const
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('cs-CZ', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <MetricCard
      label="Celkové náklady"
      value={formatCurrency(current)}
      change={change}
      className={className}
    />
  );
}

interface ImpressionsCardProps {
  current: number;
  previous: number;
  className?: string;
}

export function ImpressionsCard({ current, previous, className }: ImpressionsCardProps) {
  const change = {
    value: current - previous,
    percentage: previous > 0 ? ((current - previous) / previous) * 100 : 0,
    trend: current > previous ? 'up' as const : current < previous ? 'down' as const : 'neutral' as const
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
  };

  return (
    <MetricCard
      label="Zobrazení"
      value={formatNumber(current)}
      change={change}
      className={className}
    />
  );
}

interface ROASCardProps {
  current: number;
  previous: number;
  className?: string;
}

export function ROASCard({ current, previous, className }: ROASCardProps) {
  const change = {
    value: current - previous,
    percentage: previous > 0 ? ((current - previous) / previous) * 100 : 0,
    trend: current > previous ? 'up' as const : current < previous ? 'down' as const : 'neutral' as const
  };

  return (
    <MetricCard
      label="ROAS"
      value={current.toFixed(1) + 'x'}
      change={change}
      className={className}
    />
  );
}

interface ConversionsCardProps {
  current: number;
  previous: number;
  className?: string;
}

export function ConversionsCard({ current, previous, className }: ConversionsCardProps) {
  const change = {
    value: current - previous,
    percentage: previous > 0 ? ((current - previous) / previous) * 100 : 0,
    trend: current > previous ? 'up' as const : current < previous ? 'down' as const : 'neutral' as const
  };

  return (
    <MetricCard
      label="Konverze"
      value={current.toLocaleString()}
      change={change}
      className={className}
    />
  );
}
