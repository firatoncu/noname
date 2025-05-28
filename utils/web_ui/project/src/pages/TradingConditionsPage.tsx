import React, { useState, useEffect } from 'react';
import { TradingConditions } from '../types';
import { BarChart, ChevronLeft, CheckCircle, XCircle, Clock, LineChart, Activity, AlertCircle, TrendingUp, TrendingDown, Info } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createApiUrl, API_ENDPOINTS } from '../config/api';

// Tooltip component for smooth hover descriptions
interface TooltipProps {
  children: React.ReactNode;
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

function Tooltip({ children, content, position = 'top' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-3',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-3',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-3',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-3'
  };

  // Format content into multiple lines for better readability
  const formatContent = (text: string) => {
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';
    
    for (const word of words) {
      if (currentLine.length + word.length + 1 <= 35) { // ~35 chars per line
        currentLine += (currentLine ? ' ' : '') + word;
      } else {
        if (currentLine) lines.push(currentLine);
        currentLine = word;
      }
    }
    if (currentLine) lines.push(currentLine);
    
    return lines;
  };

  const contentLines = formatContent(content);

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      <div className={`
        absolute z-50 px-4 py-3 text-xs text-dark-text-primary bg-dark-bg-tertiary border border-dark-border-accent rounded-xl shadow-glass backdrop-blur-sm
        transition-all duration-300 ease-out pointer-events-none w-64
        ${positionClasses[position]}
        ${isVisible 
          ? 'opacity-100 scale-100 translate-y-0' 
          : 'opacity-0 scale-95 translate-y-2'
        }
      `}>
        <div className="space-y-1">
          {contentLines.map((line, index) => (
            <div key={index} className="leading-relaxed">
              {line}
            </div>
          ))}
        </div>
        {/* Arrow */}
        <div className={`
          absolute w-3 h-3 bg-dark-bg-tertiary border-dark-border-accent transform rotate-45
          ${position === 'top' ? 'top-full left-1/2 -translate-x-1/2 -mt-1.5 border-r border-b' : ''}
          ${position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 -mb-1.5 border-l border-t' : ''}
          ${position === 'left' ? 'left-full top-1/2 -translate-y-1/2 -ml-1.5 border-t border-r' : ''}
          ${position === 'right' ? 'right-full top-1/2 -translate-y-1/2 -mr-1.5 border-b border-l' : ''}
        `}></div>
      </div>
    </div>
  );
}

// Strategy descriptions - shortened and reformatted
const getStrategyDescription = (strategyName: string | undefined): string => {
  switch (strategyName) {
    case 'Bollinger Bands & RSI':
      return 'Combines volatility bands with momentum oscillator for trend reversal signals';
    case 'MACD & Fibonacci':
      return 'Uses moving average convergence with Fibonacci retracements for entry timing';
    default:
      return 'No active trading strategy configured';
  }
};

// Condition descriptions - shortened and reformatted
const getConditionDescription = (strategyName: string | undefined, conditionType: 'A' | 'B' | 'C'): string => {
  if (strategyName === 'Bollinger Bands & RSI') {
    switch (conditionType) {
      case 'A': return 'Price compression near Bollinger Band center indicates potential breakout';
      case 'B': return 'Price breaks above or below Bollinger Bands with volume confirmation';
      case 'C': return 'RSI shows oversold under 30 or overbought over 70 momentum conditions';
    }
  } else {
    switch (conditionType) {
      case 'A': return 'MACD line crosses above or below signal line indicating momentum shift';
      case 'B': return 'Price retraces to key Fibonacci levels 38.2%, 50%, 61.8% for entry';
      case 'C': return 'First wave pattern completion signals trend continuation opportunity';
    }
  }
  return 'Condition not configured';
};

interface ConditionProps {
  label: string;
  value: boolean;
  description: string;
}

function Condition({ label, value, description }: ConditionProps) {
  return (
    <Tooltip content={description} position="top">
      <div className="flex items-center space-x-3 p-3 rounded-xl bg-dark-bg-tertiary/30 border border-dark-border-secondary hover:border-dark-border-accent transition-all duration-300 group cursor-help">
        <div className={`p-1 rounded-full ${value ? 'bg-dark-accent-success/20' : 'bg-dark-accent-error/20'}`}>
          {value ? (
            <CheckCircle className="w-4 h-4 text-dark-accent-success" />
          ) : (
            <XCircle className="w-4 h-4 text-dark-accent-error" />
          )}
        </div>
        <span className="text-sm text-dark-text-secondary group-hover:text-dark-text-primary transition-colors duration-300 flex-1">
          {label}
        </span>
        <Info className="w-3 h-3 text-dark-text-muted opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>
    </Tooltip>
  );
}

interface TradingConditionCardProps {
  conditions: TradingConditions;
  index: number;
}

