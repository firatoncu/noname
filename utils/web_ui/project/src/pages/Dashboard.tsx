import React, { useEffect } from 'react';
import PositionCard from '../components/PositionCard';
import { WalletCard } from '../components/WalletCard';
import { HistoricalPositions } from '../components/HistoricalPositions';
import { LoadingSpinner, CardSkeleton } from '../components/LoadingSpinner';
import { useAppContext } from '../contexts/AppContext';
import { usePositions, useWallet, useTradingConditions, useHistoricalPositions } from '../hooks/useApi';
import { RefreshCw, AlertCircle, TrendingUp, Wallet, BarChart } from 'lucide-react';
import { Link } from 'react-router-dom';

function Dashboard() {
  const { state, actions } = useAppContext();
  const { errors } = state;

  // API hooks with automatic polling - use data directly from hooks
  const positionsApi = usePositions({
    onError: (error) => {
      console.error('Positions API Error:', error);
      actions.addError(`Positions: ${error}`);
    },
  });

  const walletApi = useWallet({
    onError: (error) => {
      console.error('Wallet API Error:', error);
      actions.addError(`Wallet: ${error}`);
    },
  });

  const tradingConditionsApi = useTradingConditions({
    onSuccess: (data) => {
      console.log('Trading Conditions loaded:', data?.length || 0, 'items');
      actions.setTradingConditions(data);
    },
    onError: (error) => {
      console.error('Trading Conditions API Error:', error);
      actions.addError(`Trading Conditions: ${error}`);
    },
  });

  // Add historical positions hook
  const historicalPositionsApi = useHistoricalPositions({
    onSuccess: (data) => {
      console.log('Historical Positions loaded:', data?.length || 0, 'items');
      actions.setHistoricalPositions(data);
    },
    onError: (error) => {
      console.error('Historical Positions API Error:', error);
      actions.addError(`Historical Positions: ${error}`);
    },
  });

  // Use data directly from API hooks instead of AppContext
  const positions = positionsApi.data || [];
  const wallet = walletApi.data || {
    totalBalance: '0',
    availableBalance: '0',
    unrealizedPnL: '0',
    dailyPnL: '0',
    weeklyPnL: '0',
    marginRatio: '0',
  };

  // Debug logging (commented out for performance)
  // console.log(`🔍 [Dashboard] Positions API:`, {
  //   data: positionsApi.data,
  //   loading: positionsApi.loading,
  //   error: positionsApi.error,
  //   lastFetch: positionsApi.lastFetch
  // });
  
  const loading = {
    positions: positionsApi.loading,
    wallet: walletApi.loading,
    tradingConditions: tradingConditionsApi.loading,
    historicalPositions: historicalPositionsApi.loading,
  };

  const lastUpdate = Math.max(
    positionsApi.lastFetch || 0,
    walletApi.lastFetch || 0,
    tradingConditionsApi.lastFetch || 0,
    historicalPositionsApi.lastFetch || 0
  ) || null;

  const handleRefresh = () => {
    actions.clearErrors();
    positionsApi.refetch();
    walletApi.refetch();
    tradingConditionsApi.refetch();
    historicalPositionsApi.refetch();
  };

  const formatLastUpdate = (timestamp: number | null) => {
    if (!timestamp) return 'Never';
    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Trading Dashboard
              </h1>
              <p className="text-gray-400">
                Real-time overview of your trading positions and performance
              </p>
            </div>
            
            <div className="mt-4 sm:mt-0 flex items-center space-x-4">
              {lastUpdate && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">
                    Last update: {formatLastUpdate(lastUpdate)}
                  </span>
                  {(loading.positions || loading.wallet) && (
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="text-xs text-green-400 ml-1">Live</span>
                    </div>
                  )}
                </div>
              )}
              
              <button
                onClick={handleRefresh}
                disabled={loading.positions || loading.wallet}
                className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
              >
                <RefreshCw 
                  className={`w-4 h-4 mr-2 ${(loading.positions || loading.wallet) ? 'animate-spin' : ''}`} 
                />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="mb-6">
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
                <h3 className="text-red-400 font-semibold">
                  {errors.length} Error{errors.length > 1 ? 's' : ''}
                </h3>
                <button
                  onClick={actions.clearErrors}
                  className="ml-auto text-red-400 hover:text-red-300 text-sm"
                >
                  Clear
                </button>
              </div>
              <ul className="space-y-1">
                {errors.map((error, index) => (
                  <li key={index} className="text-red-300 text-sm">
                    • {error}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-blue-400 mr-3" />
              <div>
                <p className="text-gray-400 text-sm">Active Positions</p>
                <p className="text-2xl font-bold text-white">
                  {loading.positions && positions.length === 0 ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    positions.length
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center">
              <Wallet className="w-8 h-8 text-green-400 mr-3" />
              <div>
                <p className="text-gray-400 text-sm">Total Balance</p>
                <p className="text-2xl font-bold text-white">
                  {loading.wallet && !wallet.totalBalance ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    `$${parseFloat(wallet.totalBalance).toLocaleString()}`
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center">
              <BarChart className="w-8 h-8 text-purple-400 mr-3" />
              <div>
                <p className="text-gray-400 text-sm">Daily PnL</p>
                <p className={`text-2xl font-bold ${
                  parseFloat(wallet.dailyPnL) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {loading.wallet && !wallet.dailyPnL ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    `${parseFloat(wallet.dailyPnL) >= 0 ? '+' : ''}$${parseFloat(wallet.dailyPnL).toLocaleString()}`
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Wallet Card */}
          <div className="xl:col-span-1">
            {loading.wallet && !wallet.totalBalance ? (
              <CardSkeleton />
            ) : (
              <WalletCard wallet={wallet} isDarkMode={true} />
            )}
          </div>

          {/* Positions */}
          <div className="xl:col-span-2">
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-6 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">
                      Active Positions
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">
                      Current trading positions and their performance
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-xs text-green-400">Real-time (1s)</span>
                  </div>
                </div>
              </div>
              
              <div className="p-6">
                {positions.length === 0 && !loading.positions ? (
                  <div className="text-center py-12">
                    <TrendingUp className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">No active positions</p>
                    <p className="text-gray-500 text-sm mt-1">
                      Positions will appear here when you have active trades
                    </p>
                  </div>
                ) : loading.positions && positions.length === 0 ? (
                  <div className="space-y-4">
                    {[...Array(3)].map((_, i) => (
                      <CardSkeleton key={i} />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {positions.map((position: any, index: number) => {
                      const PRICE_PRECISION: { [key: string]: number } = {
                        'BTCUSDT': 2,
                        'ETHUSDT': 2,
                        'SOLUSDT': 3,
                        'XRPUSDT': 4,
                        'REDUSDT': 4,
                        'BMTUSDT': 4,
                      };
                      
                      return (
                        <PositionCard 
                          key={position.symbol}
                          position={position} 
                          pricePrecision={PRICE_PRECISION[position.symbol] || 2}
                        />
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Historical Positions */}
        <div className="mt-8">
          <HistoricalPositions 
            positions={state.historicalPositions} 
            isDarkMode={true} 
          />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;