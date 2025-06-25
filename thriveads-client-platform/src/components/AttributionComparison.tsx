'use client';

import { PurchaseConversions } from '@/types/meta-ads';
import { formatCurrency, formatROAS, cn } from '@/lib/utils';
import { Info, TrendingUp, TrendingDown } from 'lucide-react';

interface AttributionComparisonProps {
  purchases: PurchaseConversions;
  spend: number;
  roasDefault: number;
  roas7dClick: number;
  className?: string;
}

export function AttributionComparison({ 
  purchases, 
  spend, 
  roasDefault, 
  roas7dClick, 
  className 
}: AttributionComparisonProps) {
  // Calculate the difference between attribution windows
  const conversionDiff = purchases.default.count - purchases['7d_click'].count;
  const valueDiff = purchases.default.value - purchases['7d_click'].value;
  const roasDiff = roasDefault - roas7dClick;

  return (
    <div className={cn('bg-white rounded-xl p-6 shadow-sm border border-gray-200', className)}>
      <div className="flex items-center gap-2 mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Porovnání atribučních oken
        </h3>
        <div className="group relative">
          <Info className="w-4 h-4 text-gray-400 cursor-help" />
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
            Default = 7d klik + 1d zobrazení | 7d klik = pouze kliky za 7 dní
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Default Attribution */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <h4 className="font-medium text-gray-900">Default (7d klik + 1d zobrazení)</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Konverze:</span>
              <span className="font-semibold text-gray-900">
                {purchases.default.count.toLocaleString()}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Hodnota:</span>
              <span className="font-semibold text-gray-900">
                {formatCurrency(purchases.default.value)}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">ROAS:</span>
              <span className="font-semibold text-green-600">
                {formatROAS(roasDefault)}
              </span>
            </div>
          </div>
        </div>

        {/* 7d Click Attribution */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
            <h4 className="font-medium text-gray-900">7d klik (pouze kliky)</h4>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Konverze:</span>
              <span className="font-semibold text-gray-900">
                {purchases['7d_click'].count.toLocaleString()}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Hodnota:</span>
              <span className="font-semibold text-gray-900">
                {formatCurrency(purchases['7d_click'].value)}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">ROAS:</span>
              <span className="font-semibold text-orange-600">
                {formatROAS(roas7dClick)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Difference Analysis */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h5 className="font-medium text-gray-900 mb-4">Rozdíl mezi atribučními okny</h5>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Rozdíl v konverzích</div>
            <div className="flex items-center justify-center gap-1">
              {conversionDiff > 0 ? (
                <TrendingUp className="w-4 h-4 text-blue-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-gray-400" />
              )}
              <span className="font-semibold text-gray-900">
                +{conversionDiff.toLocaleString()}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ({((conversionDiff / purchases['7d_click'].count) * 100).toFixed(1)}% více)
            </div>
          </div>

          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Rozdíl v hodnotě</div>
            <div className="flex items-center justify-center gap-1">
              {valueDiff > 0 ? (
                <TrendingUp className="w-4 h-4 text-blue-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-gray-400" />
              )}
              <span className="font-semibold text-gray-900">
                +{formatCurrency(valueDiff)}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ({((valueDiff / purchases['7d_click'].value) * 100).toFixed(1)}% více)
            </div>
          </div>

          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Rozdíl v ROAS</div>
            <div className="flex items-center justify-center gap-1">
              {roasDiff > 0 ? (
                <TrendingUp className="w-4 h-4 text-blue-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-gray-400" />
              )}
              <span className="font-semibold text-gray-900">
                +{roasDiff.toFixed(1)}x
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              ({((roasDiff / roas7dClick) * 100).toFixed(1)}% více)
            </div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Vysvětlení:</strong> Default atribuce zahrnuje konverze z view-through (zobrazení reklamy bez kliknutí), 
            zatímco 7d klik počítá pouze konverze po přímém kliknutí na reklamu. Rozdíl ukazuje vliv view-through konverzí.
          </p>
        </div>
      </div>
    </div>
  );
}

// Simplified version for metric cards
interface AttributionToggleProps {
  label: string;
  defaultValue: number;
  clickValue: number;
  format: 'currency' | 'number' | 'roas';
  showAttribution: 'default' | '7d_click';
  onToggle: (attribution: 'default' | '7d_click') => void;
  className?: string;
}

export function AttributionToggle({
  label,
  defaultValue,
  clickValue,
  format,
  showAttribution,
  onToggle,
  className
}: AttributionToggleProps) {
  const formatValue = (value: number) => {
    switch (format) {
      case 'currency':
        return formatCurrency(value);
      case 'roas':
        return formatROAS(value);
      default:
        return value.toLocaleString();
    }
  };

  const currentValue = showAttribution === 'default' ? defaultValue : clickValue;

  return (
    <div className={cn('metric-card', className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="metric-label">{label}</div>
        <button
          onClick={() => onToggle(showAttribution === 'default' ? '7d_click' : 'default')}
          className={cn(
            'px-2 py-1 text-xs font-medium rounded-md transition-colors',
            showAttribution === 'default' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-orange-100 text-orange-700'
          )}
        >
          {showAttribution === 'default' ? 'Default' : '7d klik'}
        </button>
      </div>
      
      <div className="metric-value">{formatValue(currentValue)}</div>
      
      <div className="text-xs text-gray-500 mt-2">
        {showAttribution === 'default' 
          ? '7d klik + 1d zobrazení' 
          : 'Pouze kliky za 7 dní'
        }
      </div>
    </div>
  );
}
