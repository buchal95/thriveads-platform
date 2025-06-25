import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Date utility functions for Meta Ads reporting
export function getLastMonday(date: Date = new Date()): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1) - 7; // Last Monday
  return new Date(d.setDate(diff));
}

export function getLastSunday(date: Date = new Date()): Date {
  const lastMonday = getLastMonday(date);
  const lastSunday = new Date(lastMonday);
  lastSunday.setDate(lastMonday.getDate() + 6);
  return lastSunday;
}

export function getFirstDayOfLastMonth(date: Date = new Date()): Date {
  const d = new Date(date);
  d.setMonth(d.getMonth() - 1);
  d.setDate(1);
  return d;
}

export function getLastDayOfLastMonth(date: Date = new Date()): Date {
  const d = new Date(date);
  d.setDate(0); // This sets to last day of previous month
  return d;
}

// Format currency for display
export function formatCurrency(amount: number, currency: string = 'CZK'): string {
  return new Intl.NumberFormat('cs-CZ', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Format large numbers (e.g., impressions)
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toLocaleString();
}

// Format percentage (for general percentages that need to be multiplied by 100)
export function formatPercentage(num: number): string {
  return (num * 100).toFixed(2) + '%';
}

// Format CTR (Meta API returns CTR as percentage already, so no multiplication needed)
export function formatCTR(ctr: number): string {
  return ctr.toFixed(2) + '%';
}

// Format ROAS
export function formatROAS(roas: number): string {
  return roas.toFixed(1) + 'x';
}
