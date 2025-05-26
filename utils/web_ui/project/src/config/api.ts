// API configuration for the trading dashboard
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://localhost:8000/api';
const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'n0name Trading Dashboard';

export { API_BASE_URL, APP_TITLE };

// Helper function to create API URLs
export const createApiUrl = (endpoint: string): string => {
  return `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};

// API endpoints
export const API_ENDPOINTS = {
  POSITIONS: '/positions',
  TRADING_CONDITIONS: '/trading-conditions',
  WALLET: '/wallet',
  HISTORICAL_POSITIONS: '/historical-positions',
} as const; 