/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Custom dark theme palette - eye-friendly and minimalist
        dark: {
          // Background colors
          bg: {
            primary: '#0a0b0f',     // Deep dark background
            secondary: '#12141a',   // Card backgrounds
            tertiary: '#1a1d26',    // Elevated surfaces
            hover: '#1f2329',       // Hover states
          },
          // Border colors
          border: {
            primary: '#2a2d36',     // Main borders
            secondary: '#363a45',   // Secondary borders
            accent: '#4a5568',      // Accent borders
          },
          // Text colors
          text: {
            primary: '#f7fafc',     // Primary text
            secondary: '#cbd5e0',   // Secondary text
            muted: '#a0aec0',       // Muted text
            disabled: '#718096',    // Disabled text
          },
          // Accent colors
          accent: {
            primary: '#667eea',     // Primary accent (soft blue)
            secondary: '#764ba2',   // Secondary accent (soft purple)
            success: '#48bb78',     // Success green
            warning: '#ed8936',     // Warning orange
            error: '#f56565',       // Error red
            info: '#4299e1',        // Info blue
          },
          // Glass effect colors
          glass: {
            bg: 'rgba(26, 29, 38, 0.8)',
            border: 'rgba(42, 45, 54, 0.5)',
          }
        }
      },
      // Custom animations
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'fade-in-up': 'fadeInUp 0.4s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-left': 'slideInLeft 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      // Custom keyframes
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(102, 126, 234, 0.3)' },
          '100%': { boxShadow: '0 0 20px rgba(102, 126, 234, 0.6)' },
        },
      },
      // Custom transitions
      transitionDuration: {
        '250': '250ms',
        '350': '350ms',
      },
      // Custom backdrop blur
      backdropBlur: {
        xs: '2px',
      },
      // Custom box shadows
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'glow-sm': '0 0 10px rgba(102, 126, 234, 0.3)',
        'glow-md': '0 0 20px rgba(102, 126, 234, 0.4)',
        'glow-lg': '0 0 30px rgba(102, 126, 234, 0.5)',
      },
      // Custom border radius
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
    },
  },
  plugins: [],
};