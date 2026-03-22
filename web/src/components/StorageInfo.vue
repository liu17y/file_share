<template>
  <div class="storage-info">
    <div class="info-header">
      <var-icon name="storage" />
      <span>存储空间</span>
    </div>
    <div class="info-content">
      <div class="progress">
        <div
          class="progress-fill"
          :style="{ width: info.percentage + '%' }"
          :class="getProgressClass(info.percentage)"
        ></div>
      </div>
      <div class="stats">
        <div class="stat">
          <span class="label">已用</span>
          <span class="value">{{ info.used_gb || 0 }} GB</span>
        </div>
        <div class="stat">
          <span class="label">剩余</span>
          <span class="value">{{ info.free_gb || 0 }} GB</span>
        </div>
        <div class="stat">
          <span class="label">总容量</span>
          <span class="value">{{ info.total_gb || 0 }} GB</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { storageApi } from '@/api'

const info = ref({
  used_gb: 0,
  free_gb: 0,
  total_gb: 0,
  percentage: 0
})

let eventSource = null

const getProgressClass = (percentage) => {
  if (percentage < 50) return 'success'
  if (percentage < 80) return 'warning'
  return 'danger'
}

const connectSSE = () => {
  const url = storageApi.getStorageStream()
  eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    info.value = data
  }

  eventSource.onerror = () => {
    setTimeout(connectSSE, 5000)
  }
}

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>

<style scoped>
.storage-info {
  background-color: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.dark .storage-info {
  background-color: #2a2a3a;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 500;
}

.progress {
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.success { background-color: #4caf50; }
.progress-fill.warning { background-color: #ff9800; }
.progress-fill.danger { background-color: #f44336; }

.stats {
  display: flex;
  justify-content: space-between;
}

.stat {
  text-align: center;
}

.stat .label {
  display: block;
  font-size: 12px;
  color: #999;
}

.stat .value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.dark .stat .value {
  color: #eee;
}
</style>