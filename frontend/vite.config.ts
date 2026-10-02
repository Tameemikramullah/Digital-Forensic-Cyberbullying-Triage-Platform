import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/evidence': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/triage': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/reviews': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/audit': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/export': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/integrity': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/explainability': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/repeatability': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/reproducibility': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/operational': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/threshold-calibration': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/model-evaluation': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/model-comparison': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/error-analysis': {
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
