import React from 'react';
import { Outlet } from 'react-router-dom';
import { AppProvider } from './contexts/AppContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Navigation } from './components/Navigation';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AppProvider>
          <div className="min-h-screen bg-gray-900 transition-colors duration-200">
            <Navigation />
            <main className="flex-1">
              <ErrorBoundary>
                <Outlet />
              </ErrorBoundary>
            </main>
          </div>
        </AppProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;