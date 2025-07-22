import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../js'),
    emptyOutDir: false,
    rollupOptions: {
      input: resolve(__dirname, 'index.html'),
    },
  },
})
