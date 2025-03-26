import React from 'react';
import { TradingConditions } from '../types';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

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

interface TradingConditionsCardProps {
  conditions: TradingConditions;
  isDarkMode: boolean;
}

export function TradingConditionsCard({ conditions, isDarkMode }: TradingConditionsCardProps) {
  return (
    <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-md p-6 mb-4 transition-colors duration-200`}>
      <div className="flex items-center justify-between mb-4">
        <span className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          {conditions.symbol}
        </span>
        <div className="flex items-center space-x-2">
          <Clock className={`w-5 h-5 ${conditions.fundingPeriod ? 'text-green-500' : 'text-red-500'}`} />
          <span className={`text-sm ${conditions.fundingPeriod ? 'text-green-500' : 'text-red-500'}`}>
            Funding Period
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-3">
          <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-900'}`}>
            Buy Conditions
          </h3>
          <Condition label="MACD Histogram Breakout" value={conditions.buyConditions.condA} isDarkMode={isDarkMode} />
          <Condition label="Fibonacci Retracement Confirmation" value={conditions.buyConditions.condB} isDarkMode={isDarkMode} />
          <Condition label="MACD Signal Line Crossover" value={conditions.buyConditions.condC} isDarkMode={isDarkMode} />
        </div>
        
        <div className="space-y-3">
          <h3 className={`font-semibold mb-2 ${isDarkMode ? 'text-gray-300' : 'text-gray-900'}`}>
            Sell Conditions
          </h3>
          <Condition label="MACD Histogram Breakout" value={conditions.sellConditions.condA} isDarkMode={isDarkMode} />
          <Condition label="Fibonacci Retracement Confirmation" value={conditions.sellConditions.condB} isDarkMode={isDarkMode} />
          <Condition label="MACD Signal Line Crossover" value={conditions.sellConditions.condC} isDarkMode={isDarkMode} />
        </div>
      </div>
    </div>
  );
}