// Multi-country client configuration system

export interface ClientConfig {
  id: string;
  name: string;
  country: string;
  currency: string;
  locale: string;
  metaAdAccountId: string;
  metaAccessToken: string;
  timezone: string;
  dateFormat: string;
  numberFormat: {
    decimal: string;
    thousands: string;
  };
}

// Country-specific configurations
export const COUNTRY_CONFIGS = {
  CZ: {
    currency: 'CZK',
    locale: 'cs-CZ',
    timezone: 'Europe/Prague',
    dateFormat: 'dd. MM. yyyy',
    numberFormat: {
      decimal: ',',
      thousands: ' '
    }
  },
  SK: {
    currency: 'EUR',
    locale: 'sk-SK',
    timezone: 'Europe/Bratislava',
    dateFormat: 'dd. MM. yyyy',
    numberFormat: {
      decimal: ',',
      thousands: ' '
    }
  },
  DE: {
    currency: 'EUR',
    locale: 'de-DE',
    timezone: 'Europe/Berlin',
    dateFormat: 'dd.MM.yyyy',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    }
  },
  AT: {
    currency: 'EUR',
    locale: 'de-AT',
    timezone: 'Europe/Vienna',
    dateFormat: 'dd.MM.yyyy',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    }
  },
  PL: {
    currency: 'PLN',
    locale: 'pl-PL',
    timezone: 'Europe/Warsaw',
    dateFormat: 'dd.MM.yyyy',
    numberFormat: {
      decimal: ',',
      thousands: ' '
    }
  }
} as const;

// Client configurations
export const CLIENT_CONFIGS: Record<string, ClientConfig> = {
  'mimilatky-cz': {
    id: 'mimilatky-cz',
    name: 'Mimilátky CZ',
    country: 'CZ',
    currency: 'CZK',
    locale: 'cs-CZ',
    metaAdAccountId: '513010266454814',
    metaAccessToken: process.env.META_ACCESS_TOKEN || '',
    timezone: 'Europe/Prague',
    dateFormat: 'dd. MM. yyyy',
    numberFormat: {
      decimal: ',',
      thousands: ' '
    }
  }
  // Future clients can be added here:
  // 'mimilatky-sk': {
  //   id: 'mimilatky-sk',
  //   name: 'Mimilátky SK',
  //   country: 'SK',
  //   currency: 'EUR',
  //   locale: 'sk-SK',
  //   metaAdAccountId: 'XXXXXXXXXX',
  //   metaAccessToken: process.env.META_ACCESS_TOKEN_SK || '',
  //   ...COUNTRY_CONFIGS.SK
  // }
};

// Get client configuration
export function getClientConfig(clientId: string): ClientConfig {
  const config = CLIENT_CONFIGS[clientId];
  if (!config) {
    throw new Error(`Client configuration not found for: ${clientId}`);
  }
  return config;
}

// Get current client (for now, default to Mimilátky CZ)
export function getCurrentClientConfig(): ClientConfig {
  const clientId = process.env.CLIENT_ID || 'mimilatky-cz';
  return getClientConfig(clientId);
}

// Validate client configuration
export function validateClientConfig(config: ClientConfig): boolean {
  return !!(
    config.id &&
    config.name &&
    config.country &&
    config.currency &&
    config.locale &&
    config.metaAdAccountId &&
    config.metaAccessToken &&
    config.metaAdAccountId.match(/^\d+$/) // Should be numeric
  );
}

// Get available countries
export function getAvailableCountries(): string[] {
  return Object.keys(COUNTRY_CONFIGS);
}

// Get clients by country
export function getClientsByCountry(country: string): ClientConfig[] {
  return Object.values(CLIENT_CONFIGS).filter(client => client.country === country);
}

// Currency formatting helper
export function formatCurrencyForClient(amount: number, clientConfig: ClientConfig): string {
  return new Intl.NumberFormat(clientConfig.locale, {
    style: 'currency',
    currency: clientConfig.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

// Date formatting helper
export function formatDateForClient(date: Date | string, clientConfig: ClientConfig): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(clientConfig.locale, {
    day: 'numeric',
    month: 'numeric',
    year: 'numeric',
    timeZone: clientConfig.timezone
  }).format(dateObj);
}

// Number formatting helper
export function formatNumberForClient(num: number, clientConfig: ClientConfig): string {
  return new Intl.NumberFormat(clientConfig.locale).format(num);
}
