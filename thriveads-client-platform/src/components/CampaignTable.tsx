'use client';

import { useState } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Download, Eye } from 'lucide-react';
import { CampaignData } from '../types/meta-ads';
import { formatCurrency, formatNumber, formatPercentage, formatCTR, formatROAS, cn } from '../lib/utils';

interface CampaignTableProps {
  campaigns: CampaignData[];
  className?: string;
}

type SortField = 'name' | 'spend' | 'impressions' | 'clicks' | 'ctr' | 'conversions' | 'roas';
type SortDirection = 'asc' | 'desc';

export function CampaignTable({ campaigns, className }: CampaignTableProps) {
  const [sortField, setSortField] = useState<SortField>('spend');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [showAttribution, setShowAttribution] = useState<'default' | '7d_click'>('default');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedCampaigns = [...campaigns].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    switch (sortField) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'spend':
        aValue = a.metrics.spend;
        bValue = b.metrics.spend;
        break;
      case 'impressions':
        aValue = a.metrics.impressions;
        bValue = b.metrics.impressions;
        break;
      case 'clicks':
        aValue = a.metrics.clicks;
        bValue = b.metrics.clicks;
        break;
      case 'ctr':
        aValue = a.metrics.ctr;
        bValue = b.metrics.ctr;
        break;
      case 'conversions':
        aValue = showAttribution === 'default' ? a.metrics.conversions : a.metrics.purchases['7d_click'].count;
        bValue = showAttribution === 'default' ? b.metrics.conversions : b.metrics.purchases['7d_click'].count;
        break;
      case 'roas':
        aValue = showAttribution === 'default' ? a.metrics.roas : a.metrics.roas_7d_click;
        bValue = showAttribution === 'default' ? b.metrics.roas : b.metrics.roas_7d_click;
        break;
      default:
        return 0;
    }

    if (sortDirection === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
    }
  });

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 text-gray-400" />;
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="w-4 h-4 text-blue-600" />
      : <ArrowDown className="w-4 h-4 text-blue-600" />;
  };

  const getStatusBadge = (status: string) => {
    const statusColors = {
      ACTIVE: 'bg-green-100 text-green-800',
      PAUSED: 'bg-yellow-100 text-yellow-800',
      DELETED: 'bg-red-100 text-red-800',
      ARCHIVED: 'bg-gray-100 text-gray-800'
    };

    const statusLabels = {
      ACTIVE: 'Aktivní',
      PAUSED: 'Pozastaveno',
      DELETED: 'Smazáno',
      ARCHIVED: 'Archivováno'
    };

    return (
      <span className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        statusColors[status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'
      )}>
        {statusLabels[status as keyof typeof statusLabels] || status}
      </span>
    );
  };

  return (
    <div className={cn('luxury-table', className)}>
      <div className="px-8 py-6 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-gray-900">
              Výkonnost kampaní
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Seřazeno podle {sortField === 'spend' ? 'nákladů' : sortField === 'roas' ? 'ROAS' : sortField} • {campaigns.length} kampaní
            </p>
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
            <button className="btn-secondary">
              <Download className="w-4 h-4 mr-2" />
              Exportovat CSV
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="luxury-table-header">
            <tr>
              <th className="px-8 py-4 text-left">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900"
                >
                  Název kampaně
                  {getSortIcon('name')}
                </button>
              </th>
              <th className="px-8 py-4 text-left">
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Stav
                </span>
              </th>
              <th className="px-8 py-4 text-right">
                <button
                  onClick={() => handleSort('spend')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900 ml-auto"
                >
                  Náklady
                  {getSortIcon('spend')}
                </button>
              </th>
              <th className="px-8 py-4 text-right">
                <button
                  onClick={() => handleSort('impressions')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900 ml-auto"
                >
                  Zobrazení
                  {getSortIcon('impressions')}
                </button>
              </th>
              <th className="px-8 py-4 text-right">
                <button
                  onClick={() => handleSort('clicks')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900 ml-auto"
                >
                  Kliky
                  {getSortIcon('clicks')}
                </button>
              </th>
              <th className="px-8 py-4 text-right">
                <button
                  onClick={() => handleSort('ctr')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900 ml-auto"
                >
                  CTR
                  {getSortIcon('ctr')}
                </button>
              </th>
              <th className="px-8 py-4 text-right">
                <button
                  onClick={() => handleSort('conversions')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900 ml-auto"
                >
                  Konverze
                  {getSortIcon('conversions')}
                </button>
              </th>
              <th className="px-8 py-4 text-right">
                <button
                  onClick={() => handleSort('roas')}
                  className="flex items-center gap-2 text-xs font-bold text-gray-700 uppercase tracking-wider hover:text-gray-900 ml-auto"
                >
                  ROAS
                  {getSortIcon('roas')}
                </button>
              </th>
              <th className="px-8 py-4 text-center">
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Akce
                </span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {sortedCampaigns.map((campaign) => {
              const conversions = showAttribution === 'default'
                ? campaign.metrics.conversions
                : campaign.metrics.purchases['7d_click'].count;
              const roas = showAttribution === 'default'
                ? campaign.metrics.roas
                : campaign.metrics.roas_7d_click;

              return (
                <tr key={campaign.id} className="luxury-table-row">
                  <td className="px-8 py-6">
                    <div className="text-sm font-semibold text-gray-900">
                      {campaign.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {campaign.objective}
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    {getStatusBadge(campaign.status)}
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(campaign.metrics.spend)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-medium text-gray-700">
                      {formatNumber(campaign.metrics.impressions)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-medium text-gray-700">
                      {formatNumber(campaign.metrics.clicks)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-medium text-gray-700">
                      {formatCTR(campaign.metrics.ctr)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="text-sm font-semibold text-gray-900">
                      {conversions.toLocaleString()}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className={cn(
                      "text-lg font-bold",
                      roas > 5 ? "text-green-600" : roas > 2 ? "text-yellow-600" : "text-red-600"
                    )}>
                      {formatROAS(roas)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-center">
                    <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl transition-all duration-200">
                      <Eye className="w-4 h-4" />
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
            Seřazeno podle {sortField === 'spend' ? 'nákladů' : sortField === 'roas' ? 'ROAS' : sortField} ({sortDirection === 'desc' ? 'sestupně' : 'vzestupně'})
          </div>
        </div>
      </div>
    </div>
  );
}
