import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@shared': path.resolve(__dirname, '../src/shared'),
      '@features': path.resolve(__dirname, './src/features'),
      'react': path.resolve(__dirname, './node_modules/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
      'react-i18next': path.resolve(__dirname, './node_modules/react-i18next'),
      'i18next': path.resolve(__dirname, './node_modules/i18next'),
    },
    dedupe: ['react', 'react-dom'],
  },
  server: {
    port: 3001,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_ADMIN_API_PROXY_TARGET ?? 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
  },
});
