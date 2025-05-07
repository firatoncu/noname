import React from 'react';
import { Outlet } from 'react-router-dom';
import { LayoutDashboard } from 'lucide-react';
import { useTheme } from './contexts/ThemeContext';

function App() {
  const { isDarkMode } = useTheme();

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-gray-100'} transition-colors duration-200`}>
      <Outlet context={{ isDarkMode }} />
    </div>
  );
}

export default App;