<template>
  <div class="settings-page">
    <!-- 系统设置 -->
    <div class="setting-card">
      <h3>系统设置</h3>
      <div class="setting-item">
        <div class="setting-label">
          <span>服务端口</span>
          <var-tooltip content="修改后需要重启服务生效">
            <var-icon name="help-circle" />
          </var-tooltip>
        </div>
        <div class="setting-value">
          <var-input v-model="settings.port" type="number" style="width: 120px" />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">最大上传大小 (MB)</div>
        <div class="setting-value">
          <var-input v-model="settings.maxUploadSize" type="number" style="width: 120px" />
          <span class="unit">MB</span>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">允许的文件类型</div>
        <div class="setting-value">
          <var-input
            v-model="settings.allowedExtensions"
            placeholder="用逗号分隔，例如: .txt,.pdf,.jpg"
            style="width: 300px"
          />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">启动时自动打开浏览器</div>
        <div class="setting-value">
          <var-switch v-model="settings.autoOpenBrowser" />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">调试模式</div>
        <div class="setting-value">
          <var-switch v-model="settings.debug" />
          <var-tooltip content="开启后输出详细日志，生产环境建议关闭">
            <var-icon name="help-circle" />
          </var-tooltip>
        </div>
      </div>

      <div class="setting-actions">
        <var-button type="primary" :loading="saving" @click="saveSettings">
          保存设置
        </var-button>
        <var-button @click="resetSettings">重置</var-button>
      </div>
    </div>

    <!-- 日志设置 -->
    <div class="setting-card">
      <h3>日志设置</h3>
      <div class="setting-item">
        <div class="setting-label">日志级别</div>
        <div class="setting-value">
          <var-select
            v-model="logSettings.level"
            :options="logLevels"
            style="width: 150px"
          />
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">日志保留天数</div>
        <div class="setting-value">
          <var-input v-model="logSettings.retentionDays" type="number" style="width: 100px" />
          <span class="unit">天</span>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label">单个日志文件大小</div>
        <div class="setting-value">
          <var-input v-model="logSettings.maxFileSize" type="number" style="width: 100px" />
          <span class="unit">MB</span>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <div class="setting-card">
      <h3>关于</h3>
      <div class="about-content">
        <div class="logo">
          <var-icon name="flash" :size="48" color="#3f51b5" />
          <h2>AuroraShare</h2>
          <p>极光共享 · 现代化文件共享系统</p>
        </div>

        <div class="info">
          <div class="info-item">
            <span class="label">版本</span>
            <span class="value">v2.0.0</span>
          </div>
          <div class="info-item">
            <span class="label">后端框架</span>
            <span class="value">FastAPI</span>
          </div>
          <div class="info-item">
            <span class="label">前端框架</span>
            <span class="value">Vue 3 + Varlet</span>
          </div>
          <div class="info-item">
            <span class="label">开源协议</span>
            <span class="value">MIT</span>
          </div>
        </div>

        <div class="links">
          <var-button text @click="openLink('https://github.com/liu17y/file_share')">
            <var-icon name="github" /> GitHub
          </var-button>
          <var-button text @click="openLink('https://gitee.com/Liuzongyi-liu/file-share')">
            <var-icon name="gitee" /> Gitee
          </var-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Snackbar } from '@varlet/ui'

const saving = ref(false)

const settings = ref({
  port: 8000,
  maxUploadSize: 1024,
  allowedExtensions: '.txt,.pdf,.png,.jpg,.jpeg,.gif,.mp4,.mp3,.doc,.docx,.zip',
  autoOpenBrowser: true,
  debug: false
})

const logSettings = ref({
  level: 'INFO',
  retentionDays: 30,
  maxFileSize: 10
})

const logLevels = [
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' }
]

const loadSettings = async () => {
  try {
    const res = await fetch('/api/settings')
    if (res.ok) {
      const data = await res.json()
      settings.value = { ...settings.value, ...data }
    }
  } catch (error) {
    console.error('加载设置失败', error)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings.value)
    })

    if (res.ok) {
      Snackbar.success('设置保存成功')
    } else {
      Snackbar.error('保存失败')
    }
  } catch (error) {
    Snackbar.error('保存失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = () => {
  settings.value = {
    port: 8000,
    maxUploadSize: 1024,
    allowedExtensions: '.txt,.pdf,.png,.jpg,.jpeg,.gif,.mp4,.mp3,.doc,.docx,.zip',
    autoOpenBrowser: true,
    debug: false
  }
  Snackbar.info('已重置为默认设置')
}

const openLink = (url) => {
  window.open(url, '_blank')
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-page {
  animation: fadeIn 0.3s ease;
}

.setting-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.setting-card h3 {
  margin-bottom: 20px;
  font-size: 16px;
  color: #666;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.setting-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unit {
  color: #999;
  font-size: 12px;
}

.setting-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.about-content {
  text-align: center;
  padding: 20px;
}

.logo {
  margin-bottom: 24px;
}

.logo h2 {
  margin: 12px 0 4px;
  color: #333;
}

.logo p {
  color: #999;
}

.info {
  margin: 24px 0;
  text-align: left;
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
}

.info-item .label {
  color: #999;
}

.info-item .value {
  color: #333;
  font-weight: 500;
}

.links {
  display: flex;
  justify-content: center;
  gap: 16px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>