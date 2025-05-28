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

// Enhanced tooltip with glassmorphism effect
const CurrencyTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-600/30 rounded-xl p-4 shadow-2xl shadow-slate-900/40">
        <p className="text-slate-300 font-semibold mb-2">{`Date: ${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }} className="font-bold text-lg">
            {`${entry.dataKey}: $${entry.value.toFixed(2)}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Enhanced percentage tooltip
const PercentageTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-600/30 rounded-xl p-4 shadow-2xl shadow-slate-900/40">
        <p className="text-slate-300 font-semibold mb-2">{`${label}`}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }} className="font-bold text-lg">
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
        <defs>
          <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#1E40AF" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" opacity={0.2} />
        <XAxis 
          dataKey="date" 
          stroke="#4B5563"
          fontSize={12}
          interval="preserveStartEnd"
          tick={{ fill: '#4B5563' }}
        />
        <YAxis 
          stroke="#4B5563"
          fontSize={12}
          tickFormatter={(value) => `$${value.toFixed(0)}`}
          tick={{ fill: '#4B5563' }}
        />
        <Tooltip content={<CurrencyTooltip />} />
        <Area
          type="monotone"
          dataKey="cumulativePnL"
          stroke="#3B82F6"
          fill="url(#pnlGradient)"
          strokeWidth={3}
          dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2, fill: '#1E40AF' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export const SymbolPieChart: React.FC<SymbolChartProps> = ({ symbolPerformance }) => {
  // Dark icy color palette with transparency
  const COLORS = [
    '#6366F1', // Indigo
    '#10B981', // Emerald  
    '#F59E0B', // Amber
    '#EF4444', // Red
    '#8B5CF6', // Violet
    '#06B6D4', // Cyan
    '#F97316', // Orange
    '#EC4899', // Pink
  ];

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
        <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-600/30 rounded-xl p-4 shadow-2xl shadow-slate-900/40">
          <p className="text-slate-300 font-bold text-lg mb-2">{data.name}</p>
          <p className={`font-bold text-xl ${data.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            P&L: ${data.pnl.toFixed(2)}
          </p>
          <p className="text-slate-400 font-medium">Trades: {data.trades}</p>
          <p className="text-slate-400 font-medium">Win Rate: {data.winRate.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <defs>
          {COLORS.map((color, index) => (
            <linearGradient key={index} id={`gradient${index}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.9}/>
              <stop offset="100%" stopColor={color} stopOpacity={0.4}/>
            </linearGradient>
          ))}
        </defs>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          outerRadius={100}
          innerRadius={40}
          fill="#8884d8"
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          labelLine={false}
          style={{ fontSize: '12px', fill: '#64748B', fontWeight: '600' }}
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={`url(#gradient${index % COLORS.length})`}
              stroke={entry.color}
              strokeWidth={1}
              strokeOpacity={0.6}
            />
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
        <defs>
          <linearGradient id="winRateGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#10B981" stopOpacity={0.9}/>
            <stop offset="95%" stopColor="#059669" stopOpacity={0.4}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" opacity={0.2} />
        <XAxis 
          dataKey="symbol" 
          stroke="#4B5563"
          fontSize={12}
          tick={{ fill: '#4B5563' }}
        />
        <YAxis 
          stroke="#4B5563"
          fontSize={12}
          domain={[0, 100]}
          tickFormatter={(value) => `${value}%`}
          tick={{ fill: '#4B5563' }}
        />
        <Tooltip content={<PercentageTooltip />} />
        <Bar 
          dataKey="winRate" 
          fill="url(#winRateGradient)"
          radius={[6, 6, 0, 0]}
          stroke="#10B981"
          strokeWidth={1}
          strokeOpacity={0.6}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

