import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'primary' | 'secondary' | 'white';
  text?: string;
  className?: string;
  fullScreen?: boolean;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

const variantClasses = {
  primary: 'text-blue-500',
  secondary: 'text-gray-500',
  white: 'text-white',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  text,
  className = '',
  fullScreen = false,
}) => {
  const spinnerContent = (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <Loader2 
        className={`animate-spin ${sizeClasses[size]} ${variantClasses[variant]}`} 
      />
      {text && (
        <p className={`mt-2 text-sm ${variantClasses[variant]}`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-8">
          {spinnerContent}
        </div>
      </div>
    );
  }

  return spinnerContent;
};

// Skeleton loading component for content placeholders
interface SkeletonProps {
  className?: string;
  lines?: number;
  height?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  className = '', 
  lines = 1, 
  height = 'h-4' 
}) => {
  return (
    <div className={`animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={`bg-gray-700 rounded ${height} ${index > 0 ? 'mt-2' : ''}`}
        />
      ))}
    </div>
  );
};

// Card skeleton for loading states
export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`bg-gray-800 rounded-lg p-6 ${className}`}>
      <div className="animate-pulse">
        <div className="flex items-center mb-4">
          <div className="w-8 h-8 bg-gray-700 rounded mr-3" />
          <div className="w-32 h-6 bg-gray-700 rounded" />
        </div>
        <div className="space-y-3">
          <div className="w-full h-4 bg-gray-700 rounded" />
          <div className="w-3/4 h-4 bg-gray-700 rounded" />
          <div className="w-1/2 h-4 bg-gray-700 rounded" />
        </div>
      </div>
    </div>
  );
}; 