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

  // Ensure isMountedRef is set correctly - remove endpoint dependency to prevent remounting
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []); // Empty dependency array to run only once

  // Use refs for callbacks to avoid dependency issues
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  
  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  }, [onSuccess, onError]);

  const fetchData = useCallback(async (attempt = 1): Promise<void> => {
    // Minimal logging for performance
    
    // Check if component is still mounted
    if (!isMountedRef.current) {
      return;
    }

    // Create new AbortController only if we don't have one
    if (!abortControllerRef.current || abortControllerRef.current.signal.aborted) {
      abortControllerRef.current = new AbortController();
    }
    
    // Only set loading to true if we don't have data yet (first load)
    setState(prev => ({ 
      ...prev, 
      loading: prev.data === null, // Only loading on first fetch
      error: null 
    }));

    try {
      const url = createApiUrl(endpoint);
      
      const response = await fetch(url, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Response received successfully

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Check if component is still mounted before updating state
      if (!isMountedRef.current) return;

      // Only update state if data has actually changed (deep comparison for arrays/objects)
      setState(prevState => {
        const dataChanged = JSON.stringify(prevState.data) !== JSON.stringify(data);
        if (!dataChanged && !prevState.loading && !prevState.error) {
          // Data hasn't changed and we're not in loading/error state, skip update
          return prevState;
        }
        
        return {
          data,
          loading: false,
          error: null,
          lastFetch: Date.now(),
        };
      });

      // Data updated successfully
      onSuccessRef.current?.(data);
          } catch (error: any) {
        // Handle fetch errors
      
              // Check if component is still mounted before handling error
        if (!isMountedRef.current) {
          return;
        }

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

      onErrorRef.current?.(errorMessage);
    }
  }, [endpoint, retryAttempts, retryDelay]);

  // Debug: Log when fetchData is recreated (commented out for performance)
  // useEffect(() => {
  //   console.log(`🔄 [${new Date().toLocaleTimeString()}] fetchData function recreated for ${endpoint}`);
  // }, [fetchData]);

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

  // Stable polling interval
  useEffect(() => {
    if (interval && interval > 0) {
      const intervalId = window.setInterval(() => {
        // Use a stable reference to fetchData
        if (isMountedRef.current) {
          fetchData();
        }
      }, interval);

      intervalRef.current = intervalId;

      return () => {
        if (intervalRef.current) {
          window.clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }
  }, [interval, endpoint]); // Only depend on interval and endpoint, not fetchData

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
  return useApi('/positions', { interval: 1000, ...options }); // 1 second for real-time trading
};

export const useTradingConditions = (options?: UseApiOptions) => {
  return useApi('/trading-conditions', { interval: 5000, ...options }); // Reduced from 1s to 5s
};

export const useWallet = (options?: UseApiOptions) => {
  return useApi('/wallet', { interval: 2000, ...options }); // 2 seconds for PnL tracking
};

export const useHistoricalPositions = (options?: UseApiOptions) => {
  return useApi('/historical-positions', { immediate: true, ...options });
}; 