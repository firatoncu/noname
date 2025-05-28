import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart, 
  Menu, 
  X, 
  TrendingUp,
  Settings
} from 'lucide-react';
import { ConnectionStatus, ConnectionStatusCompact } from './ConnectionStatus';
import { useAppContext } from '../contexts/AppContext';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

const navItems: NavItem[] = [
  {
    path: '/',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'Overview of positions and wallet'
  },
  {
    path: '/trading-conditions',
    label: 'Trading Conditions',
    icon: BarChart,
    description: 'Real-time trading signals'
  },
  {
    path: '/analysis',
    label: 'Position Analysis',
    icon: TrendingUp,
    description: 'Performance analytics and detailed position analysis'
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: Settings,
    description: 'Bot configuration and settings'
  },
];

export const Navigation: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { state } = useAppContext();

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <>
      <nav className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and brand */}
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <LayoutDashboard className="w-8 h-8 text-blue-400 mr-3" />
                <div className="hidden sm:block">
                  <h1 className="text-xl font-bold text-white">
                    n0name Trading
                  </h1>
                  <p className="text-xs text-gray-400">
                    Real-time Dashboard
                  </p>
                </div>
                <h1 className="sm:hidden text-lg font-bold text-white">
                  n0name
                </h1>
              </div>
            </div>

            {/* Desktop navigation */}
            <div className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = isActivePath(item.path);
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'text-gray-300 hover:text-white hover:bg-gray-700'
                    }`}
                    title={item.description}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>

            {/* Right side items */}
            <div className="flex items-center space-x-4">
              {/* Connection status - desktop */}
              <div className="hidden sm:block">
                <ConnectionStatus />
              </div>
              
              {/* Connection status - mobile */}
              <div className="sm:hidden">
                <ConnectionStatusCompact />
              </div>

              {/* Error indicator */}
              {state.errors.length > 0 && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  <span className="ml-2 text-red-400 text-sm hidden sm:inline">
                    {state.errors.length} error{state.errors.length > 1 ? 's' : ''}
                  </span>
                </div>
              )}

              {/* Mobile menu button */}
              <button
                onClick={toggleMobileMenu}
                className="md:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
                aria-label="Toggle mobile menu"
              >
                {isMobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-700">
            <div className="px-2 pt-2 pb-3 space-y-1 bg-gray-800">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = isActivePath(item.path);
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={closeMobileMenu}
                    className={`block px-3 py-3 rounded-lg text-base font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:text-white hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className="w-5 h-5" />
                      <div>
                        <div>{item.label}</div>
                        {item.description && (
                          <div className="text-xs text-gray-400 mt-1">
                            {item.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </Link>
                );
              })}
              
              {/* Mobile connection status */}
              <div className="px-3 py-3">
                <ConnectionStatus />
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeMobileMenu}
        />
      )}
    </>
  );
}; 