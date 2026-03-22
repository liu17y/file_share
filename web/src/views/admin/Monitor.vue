<template>
  <div class="monitor-page">
    <!-- 实时指标 -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-title">CPU 使用率</div>
        <div class="metric-value">
          <var-progress
            :percentage="cpuUsage"
            :color="getProgressColor(cpuUsage)"
          />
          <span class="value-text">{{ cpuUsage }}%</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-title">内存使用率</div>
        <div class="metric-value">
          <var-progress
            :percentage="memoryUsage"
            :color="getProgressColor(memoryUsage)"
          />
          <span class="value-text">{{ memoryUsage }}%</span>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-title">磁盘使用率</div>
        <div class="metric-value">
          <var-progress
            :percentage="diskUsage"
            :color="getProgressColor(diskUsage)"
          />
          <span class="value-text">{{ diskUsage }}%</span>
        </div>
      </div>
    </div>

    <!-- 实时图表 -->
    <div class="chart-card">
      <div class="chart-header">
        <h3>实时资源监控</h3>
        <var-radio-group v-model="chartInterval" type="button" size="small">
          <var-radio value="1m">1分钟</var-radio>
          <var-radio value="5m">5分钟</var-radio>
          <var-radio value="15m">15分钟</var-radio>
        </var-radio-group>
      </div>
      <div ref="monitorChart" class="chart"></div>
    </div>

    <!-- 当前连接 -->
    <div class="connections-card">
      <h3>当前活跃连接</h3>
      <var-table :data="connections" class="connection-table">
        <var-table-column title="IP地址" key="ip" />
        <var-table-column title="连接时间" key="time">
          <template #cell="{ row }">
            {{ formatTime(row.time) }}
          </template>
        </var-table-column>
        <var-table-column title="请求路径" key="path" />
        <var-table-column title="状态" key="status">
          <template #cell="{ row }">
            <var-tag :type="row.status === 'active' ? 'success' : 'warning'" size="small">
              {{ row.status === 'active' ? '活跃' : '等待' }}
            </var-tag>
          </template>
        </var-table-column>
      </var-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { systemApi } from '@/api'

const cpuUsage = ref(0)
const memoryUsage = ref(0)
const diskUsage = ref(0)
const connections = ref([])
const chartInterval = ref('1m')
const monitorChart = ref(null)
let monitorChartInstance = null
let timer = null
let chartData = {
  cpu: [],
  memory: [],
  disk: [],
  time: []
}

const getProgressColor = (value) => {
  if (value < 50) return '#4caf50'
  if (value < 80) return '#ff9800'
  return '#f44336'
}

const formatTime = (time) => {
  return new Date(time).toLocaleTimeString('zh-CN')
}

const loadMetrics = async () => {
  try {
    const res = await systemApi.getStats()
    if (res.metrics) {
      cpuUsage.value = Math.round(res.metrics.cpu || 0)
      memoryUsage.value = Math.round(res.metrics.memory || 0)
      diskUsage.value = Math.round(res.metrics.disk || 0)

      // 更新图表数据
      const now = new Date().toLocaleTimeString('zh-CN')
      chartData.time.push(now)
      chartData.cpu.push(cpuUsage.value)
      chartData.memory.push(memoryUsage.value)
      chartData.disk.push(diskUsage.value)

      // 限制数据量
      const maxPoints = chartInterval.value === '1m' ? 60 :
                        chartInterval.value === '5m' ? 30 : 15
      if (chartData.time.length > maxPoints) {
        chartData.time.shift()
        chartData.cpu.shift()
        chartData.memory.shift()
        chartData.disk.shift()
      }

      updateChart()
    }
  } catch (error) {
    console.error('加载监控数据失败', error)
  }
}

// SSE 连接
let eventSource = null

const connectSSE = () => {
  const token = localStorage.getItem('admin_token')
  if (!token) return

  const url = systemApi.getMonitorStream()
  eventSource = new EventSource(url + '?token=' + encodeURIComponent(token))

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      cpuUsage.value = Math.round(data.cpu || 0)
      memoryUsage.value = Math.round(data.memory || 0)
      diskUsage.value = Math.round(data.disk || 0)

      // 更新图表数据
      const now = new Date().toLocaleTimeString('zh-CN')
      chartData.time.push(now)
      chartData.cpu.push(cpuUsage.value)
      chartData.memory.push(memoryUsage.value)
      chartData.disk.push(diskUsage.value)

      // 限制数据量
      const maxPoints = chartInterval.value === '1m' ? 60 :
                        chartInterval.value === '5m' ? 30 : 15
      if (chartData.time.length > maxPoints) {
        chartData.time.shift()
        chartData.cpu.shift()
        chartData.memory.shift()
        chartData.disk.shift()
      }

      updateChart()
    } catch (e) {
      console.error('解析监控数据失败', e)
    }
  }

  eventSource.onerror = () => {
    console.error('SSE 连接错误')
    eventSource.close()
    setTimeout(connectSSE, 5000)
  }
}

const updateChart = () => {
  if (!monitorChartInstance) return

  monitorChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['CPU', '内存', '磁盘']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.time,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '使用率 (%)',
      min: 0,
      max: 100
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        data: chartData.cpu,
        smooth: true,
        lineStyle: { color: '#f44336' },
        areaStyle: { opacity: 0.1 }
      },
      {
        name: '内存',
        type: 'line',
        data: chartData.memory,
        smooth: true,
        lineStyle: { color: '#4caf50' },
        areaStyle: { opacity: 0.1 }
      },
      {
        name: '磁盘',
        type: 'line',
        data: chartData.disk,
        smooth: true,
        lineStyle: { color: '#2196f3' },
        areaStyle: { opacity: 0.1 }
      }
    ]
  })
}

const initChart = () => {
  if (!monitorChart.value) return
  monitorChartInstance = echarts.init(monitorChart.value)
  updateChart()
}

onMounted(() => {
  initChart()
  loadMetrics()
  connectSSE()
  window.addEventListener('resize', () => monitorChartInstance?.resize())
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (eventSource) {
    eventSource.close()
  }
  monitorChartInstance?.dispose()
})
</script>

<style scoped>
.monitor-page {
  animation: fadeIn 0.3s ease;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.metric-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.metric-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
}

.metric-value {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-value .var-progress {
  flex: 1;
}

.value-text {
  font-size: 18px;
  font-weight: bold;
  min-width: 50px;
}

.chart-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  font-size: 16px;
  color: #666;
}

.chart {
  height: 300px;
  width: 100%;
}

.connections-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.connections-card h3 {
  margin-bottom: 16px;
  font-size: 16px;
  color: #666;
}

.connection-table {
  width: 100%;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>