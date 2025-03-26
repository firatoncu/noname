import React, { useState, useEffect } from 'react';
import { PositionCard } from './components/PositionCard';
import { TradingConditionsCard } from './components/TradingConditions';
import { Position, TradingConditions } from './types';
import { LayoutDashboard, Moon, Sun } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

// Fallback mock data in case API is not available
const MOCK_POSITIONS: Position[] = [
  {
    symbol: 'BTCUSDT',
    positionAmt: '0.5',
    notional: '20000',
    unRealizedProfit: '150.25',
    entryPrice: '40000',
    markPrice: '40300',
  }
];

const MOCK_CONDITIONS: TradingConditions[] = [
  {
    symbol: 'BTCUSDT',
    fundingPeriod: true,
    buyConditions: {
      condA: true,
      condB: false,
      condC: true,
    },
    sellConditions: {
      condA: false,
      condB: true,
      condC: false,
    },
  }
];

function App() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [conditions, setConditions] = useState<TradingConditions[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [apiError, setApiError] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  const fetchData = async () => {
    try {
      const [positionsRes, conditionsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/positions`, { cache: 'no-store' }),
        fetch(`${API_BASE_URL}/trading-conditions`, { cache: 'no-store' })
      ]);

      if (!positionsRes.ok || !conditionsRes.ok) {
        throw new Error('API response not ok');
      }

      const positionsData = await positionsRes.json();
      const conditionsData = await conditionsRes.json();

      console.log('Fetched Positions:', positionsData);
      console.log('Fetched Conditions:', conditionsData);

      setPositions(positionsData);
      setConditions(conditionsData);
      setApiError(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setPositions(MOCK_POSITIONS);
      setConditions(MOCK_CONDITIONS);
      setApiError(true);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000); // 1 saniye
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    console.log('Positions State:', positions);
    console.log('Conditions State:', conditions);
  }, [positions, conditions]);

  const filteredPositions = selectedSymbol === 'all' 
    ? positions 
    : positions.filter(p => p.symbol === selectedSymbol);

  const filteredConditions = selectedSymbol === 'all'
    ? conditions
    : conditions.filter(c => c.symbol === selectedSymbol);

  const symbols = ['all', ...Array.from(new Set(positions.map(p => p.symbol)))];

  // Price precision for different symbols
  const PRICE_PRECISION: { [key: string]: number } = {
    'BTCUSDT': 2,
    'ETHUSDT': 2,
    'SOLUSDT': 3,
  };

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-gray-100'} transition-colors duration-200`}>
      <nav className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} shadow-sm transition-colors duration-200`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <LayoutDashboard className={`w-6 h-6 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'} mr-2`} />
              <span className={`text-xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                n0name Trading Dashboard
              </span>
            </div>
            <div className="flex items-center space-x-6">
              {apiError && (
                <span className="text-red-500 text-sm">
                  API Unavailable - Using Mock Data
                </span>
              )}
              <div className="flex items-center space-x-4">
                <label htmlFor="symbol-filter" className={`text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Filter Symbol:
                </label>
                <select
                  id="symbol-filter"
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  className={`block w-32 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm
                    ${isDarkMode 
                      ? 'bg-gray-700 border-gray-600 text-white' 
                      : 'bg-white border-gray-300 text-gray-900'}`}
                >
                  {symbols.map(symbol => (
                    <option key={symbol} value={symbol}>
                      {symbol === 'all' ? 'All Symbols' : symbol}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className={`p-2 rounded-full hover:bg-opacity-20 
                  ${isDarkMode 
                    ? 'hover:bg-gray-600 text-gray-300' 
                    : 'hover:bg-gray-200 text-gray-600'}`}
                aria-label="Toggle dark mode"
              >
                {isDarkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h2 className={`text-2xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Open Positions
            </h2>
            {filteredPositions.length > 0 ? (
              filteredPositions.map((position) => (
                <PositionCard
                  key={position.symbol}
                  position={position}
                  pricePrecision={PRICE_PRECISION[position.symbol] || 2}
                  isDarkMode={isDarkMode}
                />
              ))
            ) : (
              <div className={`${isDarkMode ? 'bg-gray-800 text-gray-400' : 'bg-white text-gray-500'} 
                rounded-lg shadow-md p-6 text-center transition-colors duration-200`}>
                No Open Positions
              </div>
            )}
          </div>

          <div>
            <h2 className={`text-2xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Trading Conditions
            </h2>
            {filteredConditions.map((condition) => (
              <TradingConditionsCard
                key={condition.symbol}
                conditions={condition}
                isDarkMode={isDarkMode}
              />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;