import React, { useState, useEffect } from 'react';
import { 
  Save, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Settings as SettingsIcon,
  Database,
  Shield,
  TrendingUp,
  Zap,
  Globe,
  Bell
} from 'lucide-react';

interface ConfigSection {
  id: string;
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

interface ConfigData {
  trading: {
    capital: number;
    leverage: number;
    margin: {
      mode: string;
      fixed_amount: number;
      percentage: number;
      ask_user_selection: boolean;
      default_to_full_margin: boolean;
      user_response_timeout: number;
    };
    symbols: string[];
    paper_trading: boolean;
    auto_start: boolean;
    strategy: {
      name: string;
      type: string;
      enabled: boolean;
      timeframe: string;
      lookback_period: number;
    };
    risk: {
      max_position_size: number;
      max_daily_loss: number;
      max_drawdown: number;
      risk_per_trade: number;
      max_open_positions: number;
      stop_loss_percentage: number;
      take_profit_ratio: number;
    };
  };
  exchange: {
    type: string;
    testnet: boolean;
    rate_limit: number;
    timeout: number;
    retry_attempts: number;
  };
  logging: {
    level: string;
    console_output: boolean;
    structured_logging: boolean;
  };
  notifications: {
    enabled: boolean;
  };
}

const configSections: ConfigSection[] = [
  {
    id: 'trading',
    title: 'Trading Configuration',
    icon: TrendingUp,
    description: 'Core trading settings, margin, and strategy parameters'
  },
  {
    id: 'risk',
    title: 'Risk Management',
    icon: Shield,
    description: 'Position sizing, stop loss, and risk limits'
  },
  {
    id: 'exchange',
    title: 'Exchange Settings',
    icon: Globe,
    description: 'API configuration and connection settings'
  },
  {
    id: 'logging',
    title: 'Logging & Debug',
    icon: Database,
    description: 'Log levels and output configuration'
  },
  {
    id: 'notifications',
    title: 'Notifications',
    icon: Bell,
    description: 'Alert and notification settings'
  }
];

const Settings: React.FC = () => {
  const [activeSection, setActiveSection] = useState('trading');
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [originalConfig, setOriginalConfig] = useState<ConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('/api/config');
      if (!response.ok) {
        throw new Error(`Failed to load configuration: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate that all required fields are present
      if (!data.trading || !data.exchange || !data.logging || !data.notifications) {
        throw new Error('Configuration is missing required sections');
      }
      
      // Validate required trading fields
      const requiredTradingFields = ['capital', 'leverage', 'symbols', 'paper_trading', 'auto_start', 'strategy', 'risk'];
      const missingTrading = requiredTradingFields.filter(field => !(field in data.trading));
      if (missingTrading.length > 0) {
        throw new Error(`Missing required trading fields: ${missingTrading.join(', ')}`);
      }
      
      // Validate required exchange fields
      const requiredExchangeFields = ['type', 'testnet', 'rate_limit', 'timeout', 'retry_attempts'];
      const missingExchange = requiredExchangeFields.filter(field => !(field in data.exchange));
      if (missingExchange.length > 0) {
        throw new Error(`Missing required exchange fields: ${missingExchange.join(', ')}`);
      }
      
      // Validate required logging fields
      const requiredLoggingFields = ['level', 'console_output', 'structured_logging'];
      const missingLogging = requiredLoggingFields.filter(field => !(field in data.logging));
      if (missingLogging.length > 0) {
        throw new Error(`Missing required logging fields: ${missingLogging.join(', ')}`);
      }
      
      // Use the exact config data without any defaults
      const normalizedConfig: ConfigData = {
        trading: {
          capital: data.trading.capital,
          leverage: data.trading.leverage,
          margin: data.trading.margin || {},
          symbols: data.trading.symbols,
          paper_trading: data.trading.paper_trading,
          auto_start: data.trading.auto_start,
          strategy: data.trading.strategy,
          risk: data.trading.risk,
        },
        exchange: {
          type: data.exchange.type,
          testnet: data.exchange.testnet,
          rate_limit: data.exchange.rate_limit,
          timeout: data.exchange.timeout,
          retry_attempts: data.exchange.retry_attempts,
        },
        logging: {
          level: data.logging.level,
          console_output: data.logging.console_output,
          structured_logging: data.logging.structured_logging,
        },
        notifications: {
          enabled: data.notifications.enabled,
        },
      };
      
      setConfig(normalizedConfig);
      setOriginalConfig(normalizedConfig);
    } catch (err) {
      console.error('Failed to load config:', err);
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    try {
      setSaving(true);
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuration saved successfully!' });
        setHasChanges(false);
        
        // Refresh trading conditions after config save
        try {
          const refreshResponse = await fetch('/api/refresh-trading-conditions', {
            method: 'POST',
          });
          if (refreshResponse.ok) {
            const refreshResult = await refreshResponse.json();
            console.log('Trading conditions refreshed:', refreshResult);
          }
        } catch (refreshError) {
          console.warn('Failed to refresh trading conditions:', refreshError);
        }
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (path: string, value: any) => {
    if (!config) return;

    const newConfig = { ...config };
    const keys = path.split('.');
    let current: any = newConfig;

    for (let i = 0; i < keys.length - 1; i++) {
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;

    setConfig(newConfig);
    setHasChanges(true);
  };

  const addSymbol = () => {
    if (!config) return;
    const newSymbol = prompt('Enter symbol (e.g., BTCUSDT):');
    if (newSymbol && !config.trading.symbols.includes(newSymbol.toUpperCase())) {
      updateConfig('trading.symbols', [...config.trading.symbols, newSymbol.toUpperCase()]);
    }
  };

  const removeSymbol = (symbol: string) => {
    if (!config) return;
    updateConfig('trading.symbols', config.trading.symbols.filter(s => s !== symbol));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="flex items-center space-x-3 text-white">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span>Loading configuration...</span>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Failed to Load Configuration</h2>
          <button
            onClick={loadConfig}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <SettingsIcon className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-3xl font-bold">Bot Configuration</h1>
                <p className="text-gray-400">Manage your trading bot settings</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={loadConfig}
                disabled={loading}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors flex items-center space-x-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Reload</span>
              </button>
              <button
                onClick={saveConfig}
                disabled={saving || !hasChanges}
                className={`px-6 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                  hasChanges
                    ? 'bg-blue-600 hover:bg-blue-700'
                    : 'bg-gray-600 cursor-not-allowed'
                }`}
              >
                <Save className={`w-4 h-4 ${saving ? 'animate-pulse' : ''}`} />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>
          </div>

          {/* Status Messages */}
          {message && (
            <div className={`mt-4 p-4 rounded-lg flex items-center space-x-2 ${
              message.type === 'success' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
            }`}>
              {message.type === 'success' ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                <AlertTriangle className="w-5 h-5" />
              )}
              <span>{message.text}</span>
              <button
                onClick={() => setMessage(null)}
                className="ml-auto text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>
          )}

          {/* Changes Indicator */}
          {hasChanges && (
            <div className="mt-4 p-3 bg-yellow-900 text-yellow-300 rounded-lg flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5" />
              <span>You have unsaved changes</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4">Configuration Sections</h3>
              <nav className="space-y-2">
                {configSections.map((section) => {
                  const Icon = section.icon;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full text-left p-3 rounded-lg transition-colors flex items-start space-x-3 ${
                        activeSection === section.id
                          ? 'bg-blue-600 text-white'
                          : 'hover:bg-gray-700 text-gray-300'
                      }`}
                    >
                      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                      <div>
                        <div className="font-medium">{section.title}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {section.description}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-gray-800 rounded-lg p-6">
              {activeSection === 'trading' && (
                <TradingSection config={config} updateConfig={updateConfig} addSymbol={addSymbol} removeSymbol={removeSymbol} />
              )}
              {activeSection === 'risk' && (
                <RiskSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'exchange' && (
                <ExchangeSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'logging' && (
                <LoggingSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'notifications' && (
                <NotificationsSection config={config} updateConfig={updateConfig} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Trading Section Component
const TradingSection: React.FC<{
  config: ConfigData;
  updateConfig: (path: string, value: any) => void;
  addSymbol: () => void;
  removeSymbol: (symbol: string) => void;
}> = ({ config, updateConfig, addSymbol, removeSymbol }) => {
  
  // Safety check to ensure config and nested properties exist
  if (!config || !config.trading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <TrendingUp className="w-6 h-6 text-blue-400" />
          <span>Trading Configuration</span>
        </h2>
        <div className="text-center text-gray-400">
          <p>Loading trading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        <span>Trading Configuration</span>
      </h2>

      {/* Basic Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Capital (USDT)</label>
          <input
            type="number"
            value={config.trading.capital || 0}
            onChange={(e) => updateConfig('trading.capital', parseFloat(e.target.value) || 0)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Leverage</label>
          <input
            type="number"
            min="1"
            max="125"
            value={config.trading.leverage || 1}
            onChange={(e) => updateConfig('trading.leverage', parseInt(e.target.value) || 1)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Margin Configuration */}
      {config.trading.margin && (
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Margin Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Margin Mode</label>
              <select
                value={config.trading.margin.mode || 'fixed'}
                onChange={(e) => updateConfig('trading.margin.mode', e.target.value)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
              >
                <option value="fixed">Fixed Amount</option>
                <option value="full">Full Margin</option>
                <option value="percentage">Percentage</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Fixed Amount (USDT)</label>
              <input
                type="number"
                value={config.trading.margin.fixed_amount || 0}
                onChange={(e) => updateConfig('trading.margin.fixed_amount', parseFloat(e.target.value) || 0)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
                disabled={config.trading.margin.mode !== 'fixed'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Percentage (%)</label>
              <input
                type="number"
                min="1"
                max="100"
                value={config.trading.margin.percentage || 50}
                onChange={(e) => updateConfig('trading.margin.percentage', parseFloat(e.target.value) || 50)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
                disabled={config.trading.margin.mode !== 'percentage'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">User Response Timeout (seconds)</label>
              <input
                type="number"
                value={config.trading.margin.user_response_timeout || 30}
                onChange={(e) => updateConfig('trading.margin.user_response_timeout', parseInt(e.target.value) || 30)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="mt-4 space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.margin.ask_user_selection || false}
                onChange={(e) => updateConfig('trading.margin.ask_user_selection', e.target.checked)}
                className="rounded bg-gray-600 border-gray-500"
              />
              <span>Ask user for margin selection at startup</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.margin.default_to_full_margin || false}
                onChange={(e) => updateConfig('trading.margin.default_to_full_margin', e.target.checked)}
                className="rounded bg-gray-600 border-gray-500"
              />
              <span>Default to full margin on timeout</span>
            </label>
          </div>
        </div>
      )}

      {/* Trading Symbols */}
      <div className="bg-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Trading Symbols</h3>
          <button
            onClick={addSymbol}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
          >
            Add Symbol
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(config.trading.symbols || []).map((symbol) => (
            <div
              key={symbol}
              className="flex items-center space-x-2 bg-gray-600 px-3 py-1 rounded-lg"
            >
              <span>{symbol}</span>
              <button
                onClick={() => removeSymbol(symbol)}
                className="text-red-400 hover:text-red-300"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Settings */}
      {config.trading.strategy && (
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold mb-4">Strategy Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Strategy Name</label>
              <input
                type="text"
                value={config.trading.strategy.name || ''}
                onChange={(e) => updateConfig('trading.strategy.name', e.target.value)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Timeframe</label>
              <select
                value={config.trading.strategy.timeframe || '5m'}
                onChange={(e) => updateConfig('trading.strategy.timeframe', e.target.value)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
              >
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Lookback Period</label>
              <input
                type="number"
                value={config.trading.strategy.lookback_period || 500}
                onChange={(e) => updateConfig('trading.strategy.lookback_period', parseInt(e.target.value) || 500)}
                className="w-full p-3 bg-gray-600 rounded-lg border border-gray-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="mt-4 space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.strategy.enabled || false}
                onChange={(e) => updateConfig('trading.strategy.enabled', e.target.checked)}
                className="rounded bg-gray-600 border-gray-500"
              />
              <span>Strategy Enabled</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.paper_trading || false}
                onChange={(e) => updateConfig('trading.paper_trading', e.target.checked)}
                className="rounded bg-gray-600 border-gray-500"
              />
              <span>Paper Trading Mode</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.auto_start || false}
                onChange={(e) => updateConfig('trading.auto_start', e.target.checked)}
                className="rounded bg-gray-600 border-gray-500"
              />
              <span>Auto Start Trading</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
};

// Risk Section Component
const RiskSection: React.FC<{
  config: ConfigData;
  updateConfig: (path: string, value: any) => void;
}> = ({ config, updateConfig }) => {
  
  // Safety check to ensure config and nested properties exist
  if (!config || !config.trading || !config.trading.risk) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <Shield className="w-6 h-6 text-blue-400" />
          <span>Risk Management</span>
        </h2>
        <div className="text-center text-gray-400">
          <p>Loading risk management configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Shield className="w-6 h-6 text-blue-400" />
        <span>Risk Management</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Max Position Size (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.max_position_size || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.max_position_size', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Daily Loss (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.max_daily_loss || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.max_daily_loss', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Drawdown (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.max_drawdown || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.max_drawdown', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Risk Per Trade (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.risk_per_trade || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.risk_per_trade', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Max Open Positions</label>
          <input
            type="number"
            min="1"
            max="20"
            value={config.trading.risk.max_open_positions || 5}
            onChange={(e) => updateConfig('trading.risk.max_open_positions', parseInt(e.target.value) || 5)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Stop Loss (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.stop_loss_percentage || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.stop_loss_percentage', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Take Profit Ratio</label>
          <input
            type="number"
            min="0.1"
            max="10"
            step="0.1"
            value={config.trading.risk.take_profit_ratio || 2.0}
            onChange={(e) => updateConfig('trading.risk.take_profit_ratio', parseFloat(e.target.value) || 2.0)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>
    </div>
  );
};

// Exchange Section Component
const ExchangeSection: React.FC<{
  config: ConfigData;
  updateConfig: (path: string, value: any) => void;
}> = ({ config, updateConfig }) => {
  
  if (!config || !config.exchange) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <Globe className="w-6 h-6 text-blue-400" />
          <span>Exchange Settings</span>
        </h2>
        <div className="text-center text-gray-400">
          <p>Loading exchange configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Globe className="w-6 h-6 text-blue-400" />
        <span>Exchange Settings</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Exchange Type</label>
          <input
            type="text"
            value={config.exchange.type || 'binance'}
            onChange={(e) => updateConfig('exchange.type', e.target.value)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            readOnly
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Rate Limit (requests/min)</label>
          <input
            type="number"
            value={config.exchange.rate_limit || 1200}
            onChange={(e) => updateConfig('exchange.rate_limit', parseInt(e.target.value) || 1200)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Timeout (seconds)</label>
          <input
            type="number"
            value={config.exchange.timeout || 30}
            onChange={(e) => updateConfig('exchange.timeout', parseInt(e.target.value) || 30)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Retry Attempts</label>
          <input
            type="number"
            min="1"
            max="10"
            value={config.exchange.retry_attempts || 3}
            onChange={(e) => updateConfig('exchange.retry_attempts', parseInt(e.target.value) || 3)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.exchange.testnet || false}
            onChange={(e) => updateConfig('exchange.testnet', e.target.checked)}
            className="rounded bg-gray-600 border-gray-500"
          />
          <span>Use Testnet</span>
        </label>
      </div>
    </div>
  );
};

// Logging Section Component
const LoggingSection: React.FC<{
  config: ConfigData;
  updateConfig: (path: string, value: any) => void;
}> = ({ config, updateConfig }) => {
  
  if (!config || !config.logging) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <Database className="w-6 h-6 text-blue-400" />
          <span>Logging & Debug</span>
        </h2>
        <div className="text-center text-gray-400">
          <p>Loading logging configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Database className="w-6 h-6 text-blue-400" />
        <span>Logging & Debug</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Log Level</label>
          <select
            value={config.logging.level || 'INFO'}
            onChange={(e) => updateConfig('logging.level', e.target.value)}
            className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.logging.console_output || false}
            onChange={(e) => updateConfig('logging.console_output', e.target.checked)}
            className="rounded bg-gray-600 border-gray-500"
          />
          <span>Console Output</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.logging.structured_logging || false}
            onChange={(e) => updateConfig('logging.structured_logging', e.target.checked)}
            className="rounded bg-gray-600 border-gray-500"
          />
          <span>Structured Logging (JSON)</span>
        </label>
      </div>
    </div>
  );
};

// Notifications Section Component
const NotificationsSection: React.FC<{
  config: ConfigData;
  updateConfig: (path: string, value: any) => void;
}> = ({ config, updateConfig }) => {
  
  if (!config || !config.notifications) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <Bell className="w-6 h-6 text-blue-400" />
          <span>Notifications</span>
        </h2>
        <div className="text-center text-gray-400">
          <p>Loading notifications configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Bell className="w-6 h-6 text-blue-400" />
        <span>Notifications</span>
      </h2>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.notifications.enabled || false}
            onChange={(e) => updateConfig('notifications.enabled', e.target.checked)}
            className="rounded bg-gray-600 border-gray-500"
          />
          <span>Enable Notifications</span>
        </label>
      </div>
    </div>
  );
};

export default Settings; 