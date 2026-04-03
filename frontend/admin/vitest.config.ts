import path from 'path';

import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import type { PluginOption } from 'vite';
import { defineConfig } from 'vitest/config';

const plugins: PluginOption[] = [
  react() as PluginOption,
  tailwindcss() as PluginOption,
];

export default defineConfig({
  plugins,
  resolve: {
    alias: {
      '@shared': path.resolve(__dirname, '../src/shared'),
      '@features': path.resolve(__dirname, './src/features'),
      'react': path.resolve(__dirname, './node_modules/react'),
      'react-dom': path.resolve(__dirname, './node_modules/react-dom'),
      'react-i18next': path.resolve(__dirname, './node_modules/react-i18next'),
      'i18next': path.resolve(__dirname, './node_modules/i18next'),
    },
    dedupe: ['react', 'react-dom', 'react-router', 'react-router-dom', 'zustand', 'react-i18next', 'i18next'],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: [path.resolve(__dirname, './src/test/setup.ts')],
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html', 'json-summary'],
      exclude: [
        'node_modules/',
        'src/test/setup.ts',
        '**/*.d.ts',
        '**/*.test.tsx',
        '**/*.test.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'dist/**'
      ],
      thresholds: {
        branches: 35,
        functions: 45,
        lines: 45,
        statements: 43,
      },
    },
  },
});
