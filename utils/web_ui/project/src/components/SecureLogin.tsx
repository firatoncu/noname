import React, { useState, useEffect } from 'react';
import { Shield, Eye, EyeOff, AlertTriangle, CheckCircle } from 'lucide-react';

interface LoginProps {
  onLogin: (sessionId: string, jwtToken: string) => void;
  onError: (message: string) => void;
}

interface LoginResponse {
  success: boolean;
  session_id?: string;
  jwt_token?: string;
  message: string;
}

const SecureLogin: React.FC<LoginProps> = ({ onLogin, onError }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [isLocked, setIsLocked] = useState(false);
  const [lockoutTime, setLockoutTime] = useState(0);

  // Password strength indicator
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    feedback: '',
    color: 'text-gray-400'
  });

  // Check password strength
  useEffect(() => {
    if (password.length === 0) {
      setPasswordStrength({ score: 0, feedback: '', color: 'text-gray-400' });
      return;
    }

    let score = 0;
    let feedback = '';
    let color = 'text-red-500';

    // Length check
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;

    // Character variety checks
    if (/[a-z]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;

    // Determine feedback and color
    if (score <= 2) {
      feedback = 'Weak password';
      color = 'text-red-500';
    } else if (score <= 4) {
      feedback = 'Medium password';
      color = 'text-yellow-500';
    } else {
      feedback = 'Strong password';
      color = 'text-green-500';
    }

    setPasswordStrength({ score, feedback, color });
  }, [password]);

  // Handle lockout countdown
  useEffect(() => {
    if (lockoutTime > 0) {
      const timer = setTimeout(() => {
        setLockoutTime(lockoutTime - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (isLocked && lockoutTime === 0) {
      setIsLocked(false);
      setAttempts(0);
    }
  }, [lockoutTime, isLocked]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLocked) {
      setError(`Account locked. Try again in ${lockoutTime} seconds.`);
      return;
    }

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          password: password
        }),
        credentials: 'include'
      });

      const data: LoginResponse = await response.json();

      if (data.success && data.session_id && data.jwt_token) {
        // Store session information securely
        sessionStorage.setItem('session_id', data.session_id);
        sessionStorage.setItem('jwt_token', data.jwt_token);
        
        // Reset attempts on successful login
        setAttempts(0);
        setIsLocked(false);
        
        onLogin(data.session_id, data.jwt_token);
      } else {
        // Handle failed login
        const newAttempts = attempts + 1;
        setAttempts(newAttempts);
        
        if (newAttempts >= 5) {
          setIsLocked(true);
          setLockoutTime(300); // 5 minutes lockout
          setError('Too many failed attempts. Account locked for 5 minutes.');
        } else {
          setError(data.message || 'Login failed');
        }
        
        onError(data.message || 'Login failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Network error occurred';
      setError(errorMessage);
      onError(errorMessage);
      
      // Increment attempts on network errors too
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);
      
      if (newAttempts >= 5) {
        setIsLocked(true);
        setLockoutTime(300);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const formatLockoutTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="bg-white/10 backdrop-blur-lg rounded-xl shadow-2xl p-8 border border-white/20">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <Shield className="h-12 w-12 text-blue-400" />
            </div>
            <h2 className="text-3xl font-bold text-white">n0name Trading Bot</h2>
            <p className="text-gray-300 mt-2">Secure Access Portal</p>
          </div>

          {/* Security Notice */}
          <div className="bg-blue-500/20 border border-blue-400/30 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <Shield className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
              <div className="text-sm text-blue-200">
                <p className="font-medium">Security Notice</p>
                <p className="mt-1">This is a secure trading interface. All actions are logged and monitored.</p>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-500/20 border border-red-400/30 rounded-lg p-4 mb-6">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
                <div className="text-sm text-red-200">
                  <p>{error}</p>
                  {attempts > 0 && !isLocked && (
                    <p className="mt-1 text-xs">
                      Attempts: {attempts}/5
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Lockout Display */}
          {isLocked && (
            <div className="bg-yellow-500/20 border border-yellow-400/30 rounded-lg p-4 mb-6">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5 mr-3 flex-shrink-0" />
                <div className="text-sm text-yellow-200">
                  <p className="font-medium">Account Temporarily Locked</p>
                  <p className="mt-1">Time remaining: {formatLockoutTime(lockoutTime)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-200 mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading || isLocked}
                className="w-full px-4 py-3 bg-white/10 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="Enter your username"
                maxLength={50}
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-200 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading || isLocked}
                  className="w-full px-4 py-3 pr-12 bg-white/10 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Enter your password"
                  maxLength={128}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading || isLocked}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              
              {/* Password Strength Indicator */}
              {password.length > 0 && (
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          passwordStrength.score <= 2 ? 'bg-red-500' :
                          passwordStrength.score <= 4 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${(passwordStrength.score / 6) * 100}%` }}
                      />
                    </div>
                    <span className={`text-xs ${passwordStrength.color}`}>
                      {passwordStrength.feedback}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || isLocked || !username.trim() || !password.trim()}
              className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Authenticating...
                </>
              ) : (
                <>
                  <Shield className="h-5 w-5 mr-2" />
                  Secure Login
                </>
              )}
            </button>
          </form>

          {/* Security Features */}
          <div className="mt-8 pt-6 border-t border-gray-600">
            <h3 className="text-sm font-medium text-gray-200 mb-3">Security Features</h3>
            <div className="space-y-2 text-xs text-gray-400">
              <div className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-400 mr-2" />
                <span>End-to-end encryption</span>
              </div>
              <div className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-400 mr-2" />
                <span>Session-based authentication</span>
              </div>
              <div className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-400 mr-2" />
                <span>Rate limiting protection</span>
              </div>
              <div className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-400 mr-2" />
                <span>Audit logging enabled</span>
              </div>
            </div>
          </div>

          {/* Default Credentials Notice (Development Only) */}
          <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-400/30 rounded-lg">
            <div className="text-xs text-yellow-200">
              <p className="font-medium">Development Mode</p>
              <p className="mt-1">Default credentials: admin / admin123!@#</p>
              <p className="mt-1 text-yellow-300">⚠️ Change default password in production!</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecureLogin; 