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
          <div className="min-h-screen bg-dark-bg-primary transition-all duration-300 ease-in-out">
            <Navigation />
            <main className="flex-1 animate-fade-in">
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