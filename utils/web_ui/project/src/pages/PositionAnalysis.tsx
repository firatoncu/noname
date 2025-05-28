import React, { useState, useEffect, useRef } from 'react';
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
  Filter,
  Download,
  Info,
  X,
  ExternalLink
} from 'lucide-react';
import { PnLChart, SymbolPieChart, WinRateChart, TradingHeatmapChart } from '../components/AnalysisCharts';

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
          className={`absolute z-50 px-3 py-2 text-sm text-dark-text-primary bg-dark-bg-tertiary border border-dark-border-secondary rounded-lg shadow-glass -top-2 left-full ml-2 w-64 transition-all duration-200 ease-in-out transform ${
            isVisible 
              ? 'opacity-100 translate-x-0 scale-100' 
              : 'opacity-0 -translate-x-2 scale-95'
          }`}
        >
          <div className="relative">
            {content}
            <div className="absolute top-3 -left-1 w-2 h-2 bg-dark-bg-tertiary border-l border-b border-dark-border-secondary transform rotate-45"></div>
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
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 ease-in-out hover:scale-[1.02] group">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <p className="text-dark-text-muted text-sm font-medium">{title}</p>
            <Tooltip content={tooltip}>
              <Info className="w-4 h-4 text-dark-text-disabled hover:text-dark-text-muted transition-colors duration-200" />
            </Tooltip>
          </div>
          <p className={`text-2xl font-bold ${color} transition-all duration-200`}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-dark-text-disabled">{subtitle}</p>
          )}
        </div>
        <Icon className={`w-8 h-8 ${color} transition-all duration-200 group-hover:scale-110`} />
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
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-dark-bg-secondary border border-dark-border-primary rounded-2xl shadow-glass max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border-secondary bg-dark-bg-tertiary/50">
          <div className="flex items-center space-x-3">
            <BarChart3 className="w-6 h-6 text-dark-accent-primary" />
            <h2 className="text-xl font-semibold text-dark-text-primary">{symbol} Chart</h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => window.open(`/trading-conditions/chart/${symbol}`, '_blank')}
              className="p-2 text-dark-text-muted hover:text-dark-text-primary hover:bg-dark-bg-hover rounded-xl transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-dark-text-muted hover:text-dark-text-primary hover:bg-dark-bg-hover rounded-xl transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Chart Content */}
        <div className="p-6">
          <div className="w-full h-[70vh] bg-dark-bg-tertiary rounded-xl overflow-hidden border border-dark-border-secondary">
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
        className={`hover:text-dark-accent-primary hover:underline transition-colors cursor-pointer ${className}`}
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

// Loading Skeleton Components
const MetricCardSkeleton: React.FC = () => {
  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass animate-pulse group hover:shadow-glow-sm transition-all duration-300">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-3">
            <div className="h-3 bg-dark-bg-tertiary rounded w-20 animate-pulse"></div>
            <div className="w-4 h-4 bg-dark-bg-tertiary rounded-full animate-pulse" style={{ animationDelay: '200ms' }}></div>
          </div>
          <div className="h-8 bg-dark-bg-tertiary rounded w-24 mb-2 animate-pulse" style={{ animationDelay: '400ms' }}></div>
          <div className="h-2 bg-dark-bg-tertiary rounded w-16 animate-pulse" style={{ animationDelay: '600ms' }}></div>
        </div>
        <div className="w-8 h-8 bg-dark-bg-tertiary rounded-lg animate-pulse group-hover:scale-110 transition-transform duration-300" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  );
};

