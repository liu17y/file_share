<!-- src/views/admin/Layout.vue -->
<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed }">
      <div class="logo">
        <var-icon name="flash" :size="28" color="#fff" />
        <span v-if="!collapsed">AuroraShare</span>
      </div>
      <div class="nav-menu">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
          @click="navigate(item.path)"
        >
          <var-icon :name="item.icon" />
          <span v-if="!collapsed">{{ item.title }}</span>
        </div>
      </div>
      <div class="sidebar-footer">
        <div class="nav-item" @click="toggleCollapse">
          <var-icon :name="collapsed ? 'chevron-right' : 'chevron-left'" />
          <span v-if="!collapsed">收起菜单</span>
        </div>
        <div class="nav-item" @click="handleLogout">
          <var-icon name="logout" />
          <span v-if="!collapsed">退出登录</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main">
      <div class="header">
        <div class="page-title">{{ $route.meta.title }}</div>
        <div class="user-info">
          <var-icon name="account-circle" />
          <span>{{ adminInfo?.username || '管理员' }}</span>
          <var-button
            size="small"
            text
            @click="handleLogout"
            style="margin-left: 12px"
          >
            <var-icon name="logout" /> 退出
          </var-button>
        </div>
      </div>
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Snackbar } from '@varlet/ui'

// 正确导入 Dialog - 使用默认导入
import Dialog from '@varlet/ui/es/dialog'
// 导入样式
import '@varlet/ui/es/dialog/style'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const collapsed = ref(false)

const adminInfo = computed(() => authStore.adminInfo)

const menuItems = [
  { path: '/admin/dashboard', title: '仪表盘', icon: 'dashboard' },
  { path: '/admin/logs', title: '操作日志', icon: 'history' },
  { path: '/admin/monitor', title: '实时监控', icon: 'monitor' },
  { path: '/admin/analytics', title: '数据分析', icon: 'chart' },
  { path: '/admin/storage', title: '存储管理', icon: 'storage' },
  { path: '/admin/settings', title: '系统设置', icon: 'settings' }
]

const navigate = (path) => {
  router.push(path)
}

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

const handleLogout = async () => {
  try {
    console.log('[登出] 准备退出...')

    // 使用 Dialog
    Dialog({
      title: '确认退出',
      message: '确定要退出登录吗？',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      onConfirm: async () => {
        console.log('[登出] 用户确认退出')

        // 调用后端登出接口
        try {
          const token = localStorage.getItem('admin_token')
          if (token) {
            await fetch('/api/admin/logout', {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            })
          }
        } catch (error) {
          console.log('[登出] 后端接口调用失败', error)
        }

        // 清除本地存储
        authStore.logout()

        // 显示成功消息
        Snackbar.success('已退出登录')

        // 跳转到登录页
        router.push('/admin/login')
      },
      onCancel: () => {
        console.log('[登出] 用户取消退出')
      }
    })
  } catch (error) {
    console.error('[登出] 错误:', error)
    Snackbar.error('退出失败')
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #1e2a3a 0%, #0f172a 100%);
  color: #fff;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  overflow-y: auto;
  z-index: 100;
}

.sidebar.collapsed {
  width: 70px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-menu {
  flex: 1;
  padding: 16px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: rgba(255, 255, 255, 0.7);
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background-color: #3f51b5;
  color: #fff;
  border-left: 3px solid #ff9800;
}

.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px 0;
}

.main {
  flex: 1;
  margin-left: 260px;
  transition: margin-left 0.3s ease;
}

.sidebar.collapsed + .main {
  margin-left: 70px;
}

.header {
  background-color: #fff;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.content {
  padding: 24px;
}

/* 暗色模式 */
.dark .admin-layout {
  background-color: #1a1a2e;
}

.dark .header {
  background-color: #2a2a3a;
  border-bottom: 1px solid #3a3a4a;
}

.dark .page-title {
  color: #eee;
}

.dark .user-info {
  color: #aaa;
}

@media (max-width: 768px) {
  .sidebar {
    width: 200px;
  }

  .main {
    margin-left: 200px;
  }
}
</style>