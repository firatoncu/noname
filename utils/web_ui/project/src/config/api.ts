// API configuration for the trading dashboard
// Use HTTP for development to avoid SSL certificate issues
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'n0name Trading Dashboard';

export { API_BASE_URL, APP_TITLE };

// Helper function to create API URLs
export const createApiUrl = (endpoint: string): string => {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  return url;
};

// API endpoints
export const API_ENDPOINTS = {
  POSITIONS: '/positions',
  TRADING_CONDITIONS: '/trading-conditions',
  WALLET: '/wallet',
  HISTORICAL_POSITIONS: '/historical-positions',
  CLOSE_POSITION: '/close-position',
  SET_TPSL: '/set-tpsl',
  CLOSE_LIMIT_ORDERS: '/close-limit-orders',
} as const;

// API response types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

// Error handling utilities
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: Response
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const handleApiResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.error || errorData.message || errorMessage;
    } catch {
      // If parsing fails, use the raw text or default message
      errorMessage = errorText || errorMessage;
    }
    
    throw new ApiError(errorMessage, response.status, response);
  }
  
  const data = await response.json();
  return data;
};

// Request utilities
export const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = createApiUrl(endpoint);
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };
  
  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };
  
  const response = await fetch(url, config);
  return handleApiResponse<T>(response);
};

// Specific API methods
export const api = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),
    
  post: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
    
  put: <T>(endpoint: string, data?: any, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
    
  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
}; 