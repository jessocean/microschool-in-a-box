import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  root: 'frontend',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './frontend'),
      '@shared': path.resolve(__dirname, './shared'),
      '@backend': path.resolve(__dirname, './backend')
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      }
    }
  }
})