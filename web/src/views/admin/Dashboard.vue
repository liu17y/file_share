<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon file">
          <var-icon name="file" :size="32" />
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalFiles || 0 }}</div>
          <div class="stat-label">文件总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon folder">
          <var-icon name="folder" :size="32" />
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalFolders || 0 }}</div>
          <div class="stat-label">文件夹总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon size">
          <var-icon name="storage" :size="32" />
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatSize(stats.totalSize || 0) }}</div>
          <div class="stat-label">总存储量</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon upload">
          <var-icon name="upload" :size="32" />
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.todayUploads || 0 }}</div>
          <div class="stat-label">今日上传</div>
        </div>
      </div>
    </div>

    <!-- 存储使用图表 -->
    <div class="chart-card">
      <h3>存储使用情况</h3>
      <div ref="storageChart" class="chart"></div>
    </div>

    <!-- 近7天上传趋势 -->
    <div class="chart-card">
      <h3>近7天上传趋势</h3>
      <div ref="trendChart" class="chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { storageApi, systemApi } from '@/api'
import { Snackbar } from '@varlet/ui'

const storageChart = ref(null)
const trendChart = ref(null)
let storageChartInstance = null
let trendChartInstance = null

const stats = ref({
  totalFiles: 0,
  totalFolders: 0,
  totalSize: 0,
  todayUploads: 0
})

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 加载存储信息
const loadStorageInfo = async () => {
  try {
    const res = await storageApi.getStorageInfo()
    if (res) {
      renderStorageChart(res)
      stats.value.totalSize = res.total || 0
      // 使用 /api/storage 端点返回的正确文件数量和文件夹数量
      stats.value.totalFiles = res.file_count || 0
      stats.value.totalFolders = res.folder_count || 0
    }
  } catch (error) {
    console.error('加载存储信息失败', error)
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const res = await systemApi.getStats()
    if (res) {
      stats.value.totalFiles = res.totalFiles || 0
      stats.value.totalFolders = res.totalFolders || 0
      stats.value.todayUploads = res.todayUploads || 0
      renderTrendChart(res.trendData || generateMockTrendData())
    }
  } catch (error) {
    console.error('加载统计数据失败', error)
    // 使用模拟数据
    renderTrendChart(generateMockTrendData())
  }
}

// 生成模拟趋势数据
const generateMockTrendData = () => {
  const dates = []
  const counts = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
    counts.push(Math.floor(Math.random() * 50) + 10)
  }
  return dates.map((date, index) => ({ date, count: counts[index] }))
}

// 渲染存储图表
const renderStorageChart = (data) => {
  if (!storageChart.value) return

  if (!storageChartInstance) {
    storageChartInstance = echarts.init(storageChart.value)
  }

  const total = data.disk_total || data.total || 100
  const used = data.used || 0
  const free = total - used

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
          { value: (used / (1024 ** 3)).toFixed(2), name: '已使用', itemStyle: { color: '#3f51b5' } },
          { value: (free / (1024 ** 3)).toFixed(2), name: '剩余', itemStyle: { color: '#4caf50' } }
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

// 渲染趋势图表
const renderTrendChart = (data) => {
  if (!trendChart.value) return

  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date),
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: '上传量'
    },
    series: [
      {
        name: '上传量',
        type: 'bar',
        data: data.map(d => d.count),
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: '#3f51b5'
        }
      }
    ]
  })
}

// 窗口大小适配
const handleResize = () => {
  storageChartInstance?.resize()
  trendChartInstance?.resize()
}

onMounted(() => {
  loadStorageInfo()
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  storageChartInstance?.dispose()
  trendChartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
  animation: fadeIn 0.3s ease;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.file { background-color: #e3f2fd; color: #2196f3; }
.stat-icon.folder { background-color: #fff3e0; color: #ff9800; }
.stat-icon.size { background-color: #e8f5e9; color: #4caf50; }
.stat-icon.upload { background-color: #f3e5f5; color: #9c27b0; }

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>