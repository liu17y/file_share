<template>
  <div class="storage-page">
    <!-- 存储信息卡片 -->
    <div class="info-card">
      <h3>存储信息</h3>
      <div class="storage-info">
        <div class="info-row">
          <span class="label">存储路径</span>
          <span class="value">{{ storageInfo.storage_path || '-' }}</span>
          <var-button size="small" @click="showPathDialog = true">
            <var-icon name="edit" /> 修改
          </var-button>
        </div>

        <div class="info-row">
          <span class="label">磁盘总空间</span>
          <span class="value">{{ storageInfo.total_gb || 0 }} GB</span>
        </div>

        <div class="info-row">
          <span class="label">已用空间</span>
          <span class="value">{{ storageInfo.used_gb || 0 }} GB</span>
        </div>

        <div class="info-row">
          <span class="label">剩余空间</span>
          <span class="value">{{ storageInfo.free_gb || 0 }} GB</span>
        </div>

        <div class="info-row">
          <span class="label">使用率</span>
          <span class="value">{{ storageInfo.percentage || 0 }}%</span>
        </div>

        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (storageInfo.percentage || 0) + '%' }"
            :class="getProgressClass(storageInfo.percentage)"
          ></div>
        </div>

        <div class="info-row">
          <span class="label">文件数量</span>
          <span class="value">{{ storageInfo.file_count || 0 }}</span>
        </div>

        <div class="info-row">
          <span class="label">文件夹数量</span>
          <span class="value">{{ storageInfo.folder_count || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 存储图表 -->
    <div class="chart-card">
      <h3>磁盘使用分布</h3>
      <div ref="storageChart" class="chart"></div>
    </div>

    <!-- 文件类型统计 -->
    <div class="chart-card">
      <h3>文件类型统计</h3>
      <div ref="typeChart" class="chart"></div>
    </div>

    <!-- 修改存储路径弹窗 -->
    <var-popup v-model:show="showPathDialog" position="center">
      <div class="path-dialog">
        <h3>修改存储路径</h3>
        <var-input
          v-model="newPath"
          placeholder="请输入新的存储路径 (绝对路径)"
          textarea
          rows="2"
        />
        <div class="tip">
          <var-icon name="info" />
          例如: D:\shared_files 或 /mnt/data/files
        </div>
        <div class="dialog-actions">
          <var-button @click="showPathDialog = false">取消</var-button>
          <var-button type="primary" :loading="updating" @click="updatePath">
            确定修改
          </var-button>
        </div>
      </div>
    </var-popup>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { storageApi } from '@/api'
import { Snackbar } from '@varlet/ui'

const storageInfo = ref({})
const showPathDialog = ref(false)
const newPath = ref('')
const updating = ref(false)

const storageChart = ref(null)
const typeChart = ref(null)
let storageChartInstance = null
let typeChartInstance = null
let eventSource = null

const getProgressClass = (percentage) => {
  if (percentage < 50) return 'success'
  if (percentage < 80) return 'warning'
  return 'danger'
}

const loadStorageInfo = async () => {
  try {
    const res = await storageApi.getStorageInfo()
    storageInfo.value = res
    renderStorageChart(res)
  } catch (error) {
    console.error('加载存储信息失败', error)
  }
}

const loadTypeStats = async () => {
  try {
    // 模拟数据，实际应从后端获取
    const mockData = [
      { type: '图片', count: 45, size: 2.3 },
      { type: '视频', count: 12, size: 15.6 },
      { type: '音频', count: 28, size: 1.2 },
      { type: '文档', count: 67, size: 0.8 },
      { type: '压缩包', count: 23, size: 5.4 },
      { type: '其他', count: 34, size: 1.5 }
    ]
    renderTypeChart(mockData)
  } catch (error) {
    console.error('加载类型统计失败', error)
  }
}

const renderStorageChart = (data) => {
  if (!storageChart.value) return

  if (!storageChartInstance) {
    storageChartInstance = echarts.init(storageChart.value)
  }

  const total = data.disk_total || data.total || 0
  const used = data.used || 0
  const free = data.free || 0

  storageChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {d}% ({c} GB)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: ['已使用', '剩余']
    },
    series: [
      {
        name: '存储空间',
        type: 'pie',
        radius: '55%',
        center: ['50%', '50%'],
        data: [
          { value: used / (1024 ** 3), name: '已使用', itemStyle: { color: '#3f51b5' } },
          { value: free / (1024 ** 3), name: '剩余', itemStyle: { color: '#4caf50' } }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

const renderTypeChart = (data) => {
  if (!typeChart.value) return

  if (!typeChartInstance) {
    typeChartInstance = echarts.init(typeChart.value)
  }

  typeChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 个文件 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      data: data.map(d => d.type)
    },
    series: [
      {
        name: '文件类型',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: data.map(d => ({ name: d.type, value: d.count })),
        label: {
          show: true,
          formatter: '{b}: {d}%'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

const updatePath = async () => {
  if (!newPath.value.trim()) {
    Snackbar.warning('请输入存储路径')
    return
  }

  updating.value = true
  try {
    const res = await storageApi.updateStoragePath(newPath.value)
    if (res.success) {
      Snackbar.success('存储路径修改成功')
      showPathDialog.value = false
      loadStorageInfo()
    } else {
      Snackbar.error(res.error || '修改失败')
    }
  } catch (error) {
    Snackbar.error('修改存储路径失败')
  } finally {
    updating.value = false
  }
}

// SSE 实时更新
const connectSSE = () => {
  const url = storageApi.getStorageStream()
  eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    storageInfo.value = data
    renderStorageChart(data)
  }

  eventSource.onerror = () => {
    console.error('SSE 连接错误')
    setTimeout(connectSSE, 5000)
  }
}

onMounted(() => {
  loadStorageInfo()
  loadTypeStats()
  connectSSE()
  window.addEventListener('resize', () => {
    storageChartInstance?.resize()
    typeChartInstance?.resize()
  })
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
  storageChartInstance?.dispose()
  typeChartInstance?.dispose()
})
</script>

<style scoped>
.storage-page {
  animation: fadeIn 0.3s ease;
}

.info-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.info-card h3 {
  margin-bottom: 20px;
  font-size: 16px;
  color: #666;
}

.storage-info {
  max-width: 500px;
}

.info-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.info-row .label {
  width: 100px;
  color: #999;
}

.info-row .value {
  flex: 1;
  color: #333;
  font-weight: 500;
}

.progress-bar {
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  margin: 16px 0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.success { background-color: #4caf50; }
.progress-fill.warning { background-color: #ff9800; }
.progress-fill.danger { background-color: #f44336; }

.chart-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.chart-card h3 {
  margin-bottom: 20px;
  font-size: 16px;
  color: #666;
}

.chart {
  height: 300px;
  width: 100%;
}

.path-dialog {
  width: 500px;
  max-width: 90vw;
  padding: 24px;
}

.path-dialog h3 {
  margin-bottom: 20px;
  text-align: center;
}

.tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 8px;
  font-size: 12px;
  color: #999;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>