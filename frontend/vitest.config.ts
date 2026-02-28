import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@shared': path.resolve(__dirname, './src/shared'),
      '@features': path.resolve(__dirname, './src/features'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache', 'e2e/**/*', 'admin/**'],
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html', 'json-summary'],
      exclude: [
        'node_modules/',
        'src/test/setup.ts',
        'e2e/**',
        '**/*.d.ts',
        '**/*.test.tsx',
        '**/*.test.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'dist/**'
      ],
      thresholds: {
        branches: 70,
        functions: 85,
        lines: 88,
        statements: 88,
      },
    },
  },
});

