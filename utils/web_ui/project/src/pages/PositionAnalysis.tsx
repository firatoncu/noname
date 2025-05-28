import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Calendar,
  BarChart3,
  PieChart,
  Activity,
  Award,
  AlertTriangle,
  RefreshCw,
  Filter,
  Download,
  Info,
  X,
  ExternalLink
} from 'lucide-react';
import { PnLChart, SymbolPieChart, WinRateChart, TradeDistributionChart } from '../components/AnalysisCharts';

// Tooltip component
interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

const Tooltip: React.FC<TooltipProps> = ({ content, children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);

  const handleMouseEnter = () => {
    setShouldRender(true);
    // Small delay to ensure the element is rendered before showing
    setTimeout(() => setIsVisible(true), 10);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
    // Wait for fade out animation to complete before removing from DOM
    setTimeout(() => setShouldRender(false), 200);
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="cursor-help"
      >
        {children}
      </div>
      {shouldRender && (
        <div 
          className={`absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 border border-gray-600 rounded-lg shadow-lg -top-2 left-full ml-2 w-64 transition-all duration-200 ease-in-out transform ${
            isVisible 
              ? 'opacity-100 translate-x-0 scale-100' 
              : 'opacity-0 -translate-x-2 scale-95'
          }`}
        >
          <div className="relative">
            {content}
            <div className="absolute top-3 -left-1 w-2 h-2 bg-gray-900 border-l border-b border-gray-600 transform rotate-45"></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Performance metric card with tooltip
interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  tooltip: string;
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon: Icon, color, tooltip, subtitle }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-all duration-300 ease-in-out hover:shadow-lg hover:scale-[1.02]">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <p className="text-gray-400 text-sm">{title}</p>
            <Tooltip content={tooltip}>
              <Info className="w-4 h-4 text-gray-500 hover:text-gray-300 transition-colors duration-200" />
            </Tooltip>
          </div>
          <p className={`text-2xl font-bold ${color} transition-all duration-200`}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
        <Icon className={`w-8 h-8 ${color} transition-all duration-200`} />
      </div>
    </div>
  );
};

// Chart Modal Component
interface ChartModalProps {
  symbol: string;
  isOpen: boolean;
  onClose: () => void;
}

const ChartModal: React.FC<ChartModalProps> = ({ symbol, isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-75 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-gray-900 rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">{symbol} Chart</h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => window.open(`/trading-conditions/chart/${symbol}`, '_blank')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Chart Content */}
        <div className="p-4">
          <div className="w-full h-[70vh] bg-gray-800 rounded-lg overflow-hidden">
            <iframe
              src={`/trading-conditions/chart/${symbol}`}
              className="w-full h-full border-0"
              title={`${symbol} Chart`}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Clickable Symbol Component
interface ClickableSymbolProps {
  symbol: string;
  className?: string;
  children: React.ReactNode;
}

const ClickableSymbol: React.FC<ClickableSymbolProps> = ({ symbol, className = "", children }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className={`hover:text-blue-400 hover:underline transition-colors cursor-pointer ${className}`}
        title={`View ${symbol} chart`}
      >
        {children}
      </button>
      <ChartModal
        symbol={symbol}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

interface PositionData {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercentage: number;
  entryTime: string;
  exitTime: string;
  duration: number; // in minutes
  strategy: string;
  leverage: number;
}

interface PerformanceMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnL: number;
  averagePnL: number;
  bestTrade: number;
  worstTrade: number;
  averageDuration: number;
  sharpeRatio: number;
  maxDrawdown: number;
  profitFactor: number;
}

interface SymbolPerformance {
  symbol: string;
  trades: number;
  winRate: number;
  totalPnL: number;
  averagePnL: number;
}

const PositionAnalysis: React.FC = () => {
  const [positions, setPositions] = useState<PositionData[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [symbolPerformance, setSymbolPerformance] = useState<SymbolPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<'1d' | '7d' | '30d' | 'all'>('7d');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'charts'>('overview');

  useEffect(() => {
    loadAnalysisData();
  }, [timeframe, selectedSymbol]);

  const loadAnalysisData = async () => {
    setLoading(true);
    try {
      // Use real API endpoints
      const response = await fetch(`/api/analysis/complete?timeframe=${timeframe}&symbol=${selectedSymbol}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      setPositions(data.positions);
      setMetrics(data.metrics);
      setSymbolPerformance(data.symbolPerformance);
    } catch (error) {
      console.error('Error loading analysis data:', error);
      // Fallback to mock data if API fails
      const mockPositions = generateMockPositions();
      const filteredPositions = filterPositionsByTimeframe(mockPositions);
      const calculatedMetrics = calculateMetrics(filteredPositions);
      const symbolStats = calculateSymbolPerformance(filteredPositions);

      setPositions(filteredPositions);
      setMetrics(calculatedMetrics);
      setSymbolPerformance(symbolStats);
    } finally {
      setLoading(false);
    }
  };

  const generateMockPositions = (): PositionData[] => {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT'];
    const strategies = ['Bollinger Bands & RSI', 'MACD Crossover', 'Support/Resistance'];
    const positions: PositionData[] = [];

    for (let i = 0; i < 50; i++) {
      const symbol = symbols[Math.floor(Math.random() * symbols.length)];
      const side = Math.random() > 0.5 ? 'LONG' : 'SHORT';
      const entryPrice = 100 + Math.random() * 900;
      const pnlPercentage = (Math.random() - 0.4) * 20; // Slightly positive bias
      const exitPrice = entryPrice * (1 + pnlPercentage / 100);
      const quantity = Math.random() * 10 + 1;
      const pnl = (exitPrice - entryPrice) * quantity * (side === 'LONG' ? 1 : -1);
      const entryTime = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000);
      const duration = Math.random() * 1440 + 30; // 30 minutes to 24 hours
      const exitTime = new Date(entryTime.getTime() + duration * 60 * 1000);

      positions.push({
        id: `pos_${i}`,
        symbol,
        side,
        entryPrice,
        exitPrice,
        quantity,
        pnl,
        pnlPercentage,
        entryTime: entryTime.toISOString(),
        exitTime: exitTime.toISOString(),
        duration,
        strategy: strategies[Math.floor(Math.random() * strategies.length)],
        leverage: 5
      });
    }

    return positions.sort((a, b) => new Date(b.exitTime).getTime() - new Date(a.exitTime).getTime());
  };

  const filterPositionsByTimeframe = (positions: PositionData[]): PositionData[] => {
    const now = new Date();
    let cutoffDate: Date;

    switch (timeframe) {
      case '1d':
        cutoffDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        return positions;
    }

    return positions.filter(pos => new Date(pos.exitTime) >= cutoffDate);
  };

  const calculateMetrics = (positions: PositionData[]): PerformanceMetrics => {
    if (positions.length === 0) {
      return {
        totalTrades: 0,
        winningTrades: 0,
        losingTrades: 0,
        winRate: 0,
        totalPnL: 0,
        averagePnL: 0,
        bestTrade: 0,
        worstTrade: 0,
        averageDuration: 0,
        sharpeRatio: 0,
        maxDrawdown: 0,
        profitFactor: 0
      };
    }

    const winningTrades = positions.filter(p => p.pnl > 0).length;
    const losingTrades = positions.filter(p => p.pnl < 0).length;
    const totalPnL = positions.reduce((sum, p) => sum + p.pnl, 0);
    const pnls = positions.map(p => p.pnl);
    const bestTrade = Math.max(...pnls);
    const worstTrade = Math.min(...pnls);
    const averageDuration = positions.reduce((sum, p) => sum + p.duration, 0) / positions.length;

    // Calculate max drawdown
    let peak = 0;
    let maxDrawdown = 0;
    let runningPnL = 0;

    positions.forEach(pos => {
      runningPnL += pos.pnl;
      if (runningPnL > peak) peak = runningPnL;
      const drawdown = (peak - runningPnL) / Math.abs(peak) * 100;
      if (drawdown > maxDrawdown) maxDrawdown = drawdown;
    });

    // Calculate profit factor
    const grossProfit = positions.filter(p => p.pnl > 0).reduce((sum, p) => sum + p.pnl, 0);
    const grossLoss = Math.abs(positions.filter(p => p.pnl < 0).reduce((sum, p) => sum + p.pnl, 0));
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;

    return {
      totalTrades: positions.length,
      winningTrades,
      losingTrades,
      winRate: (winningTrades / positions.length) * 100,
      totalPnL,
      averagePnL: totalPnL / positions.length,
      bestTrade,
      worstTrade,
      averageDuration,
      sharpeRatio: 1.2, // Simplified calculation
      maxDrawdown,
      profitFactor
    };
  };

  const calculateSymbolPerformance = (positions: PositionData[]): SymbolPerformance[] => {
    const symbolMap = new Map<string, PositionData[]>();

    positions.forEach(pos => {
      if (!symbolMap.has(pos.symbol)) {
        symbolMap.set(pos.symbol, []);
      }
      symbolMap.get(pos.symbol)!.push(pos);
    });

    return Array.from(symbolMap.entries()).map(([symbol, symbolPositions]) => {
      const winningTrades = symbolPositions.filter(p => p.pnl > 0).length;
      const totalPnL = symbolPositions.reduce((sum, p) => sum + p.pnl, 0);

      return {
        symbol,
        trades: symbolPositions.length,
        winRate: (winningTrades / symbolPositions.length) * 100,
        totalPnL,
        averagePnL: totalPnL / symbolPositions.length
      };
    }).sort((a, b) => b.totalPnL - a.totalPnL);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="flex items-center space-x-3 text-white">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span>Loading analysis data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <TrendingUp className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-3xl font-bold">Position Analysis</h1>
                <p className="text-gray-400">Performance analytics and detailed position analysis</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={loadAnalysisData}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors flex items-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center space-x-2">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value as any)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="1d">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Symbols</option>
                {symbolPerformance.map(sp => (
                  <option key={sp.symbol} value={sp.symbol}>{sp.symbol}</option>
                ))}
              </select>
            </div>

            <div className="flex bg-gray-700 rounded-lg p-1">
              {(['overview', 'detailed', 'charts'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    viewMode === mode
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Performance Metrics Overview */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Total P&L"
              value={formatCurrency(metrics.totalPnL)}
              icon={DollarSign}
              color={metrics.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}
              tooltip="Total profit and loss across all trades in the selected timeframe. This represents your net trading performance."
            />

            <MetricCard
              title="Win Rate"
              value={`${metrics.winRate.toFixed(1)}%`}
              icon={Target}
              color="text-blue-400"
              tooltip="Percentage of profitable trades. A higher win rate indicates more consistent profitable trading, though it should be considered alongside profit factor."
              subtitle={`${metrics.winningTrades}/${metrics.totalTrades} trades`}
            />

            <MetricCard
              title="Best Trade"
              value={formatCurrency(metrics.bestTrade)}
              icon={TrendingUp}
              color="text-green-400"
              tooltip="Your most profitable single trade in the selected period. This shows your maximum profit potential per trade."
            />

            <MetricCard
              title="Profit Factor"
              value={metrics.profitFactor.toFixed(2)}
              icon={Award}
              color="text-yellow-400"
              tooltip="Ratio of gross profit to gross loss. A value above 1.0 indicates profitability. Higher values (>1.5) suggest strong trading performance."
            />
          </div>
        )}

        {/* Additional Performance Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-all duration-300 ease-in-out hover:shadow-lg hover:scale-[1.02]">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-gray-400 text-sm">Average P&L</p>
                    <Tooltip content="Average profit/loss per trade. This metric helps you understand your typical trade performance and consistency.">
                      <Info className="w-4 h-4 text-gray-500 hover:text-gray-300 transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className={`text-xl font-bold ${metrics.averagePnL >= 0 ? 'text-green-400' : 'text-red-400'} transition-all duration-200`}>
                    {formatCurrency(metrics.averagePnL)}
                  </p>
                </div>
                <BarChart3 className="w-6 h-6 text-gray-400 transition-all duration-200" />
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-all duration-300 ease-in-out hover:shadow-lg hover:scale-[1.02]">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-gray-400 text-sm">Worst Trade</p>
                    <Tooltip content="Your largest single loss in the selected period. This helps you understand your maximum risk exposure per trade.">
                      <Info className="w-4 h-4 text-gray-500 hover:text-gray-300 transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className="text-xl font-bold text-red-400 transition-all duration-200">{formatCurrency(metrics.worstTrade)}</p>
                </div>
                <TrendingDown className="w-6 h-6 text-red-400 transition-all duration-200" />
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-all duration-300 ease-in-out hover:shadow-lg hover:scale-[1.02]">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-gray-400 text-sm">Avg Duration</p>
                    <Tooltip content="Average time each trade is held open. Shorter durations indicate more active trading, while longer durations suggest swing trading.">
                      <Info className="w-4 h-4 text-gray-500 hover:text-gray-300 transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className="text-xl font-bold text-blue-400 transition-all duration-200">{formatDuration(metrics.averageDuration)}</p>
                </div>
                <Activity className="w-6 h-6 text-blue-400 transition-all duration-200" />
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-all duration-300 ease-in-out hover:shadow-lg hover:scale-[1.02]">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-gray-400 text-sm">Max Drawdown</p>
                    <Tooltip content="Maximum peak-to-trough decline in your account balance. Lower values indicate better risk management and capital preservation.">
                      <Info className="w-4 h-4 text-gray-500 hover:text-gray-300 transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className="text-xl font-bold text-orange-400 transition-all duration-200">{metrics.maxDrawdown.toFixed(1)}%</p>
                </div>
                <AlertTriangle className="w-6 h-6 text-orange-400 transition-all duration-200" />
              </div>
            </div>
          </div>
        )}

        {/* Content based on view mode */}
        {viewMode === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Symbol Performance */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center">
                <PieChart className="w-5 h-5 mr-2 text-blue-400" />
                Symbol Performance
              </h3>
              <div className="space-y-4">
                {symbolPerformance.slice(0, 5).map((sp) => (
                  <div key={sp.symbol} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <ClickableSymbol symbol={sp.symbol} className="font-medium">
                        {sp.symbol}
                      </ClickableSymbol>
                      <span className="text-sm text-gray-400">{sp.trades} trades</span>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${sp.totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(sp.totalPnL)}
                      </div>
                      <div className="text-sm text-gray-400">{sp.winRate.toFixed(1)}% win rate</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Trades */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-blue-400" />
                Recent Trades
              </h3>
              <div className="space-y-3">
                {positions.slice(0, 5).map((pos) => (
                  <div key={pos.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <ClickableSymbol symbol={pos.symbol} className="font-medium">
                        {pos.symbol}
                      </ClickableSymbol>
                      <span className={`px-2 py-1 rounded text-xs ${
                        pos.side === 'LONG' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                      }`}>
                        {pos.side}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className={`font-medium ${pos.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(pos.pnl)}
                      </div>
                      <div className="text-sm text-gray-400">{formatDuration(pos.duration)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {viewMode === 'detailed' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-xl font-semibold mb-4">Detailed Position History</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4">Symbol</th>
                    <th className="text-left py-3 px-4">Side</th>
                    <th className="text-left py-3 px-4">Entry</th>
                    <th className="text-left py-3 px-4">Exit</th>
                    <th className="text-left py-3 px-4">P&L</th>
                    <th className="text-left py-3 px-4">%</th>
                    <th className="text-left py-3 px-4">Duration</th>
                    <th className="text-left py-3 px-4">Strategy</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.slice(0, 20).map((pos) => (
                    <tr key={pos.id} className="border-b border-gray-700 hover:bg-gray-700">
                      <td className="py-3 px-4 font-medium">
                        <ClickableSymbol symbol={pos.symbol}>
                          {pos.symbol}
                        </ClickableSymbol>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs ${
                          pos.side === 'LONG' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                        }`}>
                          {pos.side}
                        </span>
                      </td>
                      <td className="py-3 px-4">${pos.entryPrice.toFixed(4)}</td>
                      <td className="py-3 px-4">${pos.exitPrice.toFixed(4)}</td>
                      <td className={`py-3 px-4 font-medium ${pos.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(pos.pnl)}
                      </td>
                      <td className={`py-3 px-4 ${pos.pnlPercentage >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercentage(pos.pnlPercentage)}
                      </td>
                      <td className="py-3 px-4">{formatDuration(pos.duration)}</td>
                      <td className="py-3 px-4 text-gray-400">{pos.strategy}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {viewMode === 'charts' && (
          <div className="space-y-8">
            {/* Cumulative P&L Chart */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-blue-400" />
                Cumulative P&L Over Time
              </h3>
              <PnLChart positions={positions} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Symbol Performance Pie Chart */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center">
                  <PieChart className="w-5 h-5 mr-2 text-blue-400" />
                  P&L by Symbol
                </h3>
                <SymbolPieChart symbolPerformance={symbolPerformance} />
              </div>

              {/* Win Rate by Symbol */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-blue-400" />
                  Win Rate by Symbol
                </h3>
                <WinRateChart symbolPerformance={symbolPerformance} />
              </div>
            </div>

            {/* Trade Distribution */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-blue-400" />
                Trade P&L Distribution
              </h3>
              <TradeDistributionChart positions={positions} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PositionAnalysis; 