import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const api = {
  target: 'http://127.0.0.1:8000',
  changeOrigin: true,
  timeout: 0,
  proxyTimeout: 0,
}

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/generate-3d-model': api,
      '/models': api,
      '/pet-assets': api,
      '/sounds': api,
      '/health': api,
    },
  },
})
