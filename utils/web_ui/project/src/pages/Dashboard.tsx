import { useState, useEffect } from 'react';
import { PositionCard } from '../components/PositionCard';
import { WalletCard } from '../components/WalletCard';
import { HistoricalPositions } from '../components/HistoricalPositions';
import { Position, TradingConditions, WalletInfo, HistoricalPosition } from '../types';
import { LayoutDashboard, BarChart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createApiUrl, API_ENDPOINTS } from '../config/api';

function App() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [, setConditions] = useState<TradingConditions[]>([]);
  const [wallet, setWallet] = useState<WalletInfo>({
    totalBalance: '0',
    availableBalance: '0',
    unrealizedPnL: '0',
    dailyPnL: '0',
    weeklyPnL: '0',
    marginRatio: '0',
  });
  const [historicalPositions, setHistoricalPositions] = useState<HistoricalPosition[]>([]);
  const [selectedSymbol, ] = useState<string>('all');
  const [apiError, setApiError] = useState(false);
  const isDarkMode = true;

  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  const fetchData = async () => {
    try {
      const responses = await Promise.all([
        fetch(createApiUrl(API_ENDPOINTS.POSITIONS)),
        fetch(createApiUrl(API_ENDPOINTS.TRADING_CONDITIONS)),
        fetch(createApiUrl(API_ENDPOINTS.WALLET)),
        fetch(createApiUrl(API_ENDPOINTS.HISTORICAL_POSITIONS))
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

  const filteredPositions = selectedSymbol === 'all' 
    ? positions 
    : positions.filter(p => p.symbol === selectedSymbol);


  const PRICE_PRECISION: { [key: string]: number } = {
    'BTCUSDT': 2,
    'ETHUSDT': 2,
    'SOLUSDT': 3,
    'XRPUSDT': 4,
    'REDUSDT': 4,
    'BMTUSDT': 4,
  };

  return (
    <div className="min-h-screen bg-gray-900 transition-colors duration-200">
      <nav className="bg-gray-800 shadow-sm transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <LayoutDashboard className="w-6 h-6 text-blue-400 mr-2" />
              <span className="text-xl font-semibold text-white">
                n0name Trading Dashboard
              </span>
            </div>
            <div className="flex items-center space-x-6">
              {apiError && (
                <span className="text-red-500 text-sm">
                  API Connection Error
                </span>
              )}
              <Link 
                to="/trading-conditions" 
                className="px-4 py-2 rounded-md flex items-center bg-gray-700 hover:bg-gray-600 text-gray-200"
              >
                <BarChart className="w-4 h-4 mr-2" />
                <span>Trading Conditions</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <WalletCard wallet={wallet} isDarkMode={isDarkMode} />
        
        <div className="mb-6">
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

        <HistoricalPositions 
          positions={historicalPositions} 
          isDarkMode={isDarkMode} 
        />
      </main>
    </div>
  );
}

export default App;