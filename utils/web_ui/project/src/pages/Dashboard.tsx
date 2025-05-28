import React, { useEffect } from 'react';
import PositionCard from '../components/PositionCard';
import { HistoricalPositions } from '../components/HistoricalPositions';
import { LoadingSpinner, CardSkeleton } from '../components/LoadingSpinner';
import { useAppContext } from '../contexts/AppContext';
import { usePositions, useWallet, useTradingConditions, useHistoricalPositions } from '../hooks/useApi';
import { AlertCircle, TrendingUp, Wallet, BarChart, Activity } from 'lucide-react';
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

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="mb-8 animate-fade-in">
            <div className="bg-dark-accent-error/10 backdrop-blur-sm border border-dark-accent-error/30 rounded-2xl p-6 shadow-glass">
              <div className="flex items-center mb-4">
                <AlertCircle className="w-6 h-6 text-dark-accent-error mr-3" />
                <h3 className="text-dark-accent-error font-semibold text-lg">
                  {errors.length} Error{errors.length > 1 ? 's' : ''}
                </h3>
                <button
                  onClick={actions.clearErrors}
                  className="ml-auto text-dark-accent-error hover:text-dark-text-primary text-sm px-3 py-1 rounded-lg hover:bg-dark-accent-error/20 transition-all duration-300"
                >
                  Clear
                </button>
              </div>
              <ul className="space-y-2">
                {errors.map((error, index) => (
                  <li key={index} className="text-dark-text-secondary text-sm flex items-start">
                    <span className="text-dark-accent-error mr-2">•</span>
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group">
            <div className="flex items-center">
              <div className="p-3 bg-dark-accent-primary/20 rounded-xl mr-4 group-hover:bg-dark-accent-primary/30 transition-colors duration-300">
                <TrendingUp className="w-8 h-8 text-dark-accent-primary" />
              </div>
              <div>
                <p className="text-dark-text-muted text-sm font-medium">Active Positions</p>
                <p className="text-3xl font-bold text-dark-text-primary mt-1">
                  {loading.positions && positions.length === 0 ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    positions.length
                  )}
                </p>
              </div>
            </div>
          </div>

          <Link to="/wallet" className="block">
            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group cursor-pointer hover:border-dark-accent-success/50">
              <div className="flex items-center">
                <div className="p-3 bg-dark-accent-success/20 rounded-xl mr-4 group-hover:bg-dark-accent-success/30 transition-colors duration-300">
                  <Wallet className="w-8 h-8 text-dark-accent-success" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-dark-text-muted text-sm font-medium">Total Balance</p>
                    <span className="text-dark-accent-success text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      View Details →
                    </span>
                  </div>
                  <p className="text-3xl font-bold text-dark-text-primary mt-1">
                    {loading.wallet ? (
                      <LoadingSpinner size="sm" variant="white" />
                    ) : (
                      `$${parseFloat(wallet.totalBalance).toLocaleString()}`
                    )}
                  </p>
                </div>
              </div>
            </div>
          </Link>

          <Link to="/analysis" className="block">
            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group cursor-pointer hover:border-dark-accent-info/50">
              <div className="flex items-center">
                <div className="p-3 bg-dark-accent-info/20 rounded-xl mr-4 group-hover:bg-dark-accent-info/30 transition-colors duration-300">
                  <BarChart className="w-8 h-8 text-dark-accent-info" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-dark-text-muted text-sm font-medium">Daily P&L</p>
                    <span className="text-dark-accent-info text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      View Analysis →
                    </span>
                  </div>
                  <p className={`text-3xl font-bold mt-1 ${
                    parseFloat(wallet.dailyPnL) >= 0 
                      ? 'text-dark-accent-success' 
                      : 'text-dark-accent-error'
                  }`}>
                    {loading.wallet ? (
                      <LoadingSpinner size="sm" variant="white" />
                    ) : (
                      `${parseFloat(wallet.dailyPnL) >= 0 ? '+' : ''}$${parseFloat(wallet.dailyPnL).toLocaleString()}`
                    )}
                  </p>
                </div>
              </div>
            </div>
          </Link>
        </div>

        {/* Main Content Grid */}
        <div className="space-y-8">
          {/* Active Positions Section */}
          <div className="animate-fade-in-up">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-dark-text-primary">Active Positions</h2>
            </div>

            {loading.positions && positions.length === 0 ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <CardSkeleton key={i} />
                ))}
              </div>
            ) : positions.length === 0 ? (
              <div className="bg-dark-bg-secondary/50 backdrop-blur-sm rounded-2xl p-8 border border-dark-border-primary text-center">
                <TrendingUp className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-dark-text-primary mb-2">No Active Positions</h3>
                <p className="text-dark-text-muted">
                  Your trading positions will appear here when you have active trades.
                </p>
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
                    <div 
                      key={position.symbol} 
                      className="animate-fade-in-up"
                    >
                      <PositionCard 
                        position={position} 
                        pricePrecision={PRICE_PRECISION[position.symbol] || 2}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Historical Positions Section */}
          <div className="animate-fade-in-up">
            <HistoricalPositions 
              positions={state.historicalPositions} 
              loading={loading.historicalPositions} 
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;