import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, AlertCircle, Settings, TrendingUp, Shield, DollarSign, Zap } from 'lucide-react';

interface ConfigFormData {
  // Trading Configuration
  symbols: string[];
  capital_tbu: number;
  leverage: number;
  max_open_positions: number;
  strategy_name: string;
  
  // API Keys
  api_key: string;
  api_secret: string;
  
  // Exchange Settings
  testnet: boolean;
  
  // Risk Management
  stop_loss_percentage: number;
  take_profit_ratio: number;
  max_daily_loss: number;
  
  // Database
  db_status: string;
}

const SUPPORTED_STRATEGIES = ["Bollinger Bands & RSI", "MACD & Fibonacci"];
const POPULAR_SYMBOLS = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "SOLUSDT", "DOTUSDT", "LINKUSDT", "AVAXUSDT"];

const ConfigurationSetup: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState<ConfigFormData>({
    symbols: ["BTCUSDT"],
    capital_tbu: 100,
    leverage: 10,
    max_open_positions: 3,
    strategy_name: "Bollinger Bands & RSI",
    api_key: "",
    api_secret: "",
    testnet: true,
    stop_loss_percentage: 2.0,
    take_profit_ratio: 2.0,
    max_daily_loss: 5.0,
    db_status: "enabled"
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    // Check if we're coming from a config error
    const urlParams = new URLSearchParams(window.location.search);
    const reason = urlParams.get('reason');
    if (reason === 'missing') {
      setError('Configuration file not found. Please set up your trading bot configuration.');
    } else if (reason === 'invalid') {
      setError('Configuration file is invalid or corrupted. Please reconfigure your trading bot.');
    }
  }, []);

  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};
    
    switch (step) {
      case 1: // API Keys
        if (!formData.api_key.trim()) {
          errors.api_key = "API Key is required";
        } else if (formData.api_key.length < 10) {
          errors.api_key = "API Key appears to be too short";
        }
        
        if (!formData.api_secret.trim()) {
          errors.api_secret = "API Secret is required";
        } else if (formData.api_secret.length < 10) {
          errors.api_secret = "API Secret appears to be too short";
        }
        break;
        
      case 2: // Trading Settings
        if (formData.symbols.length === 0) {
          errors.symbols = "At least one trading symbol is required";
        }
        
        if (formData.capital_tbu <= 0 && formData.capital_tbu !== -999) {
          errors.capital_tbu = "Capital must be positive or -999 for full balance";
        }
        
        if (formData.leverage < 1 || formData.leverage > 125) {
          errors.leverage = "Leverage must be between 1 and 125";
        }
        
        if (formData.max_open_positions < 1 || formData.max_open_positions > 10) {
          errors.max_open_positions = "Max open positions must be between 1 and 10";
        }
        break;
        
      case 3: // Risk Management
        if (formData.stop_loss_percentage <= 0 || formData.stop_loss_percentage > 10) {
          errors.stop_loss_percentage = "Stop loss must be between 0.1% and 10%";
        }
        
        if (formData.take_profit_ratio <= 0 || formData.take_profit_ratio > 10) {
          errors.take_profit_ratio = "Take profit ratio must be between 0.1 and 10";
        }
        
        if (formData.max_daily_loss <= 0 || formData.max_daily_loss > 50) {
          errors.max_daily_loss = "Max daily loss must be between 0.1% and 50%";
        }
        break;
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSymbolToggle = (symbol: string) => {
    setFormData(prev => ({
      ...prev,
      symbols: prev.symbols.includes(symbol)
        ? prev.symbols.filter(s => s !== symbol)
        : [...prev.symbols, symbol]
    }));
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Prepare configuration data in the expected format
      const configData = {
        symbols: {
          symbols: formData.symbols,
          max_open_positions: formData.max_open_positions,
          leverage: formData.leverage
        },
        capital_tbu: formData.capital_tbu,
        strategy_name: formData.strategy_name,
        api_keys: {
          api_key: formData.api_key,
          api_secret: formData.api_secret
        },
        exchange: {
          type: "binance",
          testnet: formData.testnet,
          rate_limit: 1200,
          timeout: 30,
          retry_attempts: 3
        },
        risk_management: {
          stop_loss_percentage: formData.stop_loss_percentage,
          take_profit_ratio: formData.take_profit_ratio,
          max_daily_loss: formData.max_daily_loss
        },
        db_status: formData.db_status,
        logging: {
          level: "INFO",
          console_output: true,
          structured_logging: true
        },
        notifications: {
          enabled: false
        }
      };

      const response = await fetch('/api/config/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save configuration');
      }

      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <Shield className="w-16 h-16 text-blue-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">API Credentials</h2>
              <p className="text-gray-400">Enter your Binance API credentials to connect your trading account</p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  API Key
                </label>
                <input
                  type="text"
                  value={formData.api_key}
                  onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your Binance API key"
                />
                {validationErrors.api_key && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.api_key}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  API Secret
                </label>
                <input
                  type="password"
                  value={formData.api_secret}
                  onChange={(e) => setFormData(prev => ({ ...prev, api_secret: e.target.value }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your Binance API secret"
                />
                {validationErrors.api_secret && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.api_secret}</p>
                )}
              </div>
              
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="testnet"
                  checked={formData.testnet}
                  onChange={(e) => setFormData(prev => ({ ...prev, testnet: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="testnet" className="text-sm text-gray-300">
                  Use Testnet (Recommended for first-time setup)
                </label>
              </div>
            </div>
            
            <div className="bg-yellow-900/20 border border-yellow-600/30 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
                <div>
                  <h4 className="text-yellow-500 font-medium">Security Notice</h4>
                  <p className="text-yellow-200 text-sm mt-1">
                    Your API credentials will be encrypted and stored securely. Make sure your API key has futures trading permissions enabled.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
        
      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <TrendingUp className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Trading Configuration</h2>
              <p className="text-gray-400">Configure your trading parameters and strategy</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Trading Capital (USDT)
                </label>
                <input
                  type="number"
                  value={formData.capital_tbu}
                  onChange={(e) => setFormData(prev => ({ ...prev, capital_tbu: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="100"
                />
                <p className="text-gray-500 text-xs mt-1">Use -999 to use full account balance</p>
                {validationErrors.capital_tbu && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.capital_tbu}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Leverage
                </label>
                <input
                  type="number"
                  min="1"
                  max="125"
                  value={formData.leverage}
                  onChange={(e) => setFormData(prev => ({ ...prev, leverage: parseInt(e.target.value) || 1 }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {validationErrors.leverage && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.leverage}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Open Positions
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.max_open_positions}
                  onChange={(e) => setFormData(prev => ({ ...prev, max_open_positions: parseInt(e.target.value) || 1 }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {validationErrors.max_open_positions && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.max_open_positions}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Trading Strategy
                </label>
                <select
                  value={formData.strategy_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, strategy_name: e.target.value }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {SUPPORTED_STRATEGIES.map(strategy => (
                    <option key={strategy} value={strategy}>{strategy}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Trading Symbols
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {POPULAR_SYMBOLS.map(symbol => (
                  <button
                    key={symbol}
                    type="button"
                    onClick={() => handleSymbolToggle(symbol)}
                    className={`px-4 py-2 rounded-lg border transition-colors ${
                      formData.symbols.includes(symbol)
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-gray-800 border-gray-600 text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    {symbol}
                  </button>
                ))}
              </div>
              {validationErrors.symbols && (
                <p className="text-red-400 text-sm mt-2">{validationErrors.symbols}</p>
              )}
            </div>
          </div>
        );
        
      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Risk Management</h2>
              <p className="text-gray-400">Configure risk parameters to protect your capital</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Stop Loss (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10"
                  value={formData.stop_loss_percentage}
                  onChange={(e) => setFormData(prev => ({ ...prev, stop_loss_percentage: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {validationErrors.stop_loss_percentage && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.stop_loss_percentage}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Take Profit Ratio
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="10"
                  value={formData.take_profit_ratio}
                  onChange={(e) => setFormData(prev => ({ ...prev, take_profit_ratio: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {validationErrors.take_profit_ratio && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.take_profit_ratio}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Daily Loss (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0.1"
                  max="50"
                  value={formData.max_daily_loss}
                  onChange={(e) => setFormData(prev => ({ ...prev, max_daily_loss: parseFloat(e.target.value) || 0 }))}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {validationErrors.max_daily_loss && (
                  <p className="text-red-400 text-sm mt-1">{validationErrors.max_daily_loss}</p>
                )}
              </div>
            </div>
            
            <div className="bg-red-900/20 border border-red-600/30 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                <div>
                  <h4 className="text-red-500 font-medium">Risk Warning</h4>
                  <p className="text-red-200 text-sm mt-1">
                    Trading cryptocurrencies involves substantial risk. Never trade with money you cannot afford to lose. 
                    Start with small amounts and testnet to familiarize yourself with the system.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
        
      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Review & Confirm</h2>
              <p className="text-gray-400">Review your configuration before saving</p>
            </div>
            
            <div className="space-y-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Configuration Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Trading Symbols:</span>
                    <span className="text-white ml-2">{formData.symbols.join(', ')}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Capital:</span>
                    <span className="text-white ml-2">
                      {formData.capital_tbu === -999 ? 'Full Balance' : `${formData.capital_tbu} USDT`}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Leverage:</span>
                    <span className="text-white ml-2">{formData.leverage}x</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Max Positions:</span>
                    <span className="text-white ml-2">{formData.max_open_positions}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Strategy:</span>
                    <span className="text-white ml-2">{formData.strategy_name}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Environment:</span>
                    <span className="text-white ml-2">{formData.testnet ? 'Testnet' : 'Live Trading'}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Stop Loss:</span>
                    <span className="text-white ml-2">{formData.stop_loss_percentage}%</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Take Profit Ratio:</span>
                    <span className="text-white ml-2">{formData.take_profit_ratio}x</span>
                  </div>
                </div>
              </div>
              
              {success && (
                <div className="bg-green-900/20 border border-green-600/30 rounded-lg p-4">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    <div>
                      <h4 className="text-green-500 font-medium">Configuration Saved Successfully!</h4>
                      <p className="text-green-200 text-sm mt-1">
                        Redirecting to dashboard...
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="text-center">
          <CheckCircle className="w-24 h-24 text-green-500 mx-auto mb-6" />
          <h1 className="text-3xl font-bold text-white mb-4">Setup Complete!</h1>
          <p className="text-gray-400 mb-6">Your trading bot has been configured successfully.</p>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg-primary">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <Settings className="w-12 h-12 text-blue-500 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-white mb-2">Trading Bot Setup</h1>
            <p className="text-gray-400">Configure your automated trading bot in a few simple steps</p>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              {[1, 2, 3, 4].map((step) => (
                <div
                  key={step}
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    step <= currentStep
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'border-gray-600 text-gray-400'
                  }`}
                >
                  {step < currentStep ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : (
                    <span className="text-sm font-medium">{step}</span>
                  )}
                </div>
              ))}
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(currentStep / 4) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 bg-red-900/20 border border-red-600/30 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                <div>
                  <h4 className="text-red-500 font-medium">Configuration Error</h4>
                  <p className="text-red-200 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Step Content */}
          <div className="bg-gray-900 rounded-lg p-8 mb-8">
            {renderStepContent()}
          </div>

          {/* Navigation */}
          <div className="flex justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            
            {currentStep < 4 ? (
              <button
                onClick={handleNext}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>Complete Setup</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationSetup; 