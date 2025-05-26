import { useState, useEffect, useCallback, useRef } from 'react';
import { createApiUrl } from '../config/api';

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastFetch: number | null;
}

export interface UseApiOptions {
  immediate?: boolean;
  interval?: number;
  retryAttempts?: number;
  retryDelay?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: string) => void;
}

export interface ApiResponse<T> extends ApiState<T> {
  refetch: () => Promise<void>;
  clearError: () => void;
  cancel: () => void;
}

export const useApi = <T = any>(
  endpoint: string,
  options: UseApiOptions = {}
): ApiResponse<T> => {
  const {
    immediate = true,
    interval,
    retryAttempts = 3,
    retryDelay = 1000,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    lastFetch: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const intervalRef = useRef<number | null>(null);
  const retryTimeoutRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  const fetchData = useCallback(async (attempt = 1): Promise<void> => {
    if (!isMountedRef.current) return;

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch(createApiUrl(endpoint), {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!isMountedRef.current) return;

      setState({
        data,
        loading: false,
        error: null,
        lastFetch: Date.now(),
      });

      onSuccess?.(data);
    } catch (error: any) {
      if (!isMountedRef.current) return;

      // Don't treat abort as an error
      if (error.name === 'AbortError') {
        return;
      }

      const errorMessage = error.message || 'An unknown error occurred';

      // Retry logic
      if (attempt < retryAttempts) {
        retryTimeoutRef.current = window.setTimeout(() => {
          fetchData(attempt + 1);
        }, retryDelay * attempt);
        return;
      }

      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));

      onError?.(errorMessage);
    }
  }, [endpoint, retryAttempts, retryDelay, onSuccess, onError]);

  const refetch = useCallback(async (): Promise<void> => {
    await fetchData();
  }, [fetchData]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
    }
    if (retryTimeoutRef.current) {
      window.clearTimeout(retryTimeoutRef.current);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [immediate, fetchData]);

  // Polling interval
  useEffect(() => {
    if (interval && interval > 0) {
      intervalRef.current = window.setInterval(() => {
        fetchData();
      }, interval);

      return () => {
        if (intervalRef.current) {
          window.clearInterval(intervalRef.current);
        }
      };
    }
  }, [interval, fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      cancel();
    };
  }, [cancel]);

  return {
    ...state,
    refetch,
    clearError,
    cancel,
  };
};

// Specialized hooks for common API calls
export const usePositions = (options?: UseApiOptions) => {
  return useApi('/positions', { interval: 5000, ...options });
};

export const useTradingConditions = (options?: UseApiOptions) => {
  return useApi('/trading-conditions', { interval: 1000, ...options });
};

export const useWallet = (options?: UseApiOptions) => {
  return useApi('/wallet', { interval: 5000, ...options });
};

export const useHistoricalPositions = (options?: UseApiOptions) => {
  return useApi('/historical-positions', { immediate: false, ...options });
}; 