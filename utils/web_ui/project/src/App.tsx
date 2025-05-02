import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { LayoutDashboard } from 'lucide-react';

function App() {
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 transition-colors duration-200">
      <Outlet context={{ isDarkMode: true }} />
    </div>
  );
}

export default App;