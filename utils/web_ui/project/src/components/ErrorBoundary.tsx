import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg shadow-xl p-8 max-w-2xl w-full">
            <div className="flex items-center mb-6">
              <AlertTriangle className="w-8 h-8 text-red-500 mr-3" />
              <h1 className="text-2xl font-bold text-white">Something went wrong</h1>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-300 mb-4">
                An unexpected error occurred. This has been logged and we'll look into it.
              </p>
              
              {this.state.error && (
                <div className="bg-gray-700 rounded p-4 mb-4">
                  <h3 className="text-red-400 font-semibold mb-2">Error Details:</h3>
                  <p className="text-gray-300 text-sm font-mono">
                    {this.state.error.message}
                  </p>
                </div>
              )}
              
              {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
                <details className="bg-gray-700 rounded p-4">
                  <summary className="text-yellow-400 font-semibold cursor-pointer mb-2">
                    Stack Trace (Development Only)
                  </summary>
                  <pre className="text-gray-300 text-xs overflow-auto">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
            </div>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={this.handleReset}
                className="flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </button>
              
              <button
                onClick={() => window.location.reload()}
                className="flex items-center justify-center px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const captureError = React.useCallback((error: Error) => {
    console.error('Error captured:', error);
    setError(error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { captureError, resetError };
}; 