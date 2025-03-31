import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    host: '0.0.0.0', // Allows access via n0name.local
    port: 80,      // Ensure it’s running on port 5173 (default for Vite)
    allowedHosts: [
      'n0name', // Add your custom hostname here
      'localhost'     // Optional: Keep localhost allowed
    ],
    proxy: {
      '/api': {
        target: 'http://n0name:8000',  // Backend URL
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')  // Keep /api prefix
      }
    }
  }
});

