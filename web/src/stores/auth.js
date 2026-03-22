// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || null)
  const adminInfo = ref(JSON.parse(localStorage.getItem('admin_info') || 'null'))

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
        throw new Error(data.detail || data.error || '登录失败')
      }

      if (data.success && data.token) {
        token.value = data.token
        adminInfo.value = data.admin

        localStorage.setItem('admin_token', data.token)
        localStorage.setItem('admin_info', JSON.stringify(data.admin))

        console.log('[Auth] 登录成功，token已保存')
        return { success: true }
      } else {
        throw new Error(data.detail || '登录失败')
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
      return response.ok
    } catch {
      return false
    }
  }

  return {
    token,
    adminInfo,
    isAuthenticated,
    login,
    logout,
    verifyToken
  }
})