# n0name Trading Dashboard

A modern, real-time trading dashboard built with React, TypeScript, and FastAPI. Features WebSocket connections for live updates, comprehensive error handling, and responsive design.

## 🚀 Features

### Frontend Architecture
- **React 18** with TypeScript for type safety
- **Tailwind CSS** for modern, responsive styling
- **React Router** for client-side routing
- **Custom Hooks** for API calls and WebSocket management
- **Context API** for centralized state management
- **Error Boundaries** for graceful error handling
- **Real-time Updates** via WebSocket connections

### Backend Architecture
- **FastAPI** with async/await support
- **WebSocket** endpoints for real-time data streaming
- **CORS** enabled for cross-origin requests
- **SSL/HTTPS** support with self-signed certificates
- **Pydantic** models for data validation
- **Connection pooling** for WebSocket clients

### Key Components

#### State Management
- **AppContext**: Centralized application state with reducer pattern
- **ThemeContext**: Dark/light theme management
- **Real-time sync**: WebSocket integration for live data updates

#### API Layer
- **useApi Hook**: Reusable hook for HTTP requests with retry logic
- **useWebSocket Hook**: WebSocket connection management with auto-reconnect
- **Error Handling**: Comprehensive error catching and user feedback
- **Loading States**: Skeleton loaders and spinners

#### UI Components
- **Navigation**: Responsive navigation with mobile menu
- **Dashboard**: Real-time overview of positions and wallet
- **Position Cards**: Interactive position management
- **Connection Status**: Live connection indicator
- **Error Boundary**: Graceful error handling with recovery options

## 📁 Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ErrorBoundary.tsx
│   ├── LoadingSpinner.tsx
│   ├── Navigation.tsx
│   ├── ConnectionStatus.tsx
│   ├── PositionCard.tsx
│   ├── WalletCard.tsx
│   └── HistoricalPositions.tsx
├── contexts/            # React contexts for state management
│   ├── AppContext.tsx
│   └── ThemeContext.tsx
├── hooks/               # Custom React hooks
│   ├── useApi.ts
│   └── useWebSocket.ts
├── pages/               # Page components
│   ├── Dashboard.tsx
│   ├── TradingConditionsPage.tsx
│   └── PositionChart.tsx
├── config/              # Configuration files
│   └── api.ts
├── types.ts             # TypeScript type definitions
├── App.tsx              # Main application component
└── main.tsx             # Application entry point
```

## 🛠 Setup & Installation

### Prerequisites
- Node.js 16+ 
- Python 3.8+
- OpenSSL (for SSL certificates)

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd utils/web_ui/project
   npm install
   ```

2. **Generate SSL certificates** (for HTTPS):
   ```bash
   python utils/web_ui/generate_certificates.py
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

### Backend Setup

The backend is automatically started when running the main application:

```bash
python n0name.py
```

This will:
- Start the FastAPI server on `https://localhost:8000`
- Start the frontend dev server on `https://localhost:5173`
- Open your browser automatically

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file in the project root:

```env
VITE_API_BASE_URL=https://localhost:8000/api
VITE_APP_TITLE=n0name Trading Dashboard
```

### API Configuration

The API configuration is centralized in `src/config/api.ts`:

```typescript
export const API_ENDPOINTS = {
  POSITIONS: '/positions',
  TRADING_CONDITIONS: '/trading-conditions',
  WALLET: '/wallet',
  HISTORICAL_POSITIONS: '/historical-positions',
  CLOSE_POSITION: '/close-position',
  SET_TPSL: '/set-tpsl',
  CLOSE_LIMIT_ORDERS: '/close-limit-orders',
} as const;
```

## 🌐 WebSocket Integration

### Real-time Data Flow

1. **Connection**: Frontend establishes WebSocket connection to `/ws`
2. **Initial Data**: Server sends current state on connection
3. **Live Updates**: Server broadcasts changes to all connected clients
4. **Auto-reconnect**: Client automatically reconnects on disconnection

### Message Types

```typescript
// Outgoing (Client → Server)
{
  type: "refresh_data"
}

// Incoming (Server → Client)
{
  type: "positions_update",
  data: Position[]
}
{
  type: "trading_conditions_update", 
  data: TradingConditions[]
}
{
  type: "wallet_update",
  data: WalletInfo
}
{
  type: "error",
  data: { message: string }
}
```

## 🎨 UI/UX Features

### Responsive Design
- **Mobile-first**: Optimized for mobile devices
- **Breakpoints**: Tailored layouts for different screen sizes
- **Touch-friendly**: Large tap targets and gestures

### Loading States
- **Skeleton loaders**: Content placeholders during loading
- **Spinners**: Activity indicators for actions
- **Progressive loading**: Staggered content appearance

### Error Handling
- **Error boundaries**: Catch and display React errors
- **Retry mechanisms**: Automatic and manual retry options
- **User feedback**: Clear error messages and recovery actions

### Accessibility
- **Keyboard navigation**: Full keyboard support
- **Screen readers**: ARIA labels and semantic HTML
- **Color contrast**: WCAG compliant color schemes

## 🔒 Security

### HTTPS/SSL
- Self-signed certificates for local development
- Automatic HTTP → HTTPS redirect
- Secure WebSocket connections (WSS)

### CORS Configuration
- Restricted origins for production
- Credential support for authenticated requests
- Preflight request handling

## 📊 Performance

### Optimization Strategies
- **Code splitting**: Lazy loading of route components
- **Memoization**: React.memo and useMemo for expensive operations
- **Debouncing**: API call throttling for user inputs
- **Connection pooling**: Efficient WebSocket management

### Monitoring
- **Error tracking**: Comprehensive error logging
- **Performance metrics**: Loading time measurements
- **Connection status**: Real-time connection monitoring

## 🧪 Development

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Linting
npm run lint

# Preview production build
npm run preview
```

### Code Quality
- **TypeScript**: Full type safety
- **ESLint**: Code linting and formatting
- **Prettier**: Code formatting (if configured)

## 🚀 Deployment

### Production Build

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Serve static files**: Deploy the `dist/` folder to your web server

3. **Configure reverse proxy**: Point API calls to your backend server

### Docker Support

```dockerfile
# Example Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Certificate Errors**:
- Run `python utils/web_ui/generate_certificates.py`
- Accept browser security warnings for localhost

**Connection Issues**:
- Check if ports 5173 and 8000 are available
- Verify firewall settings
- Ensure backend is running

**Build Errors**:
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility

### Support

For issues and questions:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information 