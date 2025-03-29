import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { LayoutDashboard, Moon, Sun } from 'lucide-react';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gray-900' : 'bg-gray-100'} transition-colors duration-200`}>


      <Outlet context={{ isDarkMode }} />
    </div>
  );
}

export default App;