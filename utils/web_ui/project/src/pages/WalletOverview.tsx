import React from 'react';
import { Wallet, DollarSign, TrendingUp, TrendingDown, Percent, Activity } from 'lucide-react';
import { useAppContext } from '../contexts/AppContext';
import { WalletCard } from '../components/WalletCard';
import { LoadingSpinner } from '../components/LoadingSpinner';

function WalletOverview() {
  const { state, actions } = useAppContext();
  const { wallet, loading } = state;

  // Default wallet data structure
  const defaultWallet = {
    totalBalance: '0',
    availableBalance: '0',
    unrealizedPnL: '0',
    dailyPnL: '0',
    marginRatio: '0',
  };

  const walletData = wallet || defaultWallet;
  const isLoading = loading.wallet;

  const formatCurrency = (value: string) => {
    const num = parseFloat(value);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-10 animate-fade-in-up">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div className="animate-slide-in-left">
              <div className="flex items-center mb-3">
                <Wallet className="w-8 h-8 text-dark-accent-success mr-3" />
                <h1 className="text-4xl font-bold text-dark-text-primary">
                  Wallet Overview
                </h1>
              </div>
              <p className="text-dark-text-muted text-lg">
                Comprehensive view of your trading account balance and performance
              </p>
            </div>
          </div>
        </div>

        {/* Quick Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group">
            <div className="flex items-center">
              <div className="p-3 bg-dark-accent-success/20 rounded-xl mr-4 group-hover:bg-dark-accent-success/30 transition-colors duration-300">
                <DollarSign className="w-8 h-8 text-dark-accent-success" />
              </div>
              <div>
                <p className="text-dark-text-muted text-sm font-medium">Total Balance</p>
                <p className="text-3xl font-bold text-dark-text-primary mt-1">
                  {isLoading ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    formatCurrency(walletData.totalBalance)
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group">
            <div className="flex items-center">
              <div className="p-3 bg-dark-accent-info/20 rounded-xl mr-4 group-hover:bg-dark-accent-info/30 transition-colors duration-300">
                <DollarSign className="w-8 h-8 text-dark-accent-info" />
              </div>
              <div>
                <p className="text-dark-text-muted text-sm font-medium">Available Balance</p>
                <p className="text-3xl font-bold text-dark-text-primary mt-1">
                  {isLoading ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    formatCurrency(walletData.availableBalance)
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group">
            <div className="flex items-center">
              <div className="p-3 bg-dark-accent-warning/20 rounded-xl mr-4 group-hover:bg-dark-accent-warning/30 transition-colors duration-300">
                {parseFloat(walletData.dailyPnL) >= 0 ? (
                  <TrendingUp className="w-8 h-8 text-dark-accent-success" />
                ) : (
                  <TrendingDown className="w-8 h-8 text-dark-accent-error" />
                )}
              </div>
              <div>
                <p className="text-dark-text-muted text-sm font-medium">Daily P&L</p>
                <p className={`text-3xl font-bold mt-1 ${
                  parseFloat(walletData.dailyPnL) >= 0 
                    ? 'text-dark-accent-success' 
                    : 'text-dark-accent-error'
                }`}>
                  {isLoading ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    `${parseFloat(walletData.dailyPnL) >= 0 ? '+' : ''}${formatCurrency(walletData.dailyPnL)}`
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up group">
            <div className="flex items-center">
              <div className="p-3 bg-dark-accent-primary/20 rounded-xl mr-4 group-hover:bg-dark-accent-primary/30 transition-colors duration-300">
                <Percent className="w-8 h-8 text-dark-accent-primary" />
              </div>
              <div>
                <p className="text-dark-text-muted text-sm font-medium">Margin Ratio</p>
                <p className={`text-3xl font-bold mt-1 ${
                  parseFloat(walletData.marginRatio) >= 0 
                    ? 'text-dark-accent-success' 
                    : 'text-dark-accent-error'
                }`}>
                  {isLoading ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    `${parseFloat(walletData.marginRatio).toFixed(2)}%`
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Wallet Card */}
        <div className="animate-fade-in-up">
          <WalletCard wallet={walletData} loading={isLoading} />
        </div>

        {/* Additional Wallet Information */}
        <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Performance Summary */}
          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-dark-accent-info/20 rounded-xl mr-4">
                <Activity className="w-6 h-6 text-dark-accent-info" />
              </div>
              <h3 className="text-2xl font-bold text-dark-text-primary">
                Performance Summary
              </h3>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-dark-bg-tertiary/50 rounded-xl border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
                <div className="flex items-center">
                  {parseFloat(walletData.unrealizedPnL) >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-dark-accent-success mr-3" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-dark-accent-error mr-3" />
                  )}
                  <span className="text-dark-text-muted font-medium">Unrealized P&L</span>
                </div>
                <span className={`text-xl font-bold ${
                  parseFloat(walletData.unrealizedPnL) >= 0 
                    ? 'text-dark-accent-success' 
                    : 'text-dark-accent-error'
                }`}>
                  {isLoading ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    `${parseFloat(walletData.unrealizedPnL) >= 0 ? '+' : ''}${formatCurrency(walletData.unrealizedPnL)}`
                  )}
                </span>
              </div>

              <div className="flex items-center justify-between p-4 bg-dark-bg-tertiary/50 rounded-xl border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
                <div className="flex items-center">
                  {parseFloat(walletData.weeklyPnL) >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-dark-accent-success mr-3" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-dark-accent-error mr-3" />
                  )}
                  <span className="text-dark-text-muted font-medium">Weekly P&L</span>
                </div>
                <span className={`text-xl font-bold ${
                  parseFloat(walletData.weeklyPnL) >= 0 
                    ? 'text-dark-accent-success' 
                    : 'text-dark-accent-error'
                }`}>
                  {isLoading ? (
                    <LoadingSpinner size="sm" variant="white" />
                  ) : (
                    formatCurrency(walletData.weeklyPnL)
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Account Health */}
          <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-dark-accent-warning/20 rounded-xl mr-4">
                <Activity className="w-6 h-6 text-dark-accent-warning" />
              </div>
              <h3 className="text-2xl font-bold text-dark-text-primary">
                Account Health
              </h3>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-dark-bg-tertiary/50 rounded-xl border border-dark-border-secondary">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-dark-text-muted font-medium">Margin Usage</span>
                  <span className="text-dark-text-primary font-bold">
                    {parseFloat(walletData.marginRatio).toFixed(2)}%
                  </span>
                </div>
                <div className="w-full bg-dark-border-secondary rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      parseFloat(walletData.marginRatio) > 80 
                        ? 'bg-dark-accent-error' 
                        : parseFloat(walletData.marginRatio) > 60 
                        ? 'bg-dark-accent-warning' 
                        : 'bg-dark-accent-success'
                    }`}
                    style={{ width: `${Math.min(parseFloat(walletData.marginRatio), 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="p-4 bg-dark-bg-tertiary/50 rounded-xl border border-dark-border-secondary">
                <div className="text-center">
                  <div className={`text-2xl font-bold mb-2 ${
                    parseFloat(walletData.marginRatio) > 80 
                      ? 'text-dark-accent-error' 
                      : parseFloat(walletData.marginRatio) > 60 
                      ? 'text-dark-accent-warning' 
                      : 'text-dark-accent-success'
                  }`}>
                    {parseFloat(walletData.marginRatio) > 80 
                      ? 'High Risk' 
                      : parseFloat(walletData.marginRatio) > 60 
                      ? 'Medium Risk' 
                      : 'Low Risk'
                    }
                  </div>
                  <p className="text-dark-text-muted text-sm">
                    {parseFloat(walletData.marginRatio) > 80 
                      ? 'Consider reducing position sizes' 
                      : parseFloat(walletData.marginRatio) > 60 
                      ? 'Monitor positions closely' 
                      : 'Account is in good health'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WalletOverview; 