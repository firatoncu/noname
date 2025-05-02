import { useNavigate } from 'react-router-dom';
import { Position } from '../types';
import { DollarSign, TrendingUp, TrendingDown, LineChart } from 'lucide-react';

interface PositionCardProps {
  position: Position;
  pricePrecision: number;
  isDarkMode: boolean;
}

export function PositionCard({ position, pricePrecision, isDarkMode }: PositionCardProps) {
  const navigate = useNavigate();
  const isLong = parseFloat(position.positionAmt) > 0;
  const pnl = parseFloat(position.unRealizedProfit);
  const entryPrice = parseFloat(position.entryPrice);
  
  const takeProfit = isLong 
    ? (entryPrice * 1.0033).toFixed(pricePrecision)
    : (entryPrice * 0.9966).toFixed(pricePrecision);
    
  const stopLoss = isLong
    ? (entryPrice * 0.993).toFixed(pricePrecision)
    : (entryPrice * 1.007).toFixed(pricePrecision);

  const handleViewChart = () => {
    const currentPosition = {
      symbol: position.symbol,
      side: isLong ? 'LONG' : 'SHORT',
      entryPrice: position.entryPrice,
      currentPrice: position.markPrice,
      openedAt: position.entryTime,
      pnl: position.unRealizedProfit,
      isActive: true
    };
    navigate(`/position/current/${position.symbol}`, { state: { position: currentPosition } });
  };

  return (
    <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-md p-6 mb-4 transition-colors duration-200`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <span className={`text-xl font-bold mr-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            {position.symbol}
          </span>
          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
            isLong 
              ? isDarkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'
              : isDarkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800'
          }`}>
            {isLong ? 'LONG' : 'SHORT'}
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <DollarSign className={`w-5 h-5 ${isDarkMode ? 'text-blue-400' : 'text-blue-500'} mr-1`} />
            <span className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>
              ${Math.abs(parseFloat(position.notional)).toFixed(2)}
            </span>
          </div>
          <button
            onClick={handleViewChart}
            className={`flex items-center space-x-1 px-3 py-1 rounded-md 
              ${isDarkMode 
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
          >
            <LineChart className="w-4 h-4" />
            <span>View Chart</span>
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex flex-col">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>P&L</span>
          <span className={`font-semibold ${pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
            ${pnl.toFixed(2)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>P&L (&)</span>
          <span className={`font-semibold ${pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
            ${(pnl / parseFloat(position.notional) * 500).toFixed(2)}%
          </span>
        </div>
        <div className="flex flex-col">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Entry Price</span>
          <span className={`font-semibold ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>
            ${entryPrice.toFixed(pricePrecision)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Current Price</span>
          <span className={`font-semibold ${isDarkMode ? 'text-purple-400' : 'text-purple-600'}`}>
            ${parseFloat(position.markPrice).toFixed(pricePrecision)}
          </span>
        </div>

      </div>
      
      <div className={`flex items-center justify-between pt-2 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
      <div className="flex  items-center">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mr-2`}>Take Profit </span>
          <span className="font-semibold text-green-500">${takeProfit}</span>
        </div>
        <div className="flex items-center">
          <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'} mr-2`}>Stop Loss</span>
          <span className="font-semibold text-red-500">${stopLoss}</span>
        </div>
        {isLong ? (
          <TrendingUp className="w-5 h-5 text-green-500" />
        ) : (
          <TrendingDown className="w-5 h-5 text-red-500" />
        )}
      </div>
    </div>
  );
}