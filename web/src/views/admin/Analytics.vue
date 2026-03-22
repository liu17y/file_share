<template>
  <div class="analytics-page">
    <!-- 关键指标 -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value">{{ formatNumber(totalViews) }}</div>
        <div class="kpi-label">总访问量</div>
        <div class="kpi-trend up">{{ viewTrend }}%</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-value">{{ formatNumber(totalDownloads) }}</div>
        <div class="kpi-label">总下载量</div>
        <div class="kpi-trend up">{{ downloadTrend }}%</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-value">{{ formatSize(totalTransfer) }}</div>
        <div class="kpi-label">总传输量</div>
        <div class="kpi-trend up">{{ transferTrend }}%</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-value">{{ activeUsers }}</div>
        <div class="kpi-label">活跃用户</div>
        <div class="kpi-trend">{{ userTrend }}%</div>
      </div>
    </div>

    <!-- 访问趋势 -->
    <div class="chart-card">
      <div class="chart-header">
        <h3>访问趋势</h3>
        <var-radio-group v-model="trendPeriod" type="button" size="small">
          <var-radio value="week">近7天</var-radio>
          <var-radio value="month">近30天</var-radio>
        </var-radio-group>
      </div>
      <div ref="trendChart" class="chart"></div>
    </div>

    <!-- 热门文件 -->
    <div class="chart-card">
      <h3>热门文件排行</h3>
      <var-table :data="hotFiles" class="hot-table">
        <var-table-column title="排名" key="rank" width="80">
          <template #cell="{ index }">
            <span class="rank" :class="getRankClass(index)">
              {{ index + 1 }}
            </span>
          </template>
        </var-table-column>
        <var-table-column title="文件名" key="name" />
        <var-table-column title="下载次数" key="downloads" width="120" />
        <var-table-column title="文件大小" key="size" width="120">
          <template #cell="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </var-table-column>
      </var-table>
    </div>

    <!-- 文件类型分布 -->
    <div class="chart-card">
      <h3>文件类型分布</h3>
      <div ref="typeChart" class="chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { systemApi } from '@/api'

const totalViews = ref(0)
const totalDownloads = ref(0)
const totalTransfer = ref(0)
const activeUsers = ref(0)
const viewTrend = ref(0)
const downloadTrend = ref(0)
const transferTrend = ref(0)
const userTrend = ref(0)
const hotFiles = ref([])
const trendPeriod = ref('week')

const trendChart = ref(null)
const typeChart = ref(null)
let trendChartInstance = null
let typeChartInstance = null

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getRankClass = (index) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

const loadAnalytics = async () => {
  try {
    const res = await systemApi.getStats()
    if (res.analytics) {
      totalViews.value = res.analytics.totalViews || 0
      totalDownloads.value = res.analytics.totalDownloads || 0
      totalTransfer.value = res.analytics.totalTransfer || 0
      activeUsers.value = res.analytics.activeUsers || 0
      viewTrend.value = res.analytics.viewTrend || 0
      downloadTrend.value = res.analytics.downloadTrend || 0
      transferTrend.value = res.analytics.transferTrend || 0
      userTrend.value = res.analytics.userTrend || 0
      hotFiles.value = res.analytics.hotFiles || []
    }
  } catch (error) {
    console.error('加载分析数据失败', error)
  }
}

const loadTrendData = async () => {
  try {
    const res = await systemApi.getStats()
    if (res.trendData) {
      renderTrendChart(res.trendData)
    }
  } catch (error) {
    console.error('加载趋势数据失败', error)
  }
}

const loadTypeDistribution = async () => {
  try {
    const res = await systemApi.getStats()
    if (res.typeDistribution) {
      renderTypeChart(res.typeDistribution)
    }
  } catch (error) {
    console.error('加载类型分布失败', error)
  }
}

const renderTrendChart = (data) => {
  if (!trendChart.value) return

  if (!trendChartInstance) {
    trendChartInstance = echarts.init(trendChart.value)
  }

  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['访问量', '下载量']
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
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '次数'
    },
    series: [
      {
        name: '访问量',
        type: 'line',
        data: data.map(d => d.views),
        smooth: true,
        lineStyle: { color: '#3f51b5' },
        areaStyle: { opacity: 0.1 }
      },
      {
        name: '下载量',
        type: 'line',
        data: data.map(d => d.downloads),
        smooth: true,
        lineStyle: { color: '#ff9800' },
        areaStyle: { opacity: 0.1 }
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
      formatter: '{b}: {d}%'
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
        radius: '55%',
        center: ['50%', '50%'],
        data: data.map(d => ({ name: d.type, value: d.count })),
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

watch(trendPeriod, () => {
  loadTrendData()
})

onMounted(() => {
  loadAnalytics()
  loadTrendData()
  loadTypeDistribution()
  window.addEventListener('resize', () => {
    trendChartInstance?.resize()
    typeChartInstance?.resize()
  })
})
</script>

<style scoped>
.analytics-page {
  animation: fadeIn 0.3s ease;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.kpi-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s;
}

.kpi-card:hover {
  transform: translateY(-2px);
}

.kpi-value {
  font-size: 32px;
  font-weight: bold;
  color: #3f51b5;
  margin-bottom: 8px;
}

.kpi-label {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.kpi-trend {
  font-size: 12px;
}

.kpi-trend.up {
  color: #4caf50;
}

.kpi-trend.down {
  color: #f44336;
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

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart {
  height: 300px;
  width: 100%;
}

.hot-table {
  width: 100%;
}

.rank {
  display: inline-block;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  border-radius: 50%;
  background-color: #f5f5f5;
  font-weight: bold;
}

.rank-1 {
  background-color: #ffd700;
  color: #fff;
}

.rank-2 {
  background-color: #c0c0c0;
  color: #fff;
}

.rank-3 {
  background-color: #cd7f32;
  color: #fff;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>