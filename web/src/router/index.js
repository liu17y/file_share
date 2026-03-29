// src/router/index.js
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // 客户端路由（无需登录）
  {
    path: '/',
    name: 'Client',
    component: () => import('@/views/client/FileManager.vue'),
    meta: { requiresAuth: false, title: '文件管理' }
  },
  // 后台管理路由（需要登录）
  {
    path: '/admin',
    component: () => import('@/views/admin/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/admin/Logs.vue'),
        meta: { title: '操作日志' }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/admin/Monitor.vue'),
        meta: { title: '实时监控' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/admin/Analytics.vue'),
        meta: { title: '数据分析' }
      },
      {
        path: 'storage',
        name: 'Storage',
        component: () => import('@/views/admin/Storage.vue'),
        meta: { title: '存储管理' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/admin/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/admin/Login.vue'),
    meta: { requiresAuth: false, title: '管理员登录' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth

  // console.log('[路由] 目标:', to.path, '需要登录:', requiresAuth, '已登录:', authStore.isAuthenticated)

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} · AuroraShare` : 'AuroraShare · 极光共享'

  if (requiresAuth && !authStore.isAuthenticated) {
    // console.log('[路由] 未登录，跳转到登录页')
    next('/admin/login')
  } else if (to.path === '/admin/login' && authStore.isAuthenticated) {
    // console.log('[路由] 已登录，跳转到仪表盘')
    next('/admin/dashboard')
  } else {
    next()
  }installed
})

export default router