import React, { useState, useEffect } from 'react';
import { PositionCard } from '../components/PositionCard';
import { TradingConditionsCard } from '../components/TradingConditions';
import { WalletCard } from '../components/WalletCard';
import { HistoricalPositions } from '../components/HistoricalPositions';
import { Position, TradingConditions, WalletInfo, HistoricalPosition } from '../types';
import { LayoutDashboard, Moon, Sun } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api';

function App() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [conditions, setConditions] = useState<TradingConditions[]>([]);
  const [wallet, setWallet] = useState<WalletInfo>({
    totalBalance: '0',
    availableBalance: '0',
    unrealizedPnL: '0',
    dailyPnL: '0',
    weeklyPnL: '0',
    marginRatio: '0',
  });
  const [historicalPositions, setHistoricalPositions] = useState<HistoricalPosition[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [currentConditionIndex, setCurrentConditionIndex] = useState(0);
  const [apiError, setApiError] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  const fetchData = async () => {
    try {
      const responses = await Promise.all([
        fetch(`${API_BASE_URL}/positions`),
        fetch(`${API_BASE_URL}/trading-conditions`),
        fetch(`${API_BASE_URL}/wallet`),
        fetch(`${API_BASE_URL}/historical-positions`)
      ]);

      const [positionsRes, conditionsRes, walletRes, historicalRes] = responses;

      if (!responses.every(res => res.ok)) {
        throw new Error('One or more API responses not ok');
      }

      const [positionsData, conditionsData, walletData, historicalData] = await Promise.all([
        positionsRes.json(),
        conditionsRes.json(),
        walletRes.json(),
        historicalRes.json()
      ]);

      // Only update state if we have valid data
      if (Array.isArray(positionsData)) {
        setPositions(positionsData);
      }
      if (Array.isArray(conditionsData)) {
        setConditions(conditionsData);
        // Reset condition index if needed
        if (currentConditionIndex >= conditionsData.length) {
          setCurrentConditionIndex(0);
        }
      }
      if (walletData && typeof walletData === 'object') {
        setWallet(walletData);
      }
      if (Array.isArray(historicalData)) {
        setHistoricalPositions(historicalData);
      }
      setApiError(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setApiError(true);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchData();

    // Set up polling interval
    const intervalId = setInterval(fetchData, 1000);

    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, []); // Empty dependency array means this effect runs once on mount

  // Reset condition index when selected symbol changes
  useEffect(() => {
    setCurrentConditionIndex(0);
  }, [selectedSymbol]);

  const filteredPositions = selectedSymbol === 'all' 
    ? positions 
    : positions.filter(p => p.symbol === selectedSymbol);

  const filteredConditions = selectedSymbol === 'all'
    ? conditions
    : conditions.filter(c => c.symbol === selectedSymbol);

  const symbols = ['all', ...Array.from(new Set(positions.map(p => p.symbol)))];

  const PRICE_PRECISION: { [key: string]: number } = {
    'BTCUSDT': 2,
    'ETHUSDT': 2,
    'SOLUSDT': 3,
    'XRPUSDT': 4,
    'REDUSDT': 4,
    'BMTUSDT': 4,
  };

  const handlePreviousCondition = () => {
    setCurrentConditionIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNextCondition = () => {
    setCurrentConditionIndex((prev) => Math.min(filteredConditions.length - 1, prev + 1));
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
                  API Connection Error
                </span>
              )}
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
        <WalletCard wallet={wallet} isDarkMode={isDarkMode} />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
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
            {filteredConditions.length > 0 && (
              <TradingConditionsCard
                key={filteredConditions[currentConditionIndex].symbol}
                conditions={filteredConditions[currentConditionIndex]}
                isDarkMode={isDarkMode}
                onPrevious={handlePreviousCondition}
                onNext={handleNextCondition}
                isFirst={currentConditionIndex === 0}
                isLast={currentConditionIndex === filteredConditions.length - 1}
              />
            )}
          </div>
        </div>

        <HistoricalPositions 
          positions={historicalPositions} 
          isDarkMode={isDarkMode} 
        />
      </main>
    </div>
  );
}

export default App;