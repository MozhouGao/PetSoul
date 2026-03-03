import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: ['..'],
    },
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/pets': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,
      },
      '/motion': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,
      },
      '/export': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,
      },
      '/analyze-pet': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/generate-3d-model': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,
      },
      '/models': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
