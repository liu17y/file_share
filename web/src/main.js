// src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Varlet UI - 修复导入方式
import Varlet from '@varlet/ui'
import '@varlet/ui/es/style'  // 去掉 .js 后缀，或者使用以下方式

// 如果上面还是报错，可以尝试：
// import '@varlet/ui/es/style'  // 不添加 .js 后缀
// 或者
// import '@varlet/ui/style'  // 使用简化的路径

// Varlet Icons
import '@varlet/icons'

// 全局样式
import './styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Varlet)

app.mount('#app')