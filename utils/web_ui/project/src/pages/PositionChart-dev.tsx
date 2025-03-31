import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useOutletContext, useLocation } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { HistoricalPosition } from '../types';
import { createChart, CrosshairMode } from 'lightweight-charts';
import { MACD } from 'technicalindicators';

const API_BASE_URL = 'http://localhost:8000/api';

function PositionChart() {
  const { isDarkMode } = useOutletContext<{ isDarkMode: boolean }>();
  const location = useLocation();
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const widgetRef = useRef<any>(null);
  const mainChartRef = useRef<HTMLDivElement>(null);
  const macdChartRef = useRef<HTMLDivElement>(null);
  
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
    if (!currentPosition || !mainChartRef.current || !macdChartRef.current) return;

    const fetchDataAndCreateChart = async () => {
      try {
        // Parse the date string (YYYY-MM-DD HH:mm:ss)
        const parseCustomDate = (dateStr: string) => {
          const [datePart, timePart] = dateStr.split(' ');
          const [year, month, day] = datePart.split('-');
          const [hours, minutes, seconds] = timePart.split(':');
          
          return Date.UTC(
            parseInt(year),
            parseInt(month) - 1,
            parseInt(day),
            parseInt(hours),
            parseInt(minutes),
            parseInt(seconds)
          ) / 1000;
        };

        const openTime = parseCustomDate(positionDetails.openedAt);
        const closeTime = currentPosition.isActive 
          ? Math.floor(Date.now() / 1000)
          : parseCustomDate(positionDetails.closedAt);

        // Calculate time range and padding
        const timeRange = closeTime - openTime;
        const paddingTime = Math.max(timeRange * 0.1, 3600); // At least 1 hour padding
        const fromTime = (openTime - paddingTime) * 1000; // Binance expects milliseconds
        const toTime = (closeTime + paddingTime) * 1000;

        // Fetch candlestick data from Binance API
        const response = await fetch(
          `https://api.binance.com/api/v3/klines?symbol=${currentPosition.symbol}&interval=1m&startTime=${fromTime}&endTime=${toTime}`
        );
        const data = await response.json();

        // Process candlestick data for lightweight charts
        const candlestickData = data.map((d: any) => ({
          time: d[0] / 1000, // Convert to seconds for lightweight charts
          open: parseFloat(d[1]),
          high: parseFloat(d[2]),
          low: parseFloat(d[3]),
          close: parseFloat(d[4]),
        }));

        // Calculate MACD
        const closePrices = candlestickData.map(d => d.close);
        const macdInput = {
          values: closePrices,
          fastPeriod: 12,
          slowPeriod: 26,
          signalPeriod: 9,
          SimpleMAOscillator: false,
          SimpleMASignal: false,
        };
        const macdResult = MACD.calculate(macdInput);

        // Create main chart for candlesticks
        const mainChart = createChart(mainChartRef.current, {
          width: mainChartRef.current.clientWidth,
          height: 400,
          layout: {
            background :
            {Color: "black"},
            textColor: isDarkMode ? '#ffffff' : '#000000',
          },
          grid: {
            vertLines: { color: isDarkMode ? '#374151' : '#e5e7eb' },
            horzLines: { color: isDarkMode ? '#374151' : '#e5e7eb' },
          },
          crosshair: { mode: CrosshairMode.Normal },
          timeScale: { timeVisible: true, secondsVisible: false },
        });

        const candlestickSeries = mainChart.addCandlestickSeries({
          upColor: '#22c55e',
          downColor: '#ef4444',
          borderUpColor: '#22c55e',
          borderDownColor: '#ef4444',
          wickUpColor: '#22c55e',
          wickDownColor: '#ef4444',
        });
        candlestickSeries.setData(candlestickData);

        // Add entry and exit markers
        const markers = [];
        markers.push({
          time: openTime,
          position: 'belowBar',
          color: currentPosition.side === 'LONG' ? '#22c55e' : '#ef4444',
          shape: 'arrowUp',
          text: 'Entry',
        });
        if (!currentPosition.isActive) {
          markers.push({
            time: closeTime,
            position: 'aboveBar',
            color: parseFloat(currentPosition.profit) >= 0 ? '#22c55e' : '#ef4444',
            shape: 'arrowDown',
            text: 'Exit',
          });
        }
        candlestickSeries.setMarkers(markers);

    

        // Set visible range for both charts
        const visibleRange = { from: openTime - paddingTime, to: closeTime + paddingTime };
        mainChart.timeScale().setVisibleRange(visibleRange);

        mainChart.timeScale().fitContent();
        // Store chart instances for cleanup
        widgetRef.current = { mainChart };

      } catch (error) {
        console.error('Error fetching data or creating chart:', error);
      }
    };

    fetchDataAndCreateChart();

    return () => {
      if (widgetRef.current) {
        widgetRef.current.mainChart.remove();
        widgetRef.current.macdChart.remove();
      }
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

        <div className="flex flex-col gap-2">
          <div ref={mainChartRef} className="rounded-lg overflow-hidden" style={{ height: '400px' }} />
          <div ref={macdChartRef} className="rounded-lg overflow-hidden" style={{ height: '200px' }} />
        </div>
      </div>
    </div>
  );
}

export default PositionChart;