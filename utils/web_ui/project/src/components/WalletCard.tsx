import React from 'react';
import { WalletInfo } from '../types';
import { Wallet, TrendingUp, TrendingDown, Percent } from 'lucide-react';

interface WalletCardProps {
  wallet: WalletInfo;
  isDarkMode: boolean;
}

export function WalletCard({ wallet, isDarkMode }: WalletCardProps) {
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
    <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-md p-6 mb-4 transition-colors duration-200`}>
      <div className="flex items-center mb-4">
        <Wallet className={`w-6 h-6 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'} mr-2`} />
        <h2 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          Wallet Overview
        </h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="space-y-1">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Total Balance
          </span>
          <p className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {formatCurrency(wallet.totalBalance)}
          </p>
        </div>

        <div className="space-y-1">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Available Balance
          </span>
          <p className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {formatCurrency(wallet.availableBalance)}
          </p>
        </div>

        <div className="space-y-1">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Unrealized P&L
          </span>
            <p className={`text-lg font-semibold ${
            parseFloat(wallet.unrealizedPnL) > 0 
            ? 'text-green-500' 
            : parseFloat(wallet.unrealizedPnL) < 0 
            ? 'text-red-500' 
            : 'text-white'
            }`}>
            {formatCurrency(wallet.unrealizedPnL)}
          </p>
        </div>

        <div className="space-y-1">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Daily P&L
          </span>
          <div className="flex items-center">
            {parseFloat(wallet.dailyPnL) >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <p className={`text-lg font-semibold ${parseFloat(wallet.dailyPnL) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {formatCurrency(wallet.dailyPnL)}
            </p>
          </div>
        </div>

        <div className="space-y-1">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Weekly P&L
          </span>
          <div className="flex items-center">
            {parseFloat(wallet.weeklyPnL) >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500 mr-1" />
            )}
            <p className={`text-lg font-semibold ${
              parseFloat(wallet.weeklyPnL) > 0 
              ? 'text-green-500' 
              : parseFloat(wallet.weeklyPnL) < 0 
              ? 'text-red-500' 
              : 'text-white'
            }`}>
              {formatCurrency(wallet.weeklyPnL)}
            </p>
          </div>
        </div>

        <div className="space-y-1">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Margin Ratio
          </span>
          <div className="flex items-center">
            <Percent className="w-4 h-4 text-gray-400 mr-1" />
            <p className={`text-lg font-semibold ${parseFloat(wallet.marginRatio) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {parseFloat(wallet.marginRatio).toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}