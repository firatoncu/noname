import React, { useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

function TradingConditionChart() {
  const { symbol } = useParams<{ symbol: string }>();
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const widgetRef = useRef<any>(null);

  useEffect(() => {
    if (!symbol || !containerRef.current) return;

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (containerRef.current && window.TradingView) {
        widgetRef.current = new window.TradingView.widget({
          symbol: `BINANCE:${symbol}.P`,
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
          disabled_features: ["use_localstorage_for_settings"],
          enabled_features: ["study_templates"],
          charts_storage_api_version: "1.1",
          client_id: "tradingview.com",
          user_id: "public_user"
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, [symbol]);

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => navigate('/trading-conditions')}
            className="flex items-center space-x-2 text-gray-300 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Trading Conditions</span>
          </button>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-white">
              {symbol} Chart
            </h2>
          </div>

          <div ref={containerRef} id="tradingview-widget" className="rounded-lg overflow-hidden" />
        </div>
      </div>
    </div>
  );
}

export default TradingConditionChart; 