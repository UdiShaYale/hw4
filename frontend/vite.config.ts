import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The FastAPI app owns both the JSON API and the product photos, so proxy
// /api and /images straight through and keep the frontend origin-free.
export default defineConfig({
  // Pinned so the server can be launched from any working directory.
  root: fileURLToPath(new URL('.', import.meta.url)),
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/images': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