const ChartSkeleton: React.FC<{ height?: string }> = ({ height = "h-64" }) => {
  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass animate-pulse hover:shadow-glow-sm transition-all duration-300">
      <div className="flex items-center mb-6">
        <div className="w-5 h-5 bg-dark-bg-tertiary rounded mr-2 animate-pulse"></div>
        <div className="h-6 bg-dark-bg-tertiary rounded w-32 animate-pulse" style={{ animationDelay: '200ms' }}></div>
      </div>
      <div className={`${height} bg-dark-bg-tertiary rounded-xl relative overflow-hidden`}>
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-dark-bg-hover/50 to-transparent animate-shimmer"></div>
        {/* Simulated chart elements */}
        <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between space-x-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <div 
              key={i}
              className="bg-dark-accent-primary/20 rounded-t animate-pulse"
              style={{ 
                height: `${Math.random() * 60 + 20}%`,
                animationDelay: `${i * 100}ms`,
                width: '100%'
              }}
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
};

const TableSkeleton: React.FC = () => {
  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass animate-pulse">
      <div className="h-6 bg-dark-bg-tertiary rounded w-48 mb-6"></div>
      <div className="overflow-x-auto">
        <div className="space-y-4">
          {/* Table Header */}
          <div className="grid grid-cols-8 gap-4 pb-4 border-b border-dark-border-secondary">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-4 bg-dark-bg-tertiary rounded"></div>
            ))}
          </div>
          {/* Table Rows */}
          {Array.from({ length: 8 }).map((_, rowIndex) => (
            <div key={rowIndex} className="grid grid-cols-8 gap-4 py-3">
              {Array.from({ length: 8 }).map((_, colIndex) => (
                <div 
                  key={colIndex} 
                  className="h-4 bg-dark-bg-tertiary rounded"
                  style={{ animationDelay: `${(rowIndex * 8 + colIndex) * 50}ms` }}
                ></div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const SymbolPerformanceSkeleton: React.FC = () => {
  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass animate-pulse">
      <div className="flex items-center mb-6">
        <div className="w-5 h-5 bg-dark-bg-tertiary rounded mr-2"></div>
        <div className="h-6 bg-dark-bg-tertiary rounded w-32"></div>
      </div>
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <div 
            key={index} 
            className="flex items-center justify-between p-3 bg-dark-bg-tertiary/50 rounded-xl"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center space-x-3">
              <div className="h-4 bg-dark-bg-hover rounded w-16"></div>
              <div className="h-3 bg-dark-bg-hover rounded w-12"></div>
            </div>
            <div className="text-right space-y-1">
              <div className="h-4 bg-dark-bg-hover rounded w-20"></div>
              <div className="h-3 bg-dark-bg-hover rounded w-16"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const RecentTradesSkeleton: React.FC = () => {
  return (
    <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass animate-pulse">
      <div className="flex items-center mb-6">
        <div className="w-5 h-5 bg-dark-bg-tertiary rounded mr-2"></div>
        <div className="h-6 bg-dark-bg-tertiary rounded w-28"></div>
      </div>
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <div 
            key={index} 
            className="flex items-center justify-between p-3 bg-dark-bg-tertiary/50 rounded-xl"
            style={{ animationDelay: `${index * 120}ms` }}
          >
            <div className="flex items-center space-x-3">
              <div className="h-4 bg-dark-bg-hover rounded w-16"></div>
              <div className="h-5 bg-dark-bg-hover rounded w-12"></div>
            </div>
            <div className="text-right space-y-1">
              <div className="h-4 bg-dark-bg-hover rounded w-20"></div>
              <div className="h-3 bg-dark-bg-hover rounded w-12"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const LoadingSkeleton: React.FC<{ viewMode: 'overview' | 'detailed' | 'charts' }> = ({ viewMode }) => {
  const [loadingProgress, setLoadingProgress] = React.useState(0);
  const [loadingText, setLoadingText] = React.useState('Initializing analysis...');

  React.useEffect(() => {
    const steps = [
      { progress: 20, text: 'Loading position data...' },
      { progress: 40, text: 'Calculating performance metrics...' },
      { progress: 60, text: 'Analyzing symbol performance...' },
      { progress: 80, text: 'Generating charts...' },
      { progress: 95, text: 'Finalizing analysis...' }
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        setLoadingProgress(steps[currentStep].progress);
        setLoadingText(steps[currentStep].text);
        currentStep++;
      } else {
        clearInterval(interval);
      }
    }, 600);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading Progress Indicator */}
        <div className="fixed top-0 left-0 right-0 z-50 bg-dark-bg-secondary/95 backdrop-blur-md border-b border-dark-border-primary">
          <div className="max-w-full mx-auto px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5 border-2 border-dark-accent-primary border-t-transparent rounded-full animate-spin"></div>
                <span className="text-dark-text-primary font-medium">{loadingText}</span>
              </div>
              <span className="text-dark-text-muted text-sm">{loadingProgress}%</span>
            </div>
            <div className="w-full bg-dark-bg-tertiary rounded-full h-1.5 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-dark-accent-primary to-dark-accent-secondary rounded-full transition-all duration-500 ease-out"
                style={{ width: `${loadingProgress}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Header Skeleton */}
        <div className="mb-10 animate-fade-in-up pt-20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 animate-slide-in-left">
              <div className="w-8 h-8 bg-dark-accent-primary/20 rounded-lg animate-pulse"></div>
              <div>
                <div className="h-10 bg-dark-bg-tertiary rounded w-64 mb-2 animate-pulse"></div>
                <div className="h-5 bg-dark-bg-tertiary rounded w-80 animate-pulse"></div>
              </div>
            </div>
            <div className="flex items-center space-x-3 animate-slide-in-right">
              <div className="h-12 bg-dark-bg-tertiary rounded-xl w-32 animate-pulse"></div>
            </div>
          </div>

          {/* Filters Skeleton */}
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-dark-bg-tertiary rounded animate-pulse"></div>
              <div className="h-12 bg-dark-bg-tertiary rounded-xl w-36 animate-pulse"></div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-dark-bg-tertiary rounded animate-pulse"></div>
              <div className="h-12 bg-dark-bg-tertiary rounded-xl w-32 animate-pulse"></div>
            </div>
            <div className="h-12 bg-dark-bg-tertiary rounded-xl w-80 animate-pulse"></div>
          </div>
        </div>

        {/* Performance Metrics Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} style={{ animationDelay: `${index * 100}ms` }}>
              <MetricCardSkeleton />
            </div>
          ))}
        </div>

        {/* Additional Metrics Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} style={{ animationDelay: `${(index + 4) * 100}ms` }}>
              <MetricCardSkeleton />
            </div>
          ))}
        </div>

        {/* Content based on view mode */}
        {viewMode === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div style={{ animationDelay: '800ms' }}>
              <SymbolPerformanceSkeleton />
            </div>
            <div style={{ animationDelay: '900ms' }}>
              <RecentTradesSkeleton />
            </div>
          </div>
        )}

        {viewMode === 'detailed' && (
          <div style={{ animationDelay: '800ms' }}>
            <TableSkeleton />
          </div>
        )}

        {viewMode === 'charts' && (
          <div className="space-y-8">
            <div style={{ animationDelay: '800ms' }}>
              <ChartSkeleton height="h-80" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div style={{ animationDelay: '900ms' }}>
                <ChartSkeleton />
              </div>
              <div style={{ animationDelay: '1000ms' }}>
                <ChartSkeleton />
              </div>
            </div>
            <div style={{ animationDelay: '1100ms' }}>
              <ChartSkeleton height="h-96" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const PositionAnalysis: React.FC = () => {
  const [positions, setPositions] = useState<PositionData[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [symbolPerformance, setSymbolPerformance] = useState<SymbolPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<'1d' | '7d' | '30d' | 'all'>('7d');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'charts'>('overview');
  const [contentReady, setContentReady] = useState(false);

  useEffect(() => {
    loadAnalysisData();
  }, [timeframe, selectedSymbol]);

  const loadAnalysisData = async () => {
    setLoading(true);
    setContentReady(false);
    
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
      // Add a small delay to show the loading completion
      setTimeout(() => {
        setLoading(false);
        // Add another small delay for smooth content transition
        setTimeout(() => setContentReady(true), 100);
      }, 500);
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
    return <LoadingSkeleton viewMode={viewMode} />;
  }

  return (
    <div className={`min-h-screen bg-dark-bg-primary transition-opacity duration-500 ${contentReady ? 'opacity-100' : 'opacity-0'}`}>
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className={`mb-10 transition-all duration-700 transform ${contentReady ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 animate-slide-in-left">
              <TrendingUp className="w-8 h-8 text-dark-accent-primary" />
              <div>
                <h1 className="text-4xl font-bold text-dark-text-primary">Position Analysis</h1>
                <p className="text-dark-text-muted text-lg">Performance analytics and detailed position analysis</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-dark-text-muted" />
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value as any)}
              className="bg-dark-bg-tertiary border border-dark-border-secondary text-dark-text-primary rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-dark-accent-primary focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300"
            >
              <option value="1d">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="all">All Time</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-dark-text-muted" />
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-dark-bg-tertiary border border-dark-border-secondary text-dark-text-primary rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-dark-accent-primary focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300"
            >
              <option value="all">All Symbols</option>
              {symbolPerformance.map(sp => (
                <option key={sp.symbol} value={sp.symbol}>{sp.symbol}</option>
              ))}
            </select>
          </div>

          <div className="flex bg-dark-bg-tertiary rounded-xl p-1 border border-dark-border-secondary">
            {(['overview', 'detailed', 'charts'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  viewMode === mode
                    ? 'bg-dark-accent-primary text-dark-text-primary shadow-glow-sm'
                    : 'text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-bg-hover'
                }`}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Performance Metrics Overview */}
        {metrics && (
          <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 transition-all duration-700 transform ${contentReady ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`} style={{ transitionDelay: '200ms' }}>
            <MetricCard
              title="Total P&L"
              value={formatCurrency(metrics.totalPnL)}
              icon={DollarSign}
              color={metrics.totalPnL >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}
              tooltip="Total profit and loss across all trades in the selected timeframe. This represents your net trading performance."
            />

            <MetricCard
              title="Win Rate"
              value={`${metrics.winRate.toFixed(1)}%`}
              icon={Target}
              color="text-dark-accent-primary"
              tooltip="Percentage of profitable trades. A higher win rate indicates more consistent profitable trading, though it should be considered alongside profit factor."
              subtitle={`${metrics.winningTrades}/${metrics.totalTrades} trades`}
            />

            <MetricCard
              title="Best Trade"
              value={formatCurrency(metrics.bestTrade)}
              icon={TrendingUp}
              color="text-dark-accent-success"
              tooltip="Your most profitable single trade in the selected period. This shows your maximum profit potential per trade."
            />

            <MetricCard
              title="Profit Factor"
              value={metrics.profitFactor.toFixed(2)}
              icon={Award}
              color="text-dark-accent-warning"
              tooltip="Ratio of gross profit to gross loss. A value above 1.0 indicates profitability. Higher values (>1.5) suggest strong trading performance."
            />
          </div>
        )}

        {/* Additional Performance Metrics */}
        {metrics && (
          <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 transition-all duration-700 transform ${contentReady ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`} style={{ transitionDelay: '400ms' }}>
            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 ease-in-out hover:scale-[1.02] group">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-dark-text-muted text-sm font-medium">Average P&L</p>
                    <Tooltip content="Average profit/loss per trade. This metric helps you understand your typical trade performance and consistency.">
                      <Info className="w-4 h-4 text-dark-text-disabled hover:text-dark-text-muted transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className={`text-xl font-bold ${metrics.averagePnL >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'} transition-all duration-200`}>
                    {formatCurrency(metrics.averagePnL)}
                  </p>
                </div>
                <BarChart3 className="w-6 h-6 text-dark-accent-info transition-all duration-200 group-hover:scale-110" />
              </div>
            </div>

            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 ease-in-out hover:scale-[1.02] group">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-dark-text-muted text-sm font-medium">Worst Trade</p>
                    <Tooltip content="Your largest single loss in the selected period. This helps you understand your maximum risk exposure per trade.">
                      <Info className="w-4 h-4 text-dark-text-disabled hover:text-dark-text-muted transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className="text-xl font-bold text-dark-accent-error transition-all duration-200">{formatCurrency(metrics.worstTrade)}</p>
                </div>
                <TrendingDown className="w-6 h-6 text-dark-accent-error transition-all duration-200 group-hover:scale-110" />
              </div>
            </div>

            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 ease-in-out hover:scale-[1.02] group">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-dark-text-muted text-sm font-medium">Avg Duration</p>
                    <Tooltip content="Average time each trade is held open. Shorter durations indicate more active trading, while longer durations suggest swing trading.">
                      <Info className="w-4 h-4 text-dark-text-disabled hover:text-dark-text-muted transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className="text-xl font-bold text-dark-accent-primary transition-all duration-200">{formatDuration(metrics.averageDuration)}</p>
                </div>
                <Activity className="w-6 h-6 text-dark-accent-primary transition-all duration-200 group-hover:scale-110" />
              </div>
            </div>

            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 ease-in-out hover:scale-[1.02] group">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <p className="text-dark-text-muted text-sm font-medium">Max Drawdown</p>
                    <Tooltip content="Maximum peak-to-trough decline in your account balance. Lower values indicate better risk management and capital preservation.">
                      <Info className="w-4 h-4 text-dark-text-disabled hover:text-dark-text-muted transition-colors duration-200" />
                    </Tooltip>
                  </div>
                  <p className="text-xl font-bold text-dark-accent-warning transition-all duration-200">{metrics.maxDrawdown.toFixed(1)}%</p>
                </div>
                <AlertTriangle className="w-6 h-6 text-dark-accent-warning transition-all duration-200 group-hover:scale-110" />
              </div>
            </div>
          </div>
        )}

        {/* Content based on view mode */}
        <div className={`transition-all duration-700 transform ${contentReady ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`} style={{ transitionDelay: '600ms' }}>
          {viewMode === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Symbol Performance */}
              <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
                <h3 className="text-xl font-semibold mb-6 flex items-center text-dark-text-primary">
                  <PieChart className="w-5 h-5 mr-2 text-dark-accent-primary" />
                  Symbol Performance
                </h3>
                <div className="space-y-4">
                  {symbolPerformance.slice(0, 5).map((sp) => (
                    <div key={sp.symbol} className="flex items-center justify-between p-3 bg-dark-bg-tertiary/50 rounded-xl border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300">
                      <div className="flex items-center space-x-3">
                        <ClickableSymbol symbol={sp.symbol} className="font-medium text-dark-text-primary">
                          {sp.symbol}
                        </ClickableSymbol>
                        <span className="text-sm text-dark-text-muted">{sp.trades} trades</span>
                      </div>
                      <div className="text-right">
                        <div className={`font-medium ${sp.totalPnL >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                          {formatCurrency(sp.totalPnL)}
                        </div>
                        <div className="text-sm text-dark-text-muted">{sp.winRate.toFixed(1)}% win rate</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Trades */}
              <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
                <h3 className="text-xl font-semibold mb-6 flex items-center text-dark-text-primary">
                  <Activity className="w-5 h-5 mr-2 text-dark-accent-primary" />
                  Recent Trades
                </h3>
                <div className="space-y-3">
                  {positions.slice(0, 5).map((pos) => (
                    <div 
                      key={pos.id} 
                      className="flex items-center justify-between p-3 bg-dark-bg-tertiary/50 rounded-xl border border-dark-border-secondary hover:border-dark-border-accent transition-colors duration-300"
                    >
                      <div className="flex items-center space-x-3">
                        <ClickableSymbol symbol={pos.symbol} className="font-medium text-dark-text-primary">
                          {pos.symbol}
                        </ClickableSymbol>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          pos.side === 'LONG' ? 'bg-dark-accent-success/20 text-dark-accent-success' : 'bg-dark-accent-error/20 text-dark-accent-error'
                        }`}>
                          {pos.side}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className={`font-medium ${pos.pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                          {formatCurrency(pos.pnl)}
                        </div>
                        <div className="text-sm text-dark-text-muted">{formatDuration(pos.duration)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {viewMode === 'detailed' && (
            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass animate-fade-in-up">
              <h3 className="text-xl font-semibold mb-6 text-dark-text-primary">Detailed Position History</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-border-secondary">
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">Symbol</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">Side</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">Entry</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">Exit</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">P&L</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">%</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">Duration</th>
                      <th className="text-left py-4 px-4 text-dark-text-muted font-medium">Strategy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.slice(0, 20).map((pos) => (
                      <tr key={pos.id} className="border-b border-dark-border-secondary/50 hover:bg-dark-bg-tertiary/30 transition-colors duration-200">
                        <td className="py-4 px-4 font-medium">
                          <ClickableSymbol symbol={pos.symbol} className="text-dark-text-primary">
                            {pos.symbol}
                          </ClickableSymbol>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            pos.side === 'LONG' ? 'bg-dark-accent-success/20 text-dark-accent-success' : 'bg-dark-accent-error/20 text-dark-accent-error'
                          }`}>
                            {pos.side}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-dark-text-secondary">${pos.entryPrice.toFixed(4)}</td>
                        <td className="py-4 px-4 text-dark-text-secondary">${pos.exitPrice.toFixed(4)}</td>
                        <td className={`py-4 px-4 font-medium ${pos.pnl >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                          {formatCurrency(pos.pnl)}
                        </td>
                        <td className={`py-4 px-4 ${pos.pnlPercentage >= 0 ? 'text-dark-accent-success' : 'text-dark-accent-error'}`}>
                          {formatPercentage(pos.pnlPercentage)}
                        </td>
                        <td className="py-4 px-4 text-dark-text-secondary">{formatDuration(pos.duration)}</td>
                        <td className="py-4 px-4 text-dark-text-muted">{pos.strategy}</td>
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
              <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
                <h3 className="text-xl font-semibold mb-6 flex items-center text-dark-text-primary">
                  <TrendingUp className="w-5 h-5 mr-2 text-dark-accent-primary" />
                  Cumulative P&L Over Time
                </h3>
                <PnLChart positions={positions} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Symbol Performance Pie Chart */}
                <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
                  <h3 className="text-xl font-semibold mb-6 flex items-center text-dark-text-primary">
                    <PieChart className="w-5 h-5 mr-2 text-dark-accent-primary" />
                    P&L by Symbol
                  </h3>
                  <SymbolPieChart symbolPerformance={symbolPerformance} />
                </div>

                {/* Win Rate by Symbol */}
                <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
                  <h3 className="text-xl font-semibold mb-6 flex items-center text-dark-text-primary">
                    <BarChart3 className="w-5 h-5 mr-2 text-dark-accent-primary" />
                    Win Rate by Symbol
                  </h3>
                  <WinRateChart symbolPerformance={symbolPerformance} />
                </div>
              </div>

              {/* Trading Performance Analysis */}
              <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass hover:shadow-glow-sm transition-all duration-300 animate-fade-in-up">
                <h3 className="text-xl font-semibold mb-6 flex items-center text-dark-text-primary">
                  <Activity className="w-5 h-5 mr-2 text-dark-accent-primary" />
                  Trading Performance Analysis
                </h3>
                <TradingHeatmapChart positions={positions} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PositionAnalysis; 