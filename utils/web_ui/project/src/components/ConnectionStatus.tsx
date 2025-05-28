import React from 'react';
import { Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react';
import { useAppContext } from '../contexts/AppContext';

export const ConnectionStatus: React.FC = () => {
  const { state, websocket } = useAppContext();
  const { connectionStatus } = state;
  const { isConnected, reconnect } = websocket;

  const getStatusConfig = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          icon: Wifi,
          text: 'Connected',
          color: 'text-green-500',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/20',
        };
      case 'connecting':
        return {
          icon: RefreshCw,
          text: 'Connecting...',
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-500/10',
          borderColor: 'border-yellow-500/20',
          animate: true,
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected',
          color: 'text-gray-500',
          bgColor: 'bg-gray-500/10',
          borderColor: 'border-gray-500/20',
        };
      case 'error':
        return {
          icon: AlertCircle,
          text: 'Connection Error',
          color: 'text-red-500',
          bgColor: 'bg-red-500/10',
          borderColor: 'border-red-500/20',
        };
      default:
        return {
          icon: WifiOff,
          text: 'Unknown',
          color: 'text-gray-500',
          bgColor: 'bg-gray-500/10',
          borderColor: 'border-gray-500/20',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const handleReconnect = () => {
    if (!isConnected) {
      reconnect();
    }
  };

  return (
    <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <Icon 
        className={`w-4 h-4 ${config.color} ${config.animate ? 'animate-spin' : ''}`} 
      />
      <span className={`text-sm font-medium ${config.color}`}>
        {config.text}
      </span>
      
      {(connectionStatus === 'disconnected' || connectionStatus === 'error') && (
        <button
          onClick={handleReconnect}
          className="ml-2 p-1 rounded hover:bg-gray-700 transition-colors"
          title="Reconnect"
        >
          <RefreshCw className="w-3 h-3 text-gray-400 hover:text-white" />
        </button>
      )}
    </div>
  );
};

// Compact version for smaller spaces
export const ConnectionStatusCompact: React.FC = () => {
  const { state } = useAppContext();
  const { connectionStatus } = state;

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500 animate-pulse';
      case 'disconnected':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div 
      className={`w-3 h-3 rounded-full ${getStatusColor()}`}
      title={`Connection: ${connectionStatus}`}
    />
  );
}; 