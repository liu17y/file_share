// vite.config.js
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import VarletIconBuilderPlugin from '@varlet/unplugin-icon-builder/vite'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    vueDevTools(),
    VarletIconBuilderPlugin({
      dir: './src/icons'
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    open: true,
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8007',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../frontend_dist',
    emptyOutDir: true,
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'ui': ['@varlet/ui'],
          'charts': ['echarts']
        }
      }
    }
  },
  base: './',  // 保持相对路径
  // 添加以下配置确保资源路径正确
  publicDir: 'public',
}))