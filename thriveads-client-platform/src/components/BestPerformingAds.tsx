'use client';

import { useState, useEffect } from 'react';
import { ExternalLink, Eye, TrendingUp, Award, RefreshCw } from 'lucide-react';
import { AdData } from '@/types/meta-ads';
import { formatCurrency, formatROAS, formatNumber, formatCTR, cn } from '@/lib/utils';

interface BestPerformingAdsProps {
  className?: string;
}

export function BestPerformingAds({ className }: BestPerformingAdsProps) {
  const [ads, setAds] = useState<AdData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAttribution, setShowAttribution] = useState<'default' | '7d_click'>('default');

  const fetchTopAds = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/meta-insights/ads?limit=10');
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      const data = await response.json();
      setAds(data.top_performing_ads || []);
    } catch (err) {
      console.error('Failed to fetch top performing ads:', err);
      setError(err instanceof Error ? err.message : 'Failed to load ads');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopAds();
  }, []);

  const openFacebookAd = (facebookUrl: string, adName: string) => {
    window.open(facebookUrl, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
    return (
      <div className={cn('luxury-table', className)}>
        <div className="px-8 py-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
              <Award className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">Nejlepší reklamy</h3>
              <p className="text-sm text-gray-500">Načítání dat...</p>
            </div>
            <RefreshCw className="w-5 h-5 animate-spin text-gray-400 ml-auto" />
          </div>
        </div>
        <div className="p-8 space-y-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-gradient-to-r from-gray-100 to-gray-200 rounded-xl"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('luxury-table', className)}>
        <div className="px-8 py-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
              <Award className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">Nejlepší reklamy</h3>
              <p className="text-sm text-gray-500">Chyba při načítání</p>
            </div>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="badge-error mb-6 text-base px-6 py-3">
            <p className="font-semibold">Chyba při načítání reklam</p>
            <p className="text-sm mt-1 opacity-80">{error}</p>
          </div>
          <button
            onClick={fetchTopAds}
            className="btn-primary"
          >
            Zkusit znovu
          </button>
        </div>
      </div>
    );
  }

  if (ads.length === 0) {
    return (
      <div className={cn('luxury-table', className)}>
        <div className="px-8 py-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center">
              <Award className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">Nejlepší reklamy</h3>
              <p className="text-sm text-gray-500">Žádná data k zobrazení</p>
            </div>
          </div>
        </div>
        <div className="text-center py-16 text-gray-500">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <Award className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-lg font-medium">Žádné reklamy s konverzemi nebyly nalezeny</p>
          <p className="text-sm mt-1">Zkuste změnit časové období nebo zkontrolovat nastavení kampaní</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('luxury-table', className)}>
      <div className="px-8 py-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center shadow-lg">
              <Award className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900">
                Nejlepší reklamy
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Seřazeno podle ROAS • {ads.length} reklam s konverzemi
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAttribution(showAttribution === 'default' ? '7d_click' : 'default')}
              className={cn(
                'px-4 py-2 text-sm font-semibold rounded-xl transition-all duration-200',
                showAttribution === 'default'
                  ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
                  : 'bg-orange-50 text-orange-700 border border-orange-200 shadow-sm'
              )}
            >
              {showAttribution === 'default' ? 'Default atribuce' : '7d klik atribuce'}
            </button>
            <button
              onClick={fetchTopAds}
              className="p-3 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl transition-all duration-200"
              title="Obnovit data"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="luxury-table-header">
            <tr>
              <th className="px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Reklama
              </th>
              <th className="px-8 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Kampaň
              </th>
              <th className="px-8 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider">
                ROAS
              </th>
              <th className="px-8 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider">
                Konverze
              </th>
              <th className="px-8 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider">
                Náklady
              </th>
              <th className="px-8 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider">
                Zobrazení
              </th>
              <th className="px-8 py-4 text-right text-xs font-bold text-gray-700 uppercase tracking-wider">
                CTR
              </th>
              <th className="px-8 py-4 text-center text-xs font-bold text-gray-700 uppercase tracking-wider">
                Akce
              </th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {ads.map((ad, index) => {
              const roas = showAttribution === 'default' ? ad.metrics.roas : ad.metrics.roas_7d_click;
              const conversions = showAttribution === 'default'
                ? ad.metrics.purchases.default.count
                : ad.metrics.purchases['7d_click'].count;

              return (
                <tr key={ad.id} className="luxury-table-row">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-lg">
                          {index + 1}
                        </div>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-semibold text-gray-900 truncate max-w-xs">
                          {ad.name}
                        </div>
                        <div className="text-sm text-gray-500 truncate">
                          {ad.adset_name}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                      {ad.campaign_name}
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {roas > 0 && <TrendingUp className="w-4 h-4 text-green-500" />}
                      <span className={cn(
                        "text-lg font-bold",
                        roas > 5 ? "text-green-600" : roas > 2 ? "text-yellow-600" : "text-red-600"
                      )}>
                        {formatROAS(roas)}
                      </span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      {conversions.toLocaleString()}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(ad.metrics.spend)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-medium text-gray-700">
                      {formatNumber(ad.metrics.impressions)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-medium text-gray-700">
                      {formatCTR(ad.metrics.ctr)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-center">
                    <button
                      onClick={() => openFacebookAd(ad.facebook_url, ad.name)}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-blue-700 bg-blue-50 rounded-xl hover:bg-blue-100 hover:-translate-y-0.5 transition-all duration-200 shadow-sm"
                      title={`Zobrazit reklamu na Facebooku: ${ad.name}`}
                    >
                      <Eye className="w-4 h-4" />
                      Zobrazit
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="px-8 py-6 border-t border-gray-100 bg-gray-50/50 backdrop-blur-sm">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500"></div>
            <span className="font-medium text-gray-700">
              Atribuce: {showAttribution === 'default' ? '7d klik + 1d zobrazení' : 'Pouze kliky za 7 dní'}
            </span>
          </div>
          <div className="text-gray-600">
            Seřazeno podle ROAS ({showAttribution === 'default' ? 'default' : '7d klik'})
          </div>
        </div>
      </div>
    </div>
  );
}