function TradingConditionCard({ conditions, index }: TradingConditionCardProps) {
  const allBuyConditions = conditions.buyConditions.condA && conditions.buyConditions.condB && conditions.buyConditions.condC;
  const allSellConditions = conditions.sellConditions.condA && conditions.sellConditions.condB && conditions.sellConditions.condC;
  const hasSignal = allBuyConditions || allSellConditions;

  return (
    <div 
      className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 overflow-hidden group animate-fade-in-up"
    >
      {/* Header Section */}
      <div className="bg-dark-bg-tertiary/50 px-6 py-4 border-b border-dark-border-secondary">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h3 className="text-2xl font-bold text-dark-text-primary">
              {conditions.symbol}
            </h3>
            {hasSignal && (
              <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                allBuyConditions 
                  ? 'bg-dark-accent-success/20 text-dark-accent-success border-dark-accent-success/30' 
                  : 'bg-dark-accent-error/20 text-dark-accent-error border-dark-accent-error/30'
              } animate-pulse-soft`}>
                {allBuyConditions ? 'BUY SIGNAL' : 'SELL SIGNAL'}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <Link 
              to={`/trading-conditions/chart/${conditions.symbol}`}
              className="flex items-center space-x-2 px-3 py-2 bg-dark-accent-primary hover:bg-dark-accent-secondary text-dark-text-primary rounded-xl transition-all duration-300 shadow-glow-sm hover:shadow-glow-md"
              title="View Chart"
            >
              <LineChart className="w-4 h-4" />
              <span className="text-sm">Chart</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Strategy Info */}
      <div className="px-6 py-4 border-b border-dark-border-secondary">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-dark-accent-info/20 rounded-lg">
              <BarChart className="w-5 h-5 text-dark-accent-info" />
            </div>
            <div>
              <p className="text-sm text-dark-text-muted">Strategy</p>
              <Tooltip content={getStrategyDescription(conditions.strategyName)} position="bottom">
                <p className="font-semibold text-dark-text-primary cursor-help hover:text-dark-accent-primary transition-colors duration-300 flex items-center space-x-1">
                  <span>{conditions.strategyName || 'No Strategy'}</span>
                  <Info className="w-3 h-3 text-dark-text-muted" />
                </p>
              </Tooltip>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Funding Period */}
            <Tooltip content={conditions.fundingPeriod ? "Optimal funding period for position entry" : "Wait for better funding conditions"} position="top">
              <div className="flex items-center space-x-2 cursor-help">
                <div className={`p-1 rounded-full ${conditions.fundingPeriod ? 'bg-dark-accent-success/20' : 'bg-dark-accent-warning/20'}`}>
                  {conditions.fundingPeriod ? (
                    <CheckCircle className="w-4 h-4 text-dark-accent-success" />
                  ) : (
                    <Clock className="w-4 h-4 text-dark-accent-warning" />
                  )}
                </div>
                <span className="text-xs text-dark-text-muted">
                  Funding Period
                </span>
              </div>
            </Tooltip>

            {/* Market Condition */}
            <Tooltip content={conditions.trendingCondition ? "High volatility market with strong trends" : "Low volatility sideways market movement"} position="top">
              <div className="flex items-center space-x-2 cursor-help">
                <div className={`p-1 rounded-full ${conditions.trendingCondition ? 'bg-dark-accent-primary/20' : 'bg-dark-text-muted/20'}`}>
                  {conditions.trendingCondition ? (
                    <TrendingUp className="w-4 h-4 text-dark-accent-primary" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-dark-text-muted" />
                  )}
                </div>
                <span className="text-xs text-dark-text-muted">
                  {conditions.trendingCondition ? 'Volatile' : 'Ranging'}
                </span>
              </div>
            </Tooltip>
          </div>
        </div>
      </div>

      {/* Conditions Grid */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Buy Conditions */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-3">
              <div className="p-2 bg-dark-accent-success/20 rounded-lg">
                <TrendingUp className="w-4 h-4 text-dark-accent-success" />
              </div>
              <h4 className="font-semibold text-dark-text-primary">Buy Conditions</h4>
              <div className={`ml-auto w-3 h-3 rounded-full ${
                allBuyConditions ? 'bg-dark-accent-success animate-pulse' : 'bg-dark-border-secondary'
              }`}></div>
            </div>
            <div className="space-y-3">
              <Condition 
                label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Bollinger Squeeze Check' : 'MACD Signal Crossover'} 
                value={conditions.buyConditions.condA}
                description={getConditionDescription(conditions.strategyName, 'A')}
              />
              <Condition 
                label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Price Breakout' : 'Hardened Fibonacci Retracement'} 
                value={conditions.buyConditions.condB}
                description={getConditionDescription(conditions.strategyName, 'B')}
              />
              <Condition 
                label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'RSI Momentum Check' : 'First Wave Signal'} 
                value={conditions.buyConditions.condC}
                description={getConditionDescription(conditions.strategyName, 'C')}
              />
            </div>
          </div>
          
          {/* Sell Conditions */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-3">
              <div className="p-2 bg-dark-accent-error/20 rounded-lg">
                <TrendingDown className="w-4 h-4 text-dark-accent-error" />
              </div>
              <h4 className="font-semibold text-dark-text-primary">Sell Conditions</h4>
              <div className={`ml-auto w-3 h-3 rounded-full ${
                allSellConditions ? 'bg-dark-accent-error animate-pulse' : 'bg-dark-border-secondary'
              }`}></div>
            </div>
            <div className="space-y-3">
              <Condition 
                label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Bollinger Squeeze Check' : 'MACD Signal Crossover'} 
                value={conditions.sellConditions.condA}
                description={getConditionDescription(conditions.strategyName, 'A')}
              />
              <Condition 
                label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'Price Breakout' : 'Hardened Fibonacci Retracement'} 
                value={conditions.sellConditions.condB}
                description={getConditionDescription(conditions.strategyName, 'B')}
              />
              <Condition 
                label={conditions.strategyName === 'Bollinger Bands & RSI' ? 'RSI Momentum Check' : 'First Wave Signal'} 
                value={conditions.sellConditions.condC}
                description={getConditionDescription(conditions.strategyName, 'C')}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TradingConditionsPage() {
  const [conditions, setConditions] = useState<TradingConditions[]>([]);
  const [apiError, setApiError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

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
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching trading conditions:', error);
      setApiError(true);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    const intervalId = setInterval(fetchData, 5000); // Reduced frequency for better performance
    
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      {/* Header */}
      <div className="bg-dark-bg-secondary/80 backdrop-blur-md shadow-glass border-b border-dark-border-primary">
        <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div className="animate-slide-in-left">
              <div className="flex items-center mb-3">
                <Activity className="w-8 h-8 text-dark-accent-primary mr-3" />
                <h1 className="text-4xl font-bold text-dark-text-primary">
                  Trading Conditions
                </h1>
              </div>
              <p className="text-dark-text-muted text-lg">
                Real-time trading signals and market conditions
              </p>
            </div>
            
            <div className="mt-6 sm:mt-0 flex items-center space-x-4 animate-slide-in-right">
              <Link 
                to="/" 
                className="flex items-center px-6 py-3 bg-dark-bg-hover hover:bg-dark-accent-info/20 text-dark-text-secondary hover:text-dark-accent-info border border-dark-border-secondary hover:border-dark-accent-info rounded-xl transition-all duration-300"
              >
                <ChevronLeft className="w-5 h-5 mr-2" />
                <span>Back to Dashboard</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {apiError && (
        <div className="w-full px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-dark-accent-error/10 backdrop-blur-sm border border-dark-accent-error/30 rounded-2xl p-6 shadow-glass animate-fade-in">
            <div className="flex items-center">
              <AlertCircle className="w-6 h-6 text-dark-accent-error mr-3" />
              <h3 className="text-dark-accent-error font-semibold text-lg">
                API Connection Error
              </h3>
              <button
                onClick={fetchData}
                className="ml-auto text-dark-accent-error hover:text-dark-text-primary text-sm px-3 py-1 rounded-lg hover:bg-dark-accent-error/20 transition-all duration-300"
              >
                Retry
              </button>
            </div>
            <p className="text-dark-text-secondary text-sm mt-2">
              Unable to fetch trading conditions. Please check your connection and try again.
            </p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {conditions.length > 0 ? (
            conditions.map((condition, index) => (
              <TradingConditionCard 
                key={condition.symbol}
                conditions={condition}
                index={index}
              />
            ))
          ) : !isLoading ? (
            <div className="col-span-full bg-dark-bg-secondary/50 backdrop-blur-sm rounded-2xl p-12 border border-dark-border-primary text-center animate-fade-in">
              <BarChart className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-dark-text-primary mb-2">
                No Trading Conditions Available
              </h3>
              <p className="text-dark-text-muted">
                Trading conditions will appear here when data is available.
              </p>
            </div>
          ) : (
            // Loading skeleton
            <div className="col-span-full grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-dark-bg-secondary/50 rounded-2xl p-6 border border-dark-border-primary animate-pulse">
                  <div className="h-6 bg-dark-bg-tertiary rounded mb-4"></div>
                  <div className="space-y-3">
                    <div className="h-4 bg-dark-bg-tertiary rounded w-3/4"></div>
                    <div className="h-4 bg-dark-bg-tertiary rounded w-1/2"></div>
                    <div className="h-4 bg-dark-bg-tertiary rounded w-2/3"></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default TradingConditionsPage; 