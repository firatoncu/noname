import React from 'react';
import { WalletInfo } from '../types';
import { Wallet, TrendingUp, TrendingDown, Percent, DollarSign } from 'lucide-react';
import { LoadingSpinner } from './LoadingSpinner';

interface WalletCardProps {
  wallet: WalletInfo;
  loading?: boolean;
}

export function WalletCard({ wallet, loading = false }: WalletCardProps) {
  const formatCurrency = (value: string) => {
    const num = parseFloat(value);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num);
  };

  if (loading) {
    return (
      <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass">
        <div className="flex items-center mb-6">
          <div className="p-3 bg-dark-accent-success/20 rounded-xl mr-4">
            <Wallet className="w-6 h-6 text-dark-accent-success" />
          </div>
          <h2 className="text-2xl font-bold text-dark-text-primary">
            Wallet Overview
          </h2>
        </div>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="lg" variant="white" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 group">
      <div className="flex items-center mb-6">
        <div className="p-3 bg-dark-accent-success/20 rounded-xl mr-4 group-hover:bg-dark-accent-success/30 transition-colors duration-300">
          <Wallet className="w-6 h-6 text-dark-accent-success" />
        </div>
        <h2 className="text-2xl font-bold text-dark-text-primary">
          Wallet Overview
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
          <div className="flex items-center mb-2">
            <DollarSign className="w-4 h-4 text-dark-accent-primary mr-2" />
            <span className="text-sm text-dark-text-muted font-medium">
              Total Balance
            </span>
          </div>
          <p className="text-2xl font-bold text-dark-text-primary">
            {formatCurrency(wallet.totalBalance)}
          </p>
        </div>

        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
          <div className="flex items-center mb-2">
            <DollarSign className="w-4 h-4 text-dark-accent-info mr-2" />
            <span className="text-sm text-dark-text-muted font-medium">
              Available Balance
            </span>
          </div>
          <p className="text-2xl font-bold text-dark-text-primary">
            {formatCurrency(wallet.availableBalance)}
          </p>
        </div>

        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
          <div className="flex items-center mb-2">
            <TrendingUp className="w-4 h-4 text-dark-accent-warning mr-2" />
            <span className="text-sm text-dark-text-muted font-medium">
              Unrealized P&L
            </span>
          </div>
          <p className={`text-2xl font-bold ${
            parseFloat(wallet.unrealizedPnL) > 0 
              ? 'text-dark-accent-success' 
              : parseFloat(wallet.unrealizedPnL) < 0 
              ? 'text-dark-accent-error' 
              : 'text-dark-text-primary'
          }`}>
            {formatCurrency(wallet.unrealizedPnL)}
          </p>
        </div>

        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
          <div className="flex items-center mb-2">
            {parseFloat(wallet.dailyPnL) >= 0 ? (
              <TrendingUp className="w-4 h-4 text-dark-accent-success mr-2" />
            ) : (
              <TrendingDown className="w-4 h-4 text-dark-accent-error mr-2" />
            )}
            <span className="text-sm text-dark-text-muted font-medium">
              Daily P&L
            </span>
          </div>
          <p className={`text-2xl font-bold ${parseFloat(wallet.dailyPnL) >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
            {formatCurrency(wallet.dailyPnL)}
          </p>
        </div>

        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
          <div className="flex items-center mb-2">
            {parseFloat(wallet.weeklyPnL) >= 0 ? (
              <TrendingUp className="w-4 h-4 text-dark-accent-success mr-2" />
            ) : (
              <TrendingDown className="w-4 h-4 text-dark-accent-error mr-2" />
            )}
            <span className="text-sm text-dark-text-muted font-medium">
              Weekly P&L
            </span>
          </div>
          <p className={`text-2xl font-bold ${
            parseFloat(wallet.weeklyPnL) > 0 
              ? 'text-dark-accent-success' 
              : parseFloat(wallet.weeklyPnL) < 0 
              ? 'text-dark-accent-error' 
              : 'text-dark-text-primary'
          }`}>
            {formatCurrency(wallet.weeklyPnL)}
          </p>
        </div>

        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
          <div className="flex items-center mb-2">
            <Percent className="w-4 h-4 text-dark-text-muted mr-2" />
            <span className="text-sm text-dark-text-muted font-medium">
              Margin Ratio
            </span>
          </div>
          <p className={`text-2xl font-bold ${parseFloat(wallet.marginRatio) >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
            {parseFloat(wallet.marginRatio).toFixed(2)}%
          </p>
        </div>
      </div>
    </div>
  );
}