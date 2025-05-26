import React, { useState, useEffect } from 'react';
import { TradingConditions } from '../types';
import { LayoutDashboard, Moon, Sun, ChevronLeft, CheckCircle, XCircle, Clock, BarChart, LineChart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createApiUrl, API_ENDPOINTS } from '../config/api';

interface ConditionProps {
  label: string;
  value: boolean;
  isDarkMode: boolean;
}

function Condition({ label, value, isDarkMode }: ConditionProps) {
  return (
    <div className="flex items-center space-x-2">
      {value ? (
        <CheckCircle className="w-5 h-5 text-green-500" />
      ) : (
        <XCircle className="w-5 h-5 text-red-500" />
      )}
      <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-900'}`}>{label}</span>
    </div>
  );
}

interface TradingConditionCardProps {
  conditions: TradingConditions;
  isDarkMode: boolean;
}

function TradingConditionCard({ conditions, isDarkMode }: TradingConditionCardProps) {
  return (
    <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-md p-6 transition-colors duration-200`}>
      <div className="flex items-center justify-between mb-4">
        <span className={`text-xl font-bold ${isDarkMode ? 'text-gray-300' : 'text-gray-900'}`}>
          {conditions.symbol}
        </span>
        <div className="flex items-center space-x-2">
          {conditions.fundingPeriod ? (
            <CheckCircle className="w-5 h-5 text-green-500" />
          ) : (
            <Clock className="w-5 h-5 text-red-500" />
          )}
          <span className={`text-sm ${conditions.fundingPeriod ? 'text-gray-300' : 'text-gray-300'}`}>
            Funding Period
          </span>
          <span className="text-gray-400">|</span>
          <BarChart className={`w-5 h-5 ${conditions.trendingCondition ? 'text-green-500' : 'text-gray-400'}`} />
          <span className={`text-sm ${conditions.trendingCondition ? 'text-gray-300' : 'text-gray-300'}`}>
            {conditions.trendingCondition ? 'Volatile Market' : 'Ranging Market'}
          </span>
          <Link 
            to={`/trading-conditions/chart/${conditions.symbol}`}
            className={`ml-2 p-2 rounded-full hover:bg-opacity-20 
              ${isDarkMode 
                ? 'hover:bg-gray-600 text-gray-300' 
                : 'hover:bg-gray-200 text-gray-600'}`}
            aria-label="View Chart"
          >
            <LineChart className="w-5 h-5" />
          </Link>
        </div>
      </div>

      <div className="text-gray-400 mb-3">
        <span className="text-sm font-medium">
          {conditions.strategyName ? conditions.strategyName : 'No Strategy'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-3">
          <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-900'}`}>
            Buy Conditions
          </h3>
          <Condition 
            label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Bollinger Squeeze Check' : 'MACD Signal Crossover'} 
            value={conditions.buyConditions.condA} 
            isDarkMode={isDarkMode} 
          />
          <Condition 
            label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Price Breakout' : 'Hardened Fibonacci Retracement'} 
            value={conditions.buyConditions.condB} 
            isDarkMode={isDarkMode} 
          />
          <Condition 
            label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'RSI Momentum Check' : 'First Wave Signal'} 
            value={conditions.buyConditions.condC} 
            isDarkMode={isDarkMode} 
          />
        </div>
        
        <div className="space-y-3">
          <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-900'}`}>
            Sell Conditions
          </h3>
          <Condition 
            label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Bollinger Squeeze Check' : 'MACD Signal Crossover'} 
            value={conditions.sellConditions.condA} 
            isDarkMode={isDarkMode} 
          />
          <Condition 
            label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Price Breakout' : 'Hardened Fibonacci Retracement'} 
            value={conditions.sellConditions.condB} 
            isDarkMode={isDarkMode} 
          />
          <Condition 
            label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'RSI Momentum Check' : 'First Wave Signal'} 
            value={conditions.sellConditions.condC} 
            isDarkMode={isDarkMode} 
          />
        </div>
      </div>
    </div>
  );
}

function TradingConditionsPage() {
  const [conditions, setConditions] = useState<TradingConditions[]>([]);
  const [apiError, setApiError] = useState(false);
  const isDarkMode = true;

  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  const fetchData = async () => {
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.TRADING_CONDITIONS));
      
      if (!response.ok) {
        throw new Error('API response not ok');
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setConditions(data);
      }
      
      setApiError(false);
    } catch (error) {
      console.error('Error fetching trading conditions:', error);
      setApiError(true);
    }
  };

  useEffect(() => {
    fetchData();
    
    const intervalId = setInterval(fetchData, 1000);
    
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 transition-colors duration-200">
      <nav className="bg-gray-800 shadow-sm transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <LayoutDashboard className="w-6 h-6 text-blue-400 mr-2" />
              <span className="text-xl font-semibold text-white">
                Trading Conditions
              </span>
            </div>
            <div className="flex items-center space-x-6">
              {apiError && (
                <span className="text-red-500 text-sm">
                  API Connection Error
                </span>
              )}
              <Link 
                to="/" 
                className="px-4 py-2 rounded-md flex items-center bg-gray-700 hover:bg-gray-600 text-gray-200"
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                <span>Back to Dashboard</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {conditions.length > 0 ? (
            conditions.map((condition) => (
              <TradingConditionCard 
                key={condition.symbol}
                conditions={condition}
                isDarkMode={isDarkMode}
              />
            ))
          ) : (
            <div className={`col-span-full ${isDarkMode ? 'bg-gray-800 text-gray-400' : 'bg-white text-gray-500'} 
              rounded-lg shadow-md p-6 text-center transition-colors duration-200`}>
              No Trading Conditions Available
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default TradingConditionsPage; 