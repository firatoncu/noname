import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertCircle, Settings, Loader } from 'lucide-react';

interface ConfigStatus {
  exists: boolean;
  valid: boolean;
  message: string;
  setup_required: boolean;
  error?: string;
  missing_keys?: string[];
}

interface ConfigurationGuardProps {
  children: React.ReactNode;
}

const ConfigurationGuard: React.FC<ConfigurationGuardProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [configStatus, setConfigStatus] = useState<ConfigStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkConfigurationStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/config/status');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const status: ConfigStatus = await response.json();
      setConfigStatus(status);

      // If setup is required and we're not already on the setup page, redirect
      if (status.setup_required && location.pathname !== '/setup') {
        const reason = !status.exists ? 'missing' : 'invalid';
        navigate(`/setup?reason=${reason}`, { replace: true });
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      
      // If we can't check config status, assume setup is needed
      if (location.pathname !== '/setup') {
        navigate('/setup?reason=error', { replace: true });
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Don't check config status if we're already on the setup page
    if (location.pathname === '/setup') {
      setIsLoading(false);
      return;
    }

    checkConfigurationStatus();
  }, [location.pathname]);

  // If we're on the setup page, always render children
  if (location.pathname === '/setup') {
    return <>{children}</>;
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-500 mx-auto mb-4 animate-spin" />
          <h2 className="text-xl font-semibold text-white mb-2">Checking Configuration</h2>
          <p className="text-gray-400">Please wait while we verify your setup...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-white mb-4">Configuration Check Failed</h1>
          <p className="text-gray-400 mb-6">
            Unable to verify configuration status: {error}
          </p>
          <div className="space-y-3">
            <button
              onClick={checkConfigurationStatus}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry Check
            </button>
            <button
              onClick={() => navigate('/setup?reason=error')}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-center space-x-2"
            >
              <Settings className="w-4 h-4" />
              <span>Go to Setup</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show setup required state (shouldn't normally be seen due to redirect)
  if (configStatus?.setup_required) {
    return (
      <div className="min-h-screen bg-dark-bg-primary flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <Settings className="w-16 h-16 text-yellow-500 mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-white mb-4">Setup Required</h1>
          <p className="text-gray-400 mb-6">
            {configStatus.message}
          </p>
          <button
            onClick={() => {
              const reason = !configStatus.exists ? 'missing' : 'invalid';
              navigate(`/setup?reason=${reason}`);
            }}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
          >
            <Settings className="w-4 h-4" />
            <span>Complete Setup</span>
          </button>
        </div>
      </div>
    );
  }

  // Configuration is valid, render children
  return <>{children}</>;
};

export default ConfigurationGuard; 