export const TradingHeatmapChart: React.FC<PnLChartProps> = ({ positions }) => {
  const chartData = React.useMemo(() => {
    // Initialize data structure for heatmap
    const heatmapData: { hour: number; day: string; trades: number; avgPnL: number; winRate: number }[] = [];
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Create data structure
    for (let day = 0; day < 7; day++) {
      for (let hour = 0; hour < 24; hour++) {
        heatmapData.push({
          hour,
          day: days[day],
          trades: 0,
          avgPnL: 0,
          winRate: 0
        });
      }
    }

    // Group trades by day and hour
    const tradeGroups = new Map<string, PositionData[]>();
    
    positions.forEach(pos => {
      const exitDate = new Date(pos.exitTime);
      const day = exitDate.getDay(); // 0 = Sunday
      const hour = exitDate.getHours();
      const key = `${day}-${hour}`;
      
      if (!tradeGroups.has(key)) {
        tradeGroups.set(key, []);
      }
      tradeGroups.get(key)!.push(pos);
    });

    // Calculate metrics for each time slot
    tradeGroups.forEach((trades, key) => {
      const [dayIndex, hourIndex] = key.split('-').map(Number);
      const dataIndex = dayIndex * 24 + hourIndex;
      
      if (dataIndex < heatmapData.length) {
        const totalPnL = trades.reduce((sum, trade) => sum + trade.pnl, 0);
        const winningTrades = trades.filter(trade => trade.pnl > 0).length;
        
        heatmapData[dataIndex] = {
          hour: hourIndex,
          day: days[dayIndex],
          trades: trades.length,
          avgPnL: totalPnL / trades.length,
          winRate: (winningTrades / trades.length) * 100
        };
      }
    });

    return heatmapData.filter(d => d.trades > 0);
  }, [positions]);

  // Create hourly performance data
  const hourlyData = React.useMemo(() => {
    const hourlyStats = Array.from({ length: 24 }, (_, hour) => ({
      hour: `${hour.toString().padStart(2, '0')}:00`,
      trades: 0,
      avgPnL: 0,
      totalPnL: 0
    }));

    positions.forEach(pos => {
      const hour = new Date(pos.exitTime).getHours();
      hourlyStats[hour].trades++;
      hourlyStats[hour].totalPnL += pos.pnl;
    });

    hourlyStats.forEach(stat => {
      if (stat.trades > 0) {
        stat.avgPnL = stat.totalPnL / stat.trades;
      }
    });

    return hourlyStats.filter(stat => stat.trades > 0);
  }, [positions]);

  return (
    <div className="space-y-6">
      {/* Hourly Performance Chart */}
      <div>
        <h4 className="text-lg font-semibold mb-4 text-slate-300">Performance by Hour</h4>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={hourlyData}>
            <defs>
              <linearGradient id="hourlyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.9}/>
                <stop offset="95%" stopColor="#0891B2" stopOpacity={0.4}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" opacity={0.2} />
            <XAxis 
              dataKey="hour" 
              stroke="#4B5563"
              fontSize={11}
              tick={{ fill: '#4B5563' }}
            />
            <YAxis 
              stroke="#4B5563"
              fontSize={11}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
              tick={{ fill: '#4B5563' }}
            />
            <Tooltip 
              formatter={(value: any, name: string) => [
                name === 'avgPnL' ? `$${value.toFixed(2)}` : value,
                name === 'avgPnL' ? 'Avg P&L' : 'Trades'
              ]}
              labelStyle={{ color: '#64748B', fontWeight: 'bold' }}
              contentStyle={{ 
                backgroundColor: 'rgba(15, 23, 42, 0.95)', 
                border: '1px solid rgba(99, 102, 241, 0.2)',
                borderRadius: '12px',
                backdropFilter: 'blur(16px)',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.4)'
              }}
            />
            <Bar 
              dataKey="avgPnL" 
              fill="url(#hourlyGradient)"
              radius={[4, 4, 0, 0]}
              stroke="#06B6D4"
              strokeWidth={1}
              strokeOpacity={0.6}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Trading Activity Heatmap */}
      <div>
        <h4 className="text-lg font-semibold mb-4 text-slate-300">Trading Activity Heatmap</h4>
        <div className="grid grid-cols-8 gap-1 text-xs">
          {/* Header row */}
          <div className="text-slate-400 font-medium p-2"></div>
          {Array.from({ length: 7 }, (_, i) => (
            <div key={i} className="text-slate-400 font-medium p-2 text-center">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][i]}
            </div>
          ))}
          
          {/* Time slots */}
          {Array.from({ length: 24 }, (_, hour) => (
            <React.Fragment key={hour}>
              <div className="text-slate-400 font-medium p-2 text-right">
                {hour.toString().padStart(2, '0')}:00
              </div>
              {Array.from({ length: 7 }, (_, day) => {
                const data = chartData.find(d => d.hour === hour && d.day === ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][day]);
                const intensity = data ? Math.min(data.trades / 5, 1) : 0; // Normalize to max 5 trades
                const isProfit = data && data.avgPnL > 0;
                
                return (
                  <div
                    key={`${day}-${hour}`}
                    className={`p-2 rounded border border-slate-700/30 transition-all duration-200 hover:scale-110 cursor-pointer ${
                      intensity > 0 
                        ? isProfit 
                          ? 'bg-emerald-500' 
                          : 'bg-red-500'
                        : 'bg-slate-800/50'
                    }`}
                    style={{ 
                      opacity: intensity > 0 ? 0.3 + (intensity * 0.7) : 0.1 
                    }}
                    title={data ? `${data.trades} trades, Avg P&L: $${data.avgPnL.toFixed(2)}` : 'No trades'}
                  >
                    <div className="w-full h-4"></div>
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-center space-x-6 mt-4 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-emerald-500 rounded opacity-60"></div>
            <span>Profitable</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded opacity-60"></div>
            <span>Loss</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-slate-800 rounded opacity-30"></div>
            <span>No trades</span>
          </div>
          <span>Intensity = Trade frequency</span>
        </div>
      </div>
    </div>
  );
}; 