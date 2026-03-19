// frontend root/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import compression from 'vite-plugin-compression';
import path from 'path';

const API_PROXY_PATHS = [
  '/callback',
  '/login',
  '/me',
  '/genres',
  '/impersonate',
  '/now-playing',
  '/update-playing',
  '/public-genres',
  '/check-recent',
  '/playlists',
  '/recently-played',
  '/synced-playlists',
  '/dashboard',
  '/public-track',
  '/user-playlists',
  '/complete-onboarding',
  '/playback',
  '/delete-user',
  '/refresh-session',
  '/public-update-playing',
  '/public-played',
  '/ai-genres',
  '/public-playlist',
  '/playlist-info',
  '/admin/sync_playlists',
  '/spotify-playlists',
  '/all-playlists',
  '/docs',
  '/openapi.json',
  '/redoc',
  '/static',
  '/status',
  '/add-playlists',
  '/delete-playlists',
  '/update-featured',
  '/refresh_token',
  '/top-tracks',
  '/top-subgenre',
  '/analyze-genres',
  '/session',
  '/genre-map',
  '/users',
  '/user-genres',
  '/public-profile',
  '/health',
  '/refresh_genres',
  '/spotify-me',
  '/whoami',
];

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
    proxy: Object.fromEntries(
      API_PROXY_PATHS.map((p) => [p, BACKEND_URL])
    ),
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
