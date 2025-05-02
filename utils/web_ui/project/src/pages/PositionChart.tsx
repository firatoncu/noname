import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useOutletContext, useLocation } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { HistoricalPosition } from '../types';

const API_BASE_URL = 'http://n0name:8000/api';

function PositionChart() {
  const { isDarkMode } = useOutletContext<{ isDarkMode: boolean }>();
  const location = useLocation();
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const widgetRef = useRef<any>(null);
  
  const initialPosition = location.state?.position;
  const [currentPosition, setCurrentPosition] = useState(initialPosition);
  const [positionDetails, setPositionDetails] = useState(initialPosition);

  useEffect(() => {
    let intervalId: number;

    // Only fetch current position data if this is an active position
    if (initialPosition?.isActive) {
      const fetchCurrentPosition = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/positions`);
          if (!response.ok) throw new Error('Failed to fetch positions');
          
          const positions = await response.json();
          const position = positions.find((p: any) => p.symbol === initialPosition.symbol);
          
          if (position) {
            setPositionDetails({
              ...initialPosition,
              currentPrice: position.markPrice,
              profit: position.unRealizedProfit
            });
          }
        } catch (error) {
          console.error('Error fetching current position:', error);
        }
      };

      // Initial fetch
      fetchCurrentPosition();
      
      // Set up polling for active positions
      intervalId = window.setInterval(fetchCurrentPosition, 1000);
    }

    return () => {
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [initialPosition]);

  useEffect(() => {
    if (!currentPosition || !containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (containerRef.current && window.TradingView) {
        // Parse the date string (DD.MM.YYYY HH:mm:ss)
        const parseCustomDate = (dateStr: string) => {
          const [datePart, timePart] = dateStr.split(' ');
          const [day, month, year] = datePart.split('.');
          const [hours, minutes, seconds] = timePart.split(':');
          
          return new Date(
            parseInt(year),
            parseInt(month) - 1,
            parseInt(day),
            parseInt(hours),
            parseInt(minutes),
            parseInt(seconds)
          ).getTime() / 1000;
        };

        const openTime = parseCustomDate(currentPosition.openedAt);
        const closeTime = currentPosition.isActive 
          ? Math.floor(Date.now() / 1000)
          : parseCustomDate(currentPosition.closedAt);

        // Calculate time range and padding
        const timeRange = closeTime - openTime;
        const paddingTime = Math.max(timeRange * 0.1, 3600); // At least 1 hour padding

        widgetRef.current = new window.TradingView.widget({
          symbol: `BINANCE:${currentPosition.symbol}.P`,
          interval: '1',
          timezone: 'Europe/Istanbul',
          theme: 'dark',
          style: '1',
          locale: 'en',
          toolbar_bg: '#1f2937',
          enable_publishing: false,
          allow_symbol_change: false,
          container_id: 'tradingview-widget',
          width: '130%',
          height: '600',
          save_image: false,
          hide_side_toolbar: false,
          studies: ['MACD@tv-basicstudies'],
          time: openTime - paddingTime,
          range: timeRange + (paddingTime * 2),
          disabled_features: ["use_localstorage_for_settings"],
          enabled_features: ["study_templates"],
          charts_storage_api_version: "1.1",
          client_id: "tradingview.com",
          user_id: "public_user"
        });

        // Add markers after widget is ready
        widgetRef.current.onChartReady(() => {
          const chart = widgetRef.current.chart();
          
          // Create entry marker
          chart.createShape(
            { time: openTime, price: parseFloat(currentPosition.entryPrice) },
            {
              shape: "arrow_up",
              text: "Entry",
              lock: true,
              disableSelection: true,
              disableSave: true,
              overrides: {
                backgroundColor: currentPosition.side === 'LONG' ? '#22c55e' : '#ef4444',
                color: currentPosition.side === 'LONG' ? '#22c55e' : '#ef4444',
                textColor: isDarkMode ? '#ffffff' : '#000000',
                fontsize: 14,
                bold: true
              }
            }
          );

          // Create exit marker for closed positions
          if (!currentPosition.isActive) {
            chart.createShape(
              { time: closeTime, price: parseFloat(currentPosition.exitPrice) },
              {
                shape: "arrow_down",
                text: "Exit",
                lock: true,
                disableSelection: true,
                disableSave: true,
                overrides: {
                  backgroundColor: parseFloat(currentPosition.profit) >= 0 ? '#22c55e' : '#ef4444',
                  color: parseFloat(currentPosition.profit) >= 0 ? '#22c55e' : '#ef4444',
                  textColor: isDarkMode ? '#ffffff' : '#000000',
                  fontsize: 14,
                  bold: true
                }
              }
            );
          }
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, [currentPosition, isDarkMode]);

  if (!positionDetails) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center">
          <button
            onClick={() => navigate('/')}
            className={`flex items-center space-x-2 ${
              isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Dashboard</span>
          </button>
        </div>
        <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-6 shadow-lg`}>
          <div className="text-red-500 text-center">
            Position not found
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6 flex items-center">
        <button
          onClick={() => navigate('/')}
          className={`flex items-center space-x-2 ${
            isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Dashboard</span>
        </button>
      </div>

      <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-6 shadow-lg`}>
        <div className="mb-6">
          <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Position Details
          </h2>
          <div className={`mt-2 grid grid-cols-2 gap-4 ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
            <div>
              <p>Symbol: {positionDetails.symbol}</p>
              <p>Side: <span className={positionDetails.side === 'LONG' ? 'text-green-500' : 'text-red-500'}>
                {positionDetails.side}
              </span></p>
              <p>Entry Price: ${positionDetails.entryPrice}</p>
              {!positionDetails.isActive && <p>Close Price: ${positionDetails.exitPrice}</p>}
            </div>
            <div>
              <p>PnL: <span className={parseFloat(positionDetails.profit) >= 0 ? 'text-green-500' : 'text-red-500'}>
                ${parseFloat(positionDetails.profit).toFixed(2)}
              </span></p>
              <p>Open Time: {positionDetails.openedAt}</p>
              {!positionDetails.isActive && <p>Close Time: {positionDetails.closedAt}</p>}
              {positionDetails.isActive && <p>Current Price: ${positionDetails.currentPrice}</p>}
            </div>
          </div>
        </div>

        <div ref={containerRef} id="tradingview-widget" className="rounded-lg overflow-hidden" />
      </div>
    </div>
  );
}

export default PositionChart;