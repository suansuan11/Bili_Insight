import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 【核心配置】开发服务器代理
    proxy: {
      // 当请求路径以 /insight 开头时，触发此代理规则
      '/insight': {
        // 将请求转发到的目标后端服务器地址
        target: 'http://localhost:8080',
        // 是否改变请求头中的 Origin 字段，必须设置为 true
        //changeOrigin: true,
        // (可选) 如果你的后端API路径本身就带有 /insight，则无需重写
        // 如果后端路径是 /popular-videos，则需要重写：
        // rewrite: (path) => path.replace(/^\/insight/, '')
      },
    },
  },
})
