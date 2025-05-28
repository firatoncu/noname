import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  TrendingUp,
  Shield,
  Database,
  FileText,
  Bell,
  Save,
  Plus,
  X,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Percent,
  Clock,
  BarChart3,
  Zap,
  Globe,
  Lock,
  Eye,
  EyeOff
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
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="flex items-center space-x-3 text-dark-text-primary">
          <div className="w-6 h-6 border-2 border-dark-accent-primary border-t-transparent rounded-full animate-spin"></div>
          <span>Loading configuration...</span>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="text-center text-dark-text-primary">
          <AlertTriangle className="w-12 h-12 text-dark-accent-error mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Failed to Load Configuration</h2>
          <button
            onClick={loadConfig}
            className="px-4 py-2 bg-dark-accent-primary hover:bg-dark-accent-secondary rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-10 animate-fade-in-up">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 animate-slide-in-left">
              <SettingsIcon className="w-8 h-8 text-dark-accent-primary" />
              <div>
                <h1 className="text-4xl font-bold text-dark-text-primary">Bot Configuration</h1>
                <p className="text-dark-text-muted text-lg">Manage your trading bot settings</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 animate-slide-in-right">
              <button
                onClick={saveConfig}
                disabled={saving || !hasChanges}
                className={`px-6 py-3 rounded-xl transition-all duration-300 flex items-center space-x-2 shadow-glow-sm hover:shadow-glow-md text-dark-text-primary font-medium ${
                  hasChanges
                    ? 'bg-dark-accent-primary hover:bg-dark-accent-secondary'
                    : 'bg-dark-bg-disabled cursor-not-allowed'
                }`}
              >
                <Save className={`w-4 h-4 ${saving ? 'animate-pulse' : ''}`} />
                <span>{saving ? 'Saving...' : 'Save Changes'}</span>
              </button>
            </div>
          </div>

          {/* Status Messages */}
          {message && (
            <div className={`mt-6 p-4 rounded-xl flex items-center space-x-2 border backdrop-blur-sm transition-all duration-300 ${
              message.type === 'success' 
                ? 'bg-dark-accent-success/20 text-dark-accent-success border-dark-accent-success/30' 
                : 'bg-dark-accent-error/20 text-dark-accent-error border-dark-accent-error/30'
            }`}>
              {message.type === 'success' ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                <AlertTriangle className="w-5 h-5" />
              )}
              <span>{message.text}</span>
              <button
                onClick={() => setMessage(null)}
                className="ml-auto text-dark-text-muted hover:text-dark-text-primary transition-colors"
              >
                ×
              </button>
            </div>
          )}

          {/* Changes Indicator */}
          {hasChanges && (
            <div className="mt-4 p-3 bg-dark-accent-warning/20 text-dark-accent-warning rounded-xl flex items-center space-x-2 border border-dark-accent-warning/30 backdrop-blur-sm">
              <AlertTriangle className="w-5 h-5" />
              <span>You have unsaved changes</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass">
              <h3 className="text-lg font-semibold mb-4 text-dark-text-primary">Configuration Sections</h3>
              <nav className="space-y-2">
                {configSections.map((section) => {
                  const Icon = section.icon;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full text-left p-3 rounded-xl transition-all duration-300 flex items-start space-x-3 ${
                        activeSection === section.id
                          ? 'bg-dark-accent-primary text-dark-text-primary shadow-glow-sm'
                          : 'hover:bg-dark-bg-hover text-dark-text-secondary hover:text-dark-text-primary'
                      }`}
                    >
                      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                      <div>
                        <div className="font-medium">{section.title}</div>
                        <div className={`text-xs mt-1 ${
                          activeSection === section.id
                            ? 'text-white'
                            : 'text-dark-text-disabled'
                        }`}>
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
            <div className="bg-dark-bg-secondary/80 backdrop-blur-sm rounded-2xl p-6 border border-dark-border-primary shadow-glass">
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
          <TrendingUp className="w-6 h-6 text-dark-accent-primary" />
          <span className="text-dark-text-primary">Trading Configuration</span>
        </h2>
        <div className="text-center text-dark-text-muted">
          <p>Loading trading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <TrendingUp className="w-6 h-6 text-dark-accent-primary" />
        <span className="text-dark-text-primary">Trading Configuration</span>
      </h2>

      {/* Basic Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Capital (USDT)</label>
          <input
            type="number"
            value={config.trading.capital || 0}
            onChange={(e) => updateConfig('trading.capital', parseFloat(e.target.value) || 0)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Leverage</label>
          <input
            type="number"
            min="1"
            max="125"
            value={config.trading.leverage || 1}
            onChange={(e) => updateConfig('trading.leverage', parseInt(e.target.value) || 1)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
      </div>

      {/* Margin Configuration */}
      {config.trading.margin && (
        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary">
          <h3 className="text-lg font-semibold mb-4 text-dark-text-primary">Margin Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Margin Mode</label>
              <select
                value={config.trading.margin.mode || 'fixed'}
                onChange={(e) => updateConfig('trading.margin.mode', e.target.value)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
              >
                <option value="fixed">Fixed Amount</option>
                <option value="full">Full Margin</option>
                <option value="percentage">Percentage</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Fixed Amount (USDT)</label>
              <input
                type="number"
                value={config.trading.margin.fixed_amount || 0}
                onChange={(e) => updateConfig('trading.margin.fixed_amount', parseFloat(e.target.value) || 0)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary disabled:opacity-50"
                disabled={config.trading.margin.mode !== 'fixed'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Percentage (%)</label>
              <input
                type="number"
                min="1"
                max="100"
                value={config.trading.margin.percentage || 50}
                onChange={(e) => updateConfig('trading.margin.percentage', parseFloat(e.target.value) || 50)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary disabled:opacity-50"
                disabled={config.trading.margin.mode !== 'percentage'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">User Response Timeout (seconds)</label>
              <input
                type="number"
                value={config.trading.margin.user_response_timeout || 30}
                onChange={(e) => updateConfig('trading.margin.user_response_timeout', parseInt(e.target.value) || 30)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
              />
            </div>
          </div>
          <div className="mt-4 space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.margin.ask_user_selection || false}
                onChange={(e) => updateConfig('trading.margin.ask_user_selection', e.target.checked)}
                className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
              />
              <span className="text-dark-text-primary">Ask user for margin selection at startup</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.margin.default_to_full_margin || false}
                onChange={(e) => updateConfig('trading.margin.default_to_full_margin', e.target.checked)}
                className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
              />
              <span className="text-dark-text-primary">Default to full margin on timeout</span>
            </label>
          </div>
        </div>
      )}

      {/* Trading Symbols */}
      <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-dark-text-primary">Trading Symbols</h3>
          <button
            onClick={addSymbol}
            className="px-3 py-1 bg-dark-accent-primary hover:bg-dark-accent-secondary rounded-lg text-sm transition-colors text-dark-text-primary font-medium"
          >
            Add Symbol
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {(config.trading.symbols || []).map((symbol) => (
            <div
              key={symbol}
              className="flex items-center space-x-2 bg-dark-bg-primary px-3 py-1 rounded-lg border border-dark-border-secondary"
            >
              <span className="text-dark-text-primary">{symbol}</span>
              <button
                onClick={() => removeSymbol(symbol)}
                className="text-dark-accent-error hover:text-red-300 transition-colors"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Strategy Settings */}
      {config.trading.strategy && (
        <div className="bg-dark-bg-tertiary/50 rounded-xl p-4 border border-dark-border-secondary">
          <h3 className="text-lg font-semibold mb-4 text-dark-text-primary">Strategy Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Strategy Name</label>
              <input
                type="text"
                value={config.trading.strategy.name || ''}
                onChange={(e) => updateConfig('trading.strategy.name', e.target.value)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Timeframe</label>
              <select
                value={config.trading.strategy.timeframe || '5m'}
                onChange={(e) => updateConfig('trading.strategy.timeframe', e.target.value)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
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
              <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Lookback Period</label>
              <input
                type="number"
                value={config.trading.strategy.lookback_period || 500}
                onChange={(e) => updateConfig('trading.strategy.lookback_period', parseInt(e.target.value) || 500)}
                className="w-full p-3 bg-dark-bg-primary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
              />
            </div>
          </div>
          <div className="mt-4 space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.strategy.enabled || false}
                onChange={(e) => updateConfig('trading.strategy.enabled', e.target.checked)}
                className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
              />
              <span className="text-dark-text-primary">Strategy Enabled</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.paper_trading || false}
                onChange={(e) => updateConfig('trading.paper_trading', e.target.checked)}
                className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
              />
              <span className="text-dark-text-primary">Paper Trading Mode</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.trading.auto_start || false}
                onChange={(e) => updateConfig('trading.auto_start', e.target.checked)}
                className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
              />
              <span className="text-dark-text-primary">Auto Start Trading</span>
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
          <Shield className="w-6 h-6 text-dark-accent-primary" />
          <span className="text-dark-text-primary">Risk Management</span>
        </h2>
        <div className="text-center text-dark-text-muted">
          <p>Loading risk management configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Shield className="w-6 h-6 text-dark-accent-primary" />
        <span className="text-dark-text-primary">Risk Management</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Max Position Size (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.max_position_size || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.max_position_size', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Max Daily Loss (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.max_daily_loss || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.max_daily_loss', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Max Drawdown (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.max_drawdown || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.max_drawdown', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Risk Per Trade (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.risk_per_trade || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.risk_per_trade', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Max Open Positions</label>
          <input
            type="number"
            min="1"
            max="20"
            value={config.trading.risk.max_open_positions || 5}
            onChange={(e) => updateConfig('trading.risk.max_open_positions', parseInt(e.target.value) || 5)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Stop Loss (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={(config.trading.risk.stop_loss_percentage || 0) * 100}
            onChange={(e) => updateConfig('trading.risk.stop_loss_percentage', (parseFloat(e.target.value) || 0) / 100)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Take Profit Ratio</label>
          <input
            type="number"
            min="0.1"
            max="10"
            step="0.1"
            value={config.trading.risk.take_profit_ratio || 2.0}
            onChange={(e) => updateConfig('trading.risk.take_profit_ratio', parseFloat(e.target.value) || 2.0)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
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
          <Globe className="w-6 h-6 text-dark-accent-primary" />
          <span className="text-dark-text-primary">Exchange Settings</span>
        </h2>
        <div className="text-center text-dark-text-muted">
          <p>Loading exchange configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Globe className="w-6 h-6 text-dark-accent-primary" />
        <span className="text-dark-text-primary">Exchange Settings</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Exchange Type</label>
          <input
            type="text"
            value={config.exchange.type || 'binance'}
            onChange={(e) => updateConfig('exchange.type', e.target.value)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
            readOnly
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Rate Limit (requests/min)</label>
          <input
            type="number"
            value={config.exchange.rate_limit || 1200}
            onChange={(e) => updateConfig('exchange.rate_limit', parseInt(e.target.value) || 1200)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Timeout (seconds)</label>
          <input
            type="number"
            value={config.exchange.timeout || 30}
            onChange={(e) => updateConfig('exchange.timeout', parseInt(e.target.value) || 30)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Retry Attempts</label>
          <input
            type="number"
            min="1"
            max="10"
            value={config.exchange.retry_attempts || 3}
            onChange={(e) => updateConfig('exchange.retry_attempts', parseInt(e.target.value) || 3)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
          />
        </div>
      </div>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.exchange.testnet || false}
            onChange={(e) => updateConfig('exchange.testnet', e.target.checked)}
            className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
          />
          <span className="text-dark-text-primary">Use Testnet</span>
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
          <Database className="w-6 h-6 text-dark-accent-primary" />
          <span className="text-dark-text-primary">Logging & Debug</span>
        </h2>
        <div className="text-center text-dark-text-muted">
          <p>Loading logging configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Database className="w-6 h-6 text-dark-accent-primary" />
        <span className="text-dark-text-primary">Logging & Debug</span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2 text-dark-text-secondary">Log Level</label>
          <select
            value={config.logging.level || 'INFO'}
            onChange={(e) => updateConfig('logging.level', e.target.value)}
            className="w-full p-3 bg-dark-bg-tertiary rounded-xl border border-dark-border-secondary focus:border-dark-accent-primary focus:outline-none focus:ring-2 focus:ring-dark-accent-primary/20 transition-all duration-300 text-dark-text-primary"
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
            className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
          />
          <span className="text-dark-text-primary">Console Output</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.logging.structured_logging || false}
            onChange={(e) => updateConfig('logging.structured_logging', e.target.checked)}
            className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
          />
          <span className="text-dark-text-primary">Structured Logging (JSON)</span>
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
          <Bell className="w-6 h-6 text-dark-accent-primary" />
          <span className="text-dark-text-primary">Notifications</span>
        </h2>
        <div className="text-center text-dark-text-muted">
          <p>Loading notifications configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold flex items-center space-x-2">
        <Bell className="w-6 h-6 text-dark-accent-primary" />
        <span className="text-dark-text-primary">Notifications</span>
      </h2>

      <div className="space-y-3">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={config.notifications.enabled || false}
            onChange={(e) => updateConfig('notifications.enabled', e.target.checked)}
            className="rounded bg-dark-bg-primary border-dark-border-secondary text-dark-accent-primary focus:ring-dark-accent-primary/20"
          />
          <span className="text-dark-text-primary">Enable Notifications</span>
        </label>
      </div>
    </div>
  );
};

export default Settings; 