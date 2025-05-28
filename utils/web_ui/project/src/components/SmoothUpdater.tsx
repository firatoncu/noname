import React, { useState, useEffect, useRef } from 'react';

interface SmoothUpdaterProps {
  children: React.ReactNode;
  updateKey: string | number;
  transitionDuration?: number;
}

export const SmoothUpdater: React.FC<SmoothUpdaterProps> = ({ 
  children, 
  updateKey, 
  transitionDuration = 150 
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const prevUpdateKeyRef = useRef(updateKey);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (updateKey !== prevUpdateKeyRef.current) {
      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Start smooth transition
      setIsUpdating(true);
      
      // End transition after duration
      timeoutRef.current = setTimeout(() => {
        setIsUpdating(false);
        prevUpdateKeyRef.current = updateKey;
      }, transitionDuration);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [updateKey, transitionDuration]);

  return (
    <div 
      className={`transition-all duration-${transitionDuration} ${
        isUpdating ? 'opacity-95 scale-[0.999]' : 'opacity-100 scale-100'
      }`}
      style={{
        transition: `opacity ${transitionDuration}ms ease-in-out, transform ${transitionDuration}ms ease-in-out`
      }}
    >
      {children}
    </div>
  );
}; 