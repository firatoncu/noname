import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App';
import Dashboard from './pages/Dashboard';
import WalletOverview from './pages/WalletOverview';
import PositionChart from './pages/PositionChart';
import TradingConditionsPage from './pages/TradingConditionsPage';
import TradingConditionChart from './pages/TradingConditionChart';
import PositionAnalysis from './pages/PositionAnalysis';
import Settings from './pages/Settings';
import './index.css';

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        path: "/",
        element: <Dashboard />,
      },
      {
        path: "/wallet",
        element: <WalletOverview />,
      },
      {
        path: "/trading-conditions",
        element: <TradingConditionsPage />,
      },
      {
        path: "/analysis",
        element: <PositionAnalysis />,
      },
      {
        path: "/positions",
        element: <Dashboard />, // For now, redirect to dashboard
      },
      {
        path: "/history",
        element: <Dashboard />, // For now, redirect to dashboard
      },
      {
        path: "/settings",
        element: <Settings />,
      },
      {
        path: "/position/:id",
        element: <PositionChart />,
      },
      {
        path: "/position/current/:symbol",
        element: <PositionChart />,
      },
      {
        path: "/trading-conditions/chart/:symbol",
        element: <TradingConditionChart />,
      },
    ],
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);