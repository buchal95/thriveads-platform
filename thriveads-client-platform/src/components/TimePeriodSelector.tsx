'use client';

import { useState } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { cn } from '../lib/utils';
import { TimePeriod } from '../types/meta-ads';

interface TimePeriodSelectorProps {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
  className?: string;
}

const periodOptions = [
  {
    value: 'last_week' as TimePeriod,
    label: 'Minulý týden',
    description: 'Pondělí - Neděle'
  },
  {
    value: 'last_month' as TimePeriod,
    label: 'Minulý měsíc',
    description: 'Celý kalendářní měsíc'
  }
];

export function TimePeriodSelector({ 
  selectedPeriod, 
  onPeriodChange, 
  className 
}: TimePeriodSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  const selectedOption = periodOptions.find(option => option.value === selectedPeriod);

  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg',
          'hover:border-blue-300 hover:shadow-sm transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          isOpen && 'border-blue-300 shadow-sm'
        )}
      >
        <Calendar className="w-4 h-4 text-gray-500" />
        <div className="text-left">
          <div className="font-medium text-gray-900">
            {selectedOption?.label}
          </div>
          <div className="text-xs text-gray-500">
            {selectedOption?.description}
          </div>
        </div>
        <ChevronDown 
          className={cn(
            'w-4 h-4 text-gray-400 transition-transform duration-200',
            isOpen && 'rotate-180'
          )} 
        />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 mt-2 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            {periodOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onPeriodChange(option.value);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors duration-150',
                  'first:rounded-t-lg last:rounded-b-lg',
                  selectedPeriod === option.value && 'bg-blue-50 text-blue-700'
                )}
              >
                <div className="font-medium">
                  {option.label}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {option.description}
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// Date range display component
interface DateRangeDisplayProps {
  since: string;
  until: string;
  className?: string;
}

export function DateRangeDisplay({ since, until, className }: DateRangeDisplayProps) {
  const formatDate = (dateString: string) => {
    // Use UTC to ensure consistent formatting between server and client
    const date = new Date(dateString);
    const day = date.getUTCDate();
    const month = date.getUTCMonth() + 1;
    const year = date.getUTCFullYear();
    return `${day}. ${month}. ${year}`;
  };

  return (
    <div className={cn('text-sm text-gray-600', className)}>
      {formatDate(since)} - {formatDate(until)}
    </div>
  );
}
