import React, { useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface PositionState {
  symbol: string;
  positionAmt: string;
  notional: string;
  unRealizedProfit: string;
  entryPrice: string;
  markPrice: string;
  entryTime: string;
  side: 'LONG' | 'SHORT';
  isActive: boolean;
  profit: string;
  currentPrice: string;
  exitPrice?: string;
  closedAt?: string;
  takeProfitPrice?: string;
  stopLossPrice?: string;
}

function PositionChart() {
  const { isDarkMode } = useTheme();
  const location = useLocation();
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const widgetRef = useRef<any>(null);
  
  const position = location.state?.position as PositionState | undefined;

  useEffect(() => {
    if (!position || !containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (containerRef.current && window.TradingView) {
        try {
          widgetRef.current = new window.TradingView.widget({
            symbol: `BINANCE:${position.symbol}.P`,
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
            studies: [],
            disabled_features: ["use_localstorage_for_settings"],
            enabled_features: [],
            charts_storage_api_version: "1.1",
            client_id: "tradingview.com",
            user_id: "public_user",
            library_path: '/charting_library/',
            custom_css_url: '/css/tradingview.css'
          });

          // Wait for the widget to be ready
          let attempts = 0;
          const maxAttempts = 50; // 5 seconds maximum wait time
          const checkWidgetReady = setInterval(() => {
            attempts++;
            if (attempts > maxAttempts) {
              clearInterval(checkWidgetReady);
              console.error('Failed to initialize TradingView widget after maximum attempts');
              return;
            }

            try {
              if (widgetRef.current && widgetRef.current.chart && widgetRef.current.chart()) {
                clearInterval(checkWidgetReady);
                const chart = widgetRef.current.chart();
                
                // Add take profit line if it exists
                if (position.takeProfitPrice) {
                  chart.createShape(
                    { time: Math.floor(Date.now() / 1000), price: parseFloat(position.takeProfitPrice) },
                    {
                      shape: "horizontal_line",
                      lock: true,
                      disableSelection: true,
                      disableSave: true,
                      overrides: {
                        lineColor: "#22c55e",
                        lineWidth: 2,
                        lineStyle: 0, // Solid line
                      }
                    }
                  );
                }

                // Add stop loss line if it exists
                if (position.stopLossPrice) {
                  chart.createShape(
                    { time: Math.floor(Date.now() / 1000), price: parseFloat(position.stopLossPrice) },
                    {
                      shape: "horizontal_line",
                      lock: true,
                      disableSelection: true,
                      disableSave: true,
                      overrides: {
                        lineColor: "#ef4444",
                        lineWidth: 2,
                        lineStyle: 0, // Solid line
                      }
                    }
                  );
                }
              }
            } catch (error) {
              console.error('Error while adding lines:', error);
              clearInterval(checkWidgetReady);
            }
          }, 100);

          // Clean up interval if component unmounts
          return () => {
            clearInterval(checkWidgetReady);
          };
        } catch (error) {
          console.error('Error initializing TradingView widget:', error);
        }
      }
    };
    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, [position]);

  if (!position) {
    return (
      <div className="min-h-screen bg-dark-bg-primary">
        <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
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
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
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
          <div className="mb-4">
            <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              {position.symbol} Chart
            </h2>
          </div>

          <div ref={containerRef} id="tradingview-widget" className="rounded-lg overflow-hidden" />
        </div>
      </div>
    </div>
  );
}

export default PositionChart;