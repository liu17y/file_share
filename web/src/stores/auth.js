// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 修复：安全地获取和解析 localStorage 数据
  const getToken = () => {
    try {
      const storedToken = localStorage.getItem('admin_token')
      return storedToken && storedToken !== 'undefined' ? storedToken : null
    } catch (error) {
      console.error('[Auth] 读取token失败:', error)
      return null
    }
  }

  const getAdminInfo = () => {
    try {
      const storedInfo = localStorage.getItem('admin_info')
      if (storedInfo && storedInfo !== 'undefined' && storedInfo !== 'null') {
        return JSON.parse(storedInfo)
      }
      return null
    } catch (error) {
      console.error('[Auth] 解析admin_info失败:', error)
      return null
    }
  }

  const token = ref(getToken())
  const adminInfo = ref(getAdminInfo())

  const isAuthenticated = computed(() => !!token.value)

  const login = async (username, password) => {
    try {
      console.log('[Auth] 发送登录请求:', username)

      const response = await fetch('/api/admin/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      console.log('[Auth] 响应状态:', response.status)

      const data = await response.json()
      console.log('[Auth] 响应数据:', data)

      if (!response.ok) {
        // 处理不同的错误响应格式
        const errorMsg = data.detail || data.error || '登录失败'
        throw new Error(errorMsg)
      }

      // 检查响应格式
      if (data.success && data.token) {
        // 构建管理员信息对象
        const adminData = {
          username: data.username || username,
          expire: data.expire,
          loginTime: Date.now()
        }

        token.value = data.token
        adminInfo.value = adminData

        // 存储到 localStorage
        localStorage.setItem('admin_token', data.token)
        localStorage.setItem('admin_info', JSON.stringify(adminData))

        console.log('[Auth] 登录成功，token已保存')
        return { success: true }
      } else {
        // 如果后端没有返回 success 字段，但返回了 token
        if (data.token) {
          const adminData = {
            username: data.username || username,
            expire: data.expire,
            loginTime: Date.now()
          }

          token.value = data.token
          adminInfo.value = adminData

          localStorage.setItem('admin_token', data.token)
          localStorage.setItem('admin_info', JSON.stringify(adminData))

          console.log('[Auth] 登录成功（兼容模式），token已保存')
          return { success: true }
        }

        throw new Error(data.message || data.error || '登录失败')
      }
    } catch (error) {
      console.error('[Auth] 登录错误:', error)
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    console.log('[Auth] 执行登出，清除本地数据')

    // 清除所有本地存储
    token.value = null
    adminInfo.value = null

    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_info')

    // 可选：清除 sessionStorage
    sessionStorage.clear()

    console.log('[Auth] 登出完成，本地数据已清除')
  }

  const verifyToken = async () => {
    if (!token.value) return false

    try {
      const response = await fetch('/api/admin/verify', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        return data.valid === true
      }
      return false
    } catch (error) {
      console.error('[Auth] 验证token失败:', error)
      return false
    }
  }

  // 添加一个初始化函数，可以在应用启动时调用
  const initAuth = () => {
    console.log('[Auth] 初始化认证状态')
    console.log('[Auth] Token存在:', !!token.value)
    console.log('[Auth] AdminInfo存在:', !!adminInfo.value)

    // 如果 token 存在但 adminInfo 不存在，尝试修复
    if (token.value && !adminInfo.value) {
      console.warn('[Auth] Token存在但adminInfo缺失，尝试修复')
      adminInfo.value = {
        username: 'admin',
        expire: Date.now() + 86400000,
        loginTime: Date.now()
      }
      localStorage.setItem('admin_info', JSON.stringify(adminInfo.value))
    }
  }

  return {
    token,
    adminInfo,
    isAuthenticated,
    login,
    logout,
    verifyToken,
    initAuth
  }
})