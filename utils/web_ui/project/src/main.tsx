import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App';
import Dashboard from './pages/Dashboard';
import PositionChart from './pages/PositionChart';
import TradingConditionsPage from './pages/TradingConditionsPage';
import TradingConditionChart from './pages/TradingConditionChart';
import { ThemeProvider } from './contexts/ThemeContext';
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
        path: "/position/:id",
        element: <PositionChart />,
      },
      {
        path: "/position/current/:symbol",
        element: <PositionChart />,
      },
      {
        path: "/trading-conditions",
        element: <TradingConditionsPage />,
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
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  </StrictMode>
);