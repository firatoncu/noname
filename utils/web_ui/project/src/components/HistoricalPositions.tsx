import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, History, ArrowUp, ArrowDown, ChevronDown } from 'lucide-react';
import { HistoricalPosition } from '../types';

interface HistoricalPositionsProps {
  positions: HistoricalPosition[];
  isDarkMode: boolean;
}

export function HistoricalPositions({ positions, isDarkMode }: HistoricalPositionsProps) {
  const navigate = useNavigate();
  const [visiblePositions, setVisiblePositions] = useState(5);

  const handleViewChart = (position: HistoricalPosition) => {
    const positionId = `${position.symbol}-${position.closedAt}`;
    navigate(`/position/${positionId}`, { state: { position } });
  }

  const handleShowMore = () => {
    setVisiblePositions(prev => prev + 5);
  }

  const displayedPositions = positions.slice(0, visiblePositions);
  const hasMorePositions = visiblePositions < positions.length;

  return (
    <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-md p-6 mb-4 transition-colors duration-200`}>
      <div className="flex items-center mb-4">
        <History className={`w-6 h-6 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'} mr-2`} />
        <h2 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          Recent Positions
        </h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className={`text-left ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              <th className="pb-3 pr-4">Symbol</th>
              <th className="pb-3 px-4">Side</th>
              <th className="pb-3 px-4">Entry</th>
              <th className="pb-3 px-4">Exit</th>
              <th className="pb-3 px-4">Amount</th>
              <th className="pb-3 px-4">P&L</th>
              <th className="pb-3 pl-4">Opened</th>
              <th className="pb-3 pl-4">Closed</th>
            </tr>
          </thead>
          <tbody>
            {displayedPositions.map((position, index) => (
              <tr 
                key={`${position.symbol}-${position.closedAt}`}
                className={`
                  ${isDarkMode ? 'text-gray-300' : 'text-gray-900'}
                  ${index !== displayedPositions.length - 1 ? `border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}` : ''}
                `}
              >
                <td className="py-3 pr-4 font-medium">{position.symbol}</td>
                <td className="py-3 px-4">
                  <span className={`flex items-center ${
                    position.side === 'LONG' 
                      ? 'text-green-500' 
                      : 'text-red-500'
                  }`}>
                    {position.side === 'LONG' 
                      ? <ArrowUp className="w-4 h-4 mr-1" />
                      : <ArrowDown className="w-4 h-4 mr-1" />
                    }
                    {position.side}
                  </span>
                </td>
                <td className="py-3 px-4">${parseFloat(position.entryPrice).toFixed(4)}</td>
                <td className="py-3 px-4">${parseFloat(position.exitPrice).toFixed(4)}</td>
                <td className="py-3 px-4">${parseFloat(position.amount).toFixed(2)}</td>
                <td className={`py-3 px-4 font-medium ${
                  parseFloat(position.profit) >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  ${parseFloat(position.profit).toFixed(2)}
                </td>
                <td className="py-3 pl-4 text-sm">
                  {new Date(position.openedAt).toLocaleString()}
                </td>
                <td className="py-3 pl-4 text-sm">
                  {new Date(position.closedAt).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    onClick={() => handleViewChart(position)}
                    className={`flex items-center space-x-1 px-3 py-1 rounded-md 
                      ${isDarkMode 
                        ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
                  >
                    <LineChart className="w-4 h-4" />
                    <span>View Chart</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {hasMorePositions && (
        <div className="mt-4 text-center">
          <button
            onClick={handleShowMore}
            className={`flex items-center justify-center mx-auto px-4 py-2 rounded-md 
              ${isDarkMode 
                ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
          >
            <ChevronDown className="w-4 h-4 mr-2" />
            <span>Show More</span>
          </button>
        </div>
      )}
    </div>
  );
}
