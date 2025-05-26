import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { Position, TradingConditions, WalletInfo, HistoricalPosition } from '../types';
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket';
import { API_BASE_URL } from '../config/api';

// State interface
export interface AppState {
  positions: Position[];
  tradingConditions: TradingConditions[];
  wallet: WalletInfo;
  historicalPositions: HistoricalPosition[];
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate: number | null;
  errors: string[];
  loading: {
    positions: boolean;
    tradingConditions: boolean;
    wallet: boolean;
    historicalPositions: boolean;
  };
}

// Action types
type AppAction =
  | { type: 'SET_POSITIONS'; payload: Position[] }
  | { type: 'SET_TRADING_CONDITIONS'; payload: TradingConditions[] }
  | { type: 'SET_WALLET'; payload: WalletInfo }
  | { type: 'SET_HISTORICAL_POSITIONS'; payload: HistoricalPosition[] }
  | { type: 'SET_CONNECTION_STATUS'; payload: AppState['connectionStatus'] }
  | { type: 'SET_LOADING'; payload: { key: keyof AppState['loading']; value: boolean } }
  | { type: 'ADD_ERROR'; payload: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'UPDATE_LAST_UPDATE' }
  | { type: 'WEBSOCKET_MESSAGE'; payload: WebSocketMessage };

// Initial state
const initialState: AppState = {
  positions: [],
  tradingConditions: [],
  wallet: {
    totalBalance: '0',
    availableBalance: '0',
    unrealizedPnL: '0',
    dailyPnL: '0',
    weeklyPnL: '0',
    marginRatio: '0',
  },
  historicalPositions: [],
  connectionStatus: 'disconnected',
  lastUpdate: null,
  errors: [],
  loading: {
    positions: false,
    tradingConditions: false,
    wallet: false,
    historicalPositions: false,
  },
};

// Reducer
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_POSITIONS':
      return {
        ...state,
        positions: action.payload,
        lastUpdate: Date.now(),
        loading: { ...state.loading, positions: false },
      };

    case 'SET_TRADING_CONDITIONS':
      return {
        ...state,
        tradingConditions: action.payload,
        lastUpdate: Date.now(),
        loading: { ...state.loading, tradingConditions: false },
      };

    case 'SET_WALLET':
      return {
        ...state,
        wallet: action.payload,
        lastUpdate: Date.now(),
        loading: { ...state.loading, wallet: false },
      };

    case 'SET_HISTORICAL_POSITIONS':
      return {
        ...state,
        historicalPositions: action.payload,
        lastUpdate: Date.now(),
        loading: { ...state.loading, historicalPositions: false },
      };

    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: action.payload,
      };

    case 'SET_LOADING':
      return {
        ...state,
        loading: {
          ...state.loading,
          [action.payload.key]: action.payload.value,
        },
      };

    case 'ADD_ERROR':
      return {
        ...state,
        errors: [...state.errors, action.payload],
      };

    case 'CLEAR_ERRORS':
      return {
        ...state,
        errors: [],
      };

    case 'UPDATE_LAST_UPDATE':
      return {
        ...state,
        lastUpdate: Date.now(),
      };

    case 'WEBSOCKET_MESSAGE':
      // Handle real-time updates from WebSocket
      const { type, data } = action.payload;
      switch (type) {
        case 'positions_update':
          return {
            ...state,
            positions: data,
            lastUpdate: Date.now(),
          };
        case 'trading_conditions_update':
          return {
            ...state,
            tradingConditions: data,
            lastUpdate: Date.now(),
          };
        case 'wallet_update':
          return {
            ...state,
            wallet: data,
            lastUpdate: Date.now(),
          };
        case 'error':
          return {
            ...state,
            errors: [...state.errors, data.message || 'WebSocket error'],
          };
        default:
          return state;
      }

    default:
      return state;
  }
};

// Context
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  actions: {
    setPositions: (positions: Position[]) => void;
    setTradingConditions: (conditions: TradingConditions[]) => void;
    setWallet: (wallet: WalletInfo) => void;
    setHistoricalPositions: (positions: HistoricalPosition[]) => void;
    setLoading: (key: keyof AppState['loading'], value: boolean) => void;
    addError: (error: string) => void;
    clearErrors: () => void;
    refreshData: () => void;
  };
  websocket: {
    isConnected: boolean;
    reconnect: () => void;
    sendMessage: (message: any) => void;
  };
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // WebSocket connection
  const wsUrl = API_BASE_URL.replace('http', 'ws').replace('/api', '/ws');
  const {
    isConnected,
    reconnect,
    sendMessage,
    lastMessage,
  } = useWebSocket({
    url: wsUrl,
    shouldReconnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    onOpen: () => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: 'connected' });
      dispatch({ type: 'CLEAR_ERRORS' });
    },
    onClose: () => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: 'disconnected' });
    },
    onError: () => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: 'error' });
      dispatch({ type: 'ADD_ERROR', payload: 'WebSocket connection error' });
    },
    onMessage: (message: WebSocketMessage) => {
      dispatch({ type: 'WEBSOCKET_MESSAGE', payload: message });
    },
  });

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      dispatch({ type: 'WEBSOCKET_MESSAGE', payload: lastMessage });
    }
  }, [lastMessage]);

  // Action creators
  const actions = {
    setPositions: (positions: Position[]) => {
      dispatch({ type: 'SET_POSITIONS', payload: positions });
    },
    setTradingConditions: (conditions: TradingConditions[]) => {
      dispatch({ type: 'SET_TRADING_CONDITIONS', payload: conditions });
    },
    setWallet: (wallet: WalletInfo) => {
      dispatch({ type: 'SET_WALLET', payload: wallet });
    },
    setHistoricalPositions: (positions: HistoricalPosition[]) => {
      dispatch({ type: 'SET_HISTORICAL_POSITIONS', payload: positions });
    },
    setLoading: (key: keyof AppState['loading'], value: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: { key, value } });
    },
    addError: (error: string) => {
      dispatch({ type: 'ADD_ERROR', payload: error });
    },
    clearErrors: () => {
      dispatch({ type: 'CLEAR_ERRORS' });
    },
    refreshData: () => {
      // Send refresh request via WebSocket
      if (isConnected) {
        sendMessage({ type: 'refresh_data' });
      }
    },
  };

  const contextValue: AppContextType = {
    state,
    dispatch,
    actions,
    websocket: {
      isConnected,
      reconnect,
      sendMessage,
    },
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// Hook to use the context
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}; 