import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:53317',
        changeOrigin: true
      },
      '/data': {
        target: 'http://127.0.0.1:53317',
        changeOrigin: true
      },
      '/static': {
        target: 'http://127.0.0.1:53317',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'lucide-react'],
          three: ['three'],
          charts: ['recharts'],
        }
      }
    },
    chunkSizeWarningLimit: 600
  }
});
