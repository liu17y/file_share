<!-- src/views/admin/Login.vue -->
<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo">
        <var-icon name="flash" :size="48" color="#3f51b5" />
        <h1>AuroraShare</h1>
        <p>极光共享 · 管理后台</p>
      </div>

      <div class="login-form">
        <div class="input-wrapper">
          <var-icon name="account" class="input-icon" />
          <input
            v-model="form.username"
            class="login-input"
            placeholder="用户名"
            @keyup.enter="handleLogin"
          />
        </div>

        <div class="input-wrapper">
          <var-icon name="lock" class="input-icon" />
          <input
            v-model="form.password"
            type="password"
            class="login-input"
            placeholder="密码"
            @keyup.enter="handleLogin"
          />
        </div>

        <button
          class="login-button"
          :class="{ 'login-button--loading': loading }"
          :disabled="loading"
          @click="handleLogin"
        >
          <span v-if="loading" class="spinner"></span>
          <span v-else>登录</span>
        </button>
      </div>

<!--      <div class="tips">-->
<!--        <p>默认账号: admin</p>-->
<!--        <p>默认密码: admin123</p>-->
<!--      </div>-->

      <div class="back-link" @click="goBack">
        <var-icon name="arrow-left" /> 返回首页
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Snackbar } from '@varlet/ui'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const form = ref({
  username: 'admin',
  password: 'admin123'
})

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    Snackbar.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  console.log('[登录] 开始登录:', form.value.username)

  try {
    const result = await authStore.login(form.value.username, form.value.password)
    console.log('[登录] 登录结果:', result)

    if (result.success) {
      Snackbar.success('登录成功')
      console.log('[登录] 跳转到仪表盘')
      // 使用 replace 避免返回登录页
      router.replace('/admin/dashboard')
    } else {
      Snackbar.error(result.error || '登录失败')
    }
  } catch (error) {
    console.error('[登录] 错误:', error)
    Snackbar.error(error.message || '登录失败，请检查网络')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  background-color: #fff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.logo {
  text-align: center;
  margin-bottom: 32px;
}

.logo h1 {
  margin: 12px 0 4px;
  color: #333;
}

.logo p {
  color: #999;
  font-size: 14px;
}

.login-form {
  margin-bottom: 24px;
}

.input-wrapper {
  position: relative;
  margin-bottom: 20px;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  font-size: 20px;
}

.login-input {
  width: 100%;
  padding: 12px 12px 12px 40px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.login-input:focus {
  outline: none;
  border-color: #3f51b5;
  box-shadow: 0 0 0 2px rgba(63, 81, 181, 0.1);
}

.login-button {
  width: 100%;
  padding: 12px;
  background-color: #3f51b5;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.login-button:hover {
  background-color: #303f9f;
}

.login-button--loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tips {
  text-align: center;
  margin-bottom: 20px;
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 8px;
  font-size: 12px;
  color: #666;
}

.tips p {
  margin: 4px 0;
}

.back-link {
  text-align: center;
  color: #3f51b5;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  justify-content: center;
}

.back-link:hover {
  text-decoration: underline;
}
</style>