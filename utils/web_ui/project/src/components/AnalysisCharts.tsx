import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

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
  duration: number;
  strategy: string;
  leverage: number;
}

interface SymbolPerformance {
  symbol: string;
  trades: number;
  winRate: number;
  totalPnL: number;
  averagePnL: number;
}

interface PnLChartProps {
  positions: PositionData[];
}

interface SymbolChartProps {
  symbolPerformance: SymbolPerformance[];
}

// Custom tooltip for currency formatting
const CurrencyTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
        <p className="text-gray-300">{`Date: ${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }}>
            {`${entry.dataKey}: $${entry.value.toFixed(2)}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Custom tooltip for percentage formatting
const PercentageTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
        <p className="text-gray-300">{`${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }}>
            {`${entry.dataKey}: ${entry.value.toFixed(1)}%`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const PnLChart: React.FC<PnLChartProps> = ({ positions }) => {
  // Prepare data for cumulative P&L chart
  const chartData = React.useMemo(() => {
    const sortedPositions = [...positions].sort((a, b) => 
      new Date(a.exitTime).getTime() - new Date(b.exitTime).getTime()
    );

    let cumulativePnL = 0;
    return sortedPositions.map((pos, index) => {
      cumulativePnL += pos.pnl;
      return {
        date: new Date(pos.exitTime).toLocaleDateString(),
        cumulativePnL: cumulativePnL,
        tradePnL: pos.pnl,
        tradeNumber: index + 1
      };
    });
  }, [positions]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis 
          dataKey="date" 
          stroke="#9CA3AF"
          fontSize={12}
          interval="preserveStartEnd"
        />
        <YAxis 
          stroke="#9CA3AF"
          fontSize={12}
          tickFormatter={(value) => `$${value.toFixed(0)}`}
        />
        <Tooltip content={<CurrencyTooltip />} />
        <Area
          type="monotone"
          dataKey="cumulativePnL"
          stroke="#3B82F6"
          fill="#3B82F6"
          fillOpacity={0.3}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export const SymbolPieChart: React.FC<SymbolChartProps> = ({ symbolPerformance }) => {
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316'];

  const chartData = symbolPerformance.map((sp, index) => ({
    name: sp.symbol,
    value: Math.abs(sp.totalPnL),
    pnl: sp.totalPnL,
    trades: sp.trades,
    winRate: sp.winRate,
    color: COLORS[index % COLORS.length]
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium">{data.name}</p>
          <p className={`${data.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            P&L: ${data.pnl.toFixed(2)}
          </p>
          <p className="text-gray-300">Trades: {data.trades}</p>
          <p className="text-gray-300">Win Rate: {data.winRate.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  );
};

export const WinRateChart: React.FC<SymbolChartProps> = ({ symbolPerformance }) => {
  const chartData = symbolPerformance.map(sp => ({
    symbol: sp.symbol,
    winRate: sp.winRate,
    trades: sp.trades
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis 
          dataKey="symbol" 
          stroke="#9CA3AF"
          fontSize={12}
        />
        <YAxis 
          stroke="#9CA3AF"
          fontSize={12}
          domain={[0, 100]}
          tickFormatter={(value) => `${value}%`}
        />
        <Tooltip content={<PercentageTooltip />} />
        <Bar 
          dataKey="winRate" 
          fill="#10B981"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

export const TradeDistributionChart: React.FC<PnLChartProps> = ({ positions }) => {
  const chartData = React.useMemo(() => {
    // Group trades by P&L ranges
    const ranges = [
      { name: '< -$100', min: -Infinity, max: -100, count: 0, color: '#EF4444' },
      { name: '-$100 to -$50', min: -100, max: -50, count: 0, color: '#F87171' },
      { name: '-$50 to $0', min: -50, max: 0, count: 0, color: '#FCA5A5' },
      { name: '$0 to $50', min: 0, max: 50, count: 0, color: '#86EFAC' },
      { name: '$50 to $100', min: 50, max: 100, count: 0, color: '#22C55E' },
      { name: '> $100', min: 100, max: Infinity, count: 0, color: '#16A34A' }
    ];

    positions.forEach(pos => {
      const range = ranges.find(r => pos.pnl > r.min && pos.pnl <= r.max);
      if (range) range.count++;
    });

    return ranges.filter(r => r.count > 0);
  }, [positions]);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} layout="horizontal">
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis 
          type="number"
          stroke="#9CA3AF"
          fontSize={12}
        />
        <YAxis 
          type="category"
          dataKey="name"
          stroke="#9CA3AF"
          fontSize={12}
          width={100}
        />
        <Tooltip 
          formatter={(value: any) => [`${value} trades`, 'Count']}
          labelStyle={{ color: '#D1D5DB' }}
          contentStyle={{ 
            backgroundColor: '#1F2937', 
            border: '1px solid #374151',
            borderRadius: '8px'
          }}
        />
        <Bar 
          dataKey="count" 
          fill="#3B82F6"
          radius={[0, 4, 4, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}; 