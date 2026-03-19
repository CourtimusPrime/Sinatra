// frontend root/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import compression from 'vite-plugin-compression';
import path from 'path';

const BACKEND_URL = 'http://localhost:8000';

export default defineConfig({
  plugins: [
    react(),
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
      deleteOriginFile: false,
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  publicDir: 'public',
  base: '/',
  server: {
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    target: 'es2022',
    cssCodeSplit: true,
    rollupOptions: {
      input: 'index.html',
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          lucide: ['lucide-react'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
