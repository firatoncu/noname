import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart, 
  Menu, 
  X, 
  TrendingUp,
  Settings,
  Activity,
  Wallet
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
    description: 'Overview of positions and performance'
  },
  {
    path: '/wallet',
    label: 'Wallet Overview',
    icon: Wallet,
    description: 'Detailed wallet balance and account health'
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
      <nav className="bg-dark-bg-secondary/95 backdrop-blur-md border-b border-dark-border-primary shadow-glass sticky top-0 z-40">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and brand */}
            <div className="flex items-center animate-slide-in-left">
              <div className="flex-shrink-0 flex items-center group">
                <div className="relative">
                  <Activity className="w-8 h-8 text-dark-accent-primary mr-3 transition-all duration-300 group-hover:text-dark-accent-secondary group-hover:scale-110" />
                  <div className="absolute inset-0 w-8 h-8 bg-dark-accent-primary/20 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-xl font-bold text-dark-text-primary transition-colors duration-300">
                    n0name Trading
                  </h1>
                  <p className="text-xs text-dark-text-muted">
                    Real-time Dashboard
                  </p>
                </div>
                <h1 className="sm:hidden text-lg font-bold text-dark-text-primary">
                  n0name
                </h1>
              </div>
            </div>

            {/* Desktop navigation */}
            <div className="hidden md:flex items-center space-x-2 animate-fade-in">
              {navItems.map((item, index) => {
                const Icon = item.icon;
                const isActive = isActivePath(item.path);
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`group relative px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center space-x-2 ${
                      isActive
                        ? 'bg-dark-accent-primary text-dark-text-primary shadow-glow-sm'
                        : 'text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-bg-hover'
                    }`}
                    title={item.description}
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <Icon className={`w-4 h-4 transition-all duration-300 ${
                      isActive ? 'scale-110' : 'group-hover:scale-110'
                    }`} />
                    <span>{item.label}</span>
                    {isActive && (
                      <div className="absolute inset-0 bg-dark-accent-primary/10 rounded-xl blur-sm"></div>
                    )}
                  </Link>
                );
              })}
            </div>

            {/* Right side items */}
            <div className="flex items-center space-x-4 animate-slide-in-right">
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
                <div className="flex items-center animate-pulse-soft">
                  <div className="w-2 h-2 bg-dark-accent-error rounded-full animate-pulse"></div>
                  <span className="ml-2 text-dark-accent-error text-sm hidden sm:inline">
                    {state.errors.length} error{state.errors.length > 1 ? 's' : ''}
                  </span>
                </div>
              )}

              {/* Mobile menu button */}
              <button
                onClick={toggleMobileMenu}
                className="md:hidden p-2 rounded-xl text-dark-text-muted hover:text-dark-text-primary hover:bg-dark-bg-hover transition-all duration-300 group"
                aria-label="Toggle mobile menu"
              >
                {isMobileMenuOpen ? (
                  <X className="w-6 h-6 transition-transform duration-300 rotate-90 group-hover:rotate-180" />
                ) : (
                  <Menu className="w-6 h-6 transition-transform duration-300 group-hover:scale-110" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div className={`md:hidden border-t border-dark-border-primary transition-all duration-350 ease-in-out ${
          isMobileMenuOpen 
            ? 'max-h-96 opacity-100' 
            : 'max-h-0 opacity-0 overflow-hidden'
        }`}>
          <div className="px-2 pt-2 pb-3 space-y-1 bg-dark-bg-secondary/90 backdrop-blur-sm">
            {navItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = isActivePath(item.path);
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={closeMobileMenu}
                  className={`block px-3 py-3 rounded-xl text-base font-medium transition-all duration-300 animate-fade-in-up ${
                    isActive
                      ? 'bg-dark-accent-primary text-dark-text-primary shadow-glow-sm'
                      : 'text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-bg-hover'
                  }`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-5 h-5 transition-transform duration-300 ${
                      isActive ? 'scale-110' : ''
                    }`} />
                    <div>
                      <div>{item.label}</div>
                      {item.description && (
                        <div className="text-xs text-dark-text-muted mt-1">
                          {item.description}
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              );
            })}
            
            {/* Mobile connection status */}
            <div className="px-3 py-3 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
              <ConnectionStatus />
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-xs z-40 md:hidden animate-fade-in"
          onClick={closeMobileMenu}
        />
      )}
    </>
  );
}; 